import requests

from .base_provider import GenerationProvider
from generation.exceptions import GenerationAPIError


class OllamaGenerationProvider(GenerationProvider):
    """Provider for local chat models served through Ollama."""

    def __init__(self, model_name: str = "llama3.1", base_url: str = "http://localhost:11434"):
        super().__init__(model_name=model_name)
        self._base_url = base_url.rstrip("/")

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise GenerationAPIError(f"Ollama chat call failed: {e}") from e

        data = response.json()
        message = data.get("message")
        if message is None or "content" not in message:
            raise GenerationAPIError("Unexpected Ollama response: missing 'message.content'")

        return message["content"]