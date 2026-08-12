import numpy as np
import pytest

from document.splitter import Chunk
from embedding.factory import EmbeddingProviderFactory
from embedding.providers import EmbeddingProvider, OpenAIEmbeddingProvider, OllamaEmbeddingProvider
from embedding.exceptions import (
    EmbeddingAPIError,
    EmbeddingDimensionMismatchError,
    InvalidEmbeddingConfigError,
    UnsupportedEmbeddingProviderError,
)


class _FakeProvider(EmbeddingProvider):
    def __init__(self, fail_times=0, wrong_dimension=False, **kwargs):
        super().__init__(**kwargs)
        self._fail_times = fail_times
        self._wrong_dimension = wrong_dimension
        self.calls = []  # track batch sizes passed to _embed_batch

    def _embed_batch(self, texts):
        self.calls.append(list(texts))
        if self._fail_times > 0:
            self._fail_times -= 1
            raise EmbeddingAPIError("simulated transient failure")
        
        dim = self.dimensions + 1 if self._wrong_dimension else self.dimensions
        return [np.ones(dim, dtype=np.float32) for _ in texts]


def _make_chunk(chunk_id, content, metadata):
    return Chunk(
        content=content,
        chunk_index=0,
        token_count=1,
        source_metadata=metadata,
        chunk_id=chunk_id,
    )


def test_provider_rejects_non_positive_batch_size():
    with pytest.raises(InvalidEmbeddingConfigError):
        _FakeProvider(model_name="fake", dimensions=2, batch_size=0)


def test_provider_rejects_negative_max_retries():
    with pytest.raises(InvalidEmbeddingConfigError):
        _FakeProvider(model_name="fake", dimensions=2, max_retries=-1)


def test_provider_rejects_non_positive_dimensions():
    with pytest.raises(InvalidEmbeddingConfigError):
        _FakeProvider(model_name="fake", dimensions=0)


def test_embed_chunks_skips_blank_content(make_file_metadata):
    provider = _FakeProvider(model_name="fake", dimensions=2)
    chunks = [
        _make_chunk("c1", "real content", make_file_metadata()),
        _make_chunk("c2", "   ", make_file_metadata()),
    ]

    embedded = provider.embed_chunks(chunks)

    assert len(embedded) == 1
    assert embedded[0].chunk.chunk_id == "c1"


def test_embed_chunks_batches_according_to_batch_size(make_file_metadata):
    provider = _FakeProvider(model_name="fake", dimensions=2, batch_size=2)
    chunks = [_make_chunk(f"c{i}", "text", make_file_metadata()) for i in range(5)]
    provider.embed_chunks(chunks)
    assert [len(batch) for batch in provider.calls] == [2, 2, 1]


def test_embed_chunks_raises_on_dimension_mismatch(make_file_metadata):
    provider = _FakeProvider(model_name="fake", dimensions=2, wrong_dimension=True)
    chunks = [_make_chunk("c1", "text", make_file_metadata())]
    with pytest.raises(EmbeddingDimensionMismatchError):
        provider.embed_chunks(chunks)


def test_embed_query_raises_for_empty_text():
    provider = _FakeProvider(model_name="fake", dimensions=2)
    with pytest.raises(InvalidEmbeddingConfigError):
        provider.embed_query("   ")


def test_embed_query_returns_single_vector():
    provider = _FakeProvider(model_name="fake", dimensions=2)
    vector = provider.embed_query("hello")
    assert vector.shape == (2,)


def test_retry_recovers_after_transient_failures():
    provider = _FakeProvider(
        model_name="fake", dimensions=2, fail_times=2, max_retries=3, retry_backoff_seconds=0
    )
    vector = provider.embed_query("hello")
    assert vector.shape == (2,)


def test_retry_raises_after_exhausting_max_retries():
    provider = _FakeProvider(
        model_name="fake", dimensions=2, fail_times=10, max_retries=2, retry_backoff_seconds=0
    )
    with pytest.raises(EmbeddingAPIError):
        provider.embed_query("hello")


# factory
def test_factory_returns_openai_provider():
    provider = EmbeddingProviderFactory.get_provider(
        "openai", model_name="text-embedding-3-small", api_key="fake-key"
    )
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.dimensions == 1536


def test_factory_returns_ollama_provider():
    provider = EmbeddingProviderFactory.get_provider(
        "ollama", model_name="nomic-embed-text-v2-moe"
    )
    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.dimensions == 768


def test_factory_raises_for_unknown_provider():
    with pytest.raises(UnsupportedEmbeddingProviderError):
        EmbeddingProviderFactory.get_provider("anthropic", model_name="foo")