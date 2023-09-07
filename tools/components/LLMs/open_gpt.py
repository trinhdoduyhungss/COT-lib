import ftfy
from typing import Text, Union, List

from tools.utils import clean_bot_answer
from tools.components.LLMs.OpenGPT import (GetGPT,
                                           YqChatGPT,
                                           OpChatGPT,
                                           LoChatGPT,
                                           OrChatGPT)

class OpenGPTBot:
    """
    Open AI bot with gpt_4_free
    """

    def __init__(self):
        """
        Initialize OpenAIBot
        """
        self._list_provider = [GetGPT, OpChatGPT, LoChatGPT, OrChatGPT, YqChatGPT]
        self._provider = None
        self._retry = len(self._list_provider)
        self.form = {
            "role": "user",
            "content": "hi"
        }

    @staticmethod
    def _get_answer(engine, form, **kwargs):
        try:
            response = engine.create_completion(model="gpt-3.5-turbo", messages=[form],
                                                  stream=engine.supports_stream, **kwargs)
            if not isinstance(response, str):
                full_text = ""
                for text in response:
                    full_text += text
                response = full_text
            return response
        except Exception as e:
            print(e)
            return None

    def ask(self, question: Text, **kwargs) -> Union[Text, List[Text]]:
        """
        Ask a question to the bot.

        Args:
            question (Text): Question to ask.

        Returns:
            Union[Text, List[Text]]: Response from the bot.
        """
        prompt = kwargs.get("prompt", "{}")
        question = question.replace('"', '\"')
        question = prompt.replace("{}", question)
        form = self.form.copy()
        form["content"] = str(question)
        res = "Tôi xin lỗi, tôi không hiểu câu hỏi của bạn."
        if not self._provider:
            for provider in self._list_provider:
                print("Try: ", provider.__name__)
                try:
                    engine = provider()
                    res_bot = self._get_answer(engine, form, **kwargs)
                    if res_bot:
                        res = res_bot
                        self._provider = engine
                        self._retry = len(self._list_provider)
                        break
                except Exception as e:
                    print(e)
                    pass
        else:
            try:
                print("Still try: ", self._provider.__name__)
                res_bot = self._get_answer(self._provider, form, **kwargs)
                if res_bot:
                    res = res_bot
                    print(res)
            except Exception as e:
                # print(e)
                self._provider = None
                self._retry -= 1
                if self._retry > 0:
                    res = self.ask(question, **kwargs)
        res = ftfy.fix_text(clean_bot_answer(res))
        print("===> ", res)
        return res


# if __name__ == "__main__":
#     bot = OpenGPTBot()
#     print(bot.ask(
#         "trừ bữa có nghĩa là gì? Nghĩa của từ trừ bữa - từ điển việt - việt: (ăn thức gì đó) thay cho bữa cơm hằng ngày. (ăn thức gì đó) thay cho bữa cơm hằng ngày. Ăn khoai trừ bữa."))
