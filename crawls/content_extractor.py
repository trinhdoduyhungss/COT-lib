import re
import math
import random
import aiohttp
import asyncio
import pandas as pd
from bs4.element import Tag
from bs4 import BeautifulSoup
from fuzzywuzzy import process, fuzz
from typing import List, Text, Dict, Optional, Union
from crawls.constants import (
    COOKIE_LIST,
    USERAGENT_LIST,
    TAG_REMOVE,
    TAG_PARENT_EXTRACT,
    CLASS_REMOVE,
    CLASS_PRIORITIZE,
    REGEX_BREAK_PAR,
    REGEX_REMOVE_ADS,
    REGEX_CUT_ANSWER,
    REGEX_BREAK_LINE,
    REGEX_TEXT_REMOVE,
    REGEX_BREAK_BLOCK,
    REGEX_COMMAND_REMOVE,
    REGEX_TEXT_POST_REMOVE
)
from crawls.tools.req_agents import CrawlUrl
from crawls.tools.vn_text_processor import StringUtils
from crawls.tools.sentence_segment import SentenceSegment


def f(A, B):
    if A == 0 and B == 0:
        return 0
    else:
        try:
            return math.exp((math.log(A) + math.log(B)) - math.log(A + B))
        except ValueError:
            return 0


def recalculate_score(data: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate score for data crawled

    Args:
        data: data fuzzy matched

    Returns:
        pd.DataFrame: data crawled with new score
    """

    data['score'] = data.apply(lambda x: f(x['score'] / 100, len(x['text'])), axis=1)
    data = data.sort_values(by='score', ascending=False)
    return data


class ContentExtractor:
    def __init__(self):
        self.desc = ""
        self._html = None
        self._soup = None
        self.data = None
        self.tokenizer = SentenceSegment()

    @staticmethod
    def _clear_tag(tag: Tag) -> Tag:
        for t in tag.find_all(TAG_REMOVE):
            t.decompose()
        tags = tag.find_all(['div', 'p', 'ul', 'span', 'li'], attrs={"class": CLASS_REMOVE})
        for t in tags:
            t.decompose()
        return tag

    def _focus_area(self) -> Optional[Tag]:
        area_best = []
        _soup = BeautifulSoup(self._html, 'html.parser').find('body')
        list_suggest = _soup.find_all(["div"], attrs={"class": CLASS_PRIORITIZE})
        check_desc = False
        if not list_suggest:
            _soup = self._clear_tag(_soup)
            list_suggest = _soup.find_all(TAG_PARENT_EXTRACT, recursive=False)
            check_desc = True
        for tag in list_suggest:
            if self.desc not in tag.text and check_desc and self.desc:
                continue
            if not area_best:
                area_best.append(self._clear_tag(tag))
                area_best.append(len(re.findall("([a-z]|[A-Z])", tag.text)))
            else:
                if len(re.findall("([a-z]|[A-Z])", tag.text)) > area_best[1]:
                    area_best[0] = self._clear_tag(tag)
                    area_best[1] = len(re.findall("([a-z]|[A-Z])", tag.text))
        if area_best:
            return area_best[0]
        return _soup

    @staticmethod
    def _norm_text(text: Text, **kwargs) -> Text:
        text = StringUtils.normalize_res(html=text)
        ads = re.search(REGEX_REMOVE_ADS, text, re.DOTALL | re.IGNORECASE)
        if ads:
            text = text[:ads.start()] + text[ads.end():]
        text = re.sub(REGEX_REMOVE_ADS, '', text, re.DOTALL | re.IGNORECASE)
        text = re.sub(REGEX_TEXT_REMOVE, '', text, re.MULTILINE | re.IGNORECASE)
        text = re.sub(REGEX_COMMAND_REMOVE, '', text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        text = text.strip(' ')
        special_char = ''
        if text:
            special_char = ' ' if text[0].islower() or text.isnumeric() or kwargs.get('is_child', False) else '\n'
        return special_char + text

    def _extract(self) -> Optional[pd.DataFrame]:
        data = self._parse(self._soup)
        if not data:
            return None
        data = pd.DataFrame(data, columns=['text'])
        data['text'] = data['text'].str.strip()
        return data

    def _parse(self, tag: Tag, **kwargs) -> List[Text]:
        if tag is None:
            return []
        text = self._norm_text(tag.get_text(separator='\n', strip=True), **kwargs)
        if ']' not in text and '[' not in text and '|' not in text:
            focus_text = re.search(REGEX_CUT_ANSWER, text, re.MULTILINE | re.IGNORECASE)
            if focus_text:
                text = text[focus_text.start():]
        text = re.sub(REGEX_TEXT_POST_REMOVE, '', text, re.MULTILINE | re.IGNORECASE)
        paragraphs = re.split(REGEX_BREAK_BLOCK, text)
        if self.desc and len(paragraphs) > 1:
            df_paragraphs = pd.DataFrame(paragraphs, columns=['text'])
            df_paragraphs['text'] = df_paragraphs['text'].str.strip()
            df_paragraphs = df_paragraphs[df_paragraphs['text'].str.contains(self.desc, regex=False)]
            return df_paragraphs['text'].tolist()
        else:
            if self.desc:
                index = text.find(self.desc)
                if index != -1:
                    text = text[index:]
            paragraphs = re.split(REGEX_BREAK_LINE, text)
        sentences = []
        for par in paragraphs:
            try:
                seg = self.tokenizer.segment(par)
                if not seg:
                    seg = re.split(REGEX_BREAK_PAR, par)
            except Exception as e:
                # print(e)
                seg = re.split(REGEX_BREAK_PAR, par)
            sentences.extend(seg)
        if not sentences:
            return paragraphs
        return sentences

    @staticmethod
    async def _fetch_react(session, url: Text):
        raw = ""
        solution = "3"#random.choices(["1", "2", "3"], weights=[0.9, 0.8, 0.1])[0]
        # print("Solution: ", solution)
        if solution == "3":
            url = f"http://webcache.googleusercontent.com/search?q=cache:{url}&prmd=ivn&strip=1&vwsrc=0"
            resp = await session.get(url)
            raw = await resp.text()
            if "Our systems have detected unusual traffic from your computer" in raw:
                print("Google block: ", url)
                raw = ""
        if solution == "2":
            url = f"https://archive.org/wayback/available?url={url}"
            resp = await session.get(url)
            raw = await resp.json()
            if raw.get('archived_snapshots'):
                url = raw['archived_snapshots']['closest']['url']
                resp = await session.get(url)
                raw = await resp.text()
            else:
                solution = "3"
        if solution == "1":
            url += ".html"
            resp = await session.get(url)
            raw = await resp.text()
        return raw

    async def fetch_and_update(self, session, url: Text, desc: Text):
        resp = await session.get(url)
        self._html = await resp.text()
        # check if page is js page
        # if '<div id="root">' in self._html or "JavaScript to run" in self._html:
        self._html = await self._fetch_react(session, url)
        self.desc = desc
        self._soup = self._focus_area()
        self.data = self._extract()


class PipelineExtractor:
    def __init__(self, ques: Text, data_se: Union[List[Text], Dict[Text, Text]], threshold: float):
        """
        Pipeline extract content from search engine

        Args:
            ques: question
            data_se: data search from search engine as a dict[link, short_description] or list[link]
        """
        self.data_search = data_se
        self.question = ques
        self._tool = None
        self.threshold = threshold
        self._data_crawl = None
        self.best_description = ''
        self.req_agent = CrawlUrl()
        self.run()

    async def _crawl_link(self, session, link: Text) -> Optional[pd.DataFrame]:
        """
        Crawl data from a link

        Args:
            session: aiohttp ClientSession
            link: link to crawl

        Returns:
            pd.DataFrame: data crawled
        """
        desc = ''
        if isinstance(self.data_search, dict):
            desc = self.data_search[link]
        try:
            if self._tool is None:
                self._tool = ContentExtractor()
                await self._tool.fetch_and_update(session, link, desc)
            else:
                await self._tool.fetch_and_update(session, link, desc)
        except ValueError:
            return None
        data = self._tool.data
        if data is None:
            return None
        data['source'] = [link.split('/')[2].replace('www.', '')] * len(data)
        if desc:
            with_out_des = self._get_best_row(self.question, data)
            with_des = self._get_best_row(self.question + ' ' + desc, data)
            if with_des.empty:
                return with_out_des
            if with_out_des.empty:
                return with_des
            merged = pd.concat([with_des, with_out_des])
            merged = merged.sort_values(by='score', ascending=False)
            merged = merged.drop_duplicates(subset=['text'], keep='first')
            merged = merged[merged['score'] >= self.threshold]
            return merged
        return data

    @staticmethod
    def _get_best_row(ques: Text, data: pd.DataFrame) -> pd.DataFrame:
        """
        Get best row from data crawled

        Args:
            ques: question
            data: data crawled

        Returns:
            pd.DataFrame: best row
        """
        data_matched = process.extract(
            query=ques,
            choices=data['text'].tolist(),
            scorer=fuzz.token_set_ratio,
            limit=len(data)
        )
        data_matched = pd.DataFrame(data_matched, columns=['text', 'score'])
        if 'score' in data.columns:
            data = data.drop(columns=['score'])
        data = pd.merge(data, data_matched, on='text', how='left')
        data = recalculate_score(data)
        data = data.drop_duplicates(subset=['text'], keep='first')
        return data

    async def _fetch_all(self, urls) -> List[pd.DataFrame]:
        """
        Fetch data from all links

        Args:
            urls: list of links

        Returns:
            List[pd.DataFrame]: list of data crawled
        """
        headers = self.req_agent.headers
        headers['Cookie'] = random.choice(COOKIE_LIST)
        headers['User-Agent'] = random.choice([random.choice(USERAGENT_LIST), self.req_agent.ua.random])
        async with aiohttp.ClientSession(headers=headers) as session:
            crawl_tasks = [self._crawl_link(session, link) for link in urls]
            crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
            return crawl_results

    async def _crawl(self) -> pd.DataFrame:
        """
        Crawl data from search engine

        Returns:
            pd.DataFrame: data crawled
        """
        dfs = []
        if isinstance(self.data_search, dict):
            crawl_results = await self._fetch_all(self.data_search.keys())
        else:
            crawl_results = await self._fetch_all(self.data_search)
        for df in crawl_results:
            if isinstance(df, Exception):
                # handle exception if needed
                pass
            elif df is not None:
                dfs.append(df)

        if not dfs:
            raise ValueError('No data crawled')
        dfs = pd.concat(dfs)
        if isinstance(self.data_search, dict):
            dfs = dfs.sort_values(by='score', ascending=False)
        dfs = dfs.sort_index()
        return dfs

    def get_best_result(self, top_k: int, with_source: bool) -> List[Union[Text, Dict[Text, Text]]]:
        """
        Get best result from data crawled

        Returns:
            List[Union[Text, Dict[Text, Text]]]: best result
        """
        if self._data_crawl is None:
            raise ValueError('No data crawled')
        data_crawl = self._data_crawl
        if isinstance(self.data_search, dict):
            data_crawl = data_crawl[data_crawl['score'] >= self.threshold]
        if data_crawl.empty:
            return [{'text': 'Không tìm thấy kết quả phù hợp', 'source': ''}]
        data_crawl = data_crawl.groupby('source').head(top_k)
        data_crawl = data_crawl.groupby('source')
        if isinstance(self.data_search, dict):
            data_crawl = data_crawl.agg({'text': ' '.join, 'score': 'mean'})
            data_crawl = data_crawl.sort_values(by='score', ascending=False)
            data_crawl = data_crawl[data_crawl['score'] >= self.threshold]
        else:
            data_crawl = data_crawl.agg({'text': ' '.join})
        if with_source:
            data_crawl = data_crawl.reset_index()
            return data_crawl.to_dict('records')
        return data_crawl['text'].tolist()

    def run(self) -> None:
        """
        Call function of the class
        """
        loop = asyncio.get_event_loop()
        self._data_crawl = loop.run_until_complete(self._crawl())
