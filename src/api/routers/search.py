from fastapi import APIRouter, Depends

from api.dependencies import get_vector_space_manager
from api.schemas import SearchRequest, SearchResultResponse
from engine.space_manager import EmbeddingSpaceConfig, VectorSpaceManager

router = APIRouter()

@router.post("/search", response_model=list[SearchResultResponse])
def run_search(request: SearchRequest, vsm: VectorSpaceManager = Depends(get_vector_space_manager)) -> list[SearchResultResponse]:
    space = EmbeddingSpaceConfig(
        provider_name=request.provider_name,
        model_name=request.model_name,
    )
    results = vsm.search(space, request.query, top_k=request.top_k)

    return [
        SearchResultResponse(
            content=r.chunk.content,
            score=r.score,
            rank=r.rank,
            filepath=r.chunk.source_metadata.filepath,
        )
        for r in results
    ]