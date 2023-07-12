import re
import regex
from crawls.tools.vn_text_processor import (
    StringUtils,
    VN_abbreviation,
    VN_exception
)


class Regex:
    ELLIPSIS = "\\.{2,}"
    EMAIL = "([\\w\\d_\\.-]+)@(([\\d\\w-]+)\\.)*([\\d\\w-]+)"
    FULL_DATE = "(0?[1-9]|[12][0-9]|3[01])(\\/|-|\\.)(1[0-2]|(0?[1-9]))((\\/|-|\\.)\\d{4})"
    MONTH = "(1[0-2]|(0?[1-9]))(\\/)\\d{4}"
    DATE = "(0?[1-9]|[12][0-9]|3[01])(\\/)(1[0-2]|(0?[1-9]))"
    TIME = "(\\d\\d:\\d\\d:\\d\\d)|((0?\\d|1\\d|2[0-3])(:|h)(0?\\d|[1-5]\\d)(’|'|p|ph)?)"
    MONEY = r"\\p{Sc}\\d+([\\.,]\\d+)*|\\d+([\\.,]\\d+)*\\p{Sc}"
    PHONE_NUMBER = "(\\(?\\+\\d{1,2}\\)?[\\s\\.-]?)?\\d{2,}[\\s\\.-]?\\d{3,}[\\s\\.-]?\\d{3,}"
    URL = "(((https?|ftp):\\/\\/|www\\.)[^\\s/$.?#].[^\\s]*)|(https?:\\/\\/)?(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{2," \
          "256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%_\\+.~#?&//=]*)"
    NUMBER = r"[-+]?\\d+([\\.,]\\d+)*%?\\p{Sc}?"
    PUNCTUATION = ",|\\.|:|\\?|!|;|-|_|\"|'|“|”|\\||\\(|\\)|\\[|\\]|\\{" \
                  "|\\}|âŸ¨|âŸ©|Â«|Â»|\\\\|\\/|\\â€˜|\\â€™|\\â€œ|\\â€�|â€¦|…|‘|’|·"
    SPECIAL_CHAR = "\\~|\\@|\\#|\\^|\\&|\\*|\\+|\\-|\\â€“|<|>|\\|"
    EOS_PUNCTUATION = "(\\.+|\\?|!|…)"
    NUMBERS_EXPRESSION = NUMBER + "([\\+\\-\\*\\/]" + NUMBER + ")*"
    SHORT_NAME = r"([\p{L}]+([.\-][\p{L}]+)+)|([\p{L}]+-\d+)"
    WORD_WITH_HYPHEN = r"\p{L}+-\p{L}+(-\p{L}+)*"
    ALL_CAP = "[A-Z]+\\.[A-Z]+"
    BREAK_SENTENCE = r"(?<=[.?!:\n])\s+(?=\p{Lu})" #r"(?<=[.?!:\n])\s+"

    GET_REGEX_LIST = [
        ELLIPSIS,
        EMAIL,
        URL,
        FULL_DATE,
        MONTH,
        DATE,
        TIME,
        MONEY,
        PHONE_NUMBER,
        SHORT_NAME,
        NUMBERS_EXPRESSION,
        NUMBER,
        WORD_WITH_HYPHEN,
        PUNCTUATION,
        SPECIAL_CHAR,
        ALL_CAP,
    ]

    REGEX_INDEX = [
        "ELLIPSIS",
        "EMAIL",
        "URL",
        "FULL_DATE",
        "MONTH",
        "DATE",
        "TIME",
        "MONEY",
        "PHONE_NUMBER",
        "SHORT_NAME",
        "NUMBERS_EXPRESSION",
        "NUMBER",
        "WORD_WITH_HYPHEN",
        "PUNCTUATION",
        "SPECIAL_CHAR",
        "ALL_CAP",
    ]

    @staticmethod
    def get_regex_index(reg):
        return Regex.REGEX_INDEX.index(reg.upper())


def compile_(x):
    try:
        # print("Regex: " + x)
        return re.compile(x)
    except Exception:
        # print("Regex error: " + x)
        return regex.compile(x)


class SentenceSegment:

    @staticmethod
    def split_(pattern, s):
        return [x for x in re.split(pattern, s) if x != ""]

    @staticmethod
    def substring_(s, a, b):
        return s[a:b]

    @staticmethod
    def tokenize(s):
        if s is None or s.strip() == "":
            return []
        temp_tokens = SentenceSegment.split_("\\s+", s.strip())
        if len(temp_tokens) == 0:
            return []

        tokens = []
        for token in temp_tokens:
            if len(token) == 1 or not (StringUtils.has_punctuation(token)):
                tokens.append(token)
                continue

            if token.endswith(","):
                tokens.extend(SentenceSegment.tokenize(token[0: len(token) - 1]))
                tokens.append(",")
                continue
            if token in VN_abbreviation:
                tokens.append(token)
            if token.endswith(".") and StringUtils.is_alphabetic(token[len(token) - 2]):
                if (len(token) == 2 and token[len(token) - 2].isupper()) or (
                        compile_(Regex.SHORT_NAME).search(token) is not None
                ):
                    tokens.append(token)
                    continue
                tokens.extend(SentenceSegment.tokenize(token[0: len(token) - 1]))
                tokens.append(".")
                continue
            if token in VN_exception:
                tokens.append(token)
                continue

            token_contains_abb = False
            for e in VN_abbreviation:
                i = token.find(e)
                if i < 0:
                    continue
                token_contains_abb = True
                tokens = SentenceSegment.recursive(tokens, token, i, i + len(e))
                break
            if token_contains_abb:
                continue
            token_contains_exp = False
            for e in VN_exception:
                i = token.find(e)
                if i < 0:
                    continue
                token_contains_exp = True
                tokens = SentenceSegment.recursive(tokens, token, i, i + len(e))
                break
            if token_contains_exp:
                continue
            regexes = Regex.GET_REGEX_LIST
            matching = False
            for reg in regexes:
                if compile_(reg).match(token):
                    tokens.append(token)
                    matching = True
                    break
            if matching:
                continue
            for i in range(len(regexes)):
                pattern = compile_(regexes[i])
                matcher = pattern.search(token)
                if matcher:
                    if i == Regex.get_regex_index("url"):
                        elements = re.split(r"\.", token)
                        has_url = True
                        for ele in elements:
                            if len(ele) == 1 and ele[0].isupper():
                                has_url = False
                                break
                            for j in range(len(ele)):
                                if ord(ele[j]) >= 128:
                                    has_url = False
                                    break
                        if has_url:
                            tokens = SentenceSegment.recursive(tokens, token, matcher.start(), matcher.end())
                        else:
                            continue
                elif i == Regex.get_regex_index("month"):
                    start = matcher.start()
                    has_letter = False
                    for j in range(start):
                        if token[j].isalpha():
                            tokens = SentenceSegment.recursive(tokens, token, matcher.start(), matcher.end())
                            has_letter = True
                            break
                    if not has_letter:
                        tokens.append(token)
                else:
                    if matcher:
                        tokens = SentenceSegment.recursive(tokens, token, matcher.start(), matcher.end())
                    else:
                        tokens.append(token)
                matching = True
                break

            if matching:
                continue
            else:
                tokens.append(token)
        return tokens

    @staticmethod
    def recursive(tokens, token, beginMatch, endMatch):
        if beginMatch > 0:
            tokens.extend(SentenceSegment.tokenize(token[0: beginMatch]))

        tokens.extend(SentenceSegment.tokenize(token[beginMatch: endMatch]))
        if endMatch < len(token):
            tokens.extend(SentenceSegment.tokenize(token[:endMatch]))
        return tokens

    @staticmethod
    def join_sentences(tokens):
        sentences = []
        sentence = []
        for i in range(len(tokens)):
            token = tokens[i]
            next_token = None
            if i != len(tokens) - 1:
                next_token = tokens[i + 1]
            before_token = None
            if i > 0:
                before_token = tokens[i - 1]
            sentence.append(token)
            if i == len(tokens) - 1:
                sentences.extend(SentenceSegment.join_sentence(sentence))
                return sentences
            if i < len(tokens) - 2 and token == StringConst.COLON:
                if next_token[0].isdigit() and tokens[i + 2] == StringConst.STOP or tokens[i + 2] == StringConst.COMMA:
                    sentences.extend(SentenceSegment.join_sentence(sentence))
                    sentence = []
                    continue
            if compile_(Regex.EOS_PUNCTUATION).fullmatch(token):
                if next_token == '"' or next_token == "''":
                    count = 0
                    for senToken in sentence:
                        if senToken == '"' or senToken == "''":
                            count += 1
                    if count % 2 == 1:
                        continue
                if (
                        StringUtils.is_brace(next_token)
                        or next_token == ""
                        or next_token[0].islower()
                        or next_token == StringConst.COMMA
                        or next_token[0].isdigit()
                ):
                    continue
                if len(sentence) == 2 and token == StringConst.STOP:
                    if before_token[0].isdigit():
                        continue
                    if before_token[0].islower():
                        continue
                    if before_token[0].isupper():
                        if len(before_token) == 1:
                            continue

                sentences.extend(SentenceSegment.join_sentence(sentence))
                sentence = []
        return sentences

    @staticmethod
    def join_sentence(tokens):
        sent = ""
        length = len(tokens)
        for i in range(length):
            token = tokens[i]
            if token == "" or token is None or token == StringConst.SPACE:
                continue

            sent = sent + token
            if i < length - 1:
                sent = sent + StringConst.SPACE
        sent = sent.strip()
        sent = re.split(Regex.BREAK_SENTENCE, sent)
        if len(sent) > 1:
            return sent
        return [sent[0]]

    @staticmethod
    def segment(s):
        raw_sentences = SentenceSegment.join_sentences(SentenceSegment.tokenize(s))
        return raw_sentences


class StringConst:
    BOS = "<s>"
    EOS = "</s>"
    SPACE = " "
    COMMA = ","
    STOP = "."
    COLON = ":"
    UNDERSCORE = "_"
