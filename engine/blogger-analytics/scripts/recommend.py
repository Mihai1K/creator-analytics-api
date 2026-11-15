#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recommendation Engine — prototype (commercial layer, consumes the FROZEN Intelligence Engine).

Brief (budget/goal/geo/platforms) → hard filters → contextual fit → portfolio under budget →
forecast (reach/installs/CPV) → per-pick "почему". Turns analytics into a buyable campaign.

Honesty: per-blogger audience geo/category are NOT in public logged-out data, so geo/topic fit
is flagged as a data-gap (needs media-kit), never invented. TikTok reach is estimated from
followers (feed gated) and marked ESTIMATE.

Usage: python3 recommend.py <pool.json> [budget] [goal] [max_bloggers]
  pool.json = webui/data.json (bloggers with score/quality/plan/actual)
"""
from __future__ import annotations
import json, sys, statistics

# forecast assumptions (flagged; tune from real campaign data later)
CR = {"installs": 0.003, "leads": 0.0006, "awareness": 0.0, "sales": 0.0008}  # view→action
TIKTOK_REACH_FACTOR = 0.5  # conservative FYP reach vs followers (ESTIMATE, feed gated)


def expected_reach(b):
    """Return (reach, source). Actual where we have it; conservative estimate for gated TikTok."""
    a = b["actual"]
    if a.get("median_views"):
        return a["median_views"], "median факт"
    if b["platform"] == "TikTok" and a.get("subs"):
        return round(a["subs"] * TIKTOK_REACH_FACTOR), "ОЦЕНКА (лента за логином)"
    if a.get("subs"):
        return round(a["subs"] * 0.15), "ОЦЕНКА"
    return None, None


def contextual_fit(b, brief, reach, cpv):
    """0–100 fit for THIS brief (NOT the generic Score). Missing geo/topic → penalty + flag."""
    gaps = []
    # cost efficiency vs target CPV
    tgt = brief.get("target_cpv") or 1.5
    cost_eff = max(0, min(100, 100 * tgt / cpv)) if cpv else 40
    # data confidence
    q = (b.get("quality") or {}).get("quality") or 30
    # engine signal (audience+risk from frozen Score)
    s = b.get("score") or {}
    eng = s.get("total") or 40
    # geo/topic fit — UNKNOWN in public data
    geo_fit, topic_fit = 50, 50  # neutral prior
    gaps += ["гео по городам", "категория/тематика"]
    fit = 0.35 * cost_eff + 0.20 * q + 0.20 * eng + 0.15 * geo_fit + 0.10 * topic_fit
    return round(fit), gaps


def recommend(pool, brief):
    budget = brief["budget"]; goal = brief.get("goal", "installs")
    plats = set(brief.get("platforms") or ["TikTok", "Telegram", "YouTube", "VK"])
    cands, rejected = [], []
    for b in pool:
        name = b["name"]
        if not b.get("score"):
            rejected.append((name, "нет данных (сбор не удался)")); continue
        if b["platform"] not in plats:
            rejected.append((name, f"платформа {b['platform']} вне брифа")); continue
        if b["plan"].get("rkn") is False:
            rejected.append((name, "РКН отсутствует (юр-блокер, дозаявить)")); continue
        reach, rsrc = expected_reach(b)
        cost = b["plan"]["cost"]
        if not reach or not cost:
            rejected.append((name, "нет охвата/цены")); continue
        cpv = round(cost / reach, 2)
        fit, gaps = contextual_fit(b, brief, reach, cpv)
        cands.append({"name": name, "platform": b["platform"], "cost": cost, "reach": reach,
                      "reach_src": rsrc, "cpv": cpv, "fit": fit,
                      "evidence": "факт" if rsrc == "median факт" else "оценка",
                      "quality": (b.get("quality") or {}).get("quality"),
                      "score": (b.get("score") or {}).get("total")})
    # PORTFOLIO v2 — ДЕНЬГИ ИДУТ ЗА ДОКАЗАТЕЛЬСТВАМИ.
    # Раньше сортировка «охват/рубль» систематически поднимала наверх тех, о ком мы знаем МЕНЬШЕ
    # всего: неизмеренный охват оценивается оптимистично → фантомный CPV 0.04 ₽ бьёт измеренный 5.42 ₽.
    # Правило (не коэффициент): измеренный охват ранжируется выше оценочного; на оценочных авторов
    # уходит только тест-бюджет — остальное после подтверждения статистики автором.
    cands.sort(key=lambda x: (0 if x["evidence"] == "факт" else 1, -(x["reach"] / x["cost"])))
    picked, spent, per_plat = [], 0, {}
    cap = max(1, brief.get("max_bloggers", 12))
    plat_cap = brief.get("platform_cap", 8)
    test_cap = budget * brief.get("test_share", 0.35)  # потолок расходов на неподтверждённые данные
    est_spent = 0
    for c in cands:
        if len(picked) >= cap or spent + c["cost"] > budget:
            continue
        if per_plat.get(c["platform"], 0) >= plat_cap:
            continue
        if c["evidence"] == "оценка":
            if est_spent + c["cost"] > test_cap:
                continue
            est_spent += c["cost"]
        picked.append(c); spent += c["cost"]; per_plat[c["platform"]] = per_plat.get(c["platform"], 0) + 1
    # FORECAST
    reach_sum = sum(p["reach"] for p in picked)
    blended_cpv = round(spent / reach_sum, 2) if reach_sum else None
    action_est = round(reach_sum * CR.get(goal, 0.003)) if goal != "awareness" else None
    cost_per_action = round(spent / action_est) if action_est else None
    return {
        "brief": brief,
        "picks": picked,
        "media_plan": {"budget": budget, "spent": spent, "count": len(picked),
                       "by_platform": per_plat, "budget_left": budget - spent,
                       "measured_spend": spent - est_spent, "estimated_spend": est_spent,
                       "measured_reach": sum(p["reach"] for p in picked if p["evidence"] == "факт"),
                       "estimated_reach": sum(p["reach"] for p in picked if p["evidence"] == "оценка")},
        "forecast": {"reach": reach_sum, "blended_cpv": blended_cpv,
                     "goal": goal, "action_est": action_est, "cost_per_action": cost_per_action,
                     "note": "action_est по допущению CR (не факт) — уточнить пикселем/промокодом"},
        "data_gaps": ["гео аудитории по городам (медиакит)", "тематика/категория", "прошлые интеграции"],
        "rejected": rejected,
    }


def render(r):
    b = r["brief"]; mp = r["media_plan"]; f = r["forecast"]
    print(f"\n=== КАМПАНИЯ под бриф ===")
    print(f"Бюджет {b['budget']:,} ₽ · цель {b['goal']} · гео {b.get('geo_cities')} · площадки {b.get('platforms')}".replace(",", " "))
    print(f"\nПодобрано {mp['count']} блогеров, потрачено {mp['spent']:,} ₽ (остаток {mp['budget_left']:,} ₽), сплит {mp['by_platform']}".replace(",", " "))
    print(f"Прогноз: охват ~{f['reach']:,} · blended CPV {f['blended_cpv']} ₽".replace(",", " ")
          + (f" · ~{f['action_est']:,} {b['goal']} @ {f['cost_per_action']} ₽".replace(",", " ") if f['action_est'] else ""))
    print("  (прогноз действий — по допущению конверсии, помечено; охват TikTok — оценка, лента за логином)")
    print("\nСостав (fit = соответствие ЭТОМУ брифу, не общий Score):")
    for i, p in enumerate(r["picks"], 1):
        print(f"  {i:2}. {p['name']:22} {p['platform']:8} fit {p['fit']:3} · охват ~{p['reach']:>8,} ({p['reach_src']}) · CPV {p['cpv']:>5} · {p['cost']:>7,} ₽".replace(",", " "))
    print(f"\nНужно дозапросить (данных нет — НЕ выдумано): {', '.join(r['data_gaps'])}")
    print(f"Отсеяно: " + "; ".join(f"{n} ({why})" for n, why in r["rejected"][:8]) + (" …" if len(r["rejected"]) > 8 else ""))


if __name__ == "__main__":
    pool = json.load(open(sys.argv[1], encoding="utf-8"))["bloggers"]
    brief = {
        "budget": int(sys.argv[2]) if len(sys.argv) > 2 else 500000,
        "goal": sys.argv[3] if len(sys.argv) > 3 else "installs",
        "geo_cities": ["Спб", "Мск", "Казань"],
        "platforms": ["TikTok", "Telegram", "YouTube"],
        "target_cpv": 1.5,
        "max_bloggers": int(sys.argv[4]) if len(sys.argv) > 4 else 12,
    }
    render(recommend(pool, brief))
