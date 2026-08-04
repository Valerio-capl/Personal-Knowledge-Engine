import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

import numpy as np
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from text_splitter import Chunk
from embedding_exceptions import (
    EmbeddingAPIError,
    EmbeddingDimensionMismatchError,
    InvalidEmbeddingConfigError,
)

@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: Chunk
    vector: np.ndarray
    embedding_model: str
    dimensions: int
    
class EmbeddingProvider(ABC):
    """Common interface for any embedding provider, whether it is
    an external API or a local model.
    Concrete subclasses only need to implement `_embed_batch`.
    """
    
    def __init__(self, model_name: str, dimensions: int, batch_size: int = 100, max_retries: int = 3, retry_backoff_seconds: float = 2.0):
        if batch_size <= 0:
            raise InvalidEmbeddingConfigError("batch_size must be a positive integer")
        if max_retries < 0:
            raise InvalidEmbeddingConfigError("max_retries cannot be negative")
        if dimensions <= 0:
            raise InvalidEmbeddingConfigError("dimensions must be a positive integer")
    
        self.model_name = model_name
        self.dimensions = dimensions
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
    
    @abstractmethod
    def _embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        """Calls the provider on a single batch of texts
        (already filtered and non-empty). Must return the embedding vectors as NumPy arrays in the same order as the input texts.
        """
        pass
    
    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        valid_chunks = [c for c in chunks if c.content.strip()]
        # skipped = len(chunks) - len(valid_chunks) 
        # add logging to track skipped empty chunks
    
        embedded: list[EmbeddedChunk] = []
        for batch in self._batched(valid_chunks, self.batch_size):
            vectors = self._embed_batch_with_retry([c.content for c in batch])

            for chunk, vector in zip(batch, vectors):
                self._validate_dimensions(vector)
                embedded.append(EmbeddedChunk(
                    chunk=chunk,
                    vector=vector,
                    embedding_model=self.model_name,
                    dimensions=vector.shape[0],
                ))
        return embedded

    def embed_query(self, text: str) -> np.ndarray:
        if not text.strip():
            raise InvalidEmbeddingConfigError("Il testo della query non può essere vuoto")
    
        vectors = self._embed_batch_with_retry([text])
        return vectors[0]

    def _embed_batch_with_retry(self, texts: list[str]) -> list[np.ndarray]:
        attempt = 0
        while True:
            try:
                return self._embed_batch(texts)
            except EmbeddingAPIError as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise EmbeddingAPIError(f"Embedding failed after {attempt - 1} attempts: {e}")
            
                wait = self.retry_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(wait)
    
    def _validate_dimensions(self, vector: np.ndarray) -> None:
        if vector.shape[0] != self.dimensions:
            raise EmbeddingDimensionMismatchError(
                f"Model '{self.model_name}' returned a vector of "
                f"{vector.shape[0]} dimensions, expected {self.dimensions}"
            )
    
    @staticmethod
    def _batched(items: list, batch_size: int) -> Iterator[list]:
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]


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
                "OpenAI API key is missing: provide it explicitly with api_key= "
                "or set the OPENAI_API_KEY environment variable"
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

        #lista di array numpy con dtype float32 per cosinesim
        return [np.array(item.embedding, dtype=np.float32) for item in response.data]