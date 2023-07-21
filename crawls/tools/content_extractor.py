import re
import time
import asyncio
import pandas as pd
from bs4.element import Tag
from bs4 import BeautifulSoup
from typing import List, Text, Dict, Optional, Union, Tuple
from kwextractor.process.extract_keywords import ExtractKeywords

from crawls.tools.constants import (
    TAG_REMOVE,
    TAG_PARENT_EXTRACT,
    CLASS_REMOVE,
    CLASS_PRIORITIZE,
    REGEX_CUT_ANSWER,
    REGEX_BREAK_LINE,
    REGEX_BREAK_BLOCK,
    REGEX_TEXT_POST_REMOVE
)
from crawls.tools.req_agents import CrawlUrl
from crawls.tools.google_search import Google
from crawls.tools.vn_text_processor import StringUtils
from crawls.tools.sentence_segment import SentenceSegment


class ContentExtractor:
    def __init__(self):
        self.desc = ""
        self._html = None
        self._soup = None
        self.data = None
        self.tokenizer_sentence = SentenceSegment()

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

    def _extract(self) -> Optional[pd.DataFrame]:
        data = self._parse(self._soup)
        if not data:
            return None
        data = pd.DataFrame(data, columns=['text'])
        data['text'] = data['text'].str.strip()
        return data

    def _parse(self, tag: Tag) -> List[Text]:
        if tag is None:
            return []
        text = StringUtils.clean_text(tag.text.strip(' '))
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
            par = StringUtils.clean_text(par).strip()
            if not par:
                continue
            if par[-1] in ['.', '?', '!']:
                sentences.append(par)
                continue
            try:
                seg = self.tokenizer_sentence.segment(par)
                if seg:
                    seg = [StringUtils.clean_text(s).strip() for s in seg if s.strip()[-1] in ['.', '?', '!']]
            except Exception as e:
                # print(e)
                seg = [par]
            sentences.extend(seg)
        return sentences

    @staticmethod
    async def _fetch_react(req, url: Text):
        raw = ""
        solution = "1"
        if solution == "1":
            url = f"http://webcache.googleusercontent.com/search?q=cache:{url}&prmd=ivn&strip=1&vwsrc=0"
            raw = await req.gettext(url, None)
            if "Our systems have detected unusual traffic from your computer" in raw:
                print("Google block: ", url)
                raw = ""
                solution = "2"
        if solution == "2":
            url = f"https://archive.org/wayback/available?url={url}"
            raw = await req.gettext(url, None)
            if raw.get('archived_snapshots'):
                url = raw['archived_snapshots']['closest']['url']
                raw = await req.gettext(url, None)
        return raw

    async def fetch_and_update(self, req, url: Text, desc: Text):
        self._html = await req.gettext(url, None)
        if '<div id="root">' in self._html or "JavaScript to run" in self._html:
            self._html = await self._fetch_react(req, url)
        self.desc = desc
        self._soup = self._focus_area()
        self.data = self._extract()


class PipelineExtractor:
    def __init__(self):
        """
        Pipeline extract content from search engine
        """
        self.data_search = None
        self.question = None
        self._tool = None
        self.data_crawl = None
        self.req_agent = CrawlUrl()
        self.get_keywords = ExtractKeywords()

    @staticmethod
    def _only_kw(module_kw, text):
        """
        Get keywords from text

        Args:
            text: text to get keywords

        Returns:
            Text: only keywords
        """
        try:
            text_kw = module_kw.extract_keywords(text).split(",")
            if len(text_kw) > 7:
                return " ".join(text_kw)
            return text
        except Exception as e:
            # print(e)
            return text

    def _process_table(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Get best row from data crawled

        Args:
            data: data crawled

        Returns:
            pd.DataFrame: best row
        """
        data["text"] = data["text"].apply(lambda x: self._only_kw(self.get_keywords, x))
        return data

    async def _crawl_link(self, req, link: Text) -> Optional[pd.DataFrame]:
        """
        Crawl data from a link

        Args:
            req: request agent (CrawlUrl)
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
            await self._tool.fetch_and_update(req=req, url=link, desc=desc)
        except ValueError:
            return None

        data = self._tool.data
        if data is None:
            return None
        data = data[data['text'].str.len() > 20]
        data = data[data['text'].str.endswith(':') == False]
        data = data[data['text'].str.endswith('?') == False]
        data = data[data['text'].str.contains('>>') == False]
        data = data[data['text'].str.startswith('^') == False]
        data = data[data['text'].str.startswith('Xem') == False]
        data = data[data['text'].str.contains('[\[\]\|]') == False]
        data = data[data['text'].str.contains('Wayback Machine') == False]
        data['source'] = [link.split('/')[2].replace('www.', '')] * len(data)
        data = data[(data['text'].str.endswith('.') == True) |
                    (data['text'].str.endswith('!') == True) |
                    (data['text'].str[0].str.isupper() == True)]
        data["doc"] = data["text"].copy()
        # data = self._process_table(data)
        return data

    async def _fetch_all(self, urls) -> List[pd.DataFrame]:
        """
        Crawl data from a list of links

        Args:
            urls: list of links to crawl

        Returns:
            List[pd.DataFrame]: list of data crawled
        """
        list_result = []
        for url in urls:
            data = await self._crawl_link(req=self.req_agent, link=url)
            list_result.append(data)
        return list_result

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
            if df is not None:
                dfs.append(df)

        if not dfs:
            raise ValueError('No data crawled')
        dfs = pd.concat(dfs)
        return dfs

    async def run(self, ques: Text, data_se: Union[List[Text], Dict[Text, Text]]) -> None:
        """
        Call function of the class

        Args:
            ques: question
            data_se: data search from search engine as a dict[link, short_description] or list[link]
        """
        self.question = ques
        self.data_search = data_se
        self.data_crawl = await self._crawl()


class AskInternet:
    def __init__(self):
        self.google_search = Google()
        self.pipeline = PipelineExtractor()

    async def run(self, ques: Text) -> Tuple[Optional[Dict[Text, Text]], Optional[pd.DataFrame], float]:
        """
        Call function of the class

        Args:
            ques: question

        Returns:
            data search, data extract, cost time
        """
        start_time = time.time()
        data_search = await self.google_search.query(ques)
        data_search = self.google_search.search_engine_results(data_search)
        if not data_search:
            cost_time = time.time() - start_time
            return None, None, cost_time
        data_extract = {}
        for item in data_search:
            data_extract[item["url"]] = item["snippet"]
        for url in data_extract:
            split_snippet = data_extract[url].split(".")
            if len(split_snippet[-1]) < 2:
                extract = [{"doc": data_extract[url],
                            "text": data_extract[url], "source": url.split('/')[2].replace('www.', '')}]
                extract = pd.DataFrame(extract)
                return data_extract, extract, time.time() - start_time
        await self.pipeline.run(ques, data_extract)
        extract = self.pipeline.data_crawl
        if extract is None:
            return data_extract, None, time.time() - start_time
        return data_extract, extract, time.time() - start_time
