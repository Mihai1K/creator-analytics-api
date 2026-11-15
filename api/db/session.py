"""DB session. SQLite locally, Postgres on the VPS — same code, one env var.

    DATABASE_URL=postgresql+psycopg://user:pass@host/db   # VPS
    (default)     sqlite:///./creators.db                 # local dev
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./creators.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session():
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
