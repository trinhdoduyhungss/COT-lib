import os
import json
import uuid
import time
from Crypto.Cipher import AES

from tools.components.LLMs.OpenGPT.BaseProvider import BaseProvider
from tools.components.LLMs.OpenGPT.libs.typing import Any, CreateResult

class GetGPT(BaseProvider):
    url = "https://chat.getgpt.world/"
    supports_stream = True
    working = True
    supports_gpt_35_turbo = True

    def create_completion(
            self,
            model: str,
            messages: list[dict[str, str]],
            stream: bool,
            **kwargs: Any,
    ) -> CreateResult:
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://chat.getgpt.world/"
        }
        data = json.dumps(
            {
                "messages": messages,
                "frequency_penalty": kwargs.get("frequency_penalty", 0),
                "max_tokens": kwargs.get("max_tokens", 1024),
                "model": "gpt-3.5-turbo",
                "presence_penalty": kwargs.get("presence_penalty", 0),
                "temperature": kwargs.get("temperature", 1),
                "top_p": kwargs.get("top_p", 1),
                "stream": True,
                "uuid": str(uuid.uuid4()),
            }
        )

        res = self.send_request(
            method="POST",
            url="https://chat.getgpt.world/api/chat/stream",
            headers=headers,
            json={"signature": self._encrypt(data)},
            stream=True
        )

        if res is None:
            return None

        for line in res.iter_lines():
            if b"content" in line:
                line_json = json.loads(line.decode("utf-8").split("data: ")[1])
                yield line_json["choices"][0]["delta"]["content"]

    def _encrypt(self, e: str):
        t = os.urandom(8).hex().encode("utf-8")
        n = os.urandom(8).hex().encode("utf-8")
        r = e.encode("utf-8")
        cipher = AES.new(t, AES.MODE_CBC, n)
        ciphertext = cipher.encrypt(self._pad_data(r))
        return ciphertext.hex() + t.decode("utf-8") + n.decode("utf-8")

    @staticmethod
    def _pad_data(data: bytes) -> bytes:
        block_size = AES.block_size
        padding_size = block_size - len(data) % block_size
        padding = bytes([padding_size] * padding_size)
        return data + padding
