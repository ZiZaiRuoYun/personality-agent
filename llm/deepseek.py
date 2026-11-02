import os

import httpx
from dotenv import load_dotenv


load_dotenv()


class DeepSeekClient:
    """
    DeepSeek Provider Adapter。

    这里只处理 DeepSeek API 的具体格式。
    """

    def __init__(self) -> None:
        self.api_key = os.getenv(
            "DEEPSEEK_API_KEY"
        )

        self.base_url = os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        ).rstrip("/")

        self.model = os.getenv(
            "LLM_MODEL",
            "deepseek-flash",
        )

        if not self.api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not configured."
            )

    def generate_json(
        self,
        messages: list[dict],
    ) -> str:
        url = (
            f"{self.base_url}"
            "/chat/completions"
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_object"
            },
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
        }

        with httpx.Client(
            timeout=60.0
        ) as client:
            response = client.post(
                url,
                json=payload,
                headers=headers,
            )

            response.raise_for_status()

            data = response.json()

        content = (
            data["choices"][0]
            ["message"]["content"]
        )

        if (
            content is None
            or not content.strip()
        ):
            raise RuntimeError(
                "DeepSeek returned empty JSON content."
            )

        return content