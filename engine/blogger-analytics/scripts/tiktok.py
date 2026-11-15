#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok public-profile parser for the blogger-analytics engine.

TikTok blocks plain server fetch (returns only "TikTok - Make Your Day") and forbids
scraping in its ToS, so data is collected by the assistant driving the in-app Browser
(which renders the JS profile) with get_page_text, then this script parses that captured
text into structured fields. No scraping-at-scale, no anti-bot bypass — one page viewed
in your own browser, as manual due-diligence.

Flow:
  1. Assistant: Browser.navigate("https://www.tiktok.com/@<user>") then get_page_text
  2. Save that text to a file (or pipe via stdin)
  3. python3 tiktok.py <captured_text_file>   # or: get_page_text | python3 tiktok.py -

The header text looks like:
    TikTok, тикток
    <display name>
    <username>
    <following>
    Подписки
    <followers>
    Подписчики
    <likes_total>
    Лайки
    <bio lines...>
"""
from __future__ import annotations
import json, re, sys


def to_int(s):
    if s is None:
        return None
    t = str(s).strip().lower().replace("\xa0", " ").replace(",", ".")
    mult = 1
    if t.endswith("m") or "млн" in t:
        mult = 1_000_000
    elif t.endswith("k") or t.endswith("к") or "тыс" in t:
        mult = 1_000
    num = re.sub(r"[^0-9.]", "", t)
    if not num:
        return None
    try:
        return int(round(float(num) * mult))
    except ValueError:
        return None


def num_before(lines, label):
    """Return the numeric token on the line immediately before `label`."""
    for i, ln in enumerate(lines):
        if ln.strip() == label and i > 0:
            return to_int(lines[i - 1].strip())
    return None


def parse(text: str) -> dict:
    # drop the get_page_text preamble if present
    text = re.sub(r"^Title:.*?---\s*", "", text, flags=re.S)
    raw = [l for l in (x.rstrip() for x in text.splitlines()) if l.strip()]
    # strip the leading "TikTok, тикток" banner line
    lines = [l for l in raw if not re.match(r"^TikTok\b", l.strip(), re.I)]

    following = num_before(lines, "Подписки")
    followers = num_before(lines, "Подписчики")
    likes = num_before(lines, "Лайки")

    # display name + username sit just above the following-count block
    name = username = None
    for i, l in enumerate(lines):
        if l.strip() == "Подписки" and i >= 2:
            username = lines[i - 2].strip()
            name = lines[i - 3].strip() if i >= 3 else None
            break

    # bio = everything after the "Лайки" line
    bio = None
    for i, l in enumerate(lines):
        if l.strip() == "Лайки":
            bio = "\n".join(lines[i + 1:]).strip()
            break

    rkn = None
    if bio:
        if re.search(r"ркн", bio, re.I) or re.search(r"№\s*\d{6,}", bio):
            rkn = True
    # contacts / external links from bio
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", bio or "")
    tg = re.findall(r"(?:тг|tg|telegram)[:\s]*@?([A-Za-z0-9_]{3,})", bio or "", re.I)
    ext_links = re.findall(r"(https?://\S+|(?:www\.|t\.me/|instagram\.com/|vk\.com/)\S+)", bio or "")

    avg_like_per_post = None  # requires reading the video grid (read_page) separately

    return {
        "platform": "TikTok",
        "source": "browser_dom (in-app Browser get_page_text)",
        "trust": "verified",
        "name": name,
        "username": username,
        "following": following,
        "followers": followers,
        "likes_total": likes,
        "bio": bio,
        "rkn": rkn,
        "emails": emails,
        "telegram_contacts": tg,
        "external_links": ext_links,
        "note": "Per-video views/likes require reading the profile grid via Browser.read_page "
                "(accessibility tree) — parse those separately for ER/view-rate.",
    }


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    print(json.dumps(parse(text), ensure_ascii=False, indent=2))
