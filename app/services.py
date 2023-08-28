import json
from tools.dbms import DBMS
from typing import Any, Text
from tools.components.LLMs.open_gpt import OpenGPTBot

db_services = None


def get_db_services_instance():
    global db_services
    if db_services is None:
        db_services = DBMS(
            model_path='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            collection_name='search',
            threshold=0.35
        )
    return db_services


def get_query_db_json(data_query: Any, return_type: Text):
    # drop embedding column
    data_query = data_query.drop(columns=['embeddings'])
    if return_type in ['json', 'jsonl']:
        # convert dataframe to json for response to client
        data_query = data_query.to_json(orient='records',
                                        lines=True if return_type == 'jsonl' else False,
                                        force_ascii=False)
    else:
        data_query = data_query.to_csv(index=False, encoding='utf-8')
    return json.loads(data_query)


bot_services = None


def get_bot_services_instance():
    global bot_services
    if bot_services is None:
        bot_services = OpenGPTBot()
    return bot_services
