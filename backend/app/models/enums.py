"""Enums for SQLAlchemy models (mapped to PostgreSQL ENUMs)."""

import enum


class SourceTypeEnum(str, enum.Enum):
    text = "text"
    video = "video"
    links = "links"


class CarouselStatusEnum(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    failed = "failed"


class TemplateEnum(str, enum.Enum):
    classic = "classic"
    bold = "bold"
    minimal = "minimal"


class BackgroundTypeEnum(str, enum.Enum):
    color = "color"
    image = "image"


class GenerationStatusEnum(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class ExportStatusEnum(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
