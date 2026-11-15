#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scoring engine v2 — Pulse + a 6-block Score, so a buyer sees WHY, not just a number.

  PULSE (0–100)  — liveness: recency of last post + posting frequency + regularity.
  SCORE (0–100)  — buy-worthiness, decomposed into six blocks (each 0–100, higher = better):
      Audience    — is the follower base real/quality?
      Activity    — is the account alive & regular? (mirrors Pulse)
      Engagement  — ER vs platform norm, reaction/comment rates
      Content     — posting consistency, churn (deleted posts), recency of content
      Commercial  — price efficiency (CPV), reach-for-price
      Risk        — SAFETY (100 = safe): РКН, накрутка, dead audience, private/ban, geo mismatch
  TOTAL = weighted mean of the blocks that have data (missing blocks are excluded, not guessed),
          with hard rules (РКН missing → 🔴) → verdict 🟢/🟡/🔴 + a reasons list.

Input: JSON array of flat profiles (file arg or stdin). Recognized keys (all optional):
  platform, followers|subscribers, following, verified, private, ban,
  er, avg_views, median_views, views_min, views_max, view_rate, reaction_rate, comment_rate,
  posts_per_week, regularity (CV of intervals, lower=better), deleted_pct, last_post,
  cost, cpv, rkn, geo_match, name/username.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone

# FROZEN v1.0 — do NOT change Pulse/Score formulas until enough real data accumulates.
# Any change bumps VERSION and must be justified against snapshot history, not vibes.
VERSION = "1.0"
ER_BAND = {"tiktok": (0.015, 0.18), "youtube": (0.007, 0.06), "vk": (0.004, 0.05), "instagram": (0.008, 0.10)}
WEIGHTS = {"audience": 0.20, "engagement": 0.20, "activity": 0.15, "commercial": 0.20, "content": 0.10, "risk": 0.15}


def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, round(x)))


def pkey(p):
    p = (p or "").lower()
    for k in ("tiktok", "youtube", "vk", "instagram", "telegram", "rutube", "дзен", "zen", "max", "ok", "однокл"):
        if k in p:
            return k
    return p


def _vr(prof):
    if prof.get("view_rate") is not None:
        return prof["view_rate"]
    subs = prof.get("followers") or prof.get("subscribers")
    av = prof.get("avg_views") or prof.get("median_views")
    return (av / subs) if (av and subs) else None


def _days_since(iso):
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    except Exception:
        return None


def pulse(prof, R):
    # Honesty fix: with ZERO activity data (no last_post, no frequency, no regularity) we do
    # NOT fabricate a default 54 — return None (н/д). Otherwise every data-less TikTok shows
    # an identical fake Pulse. This is a bug fix, not a formula change.
    if prof.get("last_post") is None and prof.get("posts_per_week") is None and prof.get("regularity") is None:
        R.append("нет данных об активности → Pulse н/д")
        return None
    days = _days_since(prof.get("last_post")) if prof.get("last_post") else None
    rec = 50 if days is None else (100 if days <= 2 else 85 if days <= 7 else 60 if days <= 14 else 30 if days <= 30 else 10)
    if days is not None:
        R.append(f"последний пост {days:.0f}д назад")
    ppw = prof.get("posts_per_week")
    freq = 50 if ppw is None else (100 if ppw >= 5 else 85 if ppw >= 2 else 65 if ppw >= 1 else 35)
    if ppw is not None:
        R.append(f"{ppw} постов/нед")
    reg = prof.get("regularity")  # coefficient of variation of intervals; lower=better
    reg_score = 70
    if reg is not None:
        reg_score = 100 if reg < 0.5 else 75 if reg < 1.0 else 45 if reg < 1.5 else 25
        R.append(f"регулярность CV={reg:.2f}")
    return clamp(0.5 * rec + 0.3 * freq + 0.2 * reg_score)


def block_audience(prof, R):
    subs = prof.get("followers") or prof.get("subscribers")
    vr = _vr(prof)
    base = 70
    if prof.get("fake_pct") is not None:
        base = clamp(100 - prof["fake_pct"] * 100); R.append(f"fake {prof['fake_pct']*100:.0f}%"); return base
    if subs and vr is not None and subs > 300_000 and vr < 0.03:
        base -= 40; R.append("мёртвая база: view-rate<3% при крупной базе")
    fo, fol = prof.get("following"), subs
    if fo and fol and fol > 50_000 and fo / fol > 0.5:
        base -= 20; R.append("масс-фолловинг (following/followers>0.5)")
    if prof.get("verified") is True:
        base += 10; R.append("верифицирован")
    if prof.get("private") is True:
        base -= 25; R.append("приватный аккаунт")
    return clamp(base)


def block_engagement(prof, R):
    pk = pkey(prof.get("platform"))
    er = prof.get("er")
    band = ER_BAND.get(pk)
    val = None
    if er is not None and band:
        lo, hi = band
        if er > hi:
            val = 25; R.append(f"ER {er*100:.0f}% выше нормы {pk} → накрутка?")
        elif er < lo:
            val = 55; R.append(f"ER {er*100:.1f}% ниже нормы {pk}")
        else:
            val = 90; R.append(f"ER {er*100:.1f}% в норме {pk}")
    elif _vr(prof) is not None:
        vr = _vr(prof)
        val = 90 if 0.12 <= vr <= 0.7 else 55
        R.append(f"view-rate {vr*100:.0f}%")
    if val is None:
        return None
    if prof.get("comment_rate") is not None and prof["comment_rate"] < 0.001:
        val = min(val, 55); R.append("почти нет комментариев")
    return clamp(val)


def block_content(prof, R):
    base, have = 60, False
    ppw = prof.get("posts_per_week")
    if ppw is not None:
        have = True
        base += 15 if ppw >= 2 else 0 if ppw >= 1 else -15
    if prof.get("regularity") is not None:
        have = True
        base += 15 if prof["regularity"] < 0.8 else -10 if prof["regularity"] > 1.5 else 0
    dp = prof.get("deleted_pct")
    if dp is not None:
        have = True
        if dp > 0.3:
            base -= 20; R.append(f"удалено {dp*100:.0f}% постов")
    days = _days_since(prof.get("last_post")) if prof.get("last_post") else None
    if days is not None:
        have = True
        base += 10 if days <= 7 else -10 if days > 30 else 0
    return clamp(base) if have else None


def block_commercial(prof, R):
    cpv = prof.get("cpv")
    if cpv is None and prof.get("cost") and (prof.get("avg_views") or prof.get("median_views")):
        cpv = prof["cost"] / (prof.get("median_views") or prof.get("avg_views"))
    if cpv is None:
        return None, None
    R.append(f"CPV {cpv:.2f}₽")
    return (100 if cpv < 1.5 else 80 if cpv < 2 else 50 if cpv < 3 else 20), round(cpv, 2)


def block_risk(prof, R):
    safety = 100
    rkn = prof.get("rkn")
    if rkn is False:
        safety -= 60; R.append("РКН нет — юр-блокер")
    elif rkn is None:
        safety -= 15; R.append("РКН не подтверждён")
    pk = pkey(prof.get("platform")); er = prof.get("er"); band = ER_BAND.get(pk)
    if er is not None and band and er > band[1]:
        safety -= 35
    vr = _vr(prof); subs = prof.get("followers") or prof.get("subscribers")
    if subs and vr is not None and subs > 300_000 and vr < 0.03:
        safety -= 30
    if prof.get("private") is True:
        safety -= 20
    if prof.get("ban"):
        safety -= 50; R.append("бан/ограничения")
    gm = prof.get("geo_match")
    if gm is False:
        safety -= 30; R.append("гео не совпадает с целевыми городами")
    elif gm is None:
        safety -= 10; R.append("гео не подтверждено")
    if prof.get("deleted_pct") is not None and prof["deleted_pct"] > 0.4:
        safety -= 15
    return clamp(safety)


def score(prof):
    R = {"audience": [], "engagement": [], "activity": [], "content": [], "commercial": [], "risk": []}
    pl = pulse(prof, R["activity"])
    blocks = {
        "audience": block_audience(prof, R["audience"]),
        "engagement": block_engagement(prof, R["engagement"]),
        "activity": pl,
        "content": block_content(prof, R["content"]),
        "risk": block_risk(prof, R["risk"]),
    }
    comm, cpv = block_commercial(prof, R["commercial"])
    blocks["commercial"] = comm

    avail = {k: v for k, v in blocks.items() if v is not None}
    wsum = sum(WEIGHTS[k] for k in avail)
    total = clamp(sum(blocks[k] * WEIGHTS[k] for k in avail) / wsum) if wsum else None

    rkn = prof.get("rkn")
    if rkn is False or blocks["risk"] < 40 or (blocks["engagement"] is not None and blocks["engagement"] < 35) \
            or (comm is not None and comm <= 20):
        verdict = "🔴"
    elif (total is not None and total < 70) or prof.get("geo_match") is None \
            or any(v < 50 for v in avail.values()):
        verdict = "🟡"
    else:
        verdict = "🟢"

    return {
        "name": prof.get("name") or prof.get("username"),
        "platform": prof.get("platform"),
        "engine_version": VERSION,
        "pulse": pl,
        "total": total,
        "verdict": verdict,
        "blocks": {k: blocks[k] for k in ("audience", "activity", "engagement", "content", "commercial", "risk")},
        "cpv": cpv,
        "missing_blocks": [k for k, v in blocks.items() if v is None],
        "reasons": {k: v for k, v in R.items() if v},
    }


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = json.load(sys.stdin if src == "-" else open(src, encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    out = sorted((score(p) for p in data), key=lambda x: (x["total"] is None, -(x["total"] or 0)))
    print(json.dumps(out, ensure_ascii=False, indent=2))
