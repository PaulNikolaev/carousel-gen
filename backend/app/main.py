from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import get_settings
from app.services.storage_service import StorageService


def _error_response(detail: str | list, code: int) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={"detail": detail, "code": code},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return _error_response(
            detail=exc.detail if isinstance(exc.detail, (str, list)) else str(exc.detail),
            code=exc.status_code,
        )
    raise exc


def _sanitize_validation_errors(errors: list) -> list:
    """Make validation error dicts JSON-serializable (e.g. ctx may contain Exception)."""
    out = []
    for e in errors:
        if not isinstance(e, dict):
            out.append({"msg": str(e)})
            continue
        cleaned = {}
        for k, v in e.items():
            if k == "ctx" and isinstance(v, dict):
                cleaned[k] = {k2: str(v2) if not isinstance(v2, (str, int, float, bool, type(None))) else v2 for k2, v2 in v.items()}
            elif isinstance(v, Exception):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        out.append(cleaned)
    return out


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(detail=_sanitize_validation_errors(exc.errors()), code=422)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.S3_BUCKET:
        storage = StorageService()
        await storage.ensure_bucket()
    yield


app = FastAPI(
    title="Carousel Generator API",
    version="0.1.0",
    description="API для генерации LinkedIn-каруселей.",
    lifespan=lifespan,
)

_allowed_origins = [
    o.strip()
    for o in get_settings().CORS_ALLOWED_ORIGINS.split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

app.include_router(api_router)
