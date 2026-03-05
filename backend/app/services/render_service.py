"""Render carousel slides to PNG via Playwright and pack into ZIP for S3."""

import html
import io
import re
import zipfile
from uuid import UUID

from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.carousel import Carousel
from app.models.carousel_design import CarouselDesign
from app.models.enums import BackgroundTypeEnum
from app.models.slide import Slide
from app.services.storage_service import StorageService

SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

_CSS_COLOR_RE = re.compile(
    r"^(#[0-9a-fA-F]{3,8}|rgba?\(\d+,\s*\d+,\s*\d+(?:,\s*[\d.]+)?\)|[a-zA-Z]{2,32})$"
)
_SAFE_URL_RE = re.compile(r"^https?://")


def _safe_css_color(value: str | None) -> str:
    """Return value if it looks like a valid CSS color, else fallback #FFFFFF."""
    if not value or not isinstance(value, str):
        return "#FFFFFF"
    return value if _CSS_COLOR_RE.match(value.strip()) else "#FFFFFF"


def _safe_css_url(value: str | None) -> str:
    """Return value if it's a safe http/https URL, else fallback empty string."""
    if not value or not isinstance(value, str):
        return ""
    return value if _SAFE_URL_RE.match(value.strip()) else ""


def _effective_design(design: CarouselDesign, overrides: dict) -> dict:
    base = {
        "background_type": design.background_type,
        "background_value": design.background_value or "#FFFFFF",
        "overlay": design.overlay,
        "padding": design.padding,
        "alignment_h": design.alignment_h,
        "alignment_v": design.alignment_v,
        "header_enabled": design.header_enabled,
        "header_text": design.header_text or "",
        "footer_enabled": design.footer_enabled,
        "footer_text": design.footer_text or "",
    }
    for key in base:
        if key in overrides and overrides[key] is not None:
            base[key] = overrides[key]
    return base


def _build_slide_html(
    title: str,
    body: str,
    footer: str,
    slide_index: int,
    total_slides: int,
    design: CarouselDesign,
    overrides: dict,
) -> str:
    eff = _effective_design(design, overrides)
    bg = eff["background_value"]
    if str(eff["background_type"]) == BackgroundTypeEnum.image.value and bg:
        safe_url = _safe_css_url(bg)
        if safe_url:
            bg_style = f"background-image: url({html.escape(safe_url)}); background-size: cover;"
        else:
            bg_style = "background-color: #FFFFFF;"
    else:
        bg_style = f"background-color: {_safe_css_color(bg)};"
    padding = max(0, min(96, eff["padding"]))
    align_h = eff["alignment_h"]
    align_v = eff["alignment_v"]
    justify = "center" if align_h == "center" else ("flex-start" if align_h == "left" else "flex-end")
    align = "center" if align_v == "center" else ("flex-start" if align_v == "top" else "flex-end")
    overlay_opacity = max(0, min(0.8, eff["overlay"]))
    header_html = ""
    if eff["header_enabled"]:
        header_html = f'<header class="header">{html.escape(eff["header_text"])} &nbsp; {slide_index} / {total_slides}</header>'
    footer_html = ""
    if eff["footer_enabled"]:
        footer_html = f'<footer class="footer">{html.escape(eff["footer_text"])} &nbsp; {html.escape(footer)}</footer>'
    overlay_style = ""
    if overlay_opacity > 0:
        overlay_style = f'<div class="overlay" style="opacity: {overlay_opacity}"></div>'
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; overflow: hidden; font-family: system-ui, sans-serif; {bg_style} position: relative; }}
.overlay {{ position: absolute; inset: 0; background: #000; pointer-events: none; }}
.container {{ position: relative; z-index: 1; display: flex; flex-direction: column; height: 100%; padding: {padding}px; justify-content: space-between; }}
.header {{ font-size: 28px; color: #333; flex-shrink: 0; }}
.main {{ flex: 1; display: flex; flex-direction: column; justify-content: {align}; align-items: {justify}; padding: 16px 0; }}
.main h1 {{ font-size: 36px; margin-bottom: 12px; line-height: 1.2; }}
.main .body {{ font-size: 22px; line-height: 1.4; white-space: pre-wrap; }}
.footer {{ font-size: 28px; color: #333; flex-shrink: 0; }}
</style>
</head>
<body>
{overlay_style}
<div class="container">
{header_html}
<div class="main">
<h1>{html.escape(title)}</h1>
<div class="body">{html.escape(body)}</div>
</div>
{footer_html}
</div>
</body>
</html>"""


async def _screenshot_slide(browser, html_content: str) -> bytes:
    page = await browser.new_page(viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT})
    try:
        await page.set_content(html_content, wait_until="domcontentloaded", timeout=5000)
        return await page.screenshot(type="png", timeout=10000)
    finally:
        await page.close()


async def render_carousel_to_zip(
    carousel_id: UUID,
    session: AsyncSession,
    storage: StorageService | None = None,
    export_id: UUID | None = None,
) -> str:
    """
    Load carousel with slides and design, render each slide to PNG, zip, upload to S3.
    Returns s3_key. Presigned URL should be generated on demand by the caller.
    """
    result = await session.execute(
        select(Carousel)
        .where(Carousel.id == carousel_id)
        .options(
            selectinload(Carousel.slides),
            selectinload(Carousel.design),
        )
    )
    carousel = result.scalar_one_or_none()
    if carousel is None:
        raise ValueError(f"Carousel {carousel_id} not found")

    design = carousel.design
    if design is None:
        from app.models.enums import TemplateEnum

        design = CarouselDesign(
            carousel_id=carousel_id,
            template=TemplateEnum.classic,
            background_type=BackgroundTypeEnum.color,
            background_value="#FFFFFF",
            overlay=0.0,
            padding=24,
            alignment_h="center",
            alignment_v="center",
            header_enabled=True,
            header_text="",
            footer_enabled=True,
            footer_text="",
        )

    slides = sorted(carousel.slides, key=lambda s: s.order)
    if not slides:
        raise ValueError(f"Carousel {carousel_id} has no slides")

    png_list: list[bytes] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for i, slide in enumerate(slides):
                html_str = _build_slide_html(
                    title=slide.title,
                    body=slide.body,
                    footer=slide.footer,
                    slide_index=i + 1,
                    total_slides=len(slides),
                    design=design,
                    overrides=slide.design_overrides or {},
                )
                png_bytes = await _screenshot_slide(browser, html_str)
                png_list.append(png_bytes)
        finally:
            await browser.close()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for idx, png_bytes in enumerate(png_list):
            zf.writestr(f"slide_{idx + 1:02d}.png", png_bytes)
    buf.seek(0)

    bucket = get_settings().S3_BUCKET
    key = f"exports/{carousel_id}/{export_id or 'archive'}.zip"
    if storage is None:
        storage = StorageService()
    await storage.upload_fileobj_with_key(buf, key, content_type="application/zip", bucket=bucket)
    return key
