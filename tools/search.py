import pandas as pd
from typing import Text, Optional

from tools.dbms import DBMS
from tools.edge_gpt import Bot


class SearchEngine:
    """
    Search question in existing data or ask bot to answer question

    Attributes:
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
        self.db = DBMS(model_path=model_path, threshold=threshold, collection_name=collection_name, **kwargs)

    def search_db(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question from collection

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        result = self.db.query(ques)
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
            'documents': [answer],
            'metadatas': [source]
        })
        try:
            df = self.db.insert(df)
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
        if self.db.collection.count() < 20:
            return self.ask_bot(ques)
        else:
            result = self.search_db(ques)
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
