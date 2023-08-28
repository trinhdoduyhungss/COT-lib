import os
import openai
from dotenv import load_dotenv
from typing import Text, Union, List
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class OpenAIBot:
    """
    Open AI bot with gpt_4_free
    """

    def __init__(self, **kwargs):
        """
        Initialize OpenAIBot

        Args:
            prompt (Text): Prompt to use.
            model (Text): Model to use.
        """
        self.prompt = kwargs.get("prompt", "")
        self.model = kwargs.get("model", "gpt-3.5-turbo")
        # remove prompt and model from kwargs
        kwargs.pop("prompt", None)
        kwargs.pop("model", None)
        self.kwargs = kwargs
        self.form = {
            "role": "user",
            "content": "hi"
        }
        print("You are using OpenAIBot with model: {}".format(self.model))

    def ask(self, question: Text, **kwargs) -> Union[Text, List[Text]]:
        """
        Ask a question to the bot.

        Args:
            question (Text): Question to ask.

        Returns:
            Union[Text, List[Text]]: Response from the bot.
        """
        question = question.replace('"', '\"')
        prompt = kwargs.get("prompt", self.prompt)
        if kwargs.get("highlights"):
            build_highlight = ""
            for highlight in range(len(kwargs.get("highlights"))):
                if highlight == len(kwargs.get("highlights")) - 1:
                    build_highlight += "and " + kwargs.get("highlights")[highlight]
                else:
                    build_highlight += kwargs.get("highlights")[highlight] + ", "
            print(build_highlight)
            prompt = prompt.replace("###", build_highlight)
        question = prompt.replace("{}", question)
        print(question)
        form = self.form.copy()
        form["content"] = str(question)
        response = openai.ChatCompletion.create(model=self.model, messages=[form], **self.kwargs)
        response = response.choices[0].message.content
        if not isinstance(response, str):
            full_text = ""
            for text in response:
                full_text += text
            response = full_text
        return response
