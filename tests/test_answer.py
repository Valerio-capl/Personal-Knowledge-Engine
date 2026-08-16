import pytest
from document.splitter import Chunk
from engine.answer import AnswerEngine
from engine.space_manager import EmbeddingSpaceConfig
from generation.providers import GenerationProvider
from vector_store.store import SearchResult


class _FakeVectorSpaceManager:
    def __init__(self, results):
        self._results = results
        self.search_calls = []

    def search(self, space, query_text, top_k=5):
        self.search_calls.append((space, query_text, top_k))
        return self._results[:top_k]


class _FakeGenerationProvider(GenerationProvider):
    def __init__(self, response_text="fake answer"):
        super().__init__(model_name="fake-model")
        self._response_text = response_text
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self._response_text


def _make_result(chunk_id, content, score, metadata):
    chunk = Chunk(
        content=content,
        chunk_index=0,
        token_count=2,
        source_metadata=metadata,
        chunk_id=chunk_id,
    )
    return SearchResult(chunk=chunk, score=score, rank=1)


SPACE = EmbeddingSpaceConfig(provider_name="ollama", model_name="fake-model")


def test_answer_returns_fallback_when_no_results_above_min_score(make_file_metadata):
    results = [_make_result("c1", "irrelevant", 0.1, make_file_metadata())]
    vsm = _FakeVectorSpaceManager(results)
    generation_provider = _FakeGenerationProvider()
    engine = AnswerEngine(vsm)
    result = engine.answer("question", SPACE, generation_provider, min_score=0.3)

    assert result.sources == []
    assert "couldn't find" in result.answer.lower()
    assert generation_provider.prompts == []  # must not call the llm on empty context


def test_answer_filters_out_results_below_min_score(make_file_metadata):
    results = [
        _make_result("c1", "relevant", 0.8, make_file_metadata()),
        _make_result("c2", "weak match", 0.1, make_file_metadata()),
    ]
    vsm = _FakeVectorSpaceManager(results)
    generation_provider = _FakeGenerationProvider()
    engine = AnswerEngine(vsm)
    result = engine.answer("question", SPACE, generation_provider, min_score=0.3)
    assert [s.id for s in result.sources] == [1]


def test_answer_builds_context_with_matching_markers(make_file_metadata):
    results = [
        _make_result("c1", "first chunk content", 0.9, make_file_metadata()),
        _make_result("c2", "second chunk content", 0.8, make_file_metadata()),
    ]
    vsm = _FakeVectorSpaceManager(results)
    generation_provider = _FakeGenerationProvider()
    engine = AnswerEngine(vsm)
    engine.answer("question", SPACE, generation_provider)
    prompt = generation_provider.prompts[0]
    assert "[1] first chunk content" in prompt
    assert "[2] second chunk content" in prompt


def test_answer_returns_generation_provider_output(make_file_metadata):
    results = [_make_result("c1", "content", 0.9, make_file_metadata())]
    vsm = _FakeVectorSpaceManager(results)
    generation_provider = _FakeGenerationProvider(response_text="the real answer [1]")
    engine = AnswerEngine(vsm)
    result = engine.answer("question", SPACE, generation_provider)
    assert result.answer == "the real answer [1]"


def test_answer_passes_top_k_to_search(make_file_metadata):
    results = [_make_result(f"c{i}", "content", 0.9, make_file_metadata()) for i in range(5)]
    vsm = _FakeVectorSpaceManager(results)
    generation_provider = _FakeGenerationProvider()
    engine = AnswerEngine(vsm)
    engine.answer("question", SPACE, generation_provider, top_k=2)
    assert vsm.search_calls[0][2] == 2