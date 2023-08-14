from tools.dbms import DBMS

db = DBMS(
    model_path='keepitreal/vietnamese-sbert',
    collection_name='search',
    threshold=0.35
)

db.load_json('D:/Projects/COT-lib/datasets/vnd_cleaned.jsonl', cols=["output"])

db.auto_clean()

db.visualize()