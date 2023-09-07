import time
import random
from bs4 import BeautifulSoup
from typing import Any, Text, Union
from fake_useragent import UserAgent
from requests import get, Response, request

from .constants import USERAGENT_LIST

class CrawlUrl:
    def __init__(self):
        """
        Crawl url without blocking
        """
        self.ua = UserAgent()
        self.headers = {
            "Accept": "*/*",
            "Referer": "https://www.google.com",
        }
        self.proxies = None
        self.timeout = 50
        self._update_proxy()

    def _crawl_proxy(self):
        """
        Crawl proxy
        """
        proxies = []
        try:
            url = f"https://checkerproxy.net/api/archive/{time.strftime('%Y-%m-%d')}"
            resp = get(url=url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            proxies = resp.json()
        except Exception as e:
            # print(e)
            url = f"""https://www.proxynova.com/proxy-server-list/country-{random.choice(['vn', 'us',
                                                                                          'fr', 'de',
                                                                                          'jp', 'cn',
                                                                                          'ru', 'gb',
                                                                                          'ca', 'au'])}/"""
            resp = get(url=url, headers=self.headers, timeout=self.timeout)
            soup = BeautifulSoup(resp.text, "html.parser")
            table_proxies = soup.find("table", {"id": "tbl_proxy_list"})
            table_proxies = table_proxies.find("tbody").find_all("tr")
            for row in table_proxies:
                row = row.find_all("td")
                proxies.append({
                    "addr": row[0].text + ":" + row[1].text,
                    "timeout": row[3].text.replace("ms", ""),
                })
        if not proxies:
            self.proxies = None
            return
        proxies = sorted(proxies, key=lambda x: x["timeout"])[:5]
        self.timeout = round(int(proxies[-1]["timeout"]) / 1000) + 5
        self.proxies = [proxy["addr"] for proxy in proxies]

    def _update_proxy(self):
        """
        Update proxy
        """
        self._crawl_proxy()

    async def crawl_url(self, url: Text, **kwargs) -> Union[Any, Response]:
        """
        Crawl url

        Args:
            url (str): url

        Returns:
            requests.Response
        """
        proxy = None
        if self.proxies:
            proxy = {"http": random.choice(self.proxies)}
        header = kwargs.get("headers", self.headers)
        header["User-Agent"] = random.choice([random.choice(USERAGENT_LIST), self.ua.random])
        timeout = kwargs.get("timeout", self.timeout)
        method = kwargs.get("method", "get")
        resp = request(
            method=method,
            url=url,
            headers=header,
            params=kwargs.get("params", None),
            data=kwargs.get("data", None),
            proxies=proxy if proxy else None,
            timeout=timeout,
            json=kwargs.get("json", None),
        )
        if resp.status_code == 429:
            self._update_proxy()
            return await self.crawl_url(url, **kwargs)
        resp.raise_for_status()
        return resp

    async def gettext(self, url: Text, **kwargs) -> Union[str, dict]:
        """
        Get text from url

        Args:
            url (str): url

        Returns:
            str: text from url
            json: json from url
        """
        resp = await self.crawl_url(url, **kwargs)
        if resp and resp.headers.get("Content-Type") == "application/json":
            return resp.json()
        return resp.text
