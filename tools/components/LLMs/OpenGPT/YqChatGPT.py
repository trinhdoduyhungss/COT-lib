# -*- coding: utf-8 -*-
from tools.components.LLMs.OpenGPT.BaseProvider import BaseProvider
from tools.components.LLMs.OpenGPT.libs.typing import Any, CreateResult


class YqChatGPT(BaseProvider):
    url = "https://chat9.yqcloud.top"
    supports_gpt_35_turbo = True
    working = True

    def create_completion(
            self,
            model: str,
            messages: list[dict[str, str]],
            stream: bool,
            **kwargs: Any,
    ) -> CreateResult:
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://chat9.yqcloud.top",
        }

        payloads = {
            "prompt": self._format_prompt(messages),
            "network": True,
            "system": "",
            "withoutContext": False,
            "stream": False,
            "userId": "#/chat/1693025544336"
        }

        res = self.send_request(
            method="POST",
            url="https://api.aichatos.cloud/api/generateStream",
            headers=headers,
            json=payloads
        )

        if res is None:
            return None
        yield res.text

    @staticmethod
    def _format_prompt(messages: list[dict[str, str]], add_special_tokens=False):
        if add_special_tokens or len(messages) > 1:
            formatted = "\n".join(
                ["%s: %s" % ((message["role"]).capitalize(), message["content"]) for message in messages]
            )
            return f"{formatted}\nAssistant:"
        else:
            return messages.pop()["content"]
