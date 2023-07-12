import time
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from crawls.google_search import Google
from crawls.content_extractor import PipelineExtractor

DATA_PATH = "/home/hungtdd/Desktop/CoT-lib/datasets/VND/dictionary-filled-3.jsonl"

if DATA_PATH.endswith(".csv"):
    data = pd.read_csv(DATA_PATH, encoding="utf-8")
elif DATA_PATH.endswith(".jsonl"):
    data = pd.read_json(DATA_PATH, orient="records", lines=True)

data = data.dropna(subset=["instruction"])
data = data.reset_index(drop=True)
data = data.drop_duplicates(subset=["instruction"])

google_search = Google()


def process_question(index, row):
    start_time = time.time()
    data_search = google_search.query(row["instruction"])
    data_search = google_search.search_engine_results(data_search)
    if not data_search:
        cost_time = time.time() - start_time
        return index, "", "Không tìm thấy kết quả phù hợp", cost_time
    data_extract = {}
    for item in data_search:
        sn = item["snippet"].split(".")[:-1]
        sn = ".".join(sn)
        data_extract[item["url"]] = sn
    for url in data_extract:
        if data_extract[url].endswith(", ") or data_extract[url].endswith(". ."):
            data_extract[url] = data_extract[url].replace(", ", "")
            data_extract[url] = data_extract[url].replace(". .", "")
        elif ".." not in data_extract[url] or data_extract[url].endswith("."):
            cost_time = time.time() - start_time
            return index, data_extract, [{"text": data_extract[url]}], cost_time
        else:
            data_extract[url] = data_extract[url].replace("..", "")
    extractor = PipelineExtractor(row["instruction"], data_extract, threshold=0.4)
    results = extractor.get_best_result(top_k=20, with_source=True)
    cost_time = time.time() - start_time
    return index, data_extract, results, cost_time


def process_all_questions(data_sheet):
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(process_question, i, row): (i, row) for i, row in data_sheet.iterrows()}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            try:
                i, url, result, cost_time = future.result()
            except Exception as e:
                print(e)
                continue
            if not isinstance(result, str):
                tokens = [item["text"] for item in result]
                tokens = " ".join(tokens)
                if "tìm thấy kết quả phù hợp" in tokens:
                    if data_sheet.at[i, "output"]:
                        tokens = data_sheet.at[i, "output"]
                    else:
                        tokens = ""
                data_sheet.at[i, "output"] = tokens
    return data_sheet


if __name__ == "__main__":
    data = process_all_questions(data)
    data.to_json(DATA_PATH.replace(".csv", "-filled-4.jsonl"), orient="records", lines=True, force_ascii=False)
    print("Done")
