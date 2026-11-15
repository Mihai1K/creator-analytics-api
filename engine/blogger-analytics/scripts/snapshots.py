#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProfileSnapshot store + dynamics engine — the history layer that turns a number into a trend.

A blogger is added once; every update appends a snapshot. Over time the store answers
"что изменилось и ПОЧЕМУ", not just "сколько сейчас":
  - рост / падение подписчиков и просмотров
  - скачки (spikes) — быстрый неорганический рост
  - подозрительная динамика — подписчики растут, а просмотры нет (накрутка)
  - объяснение изменения Pulse: «Pulse ↓ — −34% просмотров, −2 публикации/нед, +18 дней без постов»

Storage: one JSONL per blogger under <store>/<platform>__<username>.jsonl (one snapshot/line).

Usage:
  python3 snapshots.py save   <store> <profile.json>     # append a snapshot (profile = scored+extracted)
  python3 snapshots.py history <store> <platform> <user> # print snapshots
  python3 snapshots.py dynamics <store> <platform> <user># diff of last two snapshots (+ pulse reasons)
"""
from __future__ import annotations
import json, os, re, sys
from datetime import datetime

SNAP_FIELDS = ["date", "followers", "following", "likes_total", "median_views", "avg_views",
               "view_rate", "posts_per_week", "last_post", "pulse", "total", "quality"]


def _key(platform, username):
    return re.sub(r"[^\w.-]", "_", f"{platform}__{username}")


def _path(store, platform, username):
    os.makedirs(store, exist_ok=True)
    return os.path.join(store, _key(platform, username) + ".jsonl")


def make_snapshot(profile: dict) -> dict:
    """Extract a compact snapshot from a full profile/score dict."""
    snap = {"date": profile.get("collected_at") or profile.get("date")
            or datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}
    for f in SNAP_FIELDS[1:]:
        snap[f] = profile.get(f)
    # pull nested score fields if present
    if profile.get("score"):
        snap["pulse"] = profile["score"].get("pulse", snap.get("pulse"))
        snap["total"] = profile["score"].get("total", snap.get("total"))
    return snap


def save(store, platform, username, profile):
    snap = make_snapshot(profile)
    with open(_path(store, platform, username), "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")
    return snap


def history(store, platform, username):
    p = _path(store, platform, username)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _days(a, b):
    try:
        da = datetime.fromisoformat(str(a).replace("Z", "+00:00"))
        db = datetime.fromisoformat(str(b).replace("Z", "+00:00"))
        return abs((db - da).total_seconds()) / 86400
    except Exception:
        return None


def _pct(prev, curr):
    if prev in (None, 0) or curr is None:
        return None
    return round((curr - prev) / prev * 100, 1)


def dynamics(prev: dict, curr: dict) -> dict:
    """Diff two snapshots → deltas, anomaly flags, and human Pulse-change reasons."""
    d = _days(prev.get("date"), curr.get("date")) or 0
    fol = _pct(prev.get("followers"), curr.get("followers"))
    views = _pct(prev.get("median_views") or prev.get("avg_views"),
                 curr.get("median_views") or curr.get("avg_views"))
    ppw_prev, ppw_curr = prev.get("posts_per_week"), curr.get("posts_per_week")
    pulse_prev, pulse_curr = prev.get("pulse"), curr.get("pulse")

    flags, reasons = [], []
    if fol is not None:
        if fol >= 10:
            flags.append(f"рост подписчиков {fol:+.0f}%")
        elif fol <= -5:
            flags.append(f"падение подписчиков {fol:+.0f}%")
        # spike: big jump in a short window
        if d and d <= 7 and abs(fol) >= 15:
            flags.append(f"скачок подписчиков {fol:+.0f}% за {d:.0f}д — проверить неорганический рост")
    # накрутка signature: followers up, reach flat/down
    if fol is not None and views is not None and fol >= 10 and views <= 2:
        flags.append("подозрительная динамика: подписчики растут, просмотры не растут (накрутка?)")
    # idle
    idle = _days(curr.get("last_post"), curr.get("date"))
    if idle is not None and idle > 21:
        flags.append(f"заброшен: {idle:.0f} дней без постов")

    # Pulse-change reasons — decompose the movement
    if pulse_prev is not None and pulse_curr is not None:
        pd = pulse_curr - pulse_prev
        arrow = "↑" if pd > 0 else ("↓" if pd < 0 else "→")
        if views is not None and abs(views) >= 10:
            reasons.append(f"{views:+.0f}% просмотров")
        if ppw_prev is not None and ppw_curr is not None and abs(ppw_curr - ppw_prev) >= 1:
            reasons.append(f"{ppw_curr - ppw_prev:+.1f} публикаций/нед")
        if idle is not None and idle > 7:
            reasons.append(f"{idle:.0f} дней без постов")
        pulse_line = f"Pulse {arrow} {pulse_prev}→{pulse_curr}" + (f" — {', '.join(reasons)}" if reasons else "")
    else:
        pulse_line = None

    return {
        "days_between": round(d, 1),
        "followers_pct": fol, "views_pct": views,
        "pulse_delta": (pulse_curr - pulse_prev) if (pulse_prev is not None and pulse_curr is not None) else None,
        "total_delta": (curr.get("total") - prev.get("total")) if (prev.get("total") is not None and curr.get("total") is not None) else None,
        "flags": flags,
        "pulse_explanation": pulse_line,
    }


def latest_dynamics(store, platform, username):
    h = history(store, platform, username)
    if len(h) < 2:
        return {"note": f"недостаточно истории ({len(h)} снимок) — динамика появится со 2-го обновления"}
    return dynamics(h[-2], h[-1])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "history"
    store = sys.argv[2]
    if cmd == "save":
        prof = json.load(open(sys.argv[3], encoding="utf-8"))
        s = save(store, prof.get("platform"), prof.get("username"), prof)
        print(json.dumps(s, ensure_ascii=False, indent=2))
    elif cmd == "history":
        print(json.dumps(history(store, sys.argv[3], sys.argv[4]), ensure_ascii=False, indent=2))
    elif cmd == "dynamics":
        print(json.dumps(latest_dynamics(store, sys.argv[3], sys.argv[4]), ensure_ascii=False, indent=2))
    else:
        sys.exit("cmd: save | history | dynamics")
