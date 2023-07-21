import os
import time
import torch
import asyncio
import chromadb
import itertools
import numpy as np
from typing import Text, Optional

import pandas as pd
from tabulate import tabulate
from scipy.spatial import distance
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from kwextractor.process.extract_keywords import ExtractKeywords

from crawls.tools.content_extractor import AskInternet

pd.options.mode.chained_assignment = None


class SearchEngine:
    def __init__(self, model_path: Text, collection_name: Optional[Text] = 'search', threshold: Optional[float] = 0.8):
        """
        Search engine using ChromaDB and SentenceTransformer for semantic search and store data

        Args:
            model_path: path to SentenceTransformer model
            collection_name: name of collection to store data (default: search)
            threshold: threshold to filter data (default: 0.8)

        Return:
            None
        """
        self.threshold = threshold
        self.ask_internet = AskInternet()
        self.get_keywords = ExtractKeywords()
        self.collection_name = collection_name
        if not torch.cuda.is_available():
            self.model = SentenceTransformer(model_path, device='cpu')
        else:
            self.model = SentenceTransformer(model_path, device='cuda')
        self.db = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=os.path.join(os.path.dirname(__file__), 'data')
        ))
        self.collection = self.db.get_or_create_collection(self.collection_name, metadata={"hnsw:space": "cosine"})

    def _embedding(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add embedding column to dataframe

        Args:
            data: data crawled from internet

        Returns:
            data with embedding column
        """
        data['embedding'] = self.model.encode(data['text'].tolist()).tolist()
        return data

    async def _search_internet(self, ques: Text):
        """
        Search answer for question from internet

        Args:
            ques: question

        """
        data_internet = await self.ask_internet.run(ques)
        if data_internet[1] is None:
            return None
        elif data_internet[1].empty:
            return None
        data_internet = self._embedding(data_internet[1])
        data_internet["index"] = data_internet.index
        data_internet["index"] = data_internet["index"].apply(lambda x: str(x))
        data_internet["source"] = data_internet.apply(lambda x: {"source": x["source"], "doc": x["doc"]}, axis=1)
        # ques_kw = " ".join(self.get_keywords.extract_keywords(ques).split(","))
        # if ques_kw:
        #     ques = ques_kw
        input_em = self.model.encode([ques]).tolist()[0]
        data_internet["distances"] = data_internet["embedding"].apply(lambda x: distance.cosine(x, input_em))
        data_internet = data_internet[data_internet["distances"] > 0]
        data_internet = data_internet.sort_values(by=["distances"], ascending=True)
        sum_em = np.sum([input_em, data_internet["embedding"].iloc[0]], axis=0).tolist()
        data_internet["embedding"].iloc[0] = sum_em
        print("\n")
        print(tabulate(data_internet.head(), headers='keys', tablefmt='psql'))
        try:
            self.collection.add(
                documents=data_internet["text"].tolist(),
                embeddings=data_internet["embedding"].tolist(),
                metadatas=data_internet["source"].tolist(),
                ids=data_internet["index"].tolist(),
            )
        except Exception as e:

            # print(e)
            pass
        return data_internet

    async def _search_collection(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question from collection

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        # ques_kw = " ".join(self.get_keywords.extract_keywords(ques).split(","))
        # if ques_kw:
        #     ques = ques_kw
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
        return result

    async def pipeline(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        if self.collection.count() < 2:
            return await self._search_internet(ques)
        else:
            result = await self._search_collection(ques)
            if result is None:
                return await self._search_internet(ques)
            return result

    def search(self, ques: Text) -> Optional[pd.DataFrame]:
        data_found = asyncio.run(self.pipeline(ques))
        if data_found is not None:
            if "documents" in data_found.columns:
                data_found = data_found.drop(columns=["documents"])
                data_found["source"] = data_found["metadatas"].apply(lambda x: x["source"])
                data_found["doc"] = data_found["metadatas"].apply(lambda x: x["doc"])
                data_found = data_found.drop(columns=["metadatas"])
                data_found = data_found[["ids", "doc", "source", "distances", "embeddings"]]
        return data_found


# if __name__ == '__main__':
#     search_engine = SearchEngine(model_path='keepitreal/vietnamese-sbert',
#                                  collection_name='search', threshold=0.6)
#     start_time = time.time()
#     result_search = search_engine.search("Ai chế tạo ra bom nguyên tử?")
#     if result_search is not None:
#         # result_search = result_search.drop(columns=['embeddings', 'ids'])
#         print(tabulate(result_search, headers='keys', tablefmt='psql'))
#     else:
#         print("No result!")
#     print(f"Time: {time.time() - start_time}s")
# async def main():
#     search_engine = SearchEngine(model_path='keepitreal/vietnamese-sbert',
#                                  collection_name='search', threshold=0.6)
#     start_time = time.time()
#     result_search = await search_engine.search("Ai chế tạo ra bom nguyên tử?")
#     if result_search is not None:
#         result_search = result_search.drop(columns=['embeddings', 'ids'])
#         print(tabulate(result_search, headers='keys', tablefmt='psql'))
#     else:
#         print("No result!")
#     print(f"Time: {time.time() - start_time}s")
#
# asyncio.run(main())
