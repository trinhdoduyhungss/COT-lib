import os
import re
import torch
import chromadb
import itertools
import pandas as pd
from typing import Text, Optional
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from tools.edge_gpt import Bot


class SearchEngine:
    """
    Search question in existing data or ask bot to answer question

    Attributes:
        model_path (Text): path to SentenceTransformer model
        collection_name (Text): name of collection to store data
        threshold (float): threshold to filter data
        bot (Bot): EdgeGPT Chatbot
    """

    def __init__(self,
                 model_path: Text,
                 threshold: Optional[float] = 0.8,
                 collection_name: Optional[Text] = 'search',
                 **kwargs):
        """
        Search engine using ChromaDB and SentenceTransformer for semantic search and store data

        Args:
            model_path: path to SentenceTransformer model
            collection_name: name of collection to store data (default: search)
            threshold: threshold to filter data (default: 0.8)

        Return:
            None
        """
        self.bot = Bot(**kwargs)
        self.threshold = threshold
        self.model_path = model_path
        self.collection_name = collection_name
        if not torch.cuda.is_available():
            self.model = SentenceTransformer(self.model_path, device='cpu')
        else:
            self.model = SentenceTransformer(self.model_path, device='cuda')
        self.db = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=os.path.join(os.path.dirname(__file__), 'data')
        ))
        self.collection = self.db.get_or_create_collection(self.collection_name, metadata={"hnsw:space": "cosine"})

    def _search_collection(self, ques: Text) -> Optional[pd.DataFrame]:
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
            include=["documents", "embeddings", "metadatas", "distances"]
        )
        result = pd.DataFrame({
            'ids': list(itertools.chain.from_iterable(result['ids'])),
            'embeddings': list(itertools.chain.from_iterable(result['embeddings'])),
            'documents': list(itertools.chain.from_iterable(result['documents'])),
            'metadatas': list(itertools.chain.from_iterable(result['metadatas'])),
            'distances': list(itertools.chain.from_iterable(result['distances']))
        })
        result = result[result['distances'] < self.threshold]
        if result.empty:
            return None
        result['documents'] = result['documents'].apply(lambda x: re.sub(r'\[\^\d+\^]', '', x,
                                                                         flags=re.MULTILINE | re.DOTALL))
        return result

    def ask_bot(self, ques: Text) -> pd.DataFrame:
        """
        Ask question to bot

        Args:
            ques: question

        Returns:
            answer
        """
        query = self.bot.ask(ques)
        answer = query.output
        source = {"source": query.sources}
        df = pd.DataFrame({
            'ids': [str(self.collection.count() + 1)],
            'documents': [answer],
            'embeddings': [self.model.encode([answer]).tolist()[0]],
            'metadatas': [source],
            'distances': [0]
        })
        df['documents'] = df['documents'].apply(lambda x: re.sub(r'\[\^\d+\^]', '', x, flags=re.MULTILINE | re.DOTALL))
        try:
            self.collection.add(
                documents=[answer],
                embeddings=df['embeddings'].tolist(),
                metadatas=[source],
                ids=df['ids'].tolist()
            )
        except Exception as e:
            print(e)

        return df

    def pipeline(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question from collection or ask bot

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        if self.collection.count() < 20:
            return self.ask_bot(ques)
        else:
            result = self._search_collection(ques)
            if result is None:
                return self.ask_bot(ques)
            return result

    def search(self, ques: Text) -> Optional[pd.DataFrame]:
        data_found = self.pipeline(ques)
        return data_found


# if __name__ == '__main__':
#     import time
#     from tabulate import tabulate
#     search_engine = SearchEngine(model_path='keepitreal/vietnamese-sbert',
#                                  prompt="""From the internet results, you should write a shortest answer with the rules:
# - Focus to the main information for answering my question below
# - No citation needed
# - Make sure your answer must be cleaned, easy to read, and natural
# My question:""",
#                                  echo=True,
#                                  collection_name='search',
#                                  threshold=0.6)
#     start_time = time.time()
#     result_search = search_engine.search("a-tua-đờ-rôn có nghĩa là gì")
#     if result_search is not None:
#         # result_search = result_search.drop(columns=['embeddings', 'ids'])
#         print(tabulate(result_search, headers='keys', tablefmt='psql'))
#     else:
#         print("No result!")
#     print(f"Time: {time.time() - start_time}s")
