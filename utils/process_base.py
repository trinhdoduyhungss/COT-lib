"""
This file contains the base class for pre-processing datasets.
It will support for loading and saving the data_old and some functions:
- load_data: load the data_old from the raw data_old
- save_data: save the data_old to the processed data_old
- convert_to_text: convert the data_old to text
- break_text_to_df: break the text to data_old frame
"""
import os
import re
import json
import time

import pandas as pd
import matplotlib.pyplot as plt
from typing import Text, List, Union
from pylatexenc.latex2text import LatexNodes2Text

from utils.constant import (
    REGEX_MERGE_LINES,
    HOT_WORDS_REMOVE,
    REGEX_BREAK_TEXT,
    NO_PARSE_PASS,
    COLUMN_NAMES,
    KEY_SELECT,
    COLUMN_ADD
)


class ProcessBase:
    """
    This class is the base class for pre-processing datasets.
    """

    def __init__(self):
        """
        The constructor of the class.
        """
        self.data = None
        self.data_dir = None
        self.output_dir = None
        self.large_data = 200000
        self.latex2text = LatexNodes2Text()

    def setup(self, data_dir: Union[List, Text], output_dir: Text):
        """
        Set up the data_old directory and the output directory.

        Args:
            data_dir (Text): the data_old directory
            output_dir (Text): the output directory
        """
        self.data_dir = data_dir
        self.output_dir = output_dir

    def load_data(self):
        """
        Load the data_old from the raw data_old.
        """
        raise NotImplementedError

    def analyze_data(self):
        """
        Analyze the data_old.

        - Average length of the data_old.
        - Source of the data_old.
        - Type of the data_old.
        """
        print("Analyzing the data_old ...")
        data = self.data
        data["length"] = data[COLUMN_NAMES[0]].apply(lambda x: len(x)) + data[COLUMN_NAMES[1]].apply(lambda x: len(x))
        data["length"].hist(bins=100)
        plt.savefig(os.path.join(self.output_dir, "distribution_length.png"))
        plt.close()
        data["source"].value_counts().plot(kind="pie", autopct="%.2f%%", title="Source of the data_old", y="")
        plt.savefig(os.path.join(self.output_dir, "distribution_source.png"))
        plt.close()
        data["type"].value_counts().plot(kind="pie", autopct="%.2f%%", title="Type of the data_old", y="")
        plt.savefig(os.path.join(self.output_dir, "distribution_type.png"))
        plt.close()
        data = data.drop(columns=["length", "source", "type"])
        self.data = data

    def save_data(self):
        """
        Save the data_old to the processed data_old as the parquet file.
        """
        self.data = self.data.drop_duplicates()
        self.analyze_data()
        no_data = len(self.data)
        print(f"Saving {no_data} data_old to {self.output_dir} ...")
        for column in COLUMN_ADD:
            self.data[column] = COLUMN_ADD[column]
        filename = f"data_{time.strftime('%Y%m%d-%H%M%S')}_{no_data}"
        if no_data > self.large_data:
            filename = os.path.join(self.output_dir, f"{filename}.parquet")
            self.data.to_parquet(filename, index=False)
        else:
            filename = os.path.join(self.output_dir, f"{filename}.json")
            self.data.to_json(filename, orient="records", lines=True)

    def _load_json(self, json_file):
        """
        Load the data_old from the JSON file.

        Args:
            json_file (Text): the JSON file

        Returns:
            pd.DataFrame: the data_old frame
        """
        try:
            data = json.load(open(json_file, "r", encoding="utf-8-sig"))
        except Exception as e:
            data = pd.read_json(path_or_buf=json_file, lines=True, encoding="utf-8-sig")

        if isinstance(data, dict):
            data = [data]

        data = pd.DataFrame(data)
        is_process_text = False
        if isinstance(data, pd.DataFrame):
            valid_cols = []
            for key in KEY_SELECT:
                if key in data.columns:
                    valid_cols.append(key)
                    if isinstance(data[key][0], list):
                        data[key] = data[key].apply(lambda x: " ".join(x))
                    if not is_process_text:
                        data = self.convert_to_text(data)
                        is_process_text = True
                    if isinstance(data[key][0], str):
                        data[key] = data[key].apply(lambda x: re.sub(r"\\n+", "\n", x, re.MULTILINE))
                        data[key] = data[key].apply(lambda x: re.sub(r"\s{2,}", " ", x, re.MULTILINE))
                        data[key] = data[key].apply(lambda x: re.sub(REGEX_MERGE_LINES, "\n", x, re.MULTILINE))
                        data[key] = data[key].apply(lambda x: re.sub(r"\\n+", "\n", x, re.MULTILINE))
                        data[key] = data[key].apply(lambda x: re.sub(r"\s{2,}", " ", x, re.MULTILINE))
            data = data[valid_cols]
            data.columns = COLUMN_NAMES
            for hot_word in HOT_WORDS_REMOVE:
                for i in COLUMN_NAMES:
                    data = data[~data[i].str.contains(hot_word, case=False, regex=False)]
                    data[i] = data[i].apply(lambda x: re.sub(r"\s{2,}", " ", x, re.MULTILINE))
            data = data.dropna()
        data["source"] = self.data_dir.replace("/train", "").replace("/test", "").replace("/valid", "").split("/")[-1]
        type_data = json_file.split("/")[-2]
        if type_data.isdigit():
            type_data = json_file.split("/")[-3]
        data["type"] = type_data
        return data

    def _load_txt(self, file: str):
        """
        Load the data_old from the TXT file.

        Args:
            file (str): the path to the TXT file

        Returns:
            pd.DataFrame: the data_old frame of the data_old
        """
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
        return self.break_text_to_df(column_names=COLUMN_NAMES, text=text)

    def _convert_cell_to_text(self, cell: Text) -> Text:
        """
        Convert the cell to text.

        Args:
            cell (Text): the cell to convert

        Returns:
            Text: the converted cell
        """
        if isinstance(cell, list):
            str_cell = ""
            for i in cell:
                if len(str_cell) > 0 and cell[0].isupper():
                    str_cell += ". "
                else:
                    str_cell += " "
                str_cell += i
            cell = str_cell
        return cell

    def convert_to_text(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        """
        Convert format of the cell in data_old (data_frame) to text.

        Args:
            data_frame (pd.DataFrame): the data_old frame to convert

        Returns:
            pd.DataFrame: the converted data_old frame
        """
        data_frame = data_frame.applymap(self._convert_cell_to_text)
        return data_frame

    def break_text_to_df(self, column_names: List[Text], text: Text) -> pd.DataFrame:
        """
        Break the text to data_old frame.

        Args:
            column_names (List[Text]): the column names will be separated from the text
            text (Text): the text to break

        Returns:
            pd.DataFrame: the data_old frame
        """
        for regex in REGEX_BREAK_TEXT:
            parse = re.split(regex, text, re.MULTILINE | re.IGNORECASE)
            if len(parse) > NO_PARSE_PASS:
                data = pd.DataFrame([parse], columns=column_names)
                return data
        return pd.DataFrame(columns=column_names)
