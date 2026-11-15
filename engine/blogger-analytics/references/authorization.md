# Authorization & ToS — blogger due-diligence

Checking a blogger's **public** profile before paying them is legitimate, standard practice.
The rules keep it that way — public only, no forcing.

## Do
- Read only **publicly visible** data: what any logged-out visitor sees on the profile page,
  a public `t.me/s/` preview, or an official API you hold a key/token for.
- Prefer the **official API** when one exists (YouTube Data API, VK API) — it's the cleanest,
  most reliable, and unambiguously permitted route.
- Keep **provenance** on every field (`verified`/`public`/`estimated`) so nothing measured is
  confused with something guessed, and so the source is auditable.
- Go at a **human pace**, one profile at a time. Add small delays; back off on any 429/anti-flood.

## Don't
- **No bypassing** logins, CAPTCHAs, or anti-bot. If a page (VK, a private profile) won't load
  without auth, stop — switch to that platform's official API or a licensed aggregator.
- **No scraping at scale.** TikTok's ToS forbids automated scraping; this engine views *one*
  public profile in your own browser as manual due-diligence, not a crawler. Don't build a loop
  that hammers a platform, don't rotate identities, don't defeat rate limits.
- **No private/owner-only data** without the owner's consent (audience demographics, exact
  reach, city breakdown live behind the creator's own analytics — request them, don't extract).
- **No credential sharing / logged-in scraping** of accounts that aren't yours.

## The honest gap
Public pages rarely expose the two things a location-based buyer most needs — **audience city
geo** and **bot/quality breakdown**. Don't fabricate them. The correct step (and what a good
media plan mandates) is to **request the blogger's 30-day statistics screenshot** and/or use a
licensed aggregator (LiveDune, TGStat) or the official API. The engine flags these as
"to verify" rather than filling them with estimates.
