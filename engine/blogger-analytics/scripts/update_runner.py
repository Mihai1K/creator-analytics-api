#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background updater — add a blogger ONCE, then the system re-checks it and builds dynamics.

  update_runner.py add  <registry.json> <platform> <username> <url>   # register once
  update_runner.py run  <registry.json> <store_dir>                   # re-check all + snapshot + alert
  update_runner.py due  <registry.json> <store_dir> [max_age_hours]   # list who needs refresh

On `run`, each tracked blogger is re-extracted, scored (frozen v1.0), quality-graded, appended as a
ProfileSnapshot, and diffed against the previous snapshot → alerts (падение, скачок, накрутка, заброшен).
Telegram runs fully autonomously here (server-fetch). TikTok/YouTube/VK need the Browser/official API,
so they are emitted as a to-collect queue for the browser step (not silently skipped).

Schedule `run` from cron/launchd for a true background loop, e.g. hourly:
  0 * * * *  python3 update_runner.py run /path/registry.json /path/store
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score as scoremod, quality as qmod, snapshots as snap

AUTONOMOUS = {"Telegram"}  # extractable headless right now; others need Browser/API


def _load(reg):
    return json.load(open(reg, encoding="utf-8")) if os.path.exists(reg) else []


def add(reg, platform, username, url):
    data = _load(reg)
    if not any(b["platform"] == platform and b["username"] == username for b in data):
        data.append({"platform": platform, "username": username, "url": url,
                     "added_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat()})
        json.dump(data, open(reg, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"tracked: {platform}/{username} (total {len(data)})")


def extract(platform, username):
    """Return a flat profile for a platform, or None if it needs Browser/API."""
    if platform == "Telegram":
        import telegram
        r = telegram.analyze(username)
        return None if r.get("error") else r
    return None  # TikTok/YouTube/VK: collected via Browser/official API elsewhere


def run(reg, store):
    data = _load(reg)
    alerts, queued, updated = [], [], 0
    for b in data:
        p, u = b["platform"], b["username"]
        if p not in AUTONOMOUS:
            queued.append(f"{p}/{u}")
            continue
        prof = extract(p, u)
        if not prof:
            alerts.append(f"⚠️ {p}/{u}: extract failed (fetch blocked) — retry")
            continue
        prof["username"] = u
        sc = scoremod.score(prof)
        q = qmod.quality(prof)
        prof["score"] = sc; prof["pulse"] = sc["pulse"]; prof["total"] = sc["total"]; prof["quality"] = q["quality"]
        snap.save(store, p, u, prof)
        updated += 1
        dyn = snap.latest_dynamics(store, p, u)
        if dyn.get("flags"):
            alerts.append(f"🔔 {p}/{u}: " + "; ".join(dyn["flags"]))
        if dyn.get("pulse_explanation") and dyn.get("pulse_delta") and dyn["pulse_delta"] < 0:
            alerts.append(f"   ↳ {dyn['pulse_explanation']}")
    print(f"updated {updated} · queued-for-browser/API {len(queued)}")
    if queued:
        print("  queue:", ", ".join(queued))
    print("\nALERTS:" if alerts else "no alerts")
    for a in alerts:
        print(" ", a)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "add":
        add(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "")
    elif cmd == "run":
        run(sys.argv[2], sys.argv[3])
    else:
        sys.exit("cmd: add | run")
