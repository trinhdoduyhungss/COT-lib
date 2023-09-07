from tools.components.LLMs.OpenGPT.BaseProvider import BaseProvider
from tools.components.LLMs.OpenGPT.libs.typing import Any, CreateResult

class OrChatGPT(BaseProvider):
    url = "https://chat-gpt.org/chat"
    working = True
    supports_gpt_35_turbo = True

    def create_completion(
            self,
            model: str,
            messages: list[dict[str, str]],
            stream: bool,
            **kwargs: Any,
    ) -> CreateResult:
        chat = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
        chat += "\nassistant: "

        headers = {
            "authority": "chat-gpt.org",
            "accept": "*/*",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://chat-gpt.org",
            "pragma": "no-cache",
            "referer": "https://chat-gpt.org/chat"
        }

        json_data = {
            "message": chat,
            "temperature": kwargs.get('temperature', 0.5),
            "presence_penalty": 0,
            "top_p": kwargs.get('top_p', 1),
            "frequency_penalty": 0,
        }

        res = self.send_request(
            method="POST",
            url="https://chat-gpt.org/api/text",
            headers=headers,
            json=json_data
        )

        if res is None:
            return None

        if not res.json()['response']:
            print("Error Response: ", res.json())
            return None
        yield res.json()["message"]
