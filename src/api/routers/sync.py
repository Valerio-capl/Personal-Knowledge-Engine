from fastapi import APIRouter

from api.dependencies import db, vsm
from api.schemas import SyncRequest
from engine.sync import SyncEngine
from engine.space_manager import EmbeddingSpaceConfig

router = APIRouter()

@router.post("/sync")
def run_sync(request: SyncRequest):
    space = EmbeddingSpaceConfig(
        provider_name=request.provider_name,
        model_name=request.model_name,
    )
    sync_engine = SyncEngine(database=db, vector_space_manager=vsm)
    report = sync_engine.sync(request.folder_path, space)

    return {
        "synced": report.synced,
        "skipped": report.skipped,
        "failed": report.failed,
    }