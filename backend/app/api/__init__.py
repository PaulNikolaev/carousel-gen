from fastapi import APIRouter

from app.api.assets import router as assets_router
from app.api.carousels import router as carousels_router
from app.api.exports import router as exports_router
from app.api.generations import router as generations_router
from app.api.health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(assets_router)
api_router.include_router(carousels_router)
api_router.include_router(exports_router)
api_router.include_router(generations_router)
