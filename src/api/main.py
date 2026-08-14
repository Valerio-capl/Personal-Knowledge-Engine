from fastapi import FastAPI
from api.routers import spaces, sync, search, ask
from api.exceptions import register_exception_handlers

app = FastAPI(title="Personal Knowledge Engine")
register_exception_handlers(app)

app.include_router(spaces.router)
app.include_router(sync.router)
app.include_router(search.router)
app.include_router(ask.router)