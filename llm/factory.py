import os

from dotenv import load_dotenv

from llm.base import LLMClient
from llm.deepseek import DeepSeekClient


load_dotenv()


def create_llm_client() -> LLMClient:
    """
    根据环境变量创建对应的 LLM Provider。

    上层代码不需要知道具体 Provider。
    """

    provider = os.getenv(
        "LLM_PROVIDER",
        "deepseek",
    ).lower()

    if provider == "deepseek":
        return DeepSeekClient()

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )