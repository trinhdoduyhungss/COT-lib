import json
import pandas as pd

data_input = '/home/hungtdd/Desktop/CoT-lib/datasets/VND/dictionary.jsonl'

try:
    data = json.load(open(data_input, "r", encoding="utf-8-sig"))
except Exception as e:
    data = pd.read_json(path_or_buf=data_input, lines=True, encoding="utf-8-sig")

if isinstance(data, dict):
    data = [data]

data = pd.DataFrame(data)

print(data.head())

# drop column "source"

data = data.drop(columns=["source"])

#  add post-fix into each cell of column "text"

data["instruction"] = data["text"].apply(lambda x: x + " có nghĩa là gì")

# drop column "text"
data = data.drop(columns=["text"])

print(data.head())

# add columns: "search_engine_result", "content_extractor", "cost_time", "num_of_tokens", "evaluate"
data["output"] = ""

print(data.head())

# save data_old to csv file
data.to_csv('/home/hungtdd/Desktop/CoT-lib/datasets/VND/dictionary.csv', index=False)