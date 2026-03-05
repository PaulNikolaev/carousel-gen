"""Assets API: upload files to S3/MinIO."""

import io
from typing import Set

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.services.storage_service import StorageService

router = APIRouter(prefix="/assets", tags=["assets"])

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_MIME_PREFIXES = ("image/", "video/", "font/")
ALLOWED_MIME_EXACT = ("application/pdf",)
BLOCKED_EXTENSIONS: Set[str] = {
    ".html", ".htm", ".svg", ".php", ".js", ".jsp", ".exe", ".bat",
    ".cmd", ".sh", ".vbs", ".ps1", ".cgi",
}
ALLOWED_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico",
    ".mp4", ".mov", ".avi", ".webm", ".mkv",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pdf",
}


def _get_storage() -> StorageService:
    return StorageService()


def _validate_file(filename: str, content_type: str | None) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    if content_type:
        allowed = (
            content_type.startswith(ALLOWED_MIME_PREFIXES)
            or content_type in ALLOWED_MIME_EXACT
        )
        if not allowed:
            raise HTTPException(status_code=400, detail="Content type not allowed")


@router.post("/upload")
async def upload_asset(
    file: UploadFile,
    storage: StorageService = Depends(_get_storage),
) -> dict:
    """Accept multipart file, upload to S3, return {url, key}."""
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Missing filename")
    filename = file.filename.strip()
    _validate_file(filename, file.content_type)

    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {MAX_UPLOAD_SIZE // (1024*1024)} MB)",
        )

    try:
        url, key = await storage.upload_file(
            io.BytesIO(content),
            filename,
            prefix="assets",
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upload failed: {e!s}",
        ) from e
    return {"url": url, "key": key}
