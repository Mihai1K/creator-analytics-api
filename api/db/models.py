"""Creator + CreatorCheck — the minimal store for the vertical slice.

Hard rule: the raw provider response is never discarded. Storing it means a new
Pulse/Score formula can be recomputed over history without re-crawling any
platform (and t.me anti-flood makes re-crawling expensive at scale).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (JSON, DateTime, ForeignKey, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)

# NOTE: SQLAlchemy resolves these annotations at runtime, so we use
# Optional[...]/List[...] rather than PEP-604 `str | None` — keeps the models
# importable on Python 3.9 (the machine here) as well as 3.11+ (the VPS).


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Creator(Base):
    """One author on one platform. Re-checking the same link reuses this row."""

    __tablename__ = "creator"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_creator_platform_external"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(190), index=True)
    canonical_url: Mapped[str] = mapped_column(String(500))
    username: Mapped[Optional[str]] = mapped_column(String(190), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    checks: Mapped[List["CreatorCheck"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
        order_by="CreatorCheck.checked_at.desc()",
    )


class CreatorCheck(Base):
    """One check of one creator at one moment. History = many of these."""

    __tablename__ = "creator_check"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("creator.id", ondelete="CASCADE"), index=True
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    # Never dropped — see module docstring.
    raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normalized_data: Mapped[dict] = mapped_column(JSON)
    pulse: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    report: Mapped[dict] = mapped_column(JSON)
    engine_version: Mapped[str] = mapped_column(String(16))

    creator: Mapped[Creator] = relationship(back_populates="checks")


class ReviewLead(Base):
    """A free express-review request from the /проверка lead magnet.

    The client entered a channel, we confirmed it exists, and they left a
    contact for a human-sent express review. We snapshot the check result so
    the expert has the numbers ready. Contact is one of telegram/phone
    (email optional) — asking both adds friction.
    """

    __tablename__ = "review_lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    channel_url: Mapped[str] = mapped_column(String(500))
    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("creator.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_type: Mapped[str] = mapped_column(String(16))   # telegram | phone
    contact: Mapped[str] = mapped_column(String(190))
    email: Mapped[Optional[str]] = mapped_column(String(190), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="lead_review")
    # new | in_progress | sent | deal | rejected
    status: Mapped[str] = mapped_column(String(16), default="new")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Numbers at capture time so the expert can prepare the review fast.
    snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
