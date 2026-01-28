from typing import Dict, Union, Any, List
from langchain.callbacks.base import BaseCallbackHandler
import threading

LOGGING_LOCK = threading.Lock()
LLM_INPUT = []

class MyCustomHandler(BaseCallbackHandler):
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        LOGGING_LOCK.acquire()
        LLM_INPUT.extend(prompts)
        LOGGING_LOCK.release()