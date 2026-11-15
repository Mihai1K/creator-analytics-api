"""The vertical slice: link → fetch → score → save → history.

One path, end to end. Other platforms plug in as providers later without
touching this orchestration or the engine.

Caching is not an optimisation here, it is a requirement: t.me rate-limits
repeated requests (proven live — a second fetch of the same channel seconds
later is refused). The slug resolves offline, so a fresh stored check is served
without touching the network at all.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db.models import Creator, CreatorCheck, ReviewLead, utcnow
from .engine_link import score_engine, tg_engine
from .providers import telegram as tg

# How long a stored check is considered fresh. Channel metrics move slowly;
# t.me anti-flood does not forgive. 6h is a polite default.
DEFAULT_MAX_AGE = timedelta(hours=6)

# Public-form rate limit: cache spares t.me on repeat channels, this spares it
# from one client fanning across many fresh channels. Per-IP, sliding window.
# In-memory is fine for a single-process prototype; use Redis on the VPS.
RATE_MAX = 8
RATE_WINDOW_S = 60
_hits: Dict[str, Deque[float]] = defaultdict(deque)


def rate_limit_ok(key: str, max_hits: int = RATE_MAX, window_s: int = RATE_WINDOW_S) -> bool:
    now = time.monotonic()
    dq = _hits[key]
    while dq and now - dq[0] > window_s:
        dq.popleft()
    if len(dq) >= max_hits:
        return False
    dq.append(now)
    return True


class CheckError(Exception):
    """Fetch/parse failed — surfaced to the caller as-is, never faked."""


def _find_creator(session: Session, external_id: str) -> Optional[Creator]:
    return session.scalar(
        select(Creator).where(
            Creator.platform == tg.PLATFORM,
            Creator.external_id == external_id,
        )
    )


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    # SQLite drops tz on read → naive datetime. Treat stored times as UTC so
    # comparisons with tz-aware utcnow() don't blow up across sessions.
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _fresh_check(
    session: Session, creator: Creator, max_age: timedelta
) -> Optional[CreatorCheck]:
    row = session.scalar(
        select(CreatorCheck)
        .where(CreatorCheck.creator_id == creator.id)
        .order_by(CreatorCheck.checked_at.desc())
        .limit(1)
    )
    if row and (utcnow() - _as_utc(row.checked_at)) <= max_age:
        return row
    return None


def check(
    session: Session,
    url: str,
    max_age: timedelta = DEFAULT_MAX_AGE,
    force: bool = False,
) -> Tuple[CreatorCheck, bool]:
    """Returns (check, from_cache). Never hits t.me when a fresh check exists."""
    slug = tg_engine.channel_slug(url or "")  # offline, no network
    if not slug:
        raise CheckError("пустая ссылка на канал")

    if not force:
        existing = _find_creator(session, slug)
        if existing is not None:
            cached = _fresh_check(session, existing, max_age)
            if cached is not None:
                return cached, True

    got = tg.fetch(url)
    if got.error or not got.normalized:
        raise CheckError(got.error or "не удалось разобрать канал")

    profile = got.normalized
    report = score_engine.score(profile)  # frozen v1.0 — unchanged

    creator = _find_creator(session, got.external_id)
    if creator is None:
        creator = Creator(
            platform=tg.PLATFORM,
            external_id=got.external_id,
            canonical_url=got.canonical_url,
        )
        session.add(creator)

    creator.username = profile.get("username") or creator.username
    creator.title = profile.get("name") or creator.title
    creator.canonical_url = got.canonical_url
    creator.updated_at = utcnow()

    check_row = CreatorCheck(
        creator=creator,
        raw_data=got.raw,                       # never dropped
        normalized_data=profile,
        pulse=report.get("pulse"),
        score=report.get("total"),
        report=report,
        engine_version=report.get("engine_version", "?"),
    )
    session.add(check_row)
    session.commit()
    return check_row, False


def history(session: Session, creator_id: int) -> list[CreatorCheck]:
    return list(
        session.scalars(
            select(CreatorCheck)
            .where(CreatorCheck.creator_id == creator_id)
            .order_by(CreatorCheck.checked_at.desc())
        )
    )


def creators(session: Session, limit: int = 100) -> list[Creator]:
    return list(
        session.scalars(select(Creator).order_by(Creator.updated_at.desc()).limit(limit))
    )


# Snapshot only the numbers the expert needs to prep the review by hand.
_SNAPSHOT_KEYS = (
    "name", "username", "url", "subscribers", "avg_views", "median_views",
    "view_rate", "posts_per_week", "regularity", "last_post",
)


def save_review_lead(
    session: Session,
    channel_url: str,
    contact_type: str,
    contact: str,
    email: Optional[str] = None,
    creator_id: Optional[int] = None,
    normalized: Optional[dict] = None,
    verdict: Optional[dict] = None,
) -> ReviewLead:
    snap = None
    if normalized:
        snap = {k: normalized.get(k) for k in _SNAPSHOT_KEYS}
        if verdict:
            snap["pulse"] = verdict.get("pulse")
            snap["score"] = verdict.get("total")
            snap["verdict"] = verdict.get("verdict")
    lead = ReviewLead(
        channel_url=channel_url,
        creator_id=creator_id,
        contact_type=contact_type,
        contact=contact,
        email=email or None,
        source="lead_review",
        snapshot=snap,
    )
    session.add(lead)
    session.commit()
    return lead


# Новая → В работе → Разбор отправлен → Сделка / Отказ
VALID_STATUSES = ("new", "in_progress", "sent", "deal", "rejected")


def _latest_report(session: Session, creator_id: Optional[int]) -> Optional[dict]:
    if not creator_id:
        return None
    row = session.scalar(
        select(CreatorCheck)
        .where(CreatorCheck.creator_id == creator_id)
        .order_by(CreatorCheck.checked_at.desc())
        .limit(1)
    )
    return row.report if row else None


def list_review_leads(session: Session, limit: int = 200):
    """Leads newest-first, each with the creator's latest internal report
    (pulse/score/blocks/risk reasons) attached — for the expert inbox only."""
    leads = list(
        session.scalars(
            select(ReviewLead).order_by(ReviewLead.created_at.desc()).limit(limit)
        )
    )
    return [(lead, _latest_report(session, lead.creator_id)) for lead in leads]


def update_review_lead(
    session: Session,
    lead_id: int,
    status: Optional[str] = None,
    note: Optional[str] = None,
) -> Optional[ReviewLead]:
    lead = session.get(ReviewLead, lead_id)
    if lead is None:
        return None
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError("недопустимый статус")
        lead.status = status
    if note is not None:
        lead.note = note.strip() or None
    session.commit()
    return lead
