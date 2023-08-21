import json
import pandas as pd
from typing import Any
from api.schemas import db
from tools.dbms import DBMS
from fastapi import APIRouter
from tools.components.APIs.libs.download import fetch_data_as_dataframe

router = APIRouter()

db_services = DBMS(
    model_path='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    collection_name='search',
    threshold=0.35
)

@router.post("/query/")
def query(data: db.QueryDB) -> Any:
    """
    Query the database

    Args:
        data: query data

    Returns:
        dataframe of answer
    """
    data_query = db_services.query(
        ques=data.query_text,
        threshold=data.threshold,
        limit=data.limit
    )
    # drop embedding column
    data_query = data_query.drop(columns=['embeddings'])
    if data.return_type_option in ['json', 'jsonl']:
        # convert dataframe to json for response to client
        data_query = data_query.to_json(orient='records',
                                        lines=True if data.return_type_option == 'jsonl' else False,
                                        force_ascii=False)
    else:
        data_query = data_query.to_csv(index=False, encoding='utf-8')
    return json.loads(data_query)

@router.post("/insert/")
def insert(data: db.InsertDB) -> Any:
    """
    Insert data to database

    Args:
        data: insert data

    Returns:
        status of insert
    """
    if "https" in data.path:
        data = fetch_data_as_dataframe(data.path)
    elif data.path or data.data:
        data_load = data.path if data.path else data.data
        # read data from path
        if data.data_type == 'csv':
            data = pd.read_csv(data_load, encoding='utf-8')
        elif data.data_type in ['json', 'jsonl']:
            data = pd.read_json(data_load, orient='records',
                                lines=True if data.data_type == 'jsonl' else False)
        else:
            return {"status": "Error", "message": "Data type is not supported"}

    # insert data to database
    db_services.insert(data)
    return {"status": "Success", "message": "Insert data successfully"}


