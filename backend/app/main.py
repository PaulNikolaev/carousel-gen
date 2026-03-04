from fastapi import FastAPI

from app.api import api_router

app = FastAPI(
    title="Carousel Generator API",
    version="0.1.0",
    description="API для генерации LinkedIn-каруселей.",
)

app.include_router(api_router)
