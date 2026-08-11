from fastapi import APIRouter

from api.dependencies import vsm
from api.schemas import SearchRequest
from engine.space_manager import EmbeddingSpaceConfig

router = APIRouter()

@router.post("/search")
def run_search(request: SearchRequest):
    space = EmbeddingSpaceConfig(
        provider_name=request.provider_name,
        model_name=request.model_name,
    )
    results = vsm.search(space, request.query, top_k=request.top_k)

    return [
        {
            "content": r.chunk.content,
            "score": r.score,
            "rank": r.rank,
            "filepath": r.chunk.source_metadata.filepath,
        }
        for r in results
    ]