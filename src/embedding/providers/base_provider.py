import numpy as np
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

from document.splitter import Chunk
from embedding.exceptions import (
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
    """Base interface for embedding providers."""
    
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
        """calls the provider on a single batch of texts. must return the embedding 
        vectors as NumPy arrays in the same order as the input texts."""
        pass
    
    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        valid_chunks = [c for c in chunks if c.content.strip()]
        # skipped = len(chunks) - len(valid_chunks) 
        # TODO: implement structured logging for skipped chunks
    
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
            raise InvalidEmbeddingConfigError("Query text cannot be empty.")
    
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
