import re
from dataclasses import dataclass, field
from pathlib import Path

from database.db import Database
from embedding.provider import EmbeddingProvider
from embedding.factory import EmbeddingProviderFactory
from embedding.exceptions import EmbeddingAPIError, InvalidEmbeddingConfigError
from vector_store.store import VectorStore, NumpyVectorStore, SearchResult
from vector_store.factory import VectorStoreFactory
from vector_store.exceptions import EmbeddingModelMismatchError, VectorDimensionMismatchError
from document.splitter import Chunk

_SPACE_ID_SANITIZE_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]")


@dataclass(frozen=True)
class EmbeddingSpaceConfig:
    """Identifies a vector space: the combination of provider and embedding model."""

    provider_name: str
    model_name: str
    provider_kwargs: dict = field(default_factory=dict)

    @property
    def space_id(self) -> str:
        raw=f"{self.provider_name}__{self.model_name}"
        return _SPACE_ID_SANITIZE_PATTERN.sub("_", raw)


class VectorSpaceManager:
    """Routes indexing/search operations to the correct VectorStore and
    EmbeddingProvider for a given EmbeddingSpaceConfig."""

    def __init__(self, storage_dir: str | Path, database: Database):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._stores: dict[str, VectorStore] = {}
        self._db = database

    def index_chunks(self, space: EmbeddingSpaceConfig, chunks: list[Chunk]) -> None:
        self._db.register_space(space.space_id, space.provider_name, space.model_name)
        embedder = self._get_embedder(space)
        embedded_chunks = embedder.embed_chunks(chunks)
        store = self._get_store(space, dimensions=embedder.dimensions)
        store.add(embedded_chunks)

        self._track_chunks(space.space_id, embedded_chunks)

    def search(self, space: EmbeddingSpaceConfig, query_text: str, top_k: int = 5) -> list[SearchResult]:
        """Embed the query in the given space and search only that space."""
        embedder = self._get_embedder(space)
        query_vector = embedder.embed_query(query_text)
        store = self._get_store(space, dimensions=embedder.dimensions)
        return store.search(query_vector, top_k=top_k)

    def search_all_spaces(
        self, 
        query_text: str, 
        provider_credentials: dict[str, dict] | None = None, 
        top_k: int = 5,
    ) -> dict[str, list[SearchResult]]:
        """Extend the query to all known spaces, skipping those for which we cannot auth."""
        provider_credentials = provider_credentials or {}
        results_by_space: dict[str, list[SearchResult]] = {}

        for discovered_space in self.discover_spaces():
            space_with_credentials = EmbeddingSpaceConfig(
                provider_name=discovered_space.provider_name,
                model_name=discovered_space.model_name,
                provider_kwargs=provider_credentials.get(discovered_space.provider_name, {}),
            )
            try:
                results_by_space[space_with_credentials.space_id] = self.search(space_with_credentials, query_text, top_k=top_k)
            except (InvalidEmbeddingConfigError, EmbeddingAPIError):
                continue
        return results_by_space

    def search_all_spaces_merged(
        self,
        query_text: str,
        provider_credentials: dict[str, dict] | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Same as search_all_spaces, but flattens all results into a single
        global ranking sorted by descending score, capped at top_k."""
        per_space_results=self.search_all_spaces(query_text, provider_credentials, top_k)
        flattened = [result for results in per_space_results.values() for result in results]
        flattened.sort(key=lambda r: r.score, reverse=True)
        return flattened[:top_k]

    def persist(self, space: EmbeddingSpaceConfig) -> None:
        store=self._stores.get(space.space_id)
        if store is None:
            return
        store.save(self._store_path(space.space_id))

    def persist_all(self) -> None:
        for space_id, store in self._stores.items():
            store.save(self._store_path(space_id))

    def discover_spaces(self) -> list[EmbeddingSpaceConfig]:
        return [
            EmbeddingSpaceConfig(provider_name=provider_name, model_name=model_name)
            for _, provider_name, model_name in self._db.get_all_spaces()
        ]

    def _get_embedder(self, space: EmbeddingSpaceConfig) -> EmbeddingProvider:
        return EmbeddingProviderFactory.get_provider(
            space.provider_name,
            model_name=space.model_name,
            **space.provider_kwargs,
        )

    def _get_store(self, space: EmbeddingSpaceConfig, dimensions: int) -> VectorStore:
        space_id=space.space_id
        if space_id not in self._stores:
            self._stores[space_id]=self._load_or_create_store(space_id, dimensions)

        store=self._stores[space_id]
        self._validate_store_matches_space(store, space, dimensions)
        return store

    def _load_or_create_store(self, space_id: str, dimensions: int) -> VectorStore:
        store_path = self._store_path(space_id)
        if store_path.with_suffix(".npy").exists() and store_path.with_suffix(".json").exists():
            return NumpyVectorStore.load(store_path)
        return VectorStoreFactory.get_store("numpy", dimensions=dimensions)

    def _store_path(self, space_id: str) -> Path:
        return self._storage_dir / space_id

    @staticmethod
    def _validate_store_matches_space(store: VectorStore, space: EmbeddingSpaceConfig, dimensions: int) -> None:
        if store.dimensions != dimensions:
            raise VectorDimensionMismatchError(
                f"Store loaded for space '{space.space_id}' has "
                f"{store.dimensions} dimensions, model '{space.model_name}' "
                f"returns {dimensions}"
            )
        if store.embedding_model and store.embedding_model != space.model_name:
            raise EmbeddingModelMismatchError(
                f"Store loaded for space '{space.space_id}' contains "
                f"embeddings from '{store.embedding_model}', expected "
                f"'{space.model_name}'"
            )
        
    def _track_chunks(self, space_id: str, embedded_chunks: list) -> None:
        chunks_by_file: dict[str, list[str]] = {}
        for embedded_chunk in embedded_chunks:
            filepath = embedded_chunk.chunk.source_metadata.filepath
            chunks_by_file.setdefault(filepath, []).append(embedded_chunk.chunk.chunk_id)
 
        for filepath, chunk_ids in chunks_by_file.items():
            self._db.add_chunks(filepath, space_id, chunk_ids)

    def delete_chunks(self, space: EmbeddingSpaceConfig, chunk_ids: list[str]) -> None:
        """Remove chunks from the store for this space."""
        store = self._stores.get(space.space_id)

        if store is None:
            store_path = self._store_path(space.space_id)
            if not (store_path.with_suffix(".npy").exists() and store_path.with_suffix(".json").exists()):
                return
            store = NumpyVectorStore.load(store_path)
            self._stores[space.space_id] = store

        store.delete(chunk_ids)