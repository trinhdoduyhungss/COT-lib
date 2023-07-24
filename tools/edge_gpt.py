from typing import Text, Optional
from EdgeGPT.EdgeUtils import Query, Cookie


class Bot:
    """
    EdgeGPT Chatbot

    Attributes:
        dir_cookies (Text): Path to cookies folder.
    """

    def __init__(self, dir_cookies: Optional[Text] = "./cookies", **kwargs):
        self.dir_cookies = None
        self.kwargs = kwargs
        self.update_cookie(dir_cookies=dir_cookies)

    def update_cookie(self, dir_cookies: Text):
        self.dir_cookies = dir_cookies
        Cookie.dir_path = self.dir_cookies

    def ask(self, question: Text) -> Query:
        """
        Ask a question to the bot.

        Args:
            question (Text): Question to ask.

        Returns:
            Query: Query object.
        """
        question = self.kwargs.get("prompt", "") + question
        query = Query(question, style=self.kwargs.get("style", "balanced"), locale=self.kwargs.get("locale", "vi-VN"))
        return query
