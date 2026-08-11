from fastapi import FastAPI
from api.routers import spaces, sync, search

app = FastAPI(title="Personal Knowledge Engine")

app.include_router(spaces.router)
app.include_router(sync.router)
app.include_router(search.router)