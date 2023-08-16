import g4f
from g4f.models import ModelUtils
from typing import Text, Union, List

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
        self._setup()

    def _setup(self):
        if self.model in ModelUtils.convert:
            self.model = ModelUtils.convert[self.model]
            self.provider = self.model.best_provider
        else:
            raise Exception(f'The model: {self.model} does not exist')

    @property
    def params(self):
        if self.provider is not None:
            return self.provider.params
        else:
            return None

    def ask(self, question: Text) -> Union[Text, List[Text]]:
        """
        Ask a question to the bot.

        Args:
            question (Text): Question to ask.
            des (Text): Description of the question.

        Returns:
            Union[Text, List[Text]]: Response from the bot.
        """
        question = question.replace('"', '\"')
        question = self.prompt.format(question)
        form = self.form.copy()
        form["content"] = str(question)
        response = g4f.ChatCompletion.create(model=self.model, provider=self.provider,
                                             messages=[form],
                                             **self.kwargs)
        if not isinstance(response, str):
            full_text = ""
            for text in response:
                full_text += text
            response = full_text
        return response
