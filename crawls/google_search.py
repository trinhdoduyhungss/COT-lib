from time import sleep
from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, List

from crawls.tools.req_agents import CrawlUrl
from crawls.tools.vn_text_processor import StringUtils


class Google:
    """Google search engine."""
    def __init__(self) -> None:
        """Initialize Google search engine."""
        self.req_agent = CrawlUrl()

    def query(self, q: str) -> Optional[Dict[str, Any]]:
        """Search for a query using Google search.

        Args:
            key: Your Google API key.
            cx: Your Search Engine ID.
            hl: Set the user interface language.
            num: Number of search results to return.
            q: your query that you want to search.

        Returns:
            Results from Google search engine.
        """
        params = {
            "q": q,
            "num": 1,
            "hl": "vi"
        }
        start = 0
        delay = 0
        google_results = []
        while start < params["num"]:
            crawl_params = params.copy()
            crawl_params["start"] = start
            crawl_params["num"] = params["num"] - start
            resp = self.req_agent.crawl_url("https://www.google.com/search", crawl_params)
            soup = BeautifulSoup(resp.text, "html.parser")
            result_block = soup.find_all("div", attrs={"class": "g"})
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
                    item_result["link"] = link_value
                title = result.find("h3")
                if title:
                    item_result["title"] = title.text
                description_box = result.find("div", {"style": "-webkit-line-clamp:2"})
                if description_box:
                    item_result["snippet"] = description_box.text
                google_results.append(item_result)
                start += 1
            sleep(delay)
        return {"items": google_results}

    def search_engine_results(self, response_data: Optional[Dict[str, Any]]
                              ) -> Optional[List[Dict[str, str]]]:  # noqa: E501
        """Extract title, link and snippet data from the response.

        Args:
            response_data: Response data from Google search engine.

        Returns:
            A dict contains "title", "url" and "snippet" or None.
        """
        results: List[Dict[str, str]] = []
        if response_data is None:
            return None

        # items variable has type list of dict (list[dict[str, Any]])
        if items := response_data.get("items", False):
            for item in items:
                title: str = item.get("title", "Not found")
                url: str = item.get("link", "Not found")
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
