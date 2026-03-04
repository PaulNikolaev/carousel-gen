"""Data access layer."""

from app.repositories.carousel_repository import CarouselRepository
from app.repositories.generation_repository import GenerationRepository
from app.repositories.slide_repository import SlideRepository

__all__ = ["CarouselRepository", "GenerationRepository", "SlideRepository"]
