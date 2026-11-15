# Per-platform extraction recipes

The concrete "how to get the fields" for each platform. Verified empirically this session
unless marked. The field × availability × trust matrix is in
[platform-data-map.md](platform-data-map.md).

---

## Telegram — `server_html` (fully automatable)

- **Method:** fetch `https://t.me/s/<channel>` (public preview, no login). Run
  `python3 scripts/telegram.py <channel|url> [...]`.
- **Yields:** name, description, **subscribers**, counter block (photos/videos/links), per-post
  **views**, post datetimes → **avg/min/max views**, **view_rate**, **posts_per_week**, **last_post**.
- **Stability:** high. **Trust:** public (subscriber count can lag/round). t.me anti-floods rapid
  requests → the script retries with a 1.5s delay; keep it to a human pace for many channels.
- **Not exposed:** comments (only if a discussion group is linked), audience geo/demographics.
- **Verified:** `demo_creator` → 23 800 subs, avg 4 723 views, view_rate 0.20, 11.7 posts/wk, last post parsed.

## TikTok — `browser_dom` (Claude-driven Browser) + parser

Server fetch is blocked (returns only "TikTok - Make Your Day"); the in-app Browser renders the JS
profile. ToS: view one profile as manual due-diligence, no scale scraping.

1. `Browser.navigate("https://www.tiktok.com/@<user>")`
2. `Browser.get_page_text` → header text. Pipe to `python3 scripts/tiktok.py -`.
   - **Yields:** name, username, **following**, **followers**, **likes_total**, bio, **rkn**
     (from "ркн"/registry № in bio), emails, telegram_contacts, external_links.
3. For per-video engagement: `Browser.read_page` (accessibility tree) → recent video **view counts**
   overlaid on the grid; compute ER/view-rate from those.
- **Deeper:** the page embeds JSON in `__UNIVERSAL_DATA_FOR_REHYDRATION__` / `SIGI_STATE` with richer
  stats — read only from your own opened page, don't crawl.
- **Stability:** header high; grid views med (lazy load). **Trust:** verified (rendered profile numbers).
- **Verified:** `harryotvali1` → 405.5K followers, 65.2M likes, rkn ✓, contacts parsed.

## YouTube — `official_api` preferred, `browser_dom` fallback

- **Best:** YouTube Data API v3 with an API key (no OAuth for public data):
  - `channels.list?part=snippet,statistics&id=…` → subscriberCount, viewCount, videoCount, title,
    description, country, publishedAt, thumbnails.
  - `videos.list?part=statistics&id=…` → per-video viewCount, likeCount, commentCount.
  - Quota 10 000 units/day; `channels.list`=1 unit, `search.list`=100. **Trust:** verified.
- **Fallback (no key):** Browser header gives subscribers + video count + description + links; per-video
  views in the grid are lazy/flaky. **Trust:** public.
- **Owner-only** (watch time, audience geo): YouTube Analytics API with the channel owner's OAuth.
- **Verified:** `@demo_youtuber` → 3.96M subs via Browser header.

## VK — `official_api` only (public web gated)

Browser navigation timed out; server fetch is refused. Use the VK API with a token
(register an app at id.vk.com):
- `groups.getById?fields=members_count,counters,activity,contacts` → members_count + public community fields.
- `wall.get` → public posts with `views.count`, `likes.count`, `reposts.count`, `comments.count`.
- `users.get` → public profile fields. `stats.get` (reach, demographics) is **admin-only**.
- **Stability:** high (API). **Trust:** verified. Rate ~3 rps/user-token; batch via `execute`.
- Licensed aggregators (LiveDune, Popsters) are the alternative when no token/owner access.

## RuTube · Дзен · Одноклассники · MAX

Recipes are filled from the platform data-map research (running). Known starting points:
- **RuTube — VERIFIED 2026-07-13** (public JSON, no key, no Cloudflare/CAPTCHA, ~0.6s):
  - `GET rutube.ru/api/video/<video_id>/` → **hits** (views), title, author{id,name}, category, all_tags,
    duration, age_range, created_ts, hide_comments/likes flags, **feed_subscribers_count**, is_ten_thousand (РКН).
  - `GET rutube.ru/api/profile/user/<user_id>/` → **subscribers_count** + name.
  - `GET rutube.ru/api/video/person/<user_id>/?page=1` → channel videos (20/page, paginated).
  - Discover ids from the channel/home HTML (server-fetch works; `/video/<32-hex>/`).
  - ⚠️ Corrections to earlier research: the FEED `rutube.ru/api/video/?limit=` returns **401** (needs auth,
    NOT public), and `/api/numbers/subscriber/user/<id>/` is **404** (wrong) — use `/api/profile/user/<id>/`.
- **Дзен (Zen):** public channel page shows subscriber count; data in embedded JSON in the HTML; no API;
  owner-only Studio for full stats; aggregators (zenstat, LiveDune).
- **Одноклассники (OK):** ok.ru public group/profile pages; official OK REST API with an app token.
- **MAX:** max.ru; official Bot API (`dev.max.ru`, token, bot must be in the channel); public page limited;
  since ~Feb 2026 per-post view counts are visible to subscribers in-app; aggregators (MaxFrame, mxstat).

See [platform-data-map.md](platform-data-map.md) for the field-by-field availability once research lands.
