import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from embedding import EmbeddingProvider
from embedding_factory import EmbeddingProviderFactory
from embedding_exceptions import EmbeddingAPIError, InvalidEmbeddingConfigError
from vector_store import VectorStore, NumpyVectorStore, SearchResult
from vector_store_factory import VectorStoreFactory
from vector_store_exceptions import EmbeddingModelMismatchError, VectorDimensionMismatchError
from text_splitter import Chunk

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

    def __init__(self, storage_dir: str | Path):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._stores: dict[str, VectorStore] = {}
        self._space_configs: dict[str, EmbeddingSpaceConfig] = {}

    def index_chunks(self, space: EmbeddingSpaceConfig, chunks: list[Chunk]) -> None:
        self._space_configs[space.space_id] = space
        embedder = self._get_embedder(space)
        embedded_chunks = embedder.embed_chunks(chunks)
        store = self._get_store(space, dimensions=embedder.dimensions)
        store.add(embedded_chunks)

    def search(self, space: EmbeddingSpaceConfig, query_text: str, top_k: int = 5) -> list[SearchResult]:
        """Embed the query in the given space and search only that space."""
        self._space_configs[space.space_id] = space
        embedder = self._get_embedder(space)
        query_vector = embedder.embed_query(query_text)

        store = self._get_store(space, dimensions=embedder.dimensions)
        return store.search(query_vector, top_k=top_k)

    def search_all_spaces(self, query_text: str, provider_credentials: dict[str, dict] | None = None, top_k: int = 5,) -> dict[str, list[SearchResult]]:
        """Search the query across all spaces, each with its own provider and embedding model"""
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
        space_id=space.space_id
        store=self._stores.get(space_id)
        if store is None:
            return
        store.save(self._store_path(space_id))
        self._write_manifest(space)

    def persist_all(self) -> None:
        for space_id, store in self._stores.items():
            store.save(self._store_path(space_id))
            space = self._space_configs.get(space_id)
            if space is not None:
                self._write_manifest(space)

    def discover_spaces(self) -> list[EmbeddingSpaceConfig]:
        spaces = []
        for manifest_path in sorted(self._storage_dir.glob("*.space.json")):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                spaces.append(EmbeddingSpaceConfig(
                    provider_name=data["provider_name"],
                    model_name=data["model_name"],
                ))
            except (OSError, json.JSONDecodeError, KeyError):
                continue
        return spaces

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

    def _write_manifest(self, space: EmbeddingSpaceConfig) -> None:
        manifest={"provider_name": space.provider_name, "model_name": space.model_name}
        try:
            with open(self._manifest_path(space.space_id), "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _manifest_path(self, space_id: str) -> Path:
        return self._storage_dir / f"{space_id}.space.json"

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