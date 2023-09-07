import asyncio
from abc import ABC, abstractmethod

from tools.components.APIs.libs.req_agents import CrawlUrl
from tools.components.LLMs.OpenGPT.libs.asynctask import RunThread
from tools.components.LLMs.OpenGPT.libs.typing import Any, CreateResult

class BaseProvider(ABC):
    url: str
    working = False
    needs_auth = False
    supports_stream = False
    supports_gpt_35_turbo = False
    supports_gpt_4 = False

    def __init__(self):
        self._req_agent = CrawlUrl()
        self._tasks = None

    def _get_task(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        self._tasks = loop

    def _add_task(self, task, *args, **kwargs):
        print(self._tasks)
        if self._tasks:
            thread = RunThread(task, args, kwargs)
            thread.start()
            thread.join()
            return thread.result
        else:
            return asyncio.run(task(*args, **kwargs))

    def send_request(self, url, **kwargs):
        # add timeout to kwargs
        kwargs["timeout"] = 1000
        self._get_task()
        return self._add_task(self._req_agent.crawl_url, url, **kwargs)

    @abstractmethod
    def create_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool,
        **kwargs: Any,
    ) -> CreateResult:
        raise NotImplementedError()

    @classmethod
    @property
    def params(cls):
        params = [
            ("model", "str"),
            ("messages", "list[dict[str, str]]"),
            ("stream", "bool"),
        ]
        param = ", ".join([": ".join(p) for p in params])
        return f"{cls.__name__} supports: ({param})"
