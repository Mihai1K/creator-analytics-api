# Unified blogger profile schema

Every extractor normalizes into this one shape so the scorer and reports are
platform-agnostic. Each value carries provenance — the whole point is that a buyer can tell
a measured number from a guess.

## Value wrapper (provenance)

Wherever it matters, store a value with its origin:

```json
{ "value": 405500,
  "source": "TikTok",
  "method": "browser_dom",          // browser_dom | server_html | embedded_json | official_api
  "confidence": "verified",         // verified | public | estimated
  "reliability": "high",            // high | medium | low  — from stress_test.py, per field
  "updatedAt": "2026-07-13T00:00:00Z" }
```

- **confidence** (intrinsic trust): `verified` = read from the platform's own official surface
  (API, or the rendered profile number) · `public` = a public page that could lag/round ·
  `estimated` = derived/inferred (CPV computed, ER back-calculated). Never upgrade an estimate.
- **reliability** (measured): the field's stress-test fill-rate class (`scripts/stress_test.py`
  → `reliability.json`). A field that extracts on <80% of profiles is auto-downgraded to `low`
  regardless of its intrinsic confidence, so an unstable field can't quietly dominate a Score.
- **updatedAt**: when the value was collected — stats go stale; the scorer/UI can flag old data.

Parsers emit flat dicts + a `collected_at`; the wrapper (per-field provenance) is applied by a
thin adapter using the platform's method table (`platform-data-map.md`) + the reliability report.

## Profile

```json
{
  "identity": {
    "platform": null, "username": null, "url": null, "name": null,
    "verified": null, "avatar": null, "cover": null, "bio": null,
    "category": null, "geo_country": null, "geo_cities": [], "language": null,
    "rkn": null, "rkn_id": null
  },
  "size": {
    "followers": null, "following": null, "likes_total": null, "views_total": null,
    "videos_count": null, "posts_count": null
  },
  "activity": {
    "recent_posts": [ { "url": null, "date": null, "views": null, "likes": null,
                        "comments": null, "reposts": null, "is_pinned": null } ],
    "pinned_posts": [], "last_post": null, "posts_per_week": null,
    "avg_views": null, "views_min": null, "views_max": null, "view_rate": null
  },
  "engagement": {
    "er": null, "avg_likes": null, "avg_comments": null, "reaction_rate": null,
    "telegram_premium_pct": null, "citation_index": null
  },
  "contacts": {
    "emails": [], "telegram_contacts": [], "external_links": [], "other_socials": []
  },
  "commercial": {
    "cost": null, "cpv": null, "geo_match": null,        // filled from the media plan / target
    "notes": null
  },
  "extra": { "// any platform-specific field verbatim": null },
  "_provenance": { "collected_at": null, "sources": [], "access_notes": null }
}
```

## Notes
- Telegram uses `subscribers`→`followers`, `view_rate` instead of `er` (TG measures ERR by views).
- TikTok `likes_total` is cumulative all-time; per-post likes/views come from the grid (read_page).
- `geo_cities` / `geo_match` usually can't be filled from a public page — they need the blogger's
  own 30-day stats or an official API; leave null and flag for request rather than guessing.
- The scorer reads the flattened fields (`followers`, `er`, `avg_views`, `cpv`, `posts_per_week`,
  `last_post`, `rkn`, `geo_match`, `view_rate`); a thin adapter can flatten this profile for it.
