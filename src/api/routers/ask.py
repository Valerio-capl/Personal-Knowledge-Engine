from fastapi import APIRouter

from api.dependencies import get_vector_space_manager
from api.schemas import AskRequest, AskResponse
from engine.space_manager import EmbeddingSpaceConfig
from engine.answer import answer_query
from generation.provider import OllamaGenerationProvider, OpenAIGenerationProvider

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    vsm = get_vector_space_manager()
    space = EmbeddingSpaceConfig(
        provider_name=request.provider_name,
        model_name=request.model_name,
    )

    if request.generation_provider == "openai":
        generation_provider = OpenAIGenerationProvider(model_name=request.generation_model)
    else:
        generation_provider = OllamaGenerationProvider(model_name=request.generation_model)

    result = answer_query(
        question=request.question,
        space=space,
        vsm=vsm,
        generation_provider=generation_provider,
        top_k=request.top_k,
        min_score=request.min_score,
    )

    return AskResponse(**result)