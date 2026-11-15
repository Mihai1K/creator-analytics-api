"""Telegram provider — service wrapper around the frozen skill extractor.

Why not just call `telegram.analyze()`: analyze() fetches the page and then throws
the raw HTML away. We split fetch/parse so the raw response can be persisted
(CreatorCheck.raw_data) and Pulse/Score recomputed later without re-crawling.

Extraction and scoring logic itself is untouched — this file adds no parsing.
Public preview only (t.me/s/<slug>): no login, no API key, no anti-bot bypass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..engine_link import tg_engine

PLATFORM = "Telegram"


@dataclass
class Fetched:
    external_id: str
    canonical_url: str
    raw: Optional[str]
    normalized: Optional[dict]
    error: Optional[str] = None


def fetch(url_or_slug: str) -> Fetched:
    """link/@handle/slug -> raw html + normalized profile (or a clean error)."""
    slug = tg_engine.channel_slug(url_or_slug or "")
    if not slug:
        return Fetched("", "", None, None, "пустая ссылка на канал")

    canonical = f"https://t.me/{slug}"
    html = tg_engine.fetch(slug)  # raw — kept
    if not html:
        return Fetched(
            slug, canonical, None, None,
            "нет публичного превью t.me/s (канал приватный, не существует, "
            "или сработал анти-флуд t.me — повторите позже)",
        )

    return Fetched(slug, canonical, html, tg_engine.parse(html, slug))
