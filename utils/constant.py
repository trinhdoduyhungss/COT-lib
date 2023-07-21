"""
This file contains all the constants used in the project.
REGEX_BREAK_TEXT: It will be used for breaking the data_old.
NO_PARSE_PASS: The number of sample that will be parsed. Use for verifying the rule is correct.
KEY_SELECT: The keys that will be selected from the data_old.
COLUMN_NAMES: The column names of the data_old frame.
COLUMN_ADD: The column names that will be added to the data_old frame.
HOT_WORDS_REMOVE: if the line contains these words, it will be removed.
"""

REGEX_BREAK_TEXT = [
    r"^(?=Problem|Answer).*?[:]"
]

NO_PARSE_PASS = 2

KEY_SELECT = [
    "Problem",
    "Answer",
    "Solution",
    "hints",
    "problem",
    'solution',
    "instruction",
    "output",
    "message_1",
    "message_2",
    "question",
    "answer",
]

COLUMN_NAMES = ["instruction", "output"]

COLUMN_ADD = {
    "input": ""
}

REGEX_MERGE_LINES = r"\n\s*"

HOT_WORDS_REMOVE = ["return",
                    "asy",
                    "table",
                    "draw",
                    "graph",
                    "chart",
                    "plot",
                    "diagram",
                    "picture",
                    "figure",
                    "game",
                    "matrix",
                    "vector",
                    '\\u',
                    "image"]
