import time
import pandas as pd
from tqdm import tqdm
from chromaviz import visualize_collection

from crawls.search import SearchEngine
from crawls.tools.vn_text_processor import StringUtils

DATA_PATH = "D:/Projects/COT-lib/datasets/VND/dictionary.csv"

data = None
if DATA_PATH.endswith(".csv"):
    data = pd.read_csv(DATA_PATH, encoding="utf-8")
elif DATA_PATH.endswith(".jsonl"):
    data = pd.read_json(DATA_PATH, orient="records", lines=True)

data = data.dropna(subset=["instruction"])
data = data.reset_index(drop=True)
data = data.drop_duplicates(subset=["instruction"])

search_engine = SearchEngine(model_path='keepitreal/vietnamese-sbert',
                             collection_name='search', threshold=0.4)


def process_question(index, row):
    start_time = time.time()
    result_search = search_engine.search(row["instruction"])
    if result_search is None:
        cost_time = time.time() - start_time
        return index, "Không tìm thấy kết quả phù hợp", cost_time
    # convert to list dict
    result_search = result_search.iloc[0]
    result_search = result_search.to_dict()
    cost_time = time.time() - start_time
    return index, result_search, cost_time


def save_result(data):
    if DATA_PATH.endswith(".csv"):
        data.to_csv(DATA_PATH.replace(".csv", f"-filled-6.csv"), index=False, encoding="utf-8")
    elif DATA_PATH.endswith(".jsonl"):
        data.to_json(DATA_PATH.replace(".jsonl", f"-filled-6.jsonl"),
                     orient="records", lines=True, force_ascii=False)


def post_process_result(data_sheet, results):
    for index, res in tqdm(enumerate(results), total=len(results)):
        if isinstance(res, Exception):
            print(res)
            continue

        i, result, cost_time = res
        if not isinstance(result, str):
            if "doc" not in result:
                tokens = [item["doc"] for item in result]
                tokens = " ".join(tokens)
            else:
                tokens = result["doc"]
            if "tìm thấy kết quả phù hợp" in tokens:
                if data_sheet.at[i, "output"]:
                    tokens = data_sheet.at[i, "output"]
                else:
                    tokens = ""
            data_sheet.at[i, "output"] = StringUtils.clean_text(tokens)

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
