#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram public-channel extractor for the blogger-analytics engine.

Fetches the PUBLIC preview page https://t.me/s/<channel> (no login, no API) and parses
everything the page exposes: channel name, subscriber count, description, and per-post
views / reactions / datetimes. Computes activity signals (posting frequency, avg views,
view-rate, reaction-rate) used by the Pulse/Score engine.

Public preview only — this does not authenticate, scrape private data, or bypass anything.
If a channel is private or has no public /s/ page, it simply returns what's visible (or none).

Usage:
    python3 telegram.py <channel_or_url> [<channel_or_url> ...]
    python3 telegram.py vsezpif https://t.me/demo_creator
Outputs one JSON object per channel.
"""
from __future__ import annotations
import json, re, statistics, sys, urllib.request, urllib.error
from datetime import datetime
from html import unescape

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def channel_slug(s: str) -> str:
    s = s.strip().rstrip("/")
    s = re.sub(r"^https?://t\.me/(s/)?", "", s)
    s = re.sub(r"^@", "", s)
    return s.split("/")[0].split("?")[0]


def to_int(s: str):
    """'23.8K' / '1,2 млн' / '5 892' -> int."""
    if s is None:
        return None
    t = s.strip().lower().replace("\xa0", " ").replace(",", ".")
    mult = 1
    if "m" in t or "млн" in t or "kk" in t:
        mult = 1_000_000
    elif "k" in t or "к" in t or "тыс" in t:
        mult = 1_000
    num = re.sub(r"[^0-9.]", "", t)
    if not num:
        return None
    try:
        return int(round(float(num) * mult))
    except ValueError:
        return None


def fetch(slug: str, retries: int = 2) -> str | None:
    import time
    url = f"https://t.me/s/{slug}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ru,en"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", "replace")
            if "tgme_channel_info" in html or "tgme_widget_message" in html:
                return html
        except Exception:
            pass
        if attempt < retries:
            time.sleep(1.5)  # t.me anti-flood on rapid sequential requests
    return None


def parse(html: str, slug: str) -> dict:
    def first(pat, flags=re.S):
        m = re.search(pat, html, flags)
        return unescape(m.group(1)).strip() if m else None

    name = first(r'<meta property="og:title" content="([^"]*)"') or \
           first(r'tgme_channel_info_header_title[^>]*>\s*<span[^>]*>([^<]+)</span>')
    description = first(r'<meta property="og:description" content="([^"]*)"') or \
                  first(r'tgme_channel_info_description[^>]*>(.*?)</div>')
    if description:
        description = re.sub(r"<[^>]+>", "", description).strip()

    # counters block: value + type (subscribers / photos / videos / links)
    counters = {}
    for val, typ in re.findall(
            r'tgme_channel_info_counter[^>]*>\s*<span class="counter_value">([^<]+)</span>\s*'
            r'<span class="counter_type">([^<]+)</span>', html):
        counters[typ.strip().lower()] = to_int(val)
    subscribers = counters.get("subscribers") or counters.get("subscriber") or counters.get("members")

    # per-post views, datetimes, message ids (ids drive deleted% and total post count)
    views = [v for v in (to_int(v) for v in re.findall(r'tgme_widget_message_views">([^<]+)<', html)) if v]
    dates = re.findall(r'<time[^>]*datetime="([^"]+)"', html)
    ids = sorted({int(x) for x in re.findall(r'data-post="[^"/]+/(\d+)"', html)})

    def pct(data, q):
        s = sorted(data); k = (len(s) - 1) * q; f = int(k); c = min(f + 1, len(s) - 1)
        return s[f] + (s[c] - s[f]) * (k - f)

    avg_views = round(statistics.mean(views)) if views else None
    median_views = round(statistics.median(views)) if views else None
    p10 = round(pct(views, 0.10)) if views else None
    p90 = round(pct(views, 0.90)) if views else None
    views_spread = round(p90 / p10, 1) if (p10 and p90 and p10 > 0) else None
    # view_rate uses the MEDIAN (robust to one viral post) rather than the mean
    view_rate = round(median_views / subscribers, 4) if (median_views and subscribers) else None

    posts_per_week = avg_interval_h = regularity = None
    last_post = first_post = None
    if len(dates) >= 2:
        try:
            ds = sorted(datetime.fromisoformat(d.replace("Z", "+00:00")) for d in dates)
            gaps = [(ds[i + 1] - ds[i]).total_seconds() / 3600 for i in range(len(ds) - 1)]
            span_days = max((ds[-1] - ds[0]).total_seconds() / 86400, 0.01)
            posts_per_week = round((len(ds) - 1) / span_days * 7, 1)
            avg_interval_h = round(statistics.mean(gaps), 1)
            m = statistics.mean(gaps)
            regularity = round(statistics.pstdev(gaps) / m, 2) if (m > 0 and len(gaps) > 1) else None
            last_post, first_post = ds[-1].isoformat(), ds[0].isoformat()
        except Exception:
            pass

    # total post count ≈ max message id (upper bound; ids also count service/edited msgs)
    total_posts = ids[-1] if ids else None
    # deleted % from id gaps — ONLY on a dense window (≥10 posts), else it's a false signal:
    # t.me/s shows a small recent slice and ids increment for service msgs too, so a thin
    # sample massively over-reports "deleted". Low reliability even when computed.
    deleted_pct = None
    if len(ids) >= 10:
        id_window = ids[-1] - ids[0] + 1
        if id_window > 0:
            deleted_pct = round(1 - len(ids) / id_window, 3)

    return {
        "platform": "Telegram",
        "username": slug,
        "url": f"https://t.me/{slug}",
        "source": "server_html (t.me/s public preview)",
        "trust": "public",
        "collected_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "name": name,
        "description": description,
        "subscribers": subscribers,
        "counters": counters,
        "total_posts": total_posts,
        "posts_sampled": len(views),
        "avg_views": avg_views,
        "median_views": median_views,
        "views_min": min(views) if views else None,
        "views_max": max(views) if views else None,
        "views_p10": p10,
        "views_p90": p90,
        "views_spread": views_spread,
        "view_rate": view_rate,
        "posts_per_week": posts_per_week,
        "avg_interval_h": avg_interval_h,
        "regularity": regularity,
        "deleted_pct": deleted_pct,
        "last_post": last_post,
        "first_post": first_post,
        "post_views_sample": views[:12],
    }


def analyze(arg: str) -> dict:
    slug = channel_slug(arg)
    html = fetch(slug)
    if not html or "tgme_channel_info" not in html and "tgme_widget_message" not in html:
        return {"platform": "Telegram", "username": slug, "error": "no public preview / fetch blocked",
                "note": "fallback: use WebFetch t.me/s/<slug> via the assistant, or a licensed aggregator (TGStat)"}
    return parse(html, slug)


if __name__ == "__main__":
    args = sys.argv[1:] or ["durov"]
    out = [analyze(a) for a in args]
    print(json.dumps(out if len(out) > 1 else out[0], ensure_ascii=False, indent=2))
