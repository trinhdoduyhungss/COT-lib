import re
import itertools
from typing import List, Optional, Tuple, Text


def replace_by_rule(rules: List[Tuple[Text, Text]], text: Text) -> Text:
    """
    Replace text by rule

    Args:
        rules: regex rule
        text: text to remove

    Returns:
        text after remove
    """
    for rule in rules:
        text = re.sub(rule[0], rule[1], text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        text = text.strip(' ')
    return text


def clean_data(rules: Optional[List], data):
    """
    Clean data

    Args:
        rules: list of rules to clean data
        data: dataframe
    """
    rules = rules if rules else []
    rules = [(r'\[\^\d+\^]', ''),
             (r'< p>.*', ''),
             (r':\[.*', ''),
             (r'\\n\\n.*', ''),
             (r'Searching.*', ''),
             (r'(từ tương tự|hành chính|tham khảo|lịch sử|khái quát).*sửa đổi', ''),
             (r'Tra cứu.*?\.', '')] + rules
    data['documents'] = data['documents'].apply(lambda x: replace_by_rule(rules, x))
    return data


def flatten_list(data):
    """
    Flatten values in a dict
    If data is a dict and its value contain a list, flatten it
    If data is a list, flatten it

    Args:
        data: dict or list
    """

    def flatten_dict(data):
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list) and not isinstance(value[0][0], int) and not isinstance(value[0][0], float) and not isinstance(value[0][0], float):
                try:
                    data[key] = list(itertools.chain.from_iterable(value))
                except Exception as e:
                    print(e)
                    continue
        return data

    if isinstance(data, dict):
        return flatten_dict(data)
    elif isinstance(data, list):
        return list(itertools.chain.from_iterable(data))
    else:
        return data

def clean_bot_answer(text):
    # text = re.sub(r"^.*:", "", text)
    # text = re.sub(r"^.*!", "", text)
    # text = re.sub(r"\(.*\)", "", text)
    # text = re.sub(r"^- ", "", text)
    text = re.sub(r"^Xin chào.*! ", "", text)
    text = re.sub(r"^Xin lỗi vì.*\. ", "", text)
    text = re.sub(r"^Rất vui.*\.", "", text)
    text = re.sub(r". Rất xin lỗi cho.*\.", ".", text)
    return text
