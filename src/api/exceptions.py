from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from database.exceptions import DatabaseError
from document.exceptions import DocumentLoaderError
from embedding.exceptions import EmbeddingError, InvalidEmbeddingConfigError, UnsupportedEmbeddingProviderError
from engine.exceptions import SyncEngineError
from vector_store.exceptions import UnsupportedVectorStoreError, VectorStoreError
from generation.exceptions import (
    GenerationAPIError,
    GenerationError,
    InvalidGenerationConfigError,
    UnsupportedGenerationProviderError,
)


def register_exception_handlers(app: FastAPI) -> None:

    async def not_found(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    async def bad_request(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    async def misconfigured(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    async def upstream_failure(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    async def internal_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    app.add_exception_handler(FileNotFoundError, not_found)
    app.add_exception_handler(NotADirectoryError, bad_request)
    app.add_exception_handler(UnsupportedEmbeddingProviderError, bad_request)
    app.add_exception_handler(UnsupportedVectorStoreError, bad_request)
    app.add_exception_handler(DocumentLoaderError, bad_request)
    app.add_exception_handler(InvalidEmbeddingConfigError, misconfigured)
    app.add_exception_handler(EmbeddingError, upstream_failure)
    app.add_exception_handler(VectorStoreError, internal_error)
    app.add_exception_handler(DatabaseError, internal_error)
    app.add_exception_handler(SyncEngineError, internal_error)
    app.add_exception_handler(UnsupportedGenerationProviderError, bad_request)
    app.add_exception_handler(InvalidGenerationConfigError, misconfigured)
    app.add_exception_handler(GenerationAPIError, upstream_failure)
    app.add_exception_handler(GenerationError, internal_error)