from typing import Protocol


class LLMClient(Protocol):
    """
    所有 LLM Provider 都必须实现的统一接口。

    Memory Engine 不应该知道底层到底是：
    - DeepSeek
    - OpenAI
    - Qwen
    - Ollama
    - 其他模型

    它只关心：
    messages -> JSON string
    """

    def generate_json(
        self,
        messages: list[dict],
    ) -> str:
        ...