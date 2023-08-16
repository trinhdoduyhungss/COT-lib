import re
from urllib.parse import unquote

from .constants import (
    REGEX_REMOVE_ADS,
    REGEX_COMMAND_REMOVE,
)


class StringUtils:

    @staticmethod
    def clean_text(text):
        """
        Clean text

        Args:
            text (str): text to clean

        Returns:
            str: cleaned text
        """
        text = StringUtils.normalize_res(text)
        ads = re.search(REGEX_REMOVE_ADS, text, re.DOTALL | re.IGNORECASE)
        if ads:
            text = text[:ads.start()] + text[ads.end():]
        text = re.sub(REGEX_REMOVE_ADS, '', text, re.DOTALL | re.IGNORECASE)
        text = re.sub(REGEX_COMMAND_REMOVE, '', text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        text = text.strip(' ')
        return text

    @staticmethod
    def has_punctuation(s):
        for i in range(len(s)):
            if not s[i].isalpha():
                return True
        return False

    @staticmethod
    def is_brace(string):
        if string == "”" or string == "�" or string == "'" or string == ")" or string == "}" or string == "]":
            return True
        return False

    @staticmethod
    def is_alphabetic(s):
        for c in s:
            if not c.isalpha():
                return False
        return True

    @staticmethod
    def html2vietnamese(text):
        """
        Convert html to vietnamese

        Args:
            text (str): string in html code

        Returns:
            str: string in Vietnamese
        """
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        return text

    @staticmethod
    def normalize_res(html):
        """
        Normalize html response

        Args:
            html (str): html response

        Returns:
            str: normalized html response
        """
        source = unquote(html, encoding='utf-8')
        source = StringUtils.html2vietnamese(source)
        source = re.sub(r'[\t\r\xa0\\/]', ' ', source)
        source = source.replace("...", "")
        source = re.sub(r'\s+', ' ', source)
        return source.strip()
