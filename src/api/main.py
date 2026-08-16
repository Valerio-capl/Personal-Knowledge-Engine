from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import spaces, sync, search, ask
from api.exceptions import register_exception_handlers

app = FastAPI(title="Personal Knowledge Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

app.include_router(spaces.router)
app.include_router(sync.router)
app.include_router(search.router)
app.include_router(ask.router)