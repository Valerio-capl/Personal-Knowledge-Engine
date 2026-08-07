import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from document.loader import FileMetadata
from document.splitter import Chunk
from embedding.provider import EmbeddedChunk
from vectore_store.exceptions import (
    EmbeddingModelMismatchError,
    InvalidVectorStoreConfigError,
    VectorDimensionMismatchError,
    VectorStorePersistenceError,
)


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float
    rank: int


class VectorStore(ABC):
    """Base interface for vector store backends."""

    def __init__(self, dimensions: int):
        if dimensions <= 0:
            raise InvalidVectorStoreConfigError("dimensions must be a positive integer")
        self.dimensions = dimensions
        self.embedding_model: str | None = None

    @abstractmethod
    def add(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        """Insert new chunks, or update chunks with an existing chunk_id."""
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        """Return the top_k chunks most similar to the query vector."""
        pass

    @abstractmethod
    def delete(self, chunk_ids: list[str]) -> None:
        """Remove chunks with the specified ids, if present."""
        pass

    @abstractmethod
    def save(self, path: str | Path) -> None:
        """Persist the store state to disk."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: str | Path) -> "VectorStore":
        """Rebuild a store from a previously saved state."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    def _validate_embedded_chunks(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        for embedded_chunk in embedded_chunks:
            vector_dimensions = embedded_chunk.vector.shape[0]
            if vector_dimensions != self.dimensions:
                raise VectorDimensionMismatchError(
                    f"Chunk '{embedded_chunk.chunk.chunk_id}' has a vector "
                    f"with {vector_dimensions} dimensions, but the store is "
                    f"configured for {self.dimensions}"
                )

            if self.embedding_model is None:
                self.embedding_model = embedded_chunk.embedding_model
            elif embedded_chunk.embedding_model != self.embedding_model:
                raise EmbeddingModelMismatchError(
                    f"The store contains embeddings generated with "
                    f"'{self.embedding_model}', but chunk "
                    f"'{embedded_chunk.chunk.chunk_id}' was embedded with "
                    f"'{embedded_chunk.embedding_model}'"
                )

class NumpyVectorStore(VectorStore):
    """In-memory vector store, using brute-force cosine similarity searchvia numpy."""

    def __init__(self, dimensions: int):
        super().__init__(dimensions)
        self._chunks: list[Chunk] = []
        self._vectors: list[np.ndarray] = []
        self._id_to_index: dict[str, int] = {}
        self._matrix_cache: np.ndarray | None = None

    def add(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        if not embedded_chunks:
            return

        self._validate_embedded_chunks(embedded_chunks)

        for embedded_chunk in embedded_chunks:
            chunk_id = embedded_chunk.chunk.chunk_id
            vector = self._normalize(embedded_chunk.vector)

            if chunk_id in self._id_to_index:
                idx = self._id_to_index[chunk_id]
                self._chunks[idx] = embedded_chunk.chunk
                self._vectors[idx] = vector
            else:
                self._id_to_index[chunk_id] = len(self._chunks)
                self._chunks.append(embedded_chunk.chunk)
                self._vectors.append(vector)

        self._invalidate_cache()

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if top_k <= 0:
            raise InvalidVectorStoreConfigError("top_k must be a positive integer")
        if query_vector.shape[0] != self.dimensions:
            raise VectorDimensionMismatchError(
                f"The query vector has {query_vector.shape[0]} dimensions, "
                f"but the store is configured for {self.dimensions}"
            )
        if not self._chunks:
            return []

        matrix = self._get_matrix()
        # normalized dot product == cosine similarity
        normalized_query = self._normalize(query_vector)
        scores = matrix @ normalized_query
        k = min(top_k, len(self._chunks))
        
        # extract top-k without full array sort
        top_indices = np.argpartition(-scores, k - 1)[:k]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        return [
            SearchResult(
                chunk=self._chunks[idx],
                score=float(scores[idx]),
                rank=rank,
            )
            for rank, idx in enumerate(top_indices, start=1)
        ]
    
    def delete(self, chunk_ids: list[str]) -> None:
        ids_to_delete = set(chunk_ids)
        keep_indices = [i for i, chunk in enumerate(self._chunks) if chunk.chunk_id not in ids_to_delete]
        removed = len(self._chunks) - len(keep_indices)

        if removed == 0:
            return

        self._chunks = [self._chunks[i] for i in keep_indices]
        self._vectors = [self._vectors[i] for i in keep_indices]
        self._id_to_index = {chunk.chunk_id: i for i, chunk in enumerate(self._chunks)}
        self._invalidate_cache()

    def save(self, path: str | Path) -> None:
        path = Path(path)
        matrix = self._get_matrix()

        try:
            np.save(path.with_suffix(".npy"), matrix)
            metadata = {
                "dimensions": self.dimensions,
                "embedding_model": self.embedding_model,
                "chunks": [asdict(chunk) for chunk in self._chunks],
            }

            with open(path.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

        except OSError as e:
            raise VectorStorePersistenceError(
                f"Unable to save vector store to {path}: {e}"
            ) from e

    @classmethod
    def load(cls, path: str | Path) -> "NumpyVectorStore":
        path = Path(path)

        try:
            matrix = np.load(path.with_suffix(".npy"))
            with open(path.with_suffix(".json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise VectorStorePersistenceError(
                f"Unable to load vector store from {path}: {e}"
            ) from e

        store = cls(dimensions=metadata["dimensions"])
        store.embedding_model = metadata["embedding_model"]
        store._chunks = [cls._chunk_from_dict(d) for d in metadata["chunks"]]
        store._vectors = [row.astype(np.float32) for row in matrix]
        store._id_to_index = {chunk.chunk_id: i for i, chunk in enumerate(store._chunks)}

        return store

    @staticmethod
    def _chunk_from_dict(data: dict) -> Chunk:
        metadata = FileMetadata(**data["source_metadata"])
        return Chunk(**{**data, "source_metadata": metadata})

    def _get_matrix(self) -> np.ndarray:
        if self._matrix_cache is None:
            self._matrix_cache = (
                np.vstack(self._vectors) if self._vectors
                else np.empty((0, self.dimensions), dtype=np.float32)
            )
        return self._matrix_cache

    def _invalidate_cache(self) -> None:
        # invalidate cache, rebuild on next search/save
        self._matrix_cache = None

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0: # vett nullo
            return vector.astype(np.float32)
        return (vector / norm).astype(np.float32)

    def __len__(self) -> int:
        return len(self._chunks)