import requests
import numpy as np
from .base_provider import EmbeddingProvider
from embedding.exceptions import (
    EmbeddingAPIError,
    EmbeddingDimensionMismatchError,
    InvalidEmbeddingConfigError,
)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Provider for local Ollama embedding models."""

    _KNOWN_MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "nomic-embed-text-v2-moe": 768,
        "bge-m3": 1024,
    }

    def __init__(
        self,
        model_name: str = "nomic-embed-text-v2-moe",
        dimensions: int | None = None,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: float = 2.0,
        base_url: str = "http://localhost:11434",
    ):
        resolved_dimensions = dimensions or self._KNOWN_MODEL_DIMENSIONS.get(model_name)
        if resolved_dimensions is None:
            raise InvalidEmbeddingConfigError(
                f"Unknown dimensions for model '{model_name}': specify "
                f"the 'dimensions' parameter explicitly"
            )

        super().__init__(
            model_name=model_name,
            dimensions=resolved_dimensions,
            batch_size=batch_size,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        self._base_url = base_url.rstrip("/")

    def _embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        try:
            response = requests.post(
                f"{self._base_url}/api/embed",
                json={"model": self.model_name, "input": texts},
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            # ollama not running, timeouts, HTTP 4xx/5xx
            raise EmbeddingAPIError(f"Ollama embed call failed: {e}") from e

        data = response.json()
        embeddings = data.get("embeddings")
        if embeddings is None:
            raise EmbeddingAPIError("Unexpected Ollama response: missing 'embeddings' field")

        return [np.array(vec, dtype=np.float32) for vec in embeddings]