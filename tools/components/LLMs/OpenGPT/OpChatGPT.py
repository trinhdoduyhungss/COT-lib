from tools.components.LLMs.OpenGPT.BaseProvider import BaseProvider
from tools.components.LLMs.OpenGPT.libs.typing import Any, CreateResult


class OpChatGPT(BaseProvider):
    url = "https://opchatgpts.net"
    working = True
    supports_gpt_35_turbo = True

    def create_completion(
            self,
            model: str,
            messages: list[dict[str, str]],
            stream: bool,
            **kwargs: Any,
    ) -> CreateResult:
        temperature = kwargs.get("temperature", 0.8)
        max_tokens = kwargs.get("max_tokens", 1024)
        system_prompt = kwargs.get(
            "system_prompt",
            "Converse as if you were an AI assistant. Be friendly, creative.",
        )
        payload = self._create_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        res = self.send_request(
            method="POST",
            url="https://opchatgpts.net/wp-json/ai-chatbot/v1/chat",
            json=payload
        )

        if res is None:
            return None

        yield res.json()["reply"]

    @staticmethod
    def _create_payload(
            messages: list[dict[str, str]],
            temperature: float,
            max_tokens: int,
            system_prompt: str,
    ):
        return {
            "env": "chatbot",
            "session": "N/A",
            "prompt": "\n",
            "context": system_prompt,
            "messages": messages,
            "newMessage": messages[::-1][0]["content"],
            "userName": '<div class="mwai-name-text">User:</div>',
            "aiName": '<div class="mwai-name-text">AI:</div>',
            "model": "gpt-3.5-turbo",
            "temperature": temperature,
            "maxTokens": max_tokens,
            "maxResults": 1,
            "apiKey": "",
            "service": "openai",
            "embeddingsIndex": "",
            "stop": "",
        }
