import re
import itertools
from typing import List, Optional, Tuple, Text


def replace_by_rule(rule: Tuple[Text, Text], text: Text) -> Text:
    """
    Replace text by rule

    Args:
        rule: regex rule
        text: text to remove

    Returns:
        text after remove
    """
    return re.sub(rule[0], rule[1], text, flags=re.MULTILINE | re.DOTALL)


def clean_data(rules: Optional[List], data):
    """
    Clean data

    Args:
        rules: list of rules to clean data
        data: dataframe
    """
    rules = rules if rules else []
    rules = [('\[\^\d+\^]', ''), (':\[.*', ''), ('\\n\\n.*', ''), ('Searching.*', '')] + rules
    for rule in rules:
        data['documents'] = data['documents'].apply(lambda x: replace_by_rule(rule, x))
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
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list) and isinstance(value[0][0], int):
                try:
                    data[key] = list(itertools.chain.from_iterable(value))
                except:
                    continue
        return data

    if isinstance(data, dict):
        return flatten_dict(data)
    elif isinstance(data, list):
        return list(itertools.chain.from_iterable(data))
    else:
        return data
