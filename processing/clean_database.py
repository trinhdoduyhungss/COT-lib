from tools.dbms import DBMS

db = DBMS(
    model_path='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    collection_name='search',
    threshold=0.35
)

# db.from_json('./datasets/vnd_cleaned.jsonl', cols=["output"], merge_columns=["instruction", "output"])

if __name__ == '__main__':
    # db.auto_clean()
    db.visualize()