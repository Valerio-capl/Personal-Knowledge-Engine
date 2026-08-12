from fastapi import APIRouter, Depends

from api.dependencies import get_vector_space_manager
from api.schemas import SpaceResponse
from engine.space_manager import VectorSpaceManager

router = APIRouter()

@router.get("/spaces", response_model=list[SpaceResponse])
def get_spaces(vsm: VectorSpaceManager = Depends(get_vector_space_manager)) -> list[SpaceResponse]:
    spaces = vsm.discover_spaces()
    return [
        SpaceResponse(
            space_id=s.space_id,
            provider_name=s.provider_name,
            model_name=s.model_name,
        )
        for s in spaces
    ]