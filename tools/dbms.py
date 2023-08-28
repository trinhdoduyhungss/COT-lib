import os
import re
import chromadb
import pandas as pd
from chromadb.config import Settings
from typing import Text, Optional, List, Dict
from tools.utils import clean_data, flatten_list
from sentence_transformers import SentenceTransformer


class DBMS:
    """
    Database management system for ChromaDB

    Attributes:
        device (Text): device to run model
        threshold (float): threshold to filter data
        model_path (Text): path to SentenceTransformer model huggingface
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
        try:
            import torch
            if torch.cuda.is_available():
                self.device = 'cuda'
        except ImportError:
            pass
        self.model = SentenceTransformer(self.model_path, device=self.device)
        self.db = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=os.path.join(os.path.dirname(__file__), 'data')
        ))
        self.collection = self.db.get_or_create_collection(self.collection_name, metadata={"hnsw:space": "cosine"})
        print("Current has {} records".format(self.collection.count()))
        self.kwargs = kwargs

    def query(self, ques: Text, **kwargs) -> Optional[pd.DataFrame]:
        """
        Search answer for question from collection

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        print("Query in collection has {} records".format(self.collection.count()))
        print("Get number of records to query: {}".format(kwargs.get("limit", 10)))
        limit = kwargs.get("limit", 10)
        input_em = self.model.encode([ques]).tolist()
        threshold = kwargs.get("threshold", self.threshold)
        result = self.collection.query(
            query_embeddings=input_em,
            include=self.kwargs.get("include", ["documents", "metadatas", "embeddings", "distances"]),
            n_results=limit if limit > 10 else 10
        )
        result = flatten_list(result)
        result["distances"] = result["distances"][0][:len(result["ids"])]
        result = pd.DataFrame(result)
        result = result[result['distances'] < threshold]
        if result.empty:
            return None
        result = clean_data(self.kwargs.get("pattern", None), result)
        return result.head(limit)

    @staticmethod
    def _transform(data: pd.DataFrame) -> Dict:
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
        print("Before insert, collection has {} records".format(self.collection.count()))

        # Remove ids column if exists
        if 'ids' in data:
            data.drop(columns=['ids'], inplace=True)  # Use inplace parameter

        # Remove distance column if exists
        if 'distances' in data:
            data.drop(columns=['distances'], inplace=True)  # Use inplace parameter

        # Remove duplicates
        data.drop_duplicates(subset=["documents"], inplace=True)  # Use inplace parameter

        # Add ids column
        ids_range = range(self.collection.count(), self.collection.count() + len(data))
        data['ids'] = list(ids_range)

        # Convert ids column to string
        data['ids'] = data['ids'].astype(str)

        # Finding the column for embedding
        column_4_embedding = None
        for col in data.columns:
            if isinstance(data[col][0], str):
                column_4_embedding = col
                break

        # Raise error if column for embedding is not found
        if column_4_embedding is None:
            raise ValueError('Not found column with the type of string')

        # Clean data
        data = clean_data(self.kwargs.get("pattern", None), data)

        embeddings = self.model.encode(data[column_4_embedding].tolist()).tolist()
        data['embeddings'] = embeddings

        # Check if metadatas column exists
        if 'metadatas' not in data:
            data['metadatas'] = [{"source": ""}] * len(data)
        self.db.persist()
        self.collection.add(**self._transform(data))
        self.db.persist()
        print("Now collection has {} records".format(self.collection.count()))
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
        data = data.drop_duplicates(["documents"])
        data_remove = data[data['documents'].str.len() < 3]
        data_remove = data_remove['ids'].tolist()
        print("Remove {} records".format(len(data_remove)))
        # only keep records that does not exist in data_remove
        data = data[~data['ids'].isin(data_remove)]
        print(data[["documents", "metadatas"]].head())
        # update embeddings
        data["embeddings"] = self.model.encode(data["documents"]).tolist()
        data["documents"] = data["documents"].apply(lambda x: re.sub(r"^.*#\s+", "", x))
        self.update(data)
        # show data with documents and metadatas
        print(data[["documents", "metadatas"]].head())
        # remove data
        if len(data_remove) > 0:
            self.delete(data_remove)

    def from_pandas(self, data: pd.DataFrame):
        """
        Insert data from pandas dataframe

        Args:
            data: dataframe of data

        Returns:
            None
        """
        data = data.dropna()
        data = data.drop_duplicates()
        if "documents" not in data.columns:
            for col in data.columns:
                if isinstance(data[col][0], str):
                    data = data.rename(columns={col: 'documents'})
                elif isinstance(data[col][0], dict):
                    data = data.rename(columns={col: 'metadatas'})
        if 'metadatas' not in data.columns:
            data['metadatas'] = [{"source": ""}] * len(data)
        self.insert(data)

    def from_json(self, path: Text, cols: List = None, **kwargs):
        """
        Read data from json file

        Args:
            path: path to json file
            cols: list of columns to read

        Returns:
            None
        """
        data = pd.read_json(path,
                            lines=True if path.endswith('.jsonl') else False,
                            encoding='utf-8')

        if not data.empty:
            if kwargs.get("merge_columns"):
                columns_to_merge = kwargs.get("merge_columns")
                target = columns_to_merge[-1]
                columns_to_merge = columns_to_merge[:-1]
                for col in columns_to_merge:
                    data[target] = data[col] + " # " + data[target]
            data = data[cols] if cols else data
            print(data.head())
            self.from_pandas(data)
            print(f'Load {self.collection.count()} data successfully')
        else:
            raise ValueError('Not found data in file')
