#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Index — how much can we TRUST this profile's data (completeness × reliability).

NOT Pulse (liveness) and NOT Score (buy-worthiness). Quality answers a third question:
"насколько полны и надёжны сами данные?" A TikTok profile where only the header parsed
(no feed/ER) scores ~65; a fully-parsed Telegram channel ~98; a gated VK profile ~0.
This lets the UI show a buyer "доверяй этой карточке на 65%" and prioritise re-checks.

Quality = Σ(weight · reliability_if_present) / Σ(weight) · 100, over the ideal buy-decision
field set. A missing field contributes 0 — that's the whole point (missing ≠ fine).

Usage: python3 quality.py profiles.json   (array or single dict) → per-profile quality
"""
from __future__ import annotations
import json, sys

# Quality is completeness relative to what is ACHIEVABLE on that platform (with proper access),
# NOT a universal field list — so a platform isn't penalised for fields it simply doesn't have.
# Engagement/reach ARE achievable on TikTok (with login/API), so a logged-out header-only capture
# honestly scores mid (we have identity, not engagement) — that's the point: no inflation.
ACHIEVABLE = {
    "Telegram": {"followers": 2, "reach": 2, "engagement": 2, "activity": 1.5, "content": 1},
    "TikTok":   {"followers": 2, "following": 0.5, "likes_total": 1, "verified": 0.5,
                 "reach": 2, "engagement": 2, "activity": 1.5, "content": 1},
    "YouTube":  {"followers": 2, "video": 0.5, "reach": 2, "engagement": 2, "activity": 1.5},
    "VK":       {"followers": 2, "reach": 2, "engagement": 2, "activity": 1.5, "content": 1},
    "RuTube":   {"followers": 2, "reach": 2, "engagement": 1.5, "activity": 1.5, "content": 1},
}
DEFAULT_ACHIEVABLE = {"followers": 2, "reach": 2, "engagement": 2, "activity": 1.5, "content": 1}
REL = {"verified": 1.0, "public": 0.9, "estimated": 0.75, "low": 0.6}


def _present(prof, field):
    m = {
        "followers": ["followers", "subscribers"],
        "reach": ["median_views", "avg_views", "view_rate"],
        "engagement": ["er", "view_rate"],
        "activity": ["last_post", "posts_per_week"],
        "content": ["regularity", "deleted_pct"],
        "following": ["following"],
        "verified": ["verified"],
        "likes_total": ["likes_total", "heart"],
        "video": ["video", "videos", "video_count"],
    }
    for k in m.get(field, [field]):
        v = prof.get(k)
        if v not in (None, "", [], {}):
            return True
    return False


def quality(prof: dict) -> dict:
    conf = (prof.get("confidence") or prof.get("trust") or "").lower()
    default_rel = REL.get(conf, 0.9)
    ideal = ACHIEVABLE.get(prof.get("platform"), DEFAULT_ACHIEVABLE)
    got, total, present, missing = 0.0, 0.0, [], []
    for field, w in ideal.items():
        total += w
        if _present(prof, field):
            # derived/engagement fields are trusted a bit less even when present
            rel = 0.75 if field in ("engagement", "content") and prof.get("er") is None else default_rel
            got += w * rel
            present.append(field)
        else:
            missing.append(field)
    q = round(got / total * 100) if total else 0
    band = "high" if q >= 85 else "medium" if q >= 60 else "low"
    return {"quality": q, "band": band, "present": present, "missing": missing,
            "note": f"{len(present)}/{len(ideal)} достижимых полей площадки; не хватает: {', '.join(missing) or '—'}"}


if __name__ == "__main__":
    data = json.load(sys.stdin if (len(sys.argv) < 2 or sys.argv[1] == "-") else open(sys.argv[1], encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    for p in data:
        q = quality(p)
        print(f"{(p.get('name') or p.get('username') or '?'):22} [{p.get('platform')}] "
              f"Quality={q['quality']:3} ({q['band']}) — {q['note']}")
