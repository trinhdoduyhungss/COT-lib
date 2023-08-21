from typing import *

from pydantic import BaseModel

class QueryDB(BaseModel):
    query_text: Text
    threshold: Optional[float] = 0.8
    limit: Optional[int] = 10
    return_type_option: Optional[Text] = 'json'

class InsertDB(BaseModel):
    data_type: Text
    data_name: Text
    data: Optional[Text] = None
    path: Optional[Text] = None

