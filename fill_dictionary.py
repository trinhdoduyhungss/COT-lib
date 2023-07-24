import time
import pandas as pd
from tqdm import tqdm
from tabulate import tabulate
from chromaviz import visualize_collection

from tools.search import SearchEngine

DATA_PATH = "D:/Projects/COT-lib/datasets/vnd.jsonl"

if DATA_PATH.endswith(".csv"):
    data = pd.read_csv(DATA_PATH, encoding="utf-8")
elif DATA_PATH.endswith(".jsonl"):
    data = pd.read_json(DATA_PATH, orient="records", lines=True)

data = data.dropna(subset=["instruction"])
data = data.reset_index(drop=True)
data = data.drop_duplicates(subset=["instruction"])

data = data.iloc[2000:3000]

search_engine = SearchEngine(model_path='keepitreal/vietnamese-sbert',
                             prompt="""From the internet results, you should write a shortest answer with the rules:
- Focus to the main information for answering my question below
- No citation needed
- Make sure your answer must be cleaned, easy to read, and natural
My question:""",
                             echo=False,
                             dir_cookies="D:/Projects/COT-lib/tools/cookies",
                             collection_name='search',
                             threshold=0.5)


def save_result(data):
    if DATA_PATH.endswith(".csv"):
        data.to_csv(DATA_PATH.replace(".csv", f"-filled-3.csv"), index=False, encoding="utf-8")
    elif DATA_PATH.endswith(".jsonl"):
        data.to_json(DATA_PATH.replace(".jsonl", f"-filled-3.jsonl"),
                     orient="records", lines=True, force_ascii=False)


def process_question(index, row):
    start_time = time.time()
    print(f"\nQ:{row['instruction']}")
    result_search = search_engine.search(row["instruction"])
    if result_search is None:
        cost_time = time.time() - start_time
        return index, "Không tìm thấy kết quả phù hợp", cost_time
    print("\n")
    print(tabulate(result_search, headers='keys', tablefmt='psql'))
    # convert to list dict
    result_search = result_search.iloc[0]
    result_search = result_search.to_dict()
    cost_time = time.time() - start_time
    return index, result_search, cost_time


def post_process_result(data_sheet, results):
    for index, res in tqdm(enumerate(results), total=len(results), postfix="\n"):
        if isinstance(res, Exception):
            print(res)
            continue

        i, result, cost_time = res
        if not isinstance(result, str):
            tokens = result["documents"]
            if "tìm thấy kết quả phù hợp" in tokens:
                if data_sheet.at[i, "output"]:
                    tokens = data_sheet.at[i, "output"]
                else:
                    tokens = ""
            data_sheet.at[i, "output"] = tokens

    return data_sheet


def process_all_questions(data_sheet):
    results = []
    for index, row in tqdm(data_sheet.iterrows(), total=len(data_sheet)):
        try:
            result = process_question(index, row)
            results.append(result)
        except Exception as e:
            print(e)
            results.append((index, "Không tìm thấy kết quả phù hợp", 0))
        if len(results) % 100 == 0:
            data_sheet = post_process_result(data_sheet, results)
            save_result(data_sheet)

    data_sheet = post_process_result(data_sheet, results)

    return data_sheet


if __name__ == "__main__":
    data = process_all_questions(data)
    save_result(data)
    print("Done")
    visualize_collection(search_engine.collection)
