import os
import torch
import chromadb
import pandas as pd
from chromadb.config import Settings
from typing import Text, Optional, List, Dict
from sentence_transformers import SentenceTransformer
from tools.utils import clean_data, flatten_list


class DBMS:
    """
    Database management system for ChromaDB

    Attributes:
        device (Text): device to run model
        threshold (float): threshold to filter data
        model_path (Text): path to SentenceTransformer model
        model (SentenceTransformer): SentenceTransformer model
        collection_name (Text): name of collection to store data
        collection (chromadb.Collection): ChromaDB collection
    """

    def __init__(self,
                 model_path: Text,
                 threshold: Optional[float] = 0.8,
                 collection_name: Optional[Text] = 'search',
                 **kwargs):
        self.threshold = threshold
        self.model_path = model_path
        self.collection_name = collection_name
        self.device = 'cpu'
        if torch.cuda.is_available():
            self.device = 'cuda'
        self.model = SentenceTransformer(self.model_path, device=self.device)
        self.db = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=os.path.join(os.path.dirname(__file__), 'data')
        ))
        self.collection = self.db.get_or_create_collection(self.collection_name, metadata={"hnsw:space": "cosine"})
        self.kwargs = kwargs

    def query(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question from collection

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        input_em = self.model.encode([ques]).tolist()
        result = self.collection.query(
            query_embeddings=input_em,
            include=self.kwargs.get("include", ["documents", "metadatas", "embeddings", "distances"]),
        )
        result = flatten_list(result)
        result = pd.DataFrame(result)
        result = result[result['distances'] < self.threshold]
        if result.empty:
            return None
        result = clean_data(self.kwargs.get("pattern", None), result)
        return result

    def _transform(self, data: pd.DataFrame) -> Dict:
        """
        Transform data into ChromaDB format

        Args:
            data: dataframe of data

        Returns:
            Dict
        """
        data = data.to_dict(orient='list')
        data = flatten_list(data)
        return data

    def insert(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Insert data into collection

        Args:
            data: dataframe of data

        Returns:
            None
        """
        # remove ids column if exists
        if 'ids' in data:
            data = data.drop(columns=['ids'])
        # remove distance column if exists
        if 'distances' in data:
            data = data.drop(columns=['distances'])
        # remove duplicates ids
        data = data.drop_duplicates()
        # add ids column from last index of collection to length of data
        data['ids'] = list(range(self.collection.count(), self.collection.count() + len(data)))
        # convert ids column to string
        data['ids'] = data['ids'].astype(str)
        # print last record
        # finding the column has the type of string
        column_4_embedding = None
        for col in data.columns:
            if isinstance(data[col][0], str):
                column_4_embedding = col
                break
        # if not found, raise error
        if column_4_embedding is None:
            raise ValueError('Not found column has the type of string')
        data = clean_data(self.kwargs.get("pattern", None), data)
        # encode data
        data['embeddings'] = self.model.encode(data[column_4_embedding].tolist()).tolist()
        # check if metadata is not exists
        if 'metadatas' not in data:
            data['metadatas'] = [{"source": ""}] * len(data)
        self.collection.add(**self._transform(data))
        column_4_show = ['ids', 'documents', 'embeddings', 'metadatas']
        data = data[column_4_show]
        return data

    def update(self, data: pd.DataFrame):
        """
        Update data into collection

        Args:
            data: dataframe of data

        Returns:
            None
        """
        data = clean_data(self.kwargs.get("pattern", None), data)
        self.collection.update(**self._transform(data))

    def delete(self, data: List):
        """
        Delete data into collection

        Args:
            data: list of ids to delete

        Returns:
            None
        """
        self.collection.delete(
            ids=data
        )

    def get(self, data: Optional[List], **kwargs) -> Optional[pd.DataFrame]:
        """
        Get data from collection

        Args:
            data: list of ids to get

        Returns:
            dataframe of data
        """
        result = self.collection.get(
            ids=data,
            include=self.kwargs.get("include", ["documents", "metadatas", "embeddings", "distances"]),
            **kwargs
        )
        result = flatten_list(result)
        result = pd.DataFrame(result)
        return result

    def visualize(self):
        """
        Visualize collection

        Returns:
            None
        """
        from chromaviz import visualize_collection
        visualize_collection(self.collection)

    def auto_clean(self):
        data = self.collection.get(include=self.kwargs.get("include",
                                                           ["documents", "metadatas", "embeddings"]))
        data = pd.DataFrame(data)
        data = clean_data(self.kwargs.get("pattern", None), data)
        # get ids where documents is duplicated or length of documents has length less than 3
        data_remove = data.groupby('documents').filter(lambda x: len(x) > 1 or len(x['documents'].iloc[0]) < 3)
        data_remove = data_remove['ids'].tolist()
        # only keep records that does not exist in data_remove
        data = data[~data['ids'].isin(data_remove)]
        # update embeddings
        data["embeddings"] = self.model.encode(data["documents"]).tolist()
        self.update(data)
        # remove data
        if len(data_remove) > 0:
            self.delete(data_remove)

    def load_json(self, path: Text, cols: List = None):
        """
        Read data from json file

        Args:
            path: path to json file
            cols: list of columns to read

        Returns:
            dataframe of data
        """
        # check if file is jsonl or json
        data = None
        if path.endswith('.jsonl'):
            data = pd.read_json(path, lines=True, encoding='utf-8')
        else:
            data = pd.read_json(path, encoding='utf-8')

        if not data.empty:
            data = data[cols] if cols else data
            data = data.dropna()
            data = data.drop_duplicates()
            for col in data.columns:
                if isinstance(data[col][0], str):
                    data = data.rename(columns={col: 'documents'})
                elif isinstance(data[col][0], dict):
                    data = data.rename(columns={col: 'metadatas'})
            self.insert(data)
        else:
            raise ValueError('Not found data in file')
