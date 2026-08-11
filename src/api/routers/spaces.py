from fastapi import APIRouter

from api.dependencies import vsm
from api.schemas import SpaceResponse

router = APIRouter()

@router.get("/spaces")
def get_spaces():
    spaces = vsm.discover_spaces()
    return [
        SpaceResponse(
            space_id=s.space_id,
            provider_name=s.provider_name,
            model_name=s.model_name,
        )
        for s in spaces
    ]