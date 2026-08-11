import numpy as np
import pytest

from document.splitter import Chunk
from embedding.providers import EmbeddedChunk
from vector_store.exceptions import (
    EmbeddingModelMismatchError,
    InvalidVectorStoreConfigError,
    VectorDimensionMismatchError,
    VectorStorePersistenceError,
    UnsupportedVectorStoreError,
)
from vector_store.store import NumpyVectorStore
from vector_store.factory import VectorStoreFactory


def _make_chunk(chunk_id, metadata):
    return Chunk(
        content="some text",
        chunk_index=0,
        token_count=2,
        source_metadata=metadata,
        chunk_id=chunk_id,
    )

def _make_embedded(chunk_id, vector, metadata, model="test-model"):
    vector = np.array(vector, dtype=np.float32)
    return EmbeddedChunk(
        chunk=_make_chunk(chunk_id, metadata),
        vector=vector,
        embedding_model=model,
        dimensions=vector.shape[0],
    )


def test_store_rejects_non_positive_dimensions():
    with pytest.raises(InvalidVectorStoreConfigError):
        NumpyVectorStore(dimensions=0)


def test_add_empty_list_is_noop(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([])
    assert len(store) == 0

def test_add_rejects_dimension_mismatch(make_file_metadata):
    store = NumpyVectorStore(dimensions=3)
    embedded = _make_embedded("c1", [1.0, 0.0], make_file_metadata())
    with pytest.raises(VectorDimensionMismatchError):
        store.add([embedded])

def test_add_rejects_embedding_model_mismatch(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    first = _make_embedded("c1", [1.0, 0.0], make_file_metadata(), model="model-a")
    second = _make_embedded("c2", [0.0, 1.0], make_file_metadata(), model="model-b")
    store.add([first])
    with pytest.raises(EmbeddingModelMismatchError):
        store.add([second])

def test_add_upserts_existing_chunk_id(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    original = _make_embedded("c1", [1.0, 0.0], make_file_metadata())
    updated = _make_embedded("c1", [0.0, 1.0], make_file_metadata())
    store.add([original])
    store.add([updated])
    assert len(store) == 1


def test_search_rejects_non_positive_top_k(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([_make_embedded("c1", [1.0, 0.0], make_file_metadata())])
    with pytest.raises(InvalidVectorStoreConfigError):
        store.search(np.array([1.0, 0.0], dtype=np.float32), top_k=0)

def test_search_rejects_query_dimension_mismatch(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([_make_embedded("c1", [1.0, 0.0], make_file_metadata())])
    with pytest.raises(VectorDimensionMismatchError):
        store.search(np.array([1.0, 0.0, 0.0], dtype=np.float32))

def test_search_on_empty_store_returns_empty_list():
    store = NumpyVectorStore(dimensions=2)
    results = store.search(np.array([1.0, 0.0], dtype=np.float32))
    assert results == []

def test_search_returns_most_similar_first(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([
        _make_embedded("close", [1.0, 0.01], make_file_metadata()),
        _make_embedded("far", [0.0, 1.0], make_file_metadata()),
    ])
    results = store.search(np.array([1.0, 0.0], dtype=np.float32), top_k=2)

    assert len(results) == 2
    assert results[0].chunk.chunk_id == "close"
    assert results[0].rank == 1
    assert results[1].rank == 2
    assert results[0].score >= results[1].score

def test_search_caps_top_k_to_store_size(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([_make_embedded("c1", [1.0, 0.0], make_file_metadata())])
    results = store.search(np.array([1.0, 0.0], dtype=np.float32), top_k=5)
    assert len(results) == 1



def test_delete_removes_matching_chunks(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([
        _make_embedded("c1", [1.0, 0.0], make_file_metadata()),
        _make_embedded("c2", [0.0, 1.0], make_file_metadata()),
    ])
    store.delete(["c1"])
    assert len(store) == 1
    remaining_ids = [c.chunk_id for c in store._chunks]
    assert remaining_ids == ["c2"]

def test_delete_nonexistent_id_is_noop(make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([_make_embedded("c1", [1.0, 0.0], make_file_metadata())])
    store.delete(["does-not-exist"])
    assert len(store) == 1


def test_save_and_load_roundtrip_preserves_data(tmp_path, make_file_metadata):
    store = NumpyVectorStore(dimensions=2)
    store.add([
        _make_embedded("c1", [1.0, 0.0], make_file_metadata(), model="test-model"),
        _make_embedded("c2", [0.0, 1.0], make_file_metadata(), model="test-model"),
    ])
    save_path = tmp_path / "my_space"
    store.save(save_path)
    loaded = NumpyVectorStore.load(save_path)

    assert len(loaded) == len(store)
    assert loaded.dimensions == store.dimensions
    assert loaded.embedding_model == "test-model"

    results = loaded.search(np.array([1.0, 0.0], dtype=np.float32), top_k=1)
    assert results[0].chunk.chunk_id == "c1"


def test_load_raises_persistence_error_for_missing_files(tmp_path):
    with pytest.raises(VectorStorePersistenceError):
        NumpyVectorStore.load(tmp_path / "does_not_exist")


def test_factory_returns_numpy_store():
    store = VectorStoreFactory.get_store("numpy", dimensions=4)
    assert isinstance(store, NumpyVectorStore)
    assert store.dimensions == 4

def test_factory_raises_for_unknown_backend():
    with pytest.raises(UnsupportedVectorStoreError):
        VectorStoreFactory.get_store("faiss", dimensions=4)