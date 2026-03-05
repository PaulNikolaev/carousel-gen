"""LLM service: build prompt, call OpenAI-compatible API, parse and validate slides JSON."""

import json
from typing import Any

import httpx
import structlog
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.schemas.llm import BODY_MAX, SlideGenerationResult, TITLE_MAX

_logger = structlog.get_logger()


def _log_llm_retry(retry_state) -> None:
    if retry_state.outcome is None or retry_state.outcome.failed is False:
        return
    exc = retry_state.outcome.exception()
    _logger.warning(
        "llm_call_error",
        attempt=retry_state.attempt_number,
        error=str(exc) if exc else "unknown",
    )


def _source_content_from_payload(source_payload: dict[str, Any]) -> str:
    parts: list[str] = []
    if source_payload.get("source_text"):
        parts.append(str(source_payload["source_text"]).strip())
    if source_payload.get("links"):
        links = source_payload["links"]
        joined = links if isinstance(links, str) else "\n".join(str(x) for x in links)
        parts.append(f"Links: {joined}")
    if source_payload.get("notes"):
        parts.append("Notes: " + str(source_payload["notes"]).strip())
    if source_payload.get("video_key") or source_payload.get("video_url"):
        raise NotImplementedError("Video transcription is not yet implemented")
    return "\n\n".join(parts) if parts else "No content provided."


def build_prompt(
    source_content: str,
    language: str,
    slides_count: int,
    style_hint: str | None,
) -> str:
    style_line = f"Style: {style_hint}." if style_hint else ""
    return f"""Generate exactly {slides_count} carousel slides from the following source. Output only a single JSON array, no markdown or extra text. Each item must have: "order" (1-based index), "title", "body", "footer".
Constraints: each "title" at most {TITLE_MAX} characters, each "body" at most {BODY_MAX} characters. Use language: {language}. {style_line}

Source:
{source_content}

JSON array:"""


async def _call_llm(prompt: str) -> tuple[str, int]:
    settings = get_settings()
    url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY.get_secret_value()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    usage = data.get("usage") or {}
    total_tokens = int(usage.get("total_tokens", 0))
    return content.strip(), total_tokens


def _parse_and_validate(content: str) -> SlideGenerationResult:
    raw = json.loads(content)
    if not isinstance(raw, list):
        raise ValueError("Expected JSON array")
    return SlideGenerationResult.model_validate(raw)


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, json.JSONDecodeError, ValueError, ValidationError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
    before_sleep=_log_llm_retry,
)
async def _call_llm_parse_and_validate(prompt: str) -> tuple[SlideGenerationResult, int]:
    content, total_tokens = await _call_llm(prompt)
    result = _parse_and_validate(content)
    return result, total_tokens


async def generate_slides(
    source_payload: dict[str, Any],
    language: str,
    slides_count: int,
    style_hint: str | None = None,
) -> tuple[SlideGenerationResult, int]:
    source_content = _source_content_from_payload(source_payload)
    prompt = build_prompt(source_content, language, slides_count, style_hint)
    return await _call_llm_parse_and_validate(prompt)
