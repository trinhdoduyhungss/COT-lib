import pandas as pd
from typing import Text, Optional

from tools.dbms import DBMS
from tools.components.APIs.google import Google
from tools.components.LLMs.edge_gpt import EdgeBot



class SearchEngine:
    """
    Search question in existing data or ask bot to answer question

    Attributes:
        bot (EdgeBot): EdgeGPT Chatbot
    """

    def __init__(self,
                 model_path: Text,
                 threshold: Optional[float] = 0.8,
                 collection_name: Optional[Text] = 'search',
                 use_bot: Optional[bool] = True,
                 **kwargs):
        """
        Search question in existing data or ask bot to answer question

        Args:
            model_path: path to SentenceTransformer model
            collection_name: name of collection to store data (default: search)
            threshold: threshold to filter data (default: 0.8)

        Return:
            None
        """
        self.google = Google()
        self.use_bot = use_bot
        self.bot = EdgeBot(**kwargs)
        self.db = DBMS(model_path=model_path, threshold=threshold, collection_name=collection_name, **kwargs)

    def search_db(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question from collection

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        print("\nSearch DB")
        result = self.db.query(ques)
        return result

    def ask_google(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Search answer for question from Google

        Args:
            ques: question

        Returns:
            dataframe of answer
        """
        print("\nAsk Google")
        result = self.google.ask(ques)
        if result:
            df = pd.DataFrame(result)
            try:
                df = self.db.insert(df)
            except Exception as e:
                print(e)
                pass
            return df
        return None

    def ask_bot(self, ques: Text) -> Optional[pd.DataFrame]:
        """
        Ask question to bot

        Args:
            ques: question

        Returns:
            answer
        """
        print("\nAsk Bot")
        query = self.bot.ask(ques)
        if query is None:
            return None
        answer = query.output
        source = {"source": query.sources}
        df = pd.DataFrame({
            'documents': [answer],
            'metadatas': [source]
        })
        try:
            df = self.db.insert(df)
        except Exception as e:
            # print(e)
            pass
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
            result = self.ask_google(ques)
            if result is None and self.use_bot:
                result = self.ask_bot(ques)
            return result
        else:
            result = self.search_db(ques)
            if result is None:
                result = self.ask_google(ques)
                if result is None and self.use_bot:
                    result = self.ask_bot(ques)
            return result

    def search(self, ques: Text) -> Optional[pd.DataFrame]:
        data_found = self.pipeline(ques)
        return data_found
