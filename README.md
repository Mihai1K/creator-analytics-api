# Creator Analytics API

A small FastAPI service that checks a public Telegram channel by link, stores the raw response, and returns facts plus a deterministic quality verdict. An early prototype of the analytics engine that later became part of the Blogger Market platform.

> Original notes in Russian: [README.ru.md](README.ru.md)

## Problem

Advertisers choose channels by subscriber count, which says little about real reach. Checking each channel by hand is slow, and repeated requests to the public channel page are quickly throttled.

## Solution

One endpoint takes a link, fetches open data, normalizes it and computes two scores in code, without an LLM. The raw response is always stored, so a changed formula can be recomputed over history without fetching again.

## Design rules

1. **One implementation of the scoring engine.** `api/engine_link.py` imports the scripts from `engine/blogger-analytics/scripts/`; the API is a wrapper, not a copy. The engine version is frozen and bumped only together with the formula.
2. **Raw data is never lost.** Each check stores the full platform response.
3. **The deterministic path has no LLM.** fetch -> normalize -> pulse -> score is plain code. Summaries and recommendations are a separate optional layer.
4. **Caching is required.** A fresh check (6 hours by default) is served without any network call.
5. **Open and closed parts.** `facts` (subscribers, views, ER, posting frequency) are public; `verdict` (scores and reasons) is returned separately.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/check` | `{"url": "https://t.me/<channel>", "force": false}` -> `facts`, `verdict`, `from_cache` |
| GET | `/creators` | recently checked creators |
| GET | `/creators/{id}/history` | history of checks |
| GET | `/health` | status and engine version |

## Data model

- **Creator** - a creator on a platform, unique by `(platform, external_id)`
- **CreatorCheck** - one check at one moment: raw data, normalized data, scores, report, engine version

## Tech stack

Python, FastAPI, SQLAlchemy 2, Pydantic 2, SQLite by default (PostgreSQL through `DATABASE_URL`).

## Run locally

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r api/requirements.txt
./.venv/bin/uvicorn api.main:app --reload      # http://127.0.0.1:8000/docs
```

## Layout

```
api/
  main.py          routes
  service.py       check orchestration and caching
  engine_link.py   import bridge to the scoring engine
  providers/       platform providers (Telegram)
  db/              models and session
  web/             static pages used during the prototype
engine/blogger-analytics/
  scripts/         scoring, extraction and helper scripts
  references/      design notes for the engine
```

## Status and limitations

- Prototype. Only Telegram is wired into the API; other scripts in `engine/` are experiments of different maturity.
- Reads public channel pages, so it depends on their markup and rate limits.
- No automated tests.
- Superseded by the analytics module of the Blogger Market platform (private repository).

## How this was built

I defined the metrics, the scoring rules and the product decisions. The code was written together with an AI coding agent (Claude Code) under my specifications and review.
