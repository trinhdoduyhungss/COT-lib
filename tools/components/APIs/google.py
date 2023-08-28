import re
import asyncio
from time import sleep
from rapidfuzz import fuzz
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Any, Text, Dict, Optional, List

from tools.components.LLMs.open_gpt import OpenGPTBot
from tools.components.APIs.libs.req_agents import CrawlUrl
from tools.components.APIs.libs.constants import SITE_BLOCKED
from tools.components.APIs.libs.text_processor import StringUtils

load_dotenv()

class Google:
    """Google search engine."""

    def __init__(self) -> None:
        """Initialize Google search engine."""
        self.req_agent = CrawlUrl()
        self.gpt = OpenGPTBot()

    async def query(self, q: str) -> Optional[Dict[str, Any]]:
        """Search for a query using Google search.

        Args:
            q: your query that you want to search.

        Returns:
            Results from Google search engine.
        """
        params = {
            "q": q,
            "num": 2,
            "hl": "vi"
        }
        start = 0
        delay = 0
        google_results = []
        while start < params["num"]:
            crawl_params = params.copy()
            crawl_params["start"] = start
            crawl_params["num"] = params["num"] - start
            resp = await self.req_agent.gettext("https://www.google.com/search", params=crawl_params)
            class_block = "g"
            if "ezO2md" in resp:
                # print("second block")
                class_block = "AS66f"
            soup = BeautifulSoup(resp, "html.parser")
            result_block = soup.find_all("div", attrs={"class": class_block})
            if len(result_block) == 0:
                start += 1
            for result in result_block:
                # Find link, title, description
                item_result = {}
                link = result.find("a", href=True)
                if link:
                    link_value = link["href"]
                    if link_value.startswith("/search?num="):
                        continue
                    if link_value.startswith("/url?"):
                        if "url=" in link_value:
                            link_value = link_value.split("url=")[1]
                        if "q=" in link_value:
                            link_value = link_value.split("q=")[1]
                    link_value = link_value.split("&")[0]
                    if [site for site in SITE_BLOCKED if site in link_value]:
                        continue
                    item_result["link"] = link_value
                title = result.find("h3")
                if title:
                    item_result["title"] = title.text
                if class_block == "g":
                    description_box = result.find("div", {"style": "-webkit-line-clamp:2"})
                else:
                    description_box = result.find("span", {"class": "fYyStc"})
                if description_box:
                    item_result["snippet"] = description_box.text
                google_results.append(item_result)
                start += 1
            sleep(delay)
        if google_results:
            return {"items": [google_results[0]]}
        return {"items": []}

    @staticmethod
    def search_engine_results(response_data: Optional[Dict[str, Any]]
                              ) -> Optional[List[Dict[str, str]]]:  # noqa: E501
        """Extract title, link and snippet data_old from the response.

        Args:
            response_data: Response data_old from Google search engine.

        Returns:
            A list of dict contains "title", "url" and "snippet" or None.
        """
        results: List[Dict[str, str]] = []
        if response_data is None:
            return None

        # items variable has type list of dict (list[dict[str, Any]])
        if items := response_data.get("items", False):
            for item in items:
                url: str = item.get("link", "Not found")
                if [site for site in SITE_BLOCKED if site in url]:
                    continue
                title: str = item.get("title", "Not found")
                snippet: str = item.get("snippet", "Not found")
                if snippet[0].isdigit():
                    if " — " in snippet:
                        snippet = snippet.split(" — ")[1]
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": StringUtils.normalize_res(snippet)
                })
            return results
        return None

    async def _fetch_react(self, url):
        raw = ""
        solution = "1"
        if solution == "1":
            url = f"http://webcache.googleusercontent.com/search?q=cache:{url}&prmd=ivn&strip=1&vwsrc=0"
            raw = await self.req_agent.gettext(url)
            if "Our systems have detected unusual traffic from your computer" in raw:
                print("Google block: ", url)
                raw = ""
                solution = "2"
        if solution == "2":
            url = f"https://archive.org/wayback/available?url={url}"
            raw = await self.req_agent.gettext(url)
            if raw.get("archived_snapshots"):
                url = raw["archived_snapshots"]["closest"]["url"]
                raw = await self.req_agent.gettext(url)
        return raw

    async def get_full_content(self, url, desc):
        raw_html = await self.req_agent.gettext(url)
        if '<div id="root">' in raw_html or "JavaScript to run" in raw_html:
            raw_html = await self._fetch_react(url)
        try:
            match = re.search(desc.replace("\"", '\\"').replace("(", "\\(") + ".*", raw_html)
            if match:
                desc = match.group()
        except Exception as e:
            # print(e)
            pass
        desc = StringUtils.clean_text(desc)
        desc = desc.split(".")
        desc = [des.strip(" ").capitalize() for des in desc if len(des) > 7]
        desc = ". ".join(desc[:-1]).strip(" ")
        if not desc.endswith("."):
            desc += "."
        return desc

    def ask(self, ques: Text):
        """
        Full pipeline query answer via Google Search

        Args:
            ques: Question

        Return:
            A dict contains "source" and "documents" content or None.
        """
        data_search = asyncio.run(self.query(ques))
        data_search = self.search_engine_results(data_search)
        if data_search:
            data_search = data_search[0]
            url = data_search["url"]
            desc = data_search["snippet"].replace(" · ", ", ")
            if "Not found" in desc:
                return None
            if "." in desc.replace("...", "").strip(" ")[-1]:
                relate = 100
                desc = desc.split(".")
                desc = [des.strip(" ").capitalize() for des in desc]
                desc = ". ".join(desc).strip(" ")
            else:
                desc = asyncio.run(self.get_full_content(url, desc))
                relate = fuzz.ratio(desc, ques)
            print("\nques:", ques, "desc:", desc, "relate:", relate)
            if relate > 28 and len(desc) > 25:
                gpt_reponse = self.gpt.ask(ques+"? "+desc)
                print("gpt_reponse:", gpt_reponse)
                if gpt_reponse and "Tôi xin lỗi" not in gpt_reponse and "Please visit" not in gpt_reponse:
                    desc = gpt_reponse
                    data_search = {"metadatas": [{"source": url}], "documents": [desc]}
                else:
                    data_search = None
            else:
                data_search = None
        return data_search
