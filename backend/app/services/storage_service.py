"""S3/MinIO storage: upload files, generate presigned URLs, ensure bucket at startup."""

import asyncio
import mimetypes
import os
from typing import IO
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings

_cached_s3_client = None


def _s3_client():
    global _cached_s3_client
    if _cached_s3_client is not None:
        return _cached_s3_client
    settings = get_settings()
    kwargs = {
        "service_name": "s3",
        "aws_access_key_id": settings.S3_ACCESS_KEY or None,
        "aws_secret_access_key": settings.S3_SECRET_KEY.get_secret_value() or None,
        "config": Config(signature_version="s3v4"),
    }
    if settings.S3_ENDPOINT:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT
        kwargs["region_name"] = "us-east-1"
    else:
        kwargs["region_name"] = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client(**kwargs)
    _cached_s3_client = client
    return client


def _object_key(prefix: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1] or ""
    name = f"{uuid4().hex}{ext}"
    return f"{prefix.rstrip('/')}/{name}" if prefix else name


def _sync_upload(
    client,
    file_obj: IO[bytes],
    bucket: str,
    key: str,
    content_type: str | None,
) -> None:
    extra = {"ContentType": content_type} if content_type else {}
    client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra)


def _sync_ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            region = client.meta.region_name
            if region and region != "us-east-1":
                client.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            else:
                client.create_bucket(Bucket=bucket)
        else:
            raise


def _sync_generate_presigned_url(
    client, bucket: str, key: str, expires_in: int = 3600
) -> str:
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def _public_url(bucket: str, key: str) -> str | None:
    base = get_settings().S3_PUBLIC_BASE_URL.strip()
    if not base:
        return None
    return f"{base.rstrip('/')}/{bucket}/{key}"


class StorageService:
    """Async S3/MinIO client using boto3 in threadpool."""

    def __init__(self) -> None:
        self._bucket = get_settings().S3_BUCKET
        self._client = _s3_client()

    @property
    def bucket(self) -> str:
        return self._bucket

    async def ensure_bucket(self) -> None:
        """Create bucket if it does not exist. Call at startup."""
        await asyncio.to_thread(_sync_ensure_bucket, self._client, self._bucket)

    async def upload_file(
        self,
        file_obj: IO[bytes],
        filename: str,
        bucket: str | None = None,
        prefix: str = "uploads",
    ) -> tuple[str, str]:
        """Upload file to S3; return (public or presigned url, key)."""
        b = bucket or self._bucket
        key = _object_key(prefix, filename)
        content_type = mimetypes.guess_type(filename, strict=False)[0]
        await asyncio.to_thread(
            _sync_upload, self._client, file_obj, b, key, content_type
        )
        url = _public_url(b, key)
        if url is None:
            url = await self.generate_presigned_url(key, bucket=b, expires_in=604800)
        return url, key

    async def upload_fileobj_with_key(
        self,
        file_obj: IO[bytes],
        key: str,
        content_type: str = "application/zip",
        bucket: str | None = None,
    ) -> None:
        """Upload bytes from file_obj to S3 under the given key."""
        b = bucket or self._bucket
        await asyncio.to_thread(
            _sync_upload, self._client, file_obj, b, key, content_type
        )

    async def generate_presigned_url(
        self,
        key: str,
        bucket: str | None = None,
        expires_in: int = 3600,
    ) -> str:
        """Return temporary download URL for the object."""
        b = bucket or self._bucket
        return await asyncio.to_thread(
            _sync_generate_presigned_url, self._client, b, key, expires_in
        )
