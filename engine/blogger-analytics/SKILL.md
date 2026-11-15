---
name: blogger-analytics
description: >-
  Analyze a blogger's PUBLIC page(s) across platforms and score them for ad-buy
  due-diligence. Given one or many blogger URLs (TikTok, Telegram, YouTube, VK, RuTube,
  Дзен, Одноклассники, MAX), extract every public profile field — followers, following,
  likes, views, bio, РКН mark, verification, contacts, external links, pinned/recent posts,
  post dates, posting frequency, geo — via the right method (in-app Browser for JS pages,
  server-fetch for public HTML, official API where a key/token exists), normalize to ONE
  schema with per-field provenance, then compute a Pulse (liveness/activity) and a Score
  (buy-worthiness) with antifraud flags and a 🟢/🟡/🔴 verdict. Use this whenever the user
  wants to check, verify, audit, or vet bloggers/influencers, assess engagement
  (лайки/просмотры/комментарии/ER/накрутка/вовлечённость), due-diligence a media plan's
  authors before paying, or build/extend a blogger data engine. Trigger on "проверь
  блогера", "аналитика блогеров", "антифрод", "вовлечённость", "engagement rate", "накрутка",
  "проверить медиаплан", "blogger check". Prefer this over eyeballing one page by hand.
---

# Blogger Analytics — the engine

Measure the page, don't trust the plan. A media plan's claimed subscribers/ER are
self-reported; this engine goes to the **public page**, pulls what's actually there, and
scores it. Every value is stamped with where it came from and how much to trust it, so a
buyer can tell a *verified* number from an *estimated* one.

It is **extensible by design**: adding a new platform means writing one extractor recipe +
(optionally) one parser and adding a row to the data map — not re-researching from scratch.

## 0. Authorization first

Read [references/authorization.md](references/authorization.md). Rules: only **public** data;
never bypass logins, CAPTCHAs, or anti-bot; respect ToS and rate limits. TikTok forbids
scraping-at-scale — treat it as viewing one profile in your own browser (manual
due-diligence), not a crawler. Where a platform gates its data, switch to its official API
(with your key/token) or a licensed aggregator — never force it.

## 1. Access reality (which method per platform)

The full field-by-field map is [references/platform-data-map.md](references/platform-data-map.md).
Headline (verified empirically):

| Platform | Best method | Public reach without login |
|---|---|---|
| **Telegram** | `server_html` → `scripts/telegram.py` on `t.me/s/<ch>` | ✅ subs, per-post views, dates, reactions |
| **TikTok** | `browser_dom` → Browser + `scripts/tiktok.py` | ✅ name, followers, following, likes, bio, РКН, contacts (grid views via read_page) |
| **YouTube** | `official_api` (Data API v3) ▸ or `browser_dom` | ✅ subs/videos/desc; exact per-video stats via API key |
| **VK** | `official_api` (VK API token) | ❌ public scrape gated (browser times out) → API only |
| **RuTube / Дзен / OK / MAX** | see data map | partial — public HTML / embedded JSON / official API |

## 2. Pipeline

```
URL(s) → detect platform → extract (right method) → normalize (schema) → score (Pulse+Score) → report
```

### Step 1 — Detect platform
From the host: `t.me`→Telegram, `tiktok.com`→TikTok, `youtube.com`→YouTube, `vk.com`/`vk.ru`→VK,
`rutube.ru`→RuTube, `dzen.ru`/`zen.yandex`→Дзен, `ok.ru`→OK, `max.ru`→MAX.

### Step 2 — Extract (per-platform recipes)
Full recipes + selectors/endpoints in [references/extractors.md](references/extractors.md). Quick form:

- **Telegram** — `python3 scripts/telegram.py <channel|url> [...]` → JSON (subs, avg/min/max views,
  view_rate, posts_per_week, last_post, counters, links). Runnable, no tools needed.
- **TikTok** — drive the in-app Browser: `navigate("https://www.tiktok.com/@<user>")` →
  `get_page_text` (header) and `read_page` (video grid view counts). Pipe the captured text to
  `python3 scripts/tiktok.py -` → JSON (name, username, following, followers, likes_total, bio,
  rkn, emails, telegram_contacts, external_links). For per-video ER, parse the grid views from
  `read_page`.
- **YouTube** — prefer the **Data API v3** (`channels.list?part=snippet,statistics`,
  `videos.list?part=statistics`) with an API key for exact numbers; else Browser header for subs.
- **VK** — **VK API** with a token: `groups.getById?fields=members_count`, `wall.get` (public post
  views/likes/reposts/comments). Public web is gated — don't try to scrape it.
- **Others** — see the data map for the working method per platform.

### Step 3 — Normalize
Map every extractor's output into the unified profile in [references/schema.md](references/schema.md).
Keep per-field `source`, `method`, `trust` (`verified`/`public`/`estimated`); drop nothing —
unknown fields go to `extra`.

### Step 4 — Score
`python3 scripts/score.py profiles.json` computes, per profile:
- **Pulse (0–100)** — liveness: recency of last post + posting frequency.
- **Score (0–100)** — buy-worthiness: antifraud (ER vs platform band, view-rate plausibility) +
  price (CPV) + Pulse + compliance (РКН) + geo match; ends in 🟢/🟡/🔴 with reasons.
Rubric and bands: [references/scoring.md](references/scoring.md).

### Step 5 — Report
Emit a ranked table (verdict · name · platform · followers · ER · CPV · Pulse · Score · reasons)
plus the normalized JSON. Lead with 🔴/🟡 (what to drop or verify), then 🟢 (greenlight after any
remaining checks — e.g. geo/city for a location-based product).

## 3. Scripts

| Script | Runs where | Does |
|---|---|---|
| `scripts/telegram.py` | plain Python (stdlib) | fetch+parse `t.me/s/` → subs, median/spread views, view-rate, interval, regularity, deleted%, last_post |
| `scripts/tiktok.py` | plain Python | parse Browser `get_page_text`/embedded-JSON → fields |
| `scripts/score.py` | plain Python | **v1.0 FROZEN** Pulse + 6-block Score (Audience/Activity/Engagement/Content/Commercial/Risk) + verdict |
| `scripts/quality.py` | plain Python | **Quality Index** — data completeness×reliability vs achievable-per-platform (≠ Pulse) |
| `scripts/snapshots.py` | plain Python | ProfileSnapshot store + **dynamics + Pulse-change reasons** (рост/скачок/накрутка/заброшен) |
| `scripts/provenance.py` | plain Python | per-field value·source·method·selector·confidence·reliability·updatedAt |
| `scripts/mediakit_audit.py` | plain Python | claimed (media-kit) vs actual → «устарел −71%» verdict |
| `scripts/update_runner.py` | plain Python + cron | add-once registry → re-check + snapshot + alerts (background loop) |
| `scripts/stress_test.py` | plain Python | run a parser over many public profiles → per-field fill-rate, timing, confidence downgrade |

## 5. Intelligence layer — from "check a blogger" to a knowledge system

This is where the value is. See [references/architecture.md](references/architecture.md) for the full
pipeline (Raw → Normalize → Provenance → Quality → Snapshots → Score(v1.0) → Dynamics → AI Report).
Non-negotiables:
- **Pulse/Score frozen at v1.0** — don't tune formulas until snapshot history justifies it.
- **History first:** run `update_runner.py` on a schedule; every update appends a ProfileSnapshot, so
  the engine explains *changes* (`Pulse ↓ 88→70 — −34% просмотров, −2 публикации/нед`), not just today.
- **AI Report step (killer feature):** after scoring, write a short text verdict per blogger —
  *Почему покупать · Почему нет · Главные риски · Что проверить вручную · Итог.* Ground it only in the
  engine's fields; where data is unavailable, say "недоступно — проверить вручную" (never invent).
- **Media-kit audit:** when a blogger sends a kit, run `mediakit_audit.py` (claimed vs live) before trusting it.

### Reliability discipline (this is what makes it industrial, not a prototype)
Field count means nothing without stability. Before trusting a field, stress-test it:
`python3 scripts/stress_test.py telegram` runs the parser over a batch of public channels and
reports, per field, the **fill-rate %** → confidence (`high ≥95% · medium ≥80% · low <80%`),
writing `reliability.json`. Fields that extract unstably are **auto-downgraded to `low`** so an
unreliable field can never quietly dominate a Score. Re-run per provider; the numbers, not the
claims, decide each field's trust. Endpoints are verified before they're documented — e.g. the
RuTube recipe in [extractors.md](references/extractors.md) was corrected against live 401/404s.

## 4. Adding a new platform (the extensible part)

1. Research the public page: what fields exist, and by which `method` (browser_dom /
   server_html / embedded_json / official_api). Note stability + trust.
2. Add a row-set to [references/platform-data-map.md](references/platform-data-map.md) and a recipe
   to [references/extractors.md](references/extractors.md).
3. If server-fetchable, add a small parser under `scripts/` mirroring `telegram.py`; if JS-gated,
   document the Browser steps; if API, document the endpoint + token.
4. Map its output to the schema — the scorer works unchanged.

The scorer and schema are platform-agnostic, so new platforms plug in without touching them.
