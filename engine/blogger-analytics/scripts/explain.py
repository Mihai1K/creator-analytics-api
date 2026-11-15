#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recommendation v2 — «почему выбран» вместо «Подходит 87%».

Вместо одного процента — доказательства из накопленной базы:
  ✔ лучший CPA среди «доставка» — 184 ₽ (по нашим прошлым кампаниям)
  ✔ не рекламировал вашего конкурента (проверено 8 интеграций)
  ✔ стоимость ниже ожидаемой на 18%
  ✔ рекламная нагрузка ниже медианы базы
  ✕ рекламировал Пятёрочку — прямой конкурент
  ? гео/возраст аудитории не подтверждены — запросить медиакит

ЖЁСТКОЕ ПРАВИЛО ЧЕСТНОСТИ: пункт «✔/✕» появляется, только если под ним есть данные.
Нет данных → пункт уходит в «не проверено» (?), НИКОГДА не подменяется оценкой.

Внутри — граф связей + леджер результатов + медианы собственной базы. Наружу (пользователю)
это всё называется одним словом: AI Media Buyer.

Usage: python3 explain.py            # разбор демо-брифа + запись webui/plan.json
"""
from __future__ import annotations
import json, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import recommend, learning
WEB = os.environ.get("CREATOR_WEBUI_DIR", "webui")  # папка с data.json и graph.json

PLUS, MINUS, UNK = "+", "-", "?"


# ---------- контекст: что база вообще знает ----------
def build_ctx(pool, graph, ledger):
    cpv_by_plat = {}
    for b in pool:
        if not b.get("score"):
            continue
        r, _ = recommend.expected_reach(b); c = b["plan"].get("cost")
        if r and c:
            cpv_by_plat.setdefault(b["platform"], []).append(c / r)
    medians = {p: round(statistics.median(v), 2) for p, v in cpv_by_plat.items() if len(v) >= 3}

    lab = {n["id"]: n["label"] for n in graph["nodes"]}
    advertised, promos = {}, {}
    for e in graph["edges"]:
        if e["rel"] == "РЕКЛАМИРОВАЛ":
            advertised.setdefault(lab[e["from"]], []).append(lab[e["to"]])
        elif e["rel"] == "ПРОМОКОД":
            promos.setdefault(lab[e["from"]], []).append(lab[e["to"]])

    ad_loads = {}
    for b in pool:
        al = (b.get("mi") or {}).get("ad_load")
        if al and al.get("total_posts"):
            ad_loads[b["name"]] = round(al["ad_posts"] / al["total_posts"] * 100)
    return {"cpv_median": medians, "advertised": advertised, "promos": promos,
            "ad_loads": ad_loads, "ledger": ledger,
            "ad_load_median": round(statistics.median(ad_loads.values())) if len(ad_loads) >= 5 else None,
            "mi_n": len(ad_loads)}


def _cat_rows(ledger, category):
    return [r for r in ledger if category and category.lower() in (r.get("category", "") + " " + r.get("brand", "")).lower()]


# ---------- ядро: доказательства ----------
def why(b, brief, ctx):
    """→ [(state, text)] где state: '+' довод ЗА, '-' довод ПРОТИВ, '?' не проверено."""
    out = []
    name = b["name"]

    # 0/1. ЦЕНА — только если охват ИЗМЕРЕН. Иначе это оценка ÷ оценку = фантом, а не довод.
    reach, rsrc = recommend.expected_reach(b); cost = b["plan"].get("cost")
    med = ctx["cpv_median"].get(b["platform"])
    if reach and cost and rsrc != "median факт":
        out.append((UNK, f"охват не измерен — оценка {reach:,} по подписчикам ({rsrc}); «дешёвый» CPV {cost/reach:.2f} ₽ "
                         f"держится на этой оценке. Запросить статистику автора ДО оплаты".replace(",", " ")))
    elif reach and cost and med:
        cpv = cost / reach; d = (cpv - med) / med * 100
        if d <= -10:
            out.append((PLUS, f"стоимость контакта ниже ожидаемой на {abs(d):.0f}% — {cpv:.2f} ₽ против медианы {b['platform']} в базе {med} ₽ (охват измерен)"))
        elif d >= 10:
            out.append((MINUS, f"стоимость контакта выше медианы {b['platform']} на {d:.0f}% ({cpv:.2f} vs {med} ₽) — торговаться"))
        else:
            out.append((PLUS, f"цена в рынке: {cpv:.2f} ₽ за контакт при медиане {med} ₽ (охват измерен)"))
    if rsrc == "median факт":
        out.append((PLUS, f"охват подтверждён фактическими просмотрами ({reach:,}), а не оценкой по подписчикам".replace(",", " ")))

    # 2. РЕАЛЬНЫЕ РЕЗУЛЬТАТЫ (главный актив — накопленные кампании)
    cat = brief.get("category", "")
    mine = [r for r in ctx["ledger"] if r["blogger"] == name]
    cat_rows = _cat_rows(ctx["ledger"], cat)
    if mine:
        demo = " [демо-записи]" if all(r.get("demo") for r in mine) else ""
        cpas = [r["cpa"] for r in mine if r.get("cpa")]
        romis = [r["romi"] for r in mine if r.get("romi")]
        if cpas:
            cpa = round(statistics.median(cpas))
            peers = sorted({r["cpa"] for r in cat_rows if r.get("cpa")})
            rank = f"лучший CPA среди «{cat}»" if peers and cpa == peers[0] else f"CPA в «{cat}»"
            romi = f", ROMI {round(statistics.mean(romis))}%" if romis else ""
            out.append((PLUS if (peers and cpa <= statistics.median(peers)) else MINUS,
                        f"{rank} — {cpa} ₽{romi} по нашим прошлым кампаниям ({len(mine)} запуск.){demo}"))
        if any(r.get("repeat") for r in mine):
            out.append((PLUS, f"бренд закупал у него повторно — сильнейший сигнал качества{demo}"))
    elif cat_rows:
        med_cpa = round(statistics.median([r["cpa"] for r in cat_rows if r.get("cpa")] or [0])) or None
        out.append((UNK, f"с ним мы ещё не запускались; по категории «{cat}» база знает {len(cat_rows)} запуск."
                         + (f" (медианный CPA {med_cpa} ₽)" if med_cpa else "")))
    else:
        out.append((UNK, f"результатов по категории «{cat}» в базе пока нет — знание появится после первых кампаний"))

    # 3. КОНКУРЕНТЫ (из графа: что реально рекламировал)
    adv = ctx["advertised"].get(name, [])
    comps = brief.get("competitors") or []
    hits = [c for c in comps if any(c.lower() in a.lower() or a.lower() in c.lower() for a in adv)]
    if hits:
        out.append((MINUS, f"рекламировал вашего конкурента: {', '.join(hits)} — риск конфликта/эксклюзива"))
    elif adv:
        out.append((PLUS, f"не рекламировал ваших конкурентов (проверено {len(adv)} интеграций: {', '.join(adv[:4])}{'…' if len(adv) > 4 else ''})"))
    else:
        out.append((UNK, "прошлые интеграции не проверены — нет доступа к контенту площадки"))

    # 4. РЕКЛАМНАЯ НАГРУЗКА (усталость аудитории)
    al = ctx["ad_loads"].get(name)
    if al is not None:
        m = ctx["ad_load_median"]
        if m is None:
            out.append((PLUS if al <= 25 else MINUS,
                        f"реклама в {al}% постов" + (" — низкая нагрузка" if al <= 25 else " — аудитория перегрета")
                        + f" (разбор контента есть по {ctx['mi_n']} каналам — с рынком сравнивать рано)"))
        else:
            out.append((PLUS if al <= m else MINUS, f"рекламная нагрузка {al}% против медианы базы {m}%"))
    else:
        out.append((UNK, "рекламная нагрузка не измерена — нужен разбор последних публикаций"))

    # 5. BRAND SAFETY
    bs = (b.get("mi") or {}).get("brand_safety")
    if bs:
        out.append((PLUS if bs.get("overall") == "safe" else MINUS,
                    f"brand safety: {'чисто' if bs.get('overall') == 'safe' else bs.get('overall')} — политика {bs.get('politics_pct', 0)}%, алкоголь {bs.get('alcohol_pct', 0)}%, мат {bs.get('profanity_pct', 0)}%"))
    else:
        out.append((UNK, "brand safety не проверена — нет разбора контента"))

    # 6. АУДИТОРИЯ — в публичных данных её нет. Не выдумываем процент совпадения.
    a = b.get("actual") or {}
    if a.get("geo") or a.get("age"):
        out.append((PLUS, "аудитория подтверждена данными площадки"))
    else:
        out.append((UNK, f"гео/возраст аудитории не подтверждены — запросить медиакит (бриф: {brief.get('audience', '—')})"))

    # 7. НАДЁЖНОСТЬ ДАННЫХ
    q = (b.get("quality") or {}).get("quality")
    if q is not None:
        out.append((PLUS if q >= 70 else UNK, f"надёжность анализа {q}/100 — " +
                    ((b.get("quality") or {}).get("note") or "")))
    return out


def confidence(w):
    """Не «Подходит 87%», а честная сводка: сколько доводов подтверждено данными."""
    p = sum(1 for s, _ in w if s == PLUS); m = sum(1 for s, _ in w if s == MINUS); u = sum(1 for s, _ in w if s == UNK)
    return {"pro": p, "contra": m, "unknown": u,
            "label": f"{p} довода за · {m} против · {u} не проверено"}


# ---------- сборка плана AI Media Buyer ----------
def build_plan(brief):
    pool = json.load(open(f"{WEB}/data.json", encoding="utf-8"))["bloggers"]
    graph = json.load(open(f"{WEB}/graph.json", encoding="utf-8"))
    ledger = learning.load()
    ctx = build_ctx(pool, graph, ledger)
    rec = recommend.recommend(pool, brief)
    by_name = {b["name"]: b for b in pool}
    picks = []
    for p in rec["picks"]:
        b = by_name[p["name"]]
        w = why(b, brief, ctx)
        picks.append({**p, "why": w, "confidence": confidence(w)})
    # ЧЕСТНЫЙ ПРОГНОЗ: никогда не смешивать измеренное с оценочным в одну цифру.
    mp = rec["media_plan"]; f = dict(rec["forecast"])
    f["measured"] = {"reach": mp["measured_reach"], "spend": mp["measured_spend"],
                     "cpv": round(mp["measured_spend"] / mp["measured_reach"], 2) if mp["measured_reach"] else None}
    f["estimated"] = {"reach": mp["estimated_reach"], "spend": mp["estimated_spend"],
                      "cpv": round(mp["estimated_spend"] / mp["estimated_reach"], 2) if mp["estimated_reach"] else None,
                      "note": "сбудется, только если оценка охвата по подписчикам верна — подтвердить статистикой автора до оплаты"}
    f["blended_cpv_warning"] = "смешанный CPV не показываем: он усредняет измеренное с предположением"
    # разворот: кого НЕ взяли и почему (тоже решение)
    plan = {"brief": brief, "picks": picks, "media_plan": mp,
            "forecast": f, "rejected": rec["rejected"][:10],
            "knows": learning.strategy_hint(brief.get("category", "")),
            "base": {"cpv_median": ctx["cpv_median"], "mi_channels": ctx["mi_n"],
                     "graph_edges": len(graph["edges"]), "results": len(ledger)}}
    return plan


DEMO_BRIEF = {
    "budget": 300000, "goal": "installs", "category": "доставка", "brand": "Самокат",
    "competitors": ["Яндекс Лавка", "ВкусВилл", "Купер", "Пятёрочка", "Перекрёсток Впрок", "Ozon fresh"],
    "audience": "женщины 25–35, Мск/Спб", "geo_cities": ["Спб", "Мск", "Казань"],
    "platforms": ["TikTok", "Telegram", "YouTube"], "target_cpv": 1.5, "max_bloggers": 8,
}

if __name__ == "__main__":
    plan = build_plan(DEMO_BRIEF)
    json.dump(plan, open(f"{WEB}/plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    mp, f = plan["media_plan"], plan["forecast"]
    print(f"AI MEDIA BUYER · бриф: {DEMO_BRIEF['brand']} · {DEMO_BRIEF['category']} · {DEMO_BRIEF['budget']:,} ₽".replace(",", " "))
    print(f"База знает: {plan['knows']}")
    print(f"Собрано {mp['count']} авторов на {mp['spent']:,} ₽ (остаток {mp['budget_left']:,} ₽)".replace(",", " "))
    m, e = f["measured"], f["estimated"]
    print(f"  ИЗМЕРЕНО:  охват {m['reach']:,} за {m['spend']:,} ₽ → CPV {m['cpv']} ₽ — по этим деньгам можно считать".replace(",", " "))
    print(f"  ОЦЕНКА:    охват {e['reach']:,} за {e['spend']:,} ₽ → CPV {e['cpv']} ₽ — {e['note']}\n".replace(",", " "))
    ico = {PLUS: "✔", MINUS: "✕", UNK: "?"}
    for i, p in enumerate(plan["picks"], 1):
        print(f"{i}. {p['name']} · {p['platform']} · {p['cost']:,} ₽ — {p['confidence']['label']}".replace(",", " "))
        for s, t in p["why"]:
            print(f"     {ico[s]} {t}")
        print()
    print("→ webui/plan.json")
