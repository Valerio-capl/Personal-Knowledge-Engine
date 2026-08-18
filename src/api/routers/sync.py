from fastapi import APIRouter, Depends

from api.dependencies import get_sync_engine
from api.schemas import SyncRequest, SyncResponse
from engine.sync import SyncEngine
from engine.space_manager import EmbeddingSpaceConfig

router = APIRouter()

@router.post("/sync", response_model=SyncResponse)
def run_sync(request: SyncRequest, sync_engine: SyncEngine = Depends(get_sync_engine)) -> SyncResponse:
    space = EmbeddingSpaceConfig(
        provider_name=request.provider_name,
        model_name=request.model_name,
    )
    report = sync_engine.sync(request.folder_path, space)

    return SyncResponse(
        synced=report.synced,
        skipped=report.skipped,
        failed=report.failed,
        deleted=report.deleted,
    )