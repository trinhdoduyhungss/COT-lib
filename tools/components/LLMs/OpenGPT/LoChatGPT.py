import os
import re
import base64

from tools.components.LLMs.OpenGPT.BaseProvider import BaseProvider
from tools.components.LLMs.OpenGPT.libs.typing import Any, CreateResult


class LoChatGPT(BaseProvider):
    url = "https://opchatgpts.net"
    supports_gpt_35_turbo = True
    working = True

    def __init__(self):
        super().__init__()
        self._nonce = self._get_nonce()

    def create_completion(
            self,
            model: str,
            messages: list[dict[str, str]],
            stream: bool,
            **kwargs: Any,
    ) -> CreateResult:
        headers = {
            "authority": "opchatgpts.net",
            "accept": "*/*",
            "accept-language": "en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3",
            "content-type": "multipart/form-data; boundary=----",
            "origin": "https://opchatgpts.net",
            "referer": "https://opchatgpts.net/chatgpt-free-use/"
        }

        form_data = {
            "_wpnonce": self._nonce,
            "post_id": 28,
            "url": "https://opchatgpts.net/chatgpt-free-use",
            "action": "wpaicg_chat_shortcode_message",
            "message": messages[0]["content"],
            "bot_id": 0
        }

        res = self.send_request(
            method="POST",
            url="https://opchatgpts.net/wp-admin/admin-ajax.php",
            headers=headers,
            data=form_data
        )

        if res is None:
            return None

        yield res.json()["reply"]

    def _get_nonce(self) -> str:
        res = self.send_request(
            method="GET",
            url="https://opchatgpts.net/chatgpt-free-use/",
            headers={
                "Referer": "https://opchatgpts.net/chatgpt-free-use/"
            },
        )

        if res is None:
            return ""

        result = re.search(
            r'<script defer id="wpaicg-init-js-extra" src="(.*?)">',
            res.text,
        )

        if result is None:
            return ""

        src = result.group(1)
        decoded_string = base64.b64decode(src.split(",")[-1]).decode("utf-8")
        result = re.search(r'"search_nonce":"(.*?)"', decoded_string)
        return "" if result is None else result.group(1)
