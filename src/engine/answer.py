from dataclasses import dataclass, field

from engine.space_manager import EmbeddingSpaceConfig, VectorSpaceManager
from generation.providers import GenerationProvider
from vector_store.store import SearchResult

DEFAULT_MIN_SCORE = 0.3 # to calibrate
DEFAULT_TOP_K = 5


_PROMPT_TEMPLATE = """Answer the question using only the context below. Cite sources using [1], [2] etc. matching the context numbers. If the context doesn't contain the answer, say so clearly.

Context:
{context}

Question: {question}

Answer:"""

_NO_CONTEXT_ANSWER = "I couldn't find relevant information in your documents for this question."

@dataclass(frozen=True)
class Source:
    id: int
    file: str
    score: float


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[Source] = field(default_factory=list)

class AnswerEngine:
    def __init__(self, vector_space_manager: VectorSpaceManager):
        self._vsm = vector_space_manager

    def answer(self,
        question: str,
        space: EmbeddingSpaceConfig,
        generation_provider: GenerationProvider,
        top_k: int = DEFAULT_TOP_K,
        min_score: float = DEFAULT_MIN_SCORE,
    ) -> AnswerResult:
        results = self._vsm.search(space, question, top_k=top_k)
        relevant_results = [r for r in results if r.score >= min_score]

        if not relevant_results:
            return AnswerResult(answer=_NO_CONTEXT_ANSWER, sources=[])

        context, sources = self._build_context(relevant_results)
        prompt = _PROMPT_TEMPLATE.format(context=context, question=question)
        answer_text = generation_provider.generate(prompt)
        return AnswerResult(answer=answer_text, sources=sources)
    
    @staticmethod
    def _build_context(results: list[SearchResult]) -> tuple[str, list[Source]]:
        context_parts = []
        sources = []
        for i, r in enumerate(results, start=1):
            context_parts.append(f"[{i}] {r.chunk.content}")
            sources.append(Source(id=i, file=r.chunk.source_metadata.filepath, score=r.score))
        return "\n\n".join(context_parts), sources