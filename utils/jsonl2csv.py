import pandas as pd

DATA_PATH="/home/hungtdd/Desktop/CoT-lib/datasets/VND/dictionary-filled-3.jsonl"

# Convert jsonl to csv
data = pd.read_json(DATA_PATH, orient="records", lines=True)
data.to_csv(DATA_PATH.replace(".jsonl", ".csv"), index=False, encoding="utf-8")