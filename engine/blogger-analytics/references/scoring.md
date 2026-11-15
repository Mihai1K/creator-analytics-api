# Scoring: Pulse & 6-block Score

> **FROZEN v1.0.** Pulse/Score formulas are locked (`score.py` `VERSION="1.0"`). Do not tune them
> until enough real snapshot history accumulates to justify a change on data, not intuition. Any
> change bumps VERSION and is recorded against history.


Two numbers, deliberately separate — "is this account alive?" ≠ "should I pay for it?" —
and the Score is broken into six blocks so a buyer sees **why**, not just a total.
Implemented in `scripts/score.py`; this is the rubric.

## Pulse (0–100) — liveness / activity

`Pulse = 0.5·recency + 0.3·frequency + 0.2·regularity`

| Component | Scale |
|---|---|
| Recency of last post | ≤2d→100 · ≤7d→85 · ≤14d→60 · ≤30d→30 · >30d→10 · unknown→50 |
| Posting frequency (posts/week) | ≥5→100 · ≥2→85 · ≥1→65 · <1→35 · unknown→50 |
| Regularity (CV of intervals, lower=better) | <0.5→100 · <1.0→75 · <1.5→45 · else 25 · unknown→70 |

## Score (0–100) — six blocks → TOTAL

Each block is 0–100 (higher = better) and reported individually. TOTAL = weighted mean of the
blocks that **have data** (missing blocks are excluded and listed in `missing_blocks`, never
guessed).

| Block | Weight | Measures | Key inputs |
|---|---|---|---|
| **Audience** | 0.20 | is the follower base real/quality | view-rate vs size, following/followers ratio, verified, private, fake_pct |
| **Engagement** | 0.20 | genuine interaction | ER vs platform band; TG view-rate; comment_rate |
| **Activity** | 0.15 | alive & regular (= Pulse) | recency, frequency, regularity |
| **Commercial** | 0.20 | price efficiency | CPV (`<1.5→100 · <2→80 · <3→50 · ≥3→20`) |
| **Content** | 0.10 | consistency & churn | posts/week, regularity, deleted_pct, recency |
| **Risk** | 0.15 | SAFETY (100=safe) | starts 100, subtracts: РКН missing −60, ER-suspect −35, dead-audience −30, private −20, ban −50, geo-mismatch −30, geo-unknown −10, heavy deletions −15 |

### ER healthy bands (ER = engagement / followers)
TikTok 1.5–18% · YouTube 0.7–6% · VK 0.4–5% · Instagram 0.8–10%. Above band → antifraud/Risk
penalised ("накрутка?"); Telegram uses **view-rate** (median-views/subs) 12–70% as healthy.
⚠️ TikTok view-rate >100% and huge view volatility are **normal** (FYP), not fraud.

### Verdict (hard rules first)
- **🔴** if РКН missing, **or** Risk < 40, **or** Engagement < 35, **or** Commercial ≤ 20 (CPV ≥ 3₽).
- **🟡** if TOTAL < 70, **or** geo unconfirmed, **or** any available block < 50.
- **🟢** otherwise.

Geo unconfirmed alone keeps a blogger at 🟡 — intentional for location-based products
(PowerApp stations only in Спб/Мск/Казань): nothing is fully green until the audience city is verified.

## Reading a result
`score.py` returns `pulse`, `total`, `verdict`, a `blocks` breakdown, `cpv`, `missing_blocks`,
and per-block `reasons`. The breakdown tells you the action: a low **Commercial** is a
*negotiation*, a low **Risk** or **Audience** (накрутка) is a *drop*, a low **Activity** on a
strong account is *"wait for a fresher window"*.

Example (real): `harryotvali` → Audience 70 · Engagement 90 · Activity 94 · Content 85 ·
Commercial 100 · Risk 90 → **TOTAL 88**, 🟡 only because geo/city isn't confirmed yet.
