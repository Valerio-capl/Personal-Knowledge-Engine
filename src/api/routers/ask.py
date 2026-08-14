from fastapi import APIRouter, Depends

from api.dependencies import get_answer_engine
from api.schemas import AskRequest, AskResponse, SourceItem
from engine.space_manager import EmbeddingSpaceConfig
from engine.answer import AnswerEngine
from generation.factory import GenerationProviderFactory

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    answer_engine: AnswerEngine = Depends(get_answer_engine),
) -> AskResponse:
    space = EmbeddingSpaceConfig(
        provider_name=request.provider_name,
        model_name=request.model_name,
    )

    generation_provider = GenerationProviderFactory.get_provider(
        request.generation_provider,
        model_name=request.generation_model,
    )

    result = answer_engine.answer(
        question=request.question,
        space=space,
        generation_provider=generation_provider,
        top_k=request.top_k,
        min_score=request.min_score,
    )

    return AskResponse(
        answer=result.answer,
        sources=[SourceItem(id=s.id, file=s.file, score=s.score) for s in result.sources],
    )