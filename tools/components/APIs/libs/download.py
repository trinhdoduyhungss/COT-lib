# -*- coding: utf-8 -*-
import requests
import pandas as pd
from io import StringIO
from typing import Optional

def fetch_data_as_dataframe(url: str, **kwargs) -> Optional[pd.DataFrame]:
    if kwargs.get('authen', None):
        headers = {'Authorization': kwargs.get('authen')}
        response = requests.request("GET", url, headers=headers, data={})
    else:
        response = requests.request("GET", url, data={})

    if response.status_code == 200:
        content_type = response.headers.get('content-type')
        if content_type == 'application/json':
            data = response.json()
            df = pd.read_json(data, encoding='utf-8-sig', orient='records', lines=True if '},' not in str(data) else False)
            return df
        elif content_type == 'text/csv':
            data = response.text.encode('latin-1').decode('utf-8')
            df = pd.read_csv(StringIO(data), encoding='utf-8-sig')
            return df
        else:
            print("Unsupported content type:", content_type)
    else:
        print("Failed to fetch data. Status code:", response.status_code)

    return None
