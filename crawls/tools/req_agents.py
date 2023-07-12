import time
import random
from requests import get
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from crawls.constants import USERAGENT_LIST


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
        self.timeout = 5
        self.update_proxy()

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
            url =f"https://www.proxynova.com/proxy-server-list/country-{random.choice(['vn', 'us', 'fr', 'de', 'jp', 'cn', 'ru', 'gb', 'ca', 'au'])}/"
            resp = get(url=url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            table_proxies = soup.find("table", {"id": "tbl_proxy_list"})
            table_proxies = table_proxies.find("tbody").find_all("tr")
            for row in table_proxies:
                row = row.find_all("td")
                proxies.append({
                    "addr": row[0].text+":"+row[1].text,
                    "timeout": row[3].text.replace("ms", ""),
                })
        proxies = sorted(proxies, key=lambda x: x["timeout"])[:5]
        self.timeout = round(int(proxies[-1]["timeout"])/1000)+5
        self.proxies = [proxy["addr"] for proxy in proxies]

    def update_proxy(self):
        """
        Update proxy
        """
        self._crawl_proxy()

    def crawl_url(self, url, params):
        """
        Crawl url

        Args:
            url (str): url
            params (dict): params

        Returns:
            requests.Response
        """
        proxy = {"http": random.choice(self.proxies)}
        header = self.headers
        header["User-Agent"] = random.choice([random.choice(USERAGENT_LIST), self.ua.random])
        resp = get(
            url=url,
            headers=header,
            params=params,
            proxies=proxy,
            timeout=self.timeout,
        )
        if resp.status_code == 429:
            self.update_proxy()
            return self.crawl_url(url, params)
        resp.raise_for_status()
        return resp
