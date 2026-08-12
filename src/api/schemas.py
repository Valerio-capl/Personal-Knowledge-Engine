from pydantic import BaseModel, Field

class SyncRequest(BaseModel):
    folder_path: str
    provider_name: str
    model_name: str

class SyncResponse(BaseModel):
    synced: list[str]
    skipped: list[str]
    failed: list[tuple[str, str]]


class SearchRequest(BaseModel):
    query: str
    provider_name: str
    model_name: str
    top_k: int = Field(default=5, gt=0)

class SearchResultResponse(BaseModel):
    content: str
    score: float
    rank: int
    filepath: str


class SpaceResponse(BaseModel):
    space_id: str
    provider_name: str
    model_name: str