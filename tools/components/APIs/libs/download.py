import requests
import pandas as pd
def fetch_data_as_dataframe(url):
    response = requests.get(url)

    if response.status_code == 200:
        content_type = response.headers.get('content-type')
        if content_type == 'application/json':
            data = response.json()
            df = pd.json_normalize(data)
            return df
        elif content_type == 'text/csv':
            data = response.text
            df = pd.read_csv(pd.compat.StringIO(data), encoding='utf-8')
            return df
        else:
            print("Unsupported content type:", content_type)
    else:
        print("Failed to fetch data. Status code:", response.status_code)

    return None
