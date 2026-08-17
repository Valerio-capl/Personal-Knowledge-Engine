import numpy as np
import os
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from .base_provider import EmbeddingProvider
from embedding.exceptions import (
    EmbeddingAPIError,
    InvalidEmbeddingConfigError,
)

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Provider based on the OpenAI API."""
    
    # default dimensions for the OpenAI embedding models.
    _KNOWN_MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    # Only the text-embedding-3 supports the `dimensions` parameter for reducing the dimensionality of the vectors
    _SUPPORTS_CUSTOM_DIMENSIONS_PREFIX = "text-embedding-3"
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        dimensions: int | None = None,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_backoff_seconds: float = 2.0,
        api_key: str | None = None
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
    
        resolved_api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_api_key:
            raise InvalidEmbeddingConfigError(
                "OpenAI API key is missing. Set OPENAI_API_KEY in your .env file."
            )
        self._client = OpenAI(api_key=resolved_api_key)

    def _embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        request_kwargs = {"model": self.model_name, "input": texts}
        if self.model_name.startswith(self._SUPPORTS_CUSTOM_DIMENSIONS_PREFIX):
            request_kwargs["dimensions"] = self.dimensions
    
        try:
            response = self._client.embeddings.create(**request_kwargs)
        except (RateLimitError, APIConnectionError, APIError) as e:
            raise EmbeddingAPIError(f"embeddings.create call failed: {e}") from e

        # numpy array list dtype float32 for cosinesim
        return [np.array(item.embedding, dtype=np.float32) for item in response.data]