import os
import requests
from openai import OpenAI


class OllamaGenerationProvider:
    def __init__(self, model_name="llama3.1", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


class OpenAIGenerationProvider:
    def __init__(self, model_name="gpt-4o-mini", api_key=None):
        self.model_name = model_name
        resolved_api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = OpenAI(api_key=resolved_api_key)

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content