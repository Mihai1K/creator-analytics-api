#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reliability stress-test harness. Runs a parser over many PUBLIC profiles and measures, per
field: extraction success %, cross-profile fill-rate, and timing — then suggests a confidence
level (high ≥95% · medium ≥80% · low <80%). Fields that extract unstably get auto-downgraded,
so the engine guarantees quality/reproducibility, not just a big field count.

Usage:
  python3 stress_test.py telegram [channels_file]        # live-fetches t.me/s/ for each channel
  python3 stress_test.py records  profiles.json          # scores pre-captured records (e.g. TikTok)
Outputs a per-field reliability table (stdout) and writes reliability.json next to it.
"""
from __future__ import annotations
import json, os, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TELEGRAM_FIELDS = ["name", "subscribers", "description", "total_posts", "posts_sampled",
                   "avg_views", "median_views", "views_spread", "view_rate", "posts_per_week",
                   "avg_interval_h", "regularity", "deleted_pct", "last_post"]

# a broad set of known PUBLIC channels for the reliability sample (news, finance, bloggers)
DEFAULT_TG = ["durov", "telegram", "tginfo", "breakingmash", "bbbreaking", "rian_ru",
              "rt_russian", "meduzalive", "topor", "mash", "readovkanews", "rbc_news",
              "lentadnya", "kommersant", "forbesrussia", "banksta", "tass_agency",
              "ntvnews", "rentv_news", "cbrstocks", "markettwits", "addmeto", "denissexy",
              "exploitex", "prostithml", "vsezpif", "demo_creator", "demo_creator_2"]


def confidence(rate):
    return "high" if rate >= 95 else "medium" if rate >= 80 else "low"


def run_telegram(slugs):
    import telegram
    recs, timings = [], []
    for i, s in enumerate(slugs):
        t0 = time.time()
        r = telegram.analyze(s)
        dt = time.time() - t0
        timings.append(dt)
        recs.append(r)
        print(f"  [{i+1}/{len(slugs)}] {s:20} {'ERR' if r.get('error') else 'ok '} {dt:.1f}s", flush=True)
        time.sleep(0.6)  # be polite to t.me
    return recs, timings


def report(recs, timings, fields, label):
    n = len(recs)
    good = [r for r in recs if not r.get("error")]
    ok_rate = len(good) / n * 100 if n else 0
    print(f"\n=== reliability: {label} ===")
    print(f"profiles tried: {n} | parsed OK: {len(good)} ({ok_rate:.0f}%) | "
          f"avg time: {statistics.mean(timings):.2f}s" if timings else "")
    rows = []
    print(f"\n{'field':18} {'fill%':>6}  {'confidence':<8}  sample")
    for f in fields:
        vals = [r.get(f) for r in good if r.get(f) is not None]
        rate = len(vals) / len(good) * 100 if good else 0
        conf = confidence(rate)
        sample = vals[0] if vals else "—"
        rows.append({"field": f, "fill_rate": round(rate, 1), "confidence": conf, "n": len(good)})
        print(f"{f:18} {rate:5.0f}%  {conf:<8}  {str(sample)[:40]}")
    return {"label": label, "profiles": n, "parsed_ok": len(good),
            "parse_success_pct": round(ok_rate, 1),
            "avg_seconds": round(statistics.mean(timings), 2) if timings else None,
            "fields": rows,
            "downgrades": [r["field"] for r in rows if r["confidence"] != "high"]}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "telegram"
    if mode == "telegram":
        slugs = DEFAULT_TG
        if len(sys.argv) > 2:
            slugs = [l.strip() for l in open(sys.argv[2]) if l.strip()]
        recs, timings = run_telegram(slugs)
        rep = report(recs, timings, TELEGRAM_FIELDS, "Telegram (t.me/s server_html)")
    elif mode == "records":
        recs = json.load(open(sys.argv[2]))
        fields = sorted({k for r in recs for k in r.keys()})
        rep = report(recs, [0.0] * len(recs), fields, os.path.basename(sys.argv[2]))
    else:
        sys.exit("mode must be 'telegram' or 'records'")
    out = os.path.join(HERE, "reliability.json")
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"\nsaved {out}  |  downgrades (not high-confidence): {rep['downgrades']}")


if __name__ == "__main__":
    main()
