from dataclasses import dataclass, field

from engine.space_manager import EmbeddingSpaceConfig, VectorSpaceManager
from generation.providers import GenerationProvider
from vector_store.store import SearchResult

PROVIDER_MIN_SCORES = {
    "openai": 0.65,
    "ollama": 0.45,
} # to calibrate and add models
FALLBACK_MIN_SCORE = 0.3
DEFAULT_TOP_K = 5


_PROMPT_TEMPLATE = """You are a strict technical assistant. You must answer the user's question using ONLY the provided Context. 
UNDER NO CIRCUMSTANCES should you use outside knowledge, external links, or invent information.
The Context is made of separate excerpts extracted from real documents — they may be fragmented or not perfectly continuous. Synthesize and connect information across multiple excerpts when needed to form a complete answer.
Be thorough: if the Context includes definitions, properties, lists, or steps relevant to the question, include all of them in your answer instead of summarizing them away.
If the Context does not contain enough explicit information to formulate a complete answer, you must respond EXACTLY with: "I don't have enough information in the indexed documents to answer this."

Context:
{context}

Question: {question}

Answer (with [1], [2] citations):"""
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
        min_score: float | None = None,
    ) -> AnswerResult:
        if min_score is None:
            actual_min_score = PROVIDER_MIN_SCORES.get(space.provider_name, FALLBACK_MIN_SCORE)
        else:
            actual_min_score = min_score

        results = self._vsm.search(space, question, top_k=top_k)
        relevant_results = [r for r in results if r.score >= actual_min_score]

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