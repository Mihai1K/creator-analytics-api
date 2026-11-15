"""Single source of truth for the analytics algorithms.

The platform extractors and the Pulse/Score formulas live in the blogger-analytics
skill (`engine/blogger-analytics/scripts/`). This service does NOT copy
them — it imports them, so exactly one implementation exists. Changing an
algorithm means changing it there, once, and bumping score.VERSION.
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / "engine" / "blogger-analytics" / "scripts"
)

if not SKILL_SCRIPTS.is_dir():
    raise RuntimeError(
        f"blogger-analytics scripts not found at {SKILL_SCRIPTS}. "
        "The API is a wrapper around the skill engine, not a copy of it."
    )

if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import mediakit_audit as mediakit_engine  # noqa: E402
import score as score_engine  # noqa: E402
import telegram as tg_engine  # noqa: E402

ENGINE_VERSION = score_engine.VERSION

__all__ = [
    "tg_engine",
    "score_engine",
    "mediakit_engine",
    "ENGINE_VERSION",
    "SKILL_SCRIPTS",
]
