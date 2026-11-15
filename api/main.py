"""api.mediacentr.online — Analytics API (Telegram slice).

    POST /check                {"url": "https://t.me/durov"}  -> report + creator_id
    GET  /creators                                            -> recent creators
    GET  /creators/{id}/history                               -> check history
    GET  /health

Open/gated split (product decision): `facts` are public and indexable,
`verdict` (pulse/score/blocks/reasons) is the part worth registering for.
The API returns both; the frontend decides what to show to whom.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .db.session import get_session, init_db
from .engine_link import ENGINE_VERSION, mediakit_engine
from .service import (CheckError, check, creators, history, list_review_leads,
                      rate_limit_ok, save_review_lead, update_review_lead)

app = FastAPI(title="Mediacentr Analytics API", version="0.1.0")

WEB_DIR = Path(__file__).parent / "web"

# The inbox exposes INTERNAL Pulse/Score/risks + client contacts — never public.
# Local dev (no token): loopback only. Prod: set ADMIN_TOKEN, send X-Admin-Token.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


def admin_guard(request: Request) -> None:
    if ADMIN_TOKEN:
        if request.headers.get("x-admin-token") != ADMIN_TOKEN:
            raise HTTPException(status_code=403, detail="admin only")
        return
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(
            status_code=403,
            detail="admin only — set ADMIN_TOKEN to expose beyond localhost",
        )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Local demo: same server serves the check UI and the API (no CORS).
    In prod the front lives on check.mediacentr.online; the API stays here."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/review", include_in_schema=False)
def review_page() -> FileResponse:
    """Lead-magnet flow «/проверка»: check a channel → leave a contact for a
    human-sent express review. Prototype; on the live landing it becomes /proverka."""
    return FileResponse(WEB_DIR / "review.html")


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


@app.on_event("startup")
def _startup() -> None:
    init_db()


class CheckIn(BaseModel):
    url: str = Field(..., examples=["https://t.me/durov", "@durov", "durov"])
    # t.me rate-limits repeats — force=True re-fetches anyway (use sparingly).
    force: bool = False
    # Optional media-kit figures → we audit them against the live actuals.
    # This is the conversion hook (claimed 1.9M vs real 564K = -71%).
    claimed_subscribers: Optional[int] = None
    claimed_views: Optional[int] = None


FACT_KEYS = (
    "platform", "username", "url", "name", "description", "subscribers",
    "avg_views", "median_views", "view_rate", "posts_per_week",
    "avg_interval_h", "regularity", "last_post", "posts_sampled",
    "collected_at", "source", "trust",
)


def _facts(normalized: dict) -> dict:
    return {k: normalized.get(k) for k in FACT_KEYS}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "engine_version": ENGINE_VERSION}


def _audit(body: CheckIn, normalized: dict) -> Optional[dict]:
    """Media-kit audit: claimed figures vs live actuals — the conversion hook."""
    if body.claimed_subscribers is None and body.claimed_views is None:
        return None
    claimed = {}
    if body.claimed_subscribers is not None:
        claimed["followers"] = body.claimed_subscribers
    if body.claimed_views is not None:
        claimed["avg_views"] = body.claimed_views
    return mediakit_engine.audit(claimed, normalized)


@app.post("/check")
def post_check(
    body: CheckIn, request: Request, session: Session = Depends(get_session)
) -> dict:
    if not rate_limit_ok(_client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="слишком много проверок подряд — подождите минуту",
        )
    try:
        row, from_cache = check(session, body.url, force=body.force)
    except CheckError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "creator_id": row.creator_id,
        "checked_at": row.checked_at,
        "from_cache": from_cache,
        "engine_version": row.engine_version,
        "facts": _facts(row.normalized_data),          # open
        "audit": _audit(body, row.normalized_data),    # conversion hook
        "verdict": row.report,                          # gated later
    }


class ReviewLeadIn(BaseModel):
    channel_url: str
    contact_type: str = Field(..., examples=["telegram", "phone"])
    contact: str
    email: Optional[str] = None


@app.post("/review-lead")
def post_review_lead(
    body: ReviewLeadIn, session: Session = Depends(get_session)
) -> dict:
    ct = (body.contact_type or "").strip().lower()
    contact = (body.contact or "").strip()
    if ct not in ("telegram", "phone"):
        raise HTTPException(status_code=422, detail="контакт: telegram или phone")
    if not contact:
        raise HTTPException(status_code=422, detail="укажите контакт")
    if not (body.channel_url or "").strip():
        raise HTTPException(status_code=422, detail="нет ссылки на канал")

    # Attach the (cached) check so the expert gets numbers with the lead.
    creator_id = normalized = verdict = None
    try:
        row, _ = check(session, body.channel_url)   # cache hit — no t.me call
        creator_id = row.creator_id
        normalized = row.normalized_data
        verdict = row.report
    except CheckError:
        pass  # lead is still saved; expert re-checks manually

    lead = save_review_lead(
        session,
        channel_url=body.channel_url.strip(),
        contact_type=ct,
        contact=contact,
        email=(body.email or "").strip() or None,
        creator_id=creator_id,
        normalized=normalized,
        verdict=verdict,
    )
    return {"ok": True, "lead_id": lead.id}


STATUS_LABELS = {
    "new": "Новая",
    "in_progress": "В работе",
    "sent": "Разбор отправлен",
    "deal": "Сделка",
    "rejected": "Отказ",
}


@app.get("/inbox", include_in_schema=False, dependencies=[Depends(admin_guard)])
def inbox_page() -> FileResponse:
    """Expert inbox UI. Admin-only — shows internal Pulse/Score + contacts."""
    return FileResponse(WEB_DIR / "inbox.html")


@app.get(
    "/review-leads",
    include_in_schema=False,
    dependencies=[Depends(admin_guard)],
)
def get_review_leads(session: Session = Depends(get_session)) -> dict:
    """Expert inbox data. ADMIN-ONLY — internal Pulse/Score/risks live here,
    never on the public API."""
    items = []
    for lead, report in list_review_leads(session):
        risk_reasons = (report or {}).get("reasons", {}).get("risk", [])
        blocks = (report or {}).get("blocks", {})
        items.append(
            {
                "id": lead.id,
                "created_at": lead.created_at,
                "channel_url": lead.channel_url,
                "contact_type": lead.contact_type,
                "contact": lead.contact,
                "email": lead.email,
                "status": lead.status,
                "note": lead.note,
                "snapshot": lead.snapshot,        # facts
                "pulse": (report or {}).get("pulse"),     # internal
                "score": (report or {}).get("total"),     # internal
                "verdict": (report or {}).get("verdict"),
                "risk_score": blocks.get("risk"),
                "risk_reasons": risk_reasons,
            }
        )
    return {"labels": STATUS_LABELS, "leads": items}


class LeadPatch(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None


@app.patch(
    "/review-leads/{lead_id}",
    include_in_schema=False,
    dependencies=[Depends(admin_guard)],
)
def patch_review_lead(
    lead_id: int, body: LeadPatch, session: Session = Depends(get_session)
) -> dict:
    try:
        lead = update_review_lead(session, lead_id, status=body.status, note=body.note)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if lead is None:
        raise HTTPException(status_code=404, detail="заявка не найдена")
    return {"ok": True, "id": lead.id, "status": lead.status, "note": lead.note}


@app.get("/creators")
def get_creators(session: Session = Depends(get_session)) -> list[dict]:
    return [
        {
            "id": c.id,
            "platform": c.platform,
            "username": c.username,
            "title": c.title,
            "canonical_url": c.canonical_url,
            "updated_at": c.updated_at,
            "checks": len(c.checks),
        }
        for c in creators(session)
    ]


@app.get("/creators/{creator_id}/history")
def get_history(creator_id: int, session: Session = Depends(get_session)) -> list[dict]:
    rows = history(session, creator_id)
    if not rows:
        raise HTTPException(status_code=404, detail="creator not found / no checks")
    return [
        {
            "checked_at": r.checked_at,
            "pulse": r.pulse,
            "score": r.score,
            "verdict": r.report.get("verdict"),
            "subscribers": r.normalized_data.get("subscribers"),
            "median_views": r.normalized_data.get("median_views"),
            "engine_version": r.engine_version,
            "raw_kept": r.raw_data is not None,
        }
        for r in rows
    ]
