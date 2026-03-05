"""Shared helpers for building API responses."""

from app.models.carousel import Carousel
from app.schemas.carousel import CarouselResponse


def carousel_to_response(carousel: Carousel, preview_base_url: str) -> CarouselResponse:
    """Build CarouselResponse from Carousel ORM and preview base URL."""
    preview_url = f"{preview_base_url.rstrip('/')}/api/v1/carousels/{carousel.id}/preview"
    return CarouselResponse(
        id=carousel.id,
        title=carousel.title,
        source_type=carousel.source_type,
        source_payload=carousel.source_payload,
        format=carousel.format,
        status=carousel.status,
        language=carousel.language,
        slides_count=carousel.slides_count,
        created_at=carousel.created_at,
        updated_at=carousel.updated_at,
        preview_url=preview_url,
    )
