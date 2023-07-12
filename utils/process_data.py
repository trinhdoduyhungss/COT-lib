"""
This file contains the code to pre-process the dataset.
"""

import os
import glob
import asyncio
import pandas as pd
from tqdm import tqdm
import concurrent.futures
from tabulate import tabulate

from utils.process_base import ProcessBase


class ProcessData(ProcessBase):
    """
    This class is the pre-processing class for the dataset.
    """

    async def load_data(self):
        """
        Load the data from the raw data.
        We have two types of data need to load:
        - The data from the JSON files
        - The data from the TXT files
        """
        if isinstance(self.data_dir, list):
            for data_dir in tqdm(self.data_dir, desc="Loading data"):
                self.data_dir = data_dir
                file_loaded = await self.load_data()
                if isinstance(self.data, pd.DataFrame):
                    self.data = pd.concat([self.data, file_loaded], ignore_index=True)
                else:
                    self.data = file_loaded
                self.data = self.data.drop_duplicates()

        json_files = glob.glob(os.path.join(self.data_dir, "**/*.json"), recursive=True)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            data = list(
                tqdm(executor.map(self._load_json, json_files), total=len(json_files),
                     desc=f"Loading JSON files in {self.data_dir}"))

        txt_files = glob.glob(os.path.join(self.data_dir, "**/*_steps*.txt"), recursive=True)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            data += list(
                tqdm(executor.map(self._load_txt, txt_files), total=len(txt_files),
                     desc=f"Loading TXT files in {self.data_dir}"))

        data = pd.concat(data, ignore_index=True)
        return data


if __name__ == "__main__":
    async def main():
        process_data = ProcessData()
        process_data.setup(
            data_dir=[
                # "/home/hungtdd/Desktop/CoT-lib/datasets/MATH/train",
                # "/home/hungtdd/Desktop/CoT-lib/datasets/AMPS/khan",
                "/home/hungtdd/Desktop/CoT-lib/datasets/ACoT/train/auto-cot",
                "/home/hungtdd/Desktop/CoT-lib/datasets/ACoT/train/gsm8k",
                "/home/hungtdd/Desktop/CoT-lib/datasets/GPT4ALL",
                "/home/hungtdd/Desktop/CoT-lib/datasets/GRADE",
                # "/home/hungtdd/Desktop/CoT-lib/datasets/ARXIV",
                "/home/hungtdd/Desktop/CoT-lib/datasets/CAMEL"
            ],
            output_dir="/home/hungtdd/Desktop/CoT-lib/datasets/BCoT"
        )
        await process_data.load_data()
        if process_data.data is not None:
            print(tabulate(process_data.data.head(25), headers="keys", tablefmt="psql"))
            process_data.save_data()

    asyncio.run(main())

