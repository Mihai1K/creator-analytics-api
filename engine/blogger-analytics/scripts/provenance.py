#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Per-field provenance builder — every value carries WHERE it came from and HOW MUCH to trust it.
In six months this saves enormous time: you can see exactly which field was scraped from a page
vs read from an API vs derived, and re-verify only the shaky ones.

Wraps a flat parser dict into { field: {value, source, method, confidence, reliability, url,
selector, updatedAt} } using a per-platform extraction map + the stress-test reliability file.

Usage: python3 provenance.py <platform> <url> <profile.json>
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime

# (method, confidence, selector/locus) per platform+field — verified this session
META = {
    "TikTok": {
        "followers":   ("browser_dom/embedded_json", "verified", "__UNIVERSAL_DATA__…userInfo.stats.followerCount"),
        "following":   ("browser_dom/embedded_json", "verified", "…userInfo.stats.followingCount"),
        "likes_total": ("browser_dom/embedded_json", "verified", "…userInfo.stats.heartCount"),
        "heart":       ("browser_dom/embedded_json", "verified", "…userInfo.stats.heartCount"),
        "video":       ("browser_dom/embedded_json", "verified", "…userInfo.stats.videoCount"),
        "verified":    ("browser_dom/embedded_json", "verified", "…userInfo.user.verified"),
        "bio":         ("browser_dom/embedded_json", "public",   "…userInfo.user.signature"),
        "rkn":         ("browser_dom",               "estimated", "bio regex /ркн|№\\d{6,}/ — LOW, use registry"),
    },
    "Telegram": {
        "subscribers":    ("server_html", "verified",  "tgme_channel_info_counter[subscribers]"),
        "median_views":   ("server_html", "public",    "median(tgme_widget_message_views)"),
        "avg_views":      ("server_html", "public",    "mean(tgme_widget_message_views)"),
        "view_rate":      ("server_html", "estimated", "median_views / subscribers"),
        "posts_per_week": ("server_html", "estimated", "Δ(time[datetime])"),
        "regularity":     ("server_html", "estimated", "CV of post intervals"),
        "deleted_pct":    ("server_html", "estimated", "message-id gaps (LOW if <10 posts)"),
        "last_post":      ("server_html", "verified",  "last time[datetime]"),
        "description":    ("server_html", "public",    "og:description / tgme_channel_info_description"),
    },
    "YouTube": {
        "subscribers": ("official_api|browser_dom", "verified", "channels.list.statistics.subscriberCount | header"),
        "video":       ("official_api|browser_dom", "verified", "statistics.videoCount | header"),
        "median_views":("browser_dom",              "public",   "grid video view overlays"),
    },
}
REL = {"verified": "high", "public": "high", "estimated": "medium"}
# fields explicitly known-unstable get forced low regardless of source
FORCE_LOW = {("TikTok", "rkn"), ("Telegram", "deleted_pct")}


def provenance(profile: dict, platform: str, url: str = "", updated_at: str = None):
    updated_at = updated_at or profile.get("collected_at") or (datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    m = META.get(platform, {})
    out = {}
    for field, meta in m.items():
        if field not in profile or profile.get(field) in (None, "", [], {}):
            continue
        method, confidence, selector = meta
        reliability = "low" if (platform, field) in FORCE_LOW else REL.get(confidence, "medium")
        out[field] = {
            "value": profile[field],
            "source": platform,
            "method": method,
            "confidence": confidence,
            "reliability": reliability,
            "url": url or profile.get("url", ""),
            "selector": selector,
            "updatedAt": updated_at,
        }
    return out


if __name__ == "__main__":
    platform, url, path = sys.argv[1], sys.argv[2], sys.argv[3]
    prof = json.load(open(path, encoding="utf-8"))
    print(json.dumps(provenance(prof, platform, url), ensure_ascii=False, indent=2))
