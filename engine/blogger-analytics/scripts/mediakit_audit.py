#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media-kit audit — a blogger sends their kit (PDF/screenshot → numbers); the engine compares
the CLAIMED figures against LIVE-extracted actuals and calls it: устарел / расхождение / совпадает.

  Медиакит: подписчики 1,9 млн · Факт: 564 тыс · Расхождение −71% → «вероятно медиакит устарел /
  завышен». Просмотры завышены на 91% → «плановые просмотры недостоверны».

This is the exact check that caught Даниэла in the 34-blogger run, formalised for reuse.

Usage: python3 mediakit_audit.py claimed.json actual.json
  claimed.json: {"followers":1970000,"avg_views":184000,"er":0.01}
  actual.json:  {"followers":564000,"median_views":320000,...}  (engine output)
"""
from __future__ import annotations
import json, sys

FIELDS = [("followers", ["followers", "subscribers"]),
          ("views", ["median_views", "avg_views"]),
          ("er", ["er", "view_rate"])]


def pick(d, keys):
    for k in keys:
        if d.get(k) is not None:
            return d[k]
    return None


def audit(claimed: dict, actual: dict) -> dict:
    lines, worst = [], 0
    for label, keys in FIELDS:
        c = pick(claimed, keys)
        a = pick(actual, keys)
        if c is None:
            continue
        if a is None:
            lines.append({"field": label, "claimed": c, "actual": None,
                          "verdict": "не проверено (нет факта — площадка/логин)"})
            continue
        dev = (a - c) / c * 100 if c else None
        worst = max(worst, abs(dev)) if dev is not None else worst
        if abs(dev) <= 10:
            v = "совпадает"
        elif dev < 0:
            v = f"завышено в медиаките на {abs(dev):.0f}% (факт ниже)"
        else:
            v = f"занижено в медиаките на {dev:.0f}% (факт выше)"
        lines.append({"field": label, "claimed": c, "actual": a, "deviation_pct": round(dev), "verdict": v})

    if worst >= 50:
        overall = "🔴 МЕДИАКИТ НЕДОСТОВЕРЕН — крупное расхождение с фактом (устарел/завышен). Требовать свежую статистику."
    elif worst >= 20:
        overall = "🟡 Расхождения с фактом — уточнить дату медиакита и запросить актуальные скрины."
    else:
        overall = "🟢 Медиакит соответствует факту в пределах погрешности."
    return {"fields": lines, "max_deviation_pct": round(worst), "overall": overall}


if __name__ == "__main__":
    claimed = json.load(open(sys.argv[1], encoding="utf-8"))
    actual = json.load(open(sys.argv[2], encoding="utf-8"))
    r = audit(claimed, actual)
    print(r["overall"], "\n")
    for f in r["fields"]:
        print(f"  {f['field']:10} медиакит={f['claimed']} факт={f['actual']} → {f['verdict']}")
