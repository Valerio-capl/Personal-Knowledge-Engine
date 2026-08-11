from pydantic import BaseModel

class SyncRequest(BaseModel):
    folder_path: str
    provider_name: str
    model_name: str

class SearchRequest(BaseModel):
    query: str
    provider_name: str
    model_name: str
    top_k: int = 5

class SpaceResponse(BaseModel):
    space_id: str
    provider_name: str
    model_name: str