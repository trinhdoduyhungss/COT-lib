import uvicorn
import pandas as pd
from typing import Any
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.api.schemas import db
from tools.components.APIs.libs.download import fetch_data_as_dataframe
from app.services import get_db_services_instance, get_query_db_json, get_bot_services_instance

middleware = [
    Middleware(CORSMiddleware,
               allow_origins=["*"],
               allow_credentials=True,
               allow_methods=["*"],
               allow_headers=["*"], )
]

app = FastAPI(middleware=middleware)

@app.get("/")
async def root():
    """Root page."""
    return {"text": f"Hello, This is an api for COT backend"}

@app.post('/ask/')
async def ask(data: db.Ask) -> Any:
    """
    Ask a question to the bot.

    Args:
        data : Data to ask.

    Returns:
        Union[Text, List[Text]]: Response from the bot.
    """
    bot_services = get_bot_services_instance()
    answer = bot_services.ask(data.question)
    return {"answer": answer}

@app.post("/query/")
async def query(data: db.QueryDB) -> Any:
    """
    Query the database

    Args:
        data: query data

    Returns:
        dataframe of answer
    """
    db_services = get_db_services_instance()
    data_query = db_services.query(
        ques=data.query_text,
        threshold=data.threshold,
        limit=data.limit
    )
    # check if data_query is empty
    if data_query is None:
        return [{"metadatas": {}}]
    return get_query_db_json(data_query, data.return_type_option)

@app.post("/insert/")
async def insert(data: db.InsertDB) -> Any:
    """
    Insert data to database

    Args:
        data: insert data

    Returns:
        status of insert
    """
    db_services = get_db_services_instance()
    main_column_name = data.main_column_name
    if "https" in data.path:
        data = fetch_data_as_dataframe(data.path, authen=data.authen)
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
    if not isinstance(data, pd.DataFrame):
        return {"status": "Error", "message": "Data is not supported"}
    # make main_column_name to "documents" and all other columns to "metadatas"
    # rename main_column_name to "documents"
    data = data.rename(columns={main_column_name: 'documents'})
    # merge all other columns to "metadatas" as dict
    data['metadatas'] = data.drop(columns=['documents']).to_dict('records')
    # remove all columns except "documents" and "metadatas"
    data = data[['documents', 'metadatas']]
    # insert data to database
    db_services.insert(data)
    return {"status": "Success", "message": "Insert data successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000, workers=1)
