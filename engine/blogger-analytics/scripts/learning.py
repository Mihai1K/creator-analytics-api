#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Learning Engine — главный долгосрочный моат. Запоминает РЕЗУЛЬТАТЫ реальных кампаний и
превращает их в знание: «Самокат: 20 запусков → лучше всего TG 80–150k, женщины 25–35, лайфстайл, CPA 184 ₽».

Ключевая идея (по CTO): Knowledge Graph хранит НЕ связи, а РЕЗУЛЬТАТЫ связей —
brand → что рекламировали → оффер → CTA → формат → CPM → CPA → ROMI → повторил ли бренд.

Начинает ПУСТЫМ. Заполняется автоматически при закрытии каждой кампании (Deal Engine → record()).
Пока реальных кампаний нет — запросы честно отвечают «нет данных», а не выдумывают.

Usage:
  python3 learning.py demo     # показать механику на ПОМЕЧЕННЫХ демо-записях
  python3 learning.py query <бренд|категория>
"""
from __future__ import annotations
import json, os, statistics, sys
from datetime import datetime, timezone
WEB = os.environ.get("CREATOR_WEBUI_DIR", "webui")  # папка с data.json и graph.json
LEDGER=os.path.join(WEB,"results_ledger.jsonl")
GRAPH=os.path.join(WEB,"graph.json")
_UNSET=object()  # graph омитнут → пишем в боевой граф; graph=None → не трогаем граф (демо)

# Полный набор, который сохраняем после КАЖДОЙ сделки (список полей — по требованию CTO):
# блогер · бренд · цена · просмотры · CTR · CPC · CPA · ROMI · повторная закупка · оценка менеджера.
FIELDS=["campaign_id","blogger","platform","tier","brand","category","audience","offer","cta","format",
        "cost","reach","clicks","installs","orders","cpm","cpi","cpa","cpc","ctr","cr","romi",
        "repeat","manager_rating","demo"]

def record(r: dict, ledger: str = None, graph=_UNSET):
    """Записать РЕАЛЬНЫЙ результат кампании + добавить ребро-РЕЗУЛЬТАТ в граф.
    ledger=None → боевой леджер; своя строка пути → отдельный (демо не засоряет moat).
    graph омитнут → боевой граф; graph=None → не трогать граф."""
    ledger=ledger or LEDGER
    r.setdefault("ts", datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    if r.get("reach") and r.get("cost"): r.setdefault("cpm", round(r["cost"]/r["reach"]*1000,1))
    if r.get("installs"): r.setdefault("cpi", round(r["cost"]/r["installs"]))
    if r.get("orders"): r.setdefault("cpa", round(r["cost"]/r["orders"]))
    if r.get("clicks") and r.get("cost"): r.setdefault("cpc", round(r["cost"]/r["clicks"]))
    if r.get("clicks") and r.get("reach"):
        ctr=round(r["clicks"]/r["reach"]*100,2); r.setdefault("ctr", ctr); r.setdefault("cr", ctr)
    with open(ledger,"a",encoding="utf-8") as f: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    _graph_edge(r, GRAPH if graph is _UNSET else graph)
    return r

def _graph_edge(r, p):
    """Ребро blogger -[РЕЗУЛЬТАТ {cpa,romi,offer,cta,format}]-> brand — граф хранит РЕЗУЛЬТАТ связи."""
    if not p or not os.path.exists(p): return
    G=json.load(open(p,encoding="utf-8"))
    ids={n["id"] for n in G["nodes"]}
    for nid,typ,label in [(f"blogger:{r['blogger']}","blogger",r["blogger"]),(f"brand:{r['brand']}","brand",r["brand"])]:
        if nid not in ids: G["nodes"].append({"id":nid,"type":typ,"label":label}); ids.add(nid)
    G["edges"].append({"from":f"blogger:{r['blogger']}","to":f"brand:{r['brand']}","rel":"РЕЗУЛЬТАТ",
        "meta":{k:r.get(k) for k in ("cpa","cpi","cpc","ctr","romi","cpm","offer","cta","format","repeat","manager_rating","demo") if r.get(k) is not None}})
    json.dump(G,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=1)

def load(ledger: str = None):
    ledger=ledger or LEDGER
    if not os.path.exists(ledger): return []
    return [json.loads(l) for l in open(ledger,encoding="utf-8") if l.strip()]

def what_works(key: str, ledger: str = None):
    """Что работает для бренда/категории — по НАКОПЛЕННЫМ результатам. Пусто → так и говорим."""
    rows=[r for r in load(ledger) if key.lower() in (r.get("brand","")+" "+r.get("category","")).lower()]
    if not rows:
        return {"key":key,"n":0,"note":"нет данных — знание появится после первых закрытых кампаний"}
    def top(field):
        c={}
        for r in rows: c[r.get(field)]=c.get(r.get(field),0)+1
        return sorted([x for x in c.items() if x[0]],key=lambda x:-x[1])
    cpas=[r["cpa"] for r in rows if r.get("cpa")]; romis=[r["romi"] for r in rows if r.get("romi")]
    demo=all(r.get("demo") for r in rows)
    return {"key":key,"n":len(rows),"demo_only":demo,
            "best_platforms":top("platform")[:3],"best_tiers":top("tier")[:2],
            "best_audience":top("audience")[:2],"best_format":top("format")[:2],"best_offer":top("offer")[:2],
            "avg_cpa":round(statistics.mean(cpas)) if cpas else None,
            "median_cpa":round(statistics.median(cpas)) if cpas else None,
            "avg_romi":round(statistics.mean(romis)) if romis else None,
            "repeat_rate":round(sum(1 for r in rows if r.get("repeat"))/len(rows)*100)}

def strategy_hint(key, ledger: str = None):
    w=what_works(key, ledger)
    if not w["n"]: return f"«{key}»: {w['note']}."
    pl=", ".join(f"{p}({n})" for p,n in w["best_platforms"]); aud=w["best_audience"][0][0] if w["best_audience"] else "—"
    tag=" [ДЕМО-записи, не реальные кампании]" if w.get("demo_only") else ""
    return (f"«{key}»: {w['n']} запусков. Лучше всего {pl}, тир {w['best_tiers'][0][0] if w['best_tiers'] else '—'}, "
            f"аудитория {aud}, формат {w['best_format'][0][0] if w['best_format'] else '—'}. "
            f"Медианный CPA {w['median_cpa']} ₽, ROMI {w['avg_romi']}%, повторных размещений {w['repeat_rate']}%.{tag}")

if __name__=="__main__":
    cmd=sys.argv[1] if len(sys.argv)>1 else "demo"
    if cmd=="query":
        print(strategy_hint(" ".join(sys.argv[2:]))); sys.exit()
    print("Состояние леджера ДО:", len(load()), "записей")
    print(" запрос по пустому:", strategy_hint("Самокат"), "\n")
    # ДЕМО-записи (помечены demo=True) — показывают механику флайвила, НЕ реальные кампании
    demo=[
     {"campaign_id":"DEMO-1","blogger":"demo_creator","platform":"Telegram","tier":"микро","brand":"Самокат",
      "category":"доставка","audience":"женщины 25–35","offer":"скидка 30% на первый заказ","cta":"промокод",
      "format":"нативный пост","cost":26712,"reach":4925,"clicks":410,"installs":150,"orders":145,"romi":214,"repeat":True,"demo":True},
     {"campaign_id":"DEMO-2","blogger":"Текила Картер (TG)","platform":"Telegram","tier":"микро","brand":"Самокат",
      "category":"доставка","audience":"женщины 18–24","offer":"бесплатная доставка","cta":"ссылка",
      "format":"сторис-серия","cost":3180,"reach":3470,"clicks":95,"installs":31,"orders":22,"romi":132,"repeat":False,"demo":True},
     {"campaign_id":"DEMO-3","blogger":"Юлик","platform":"YouTube","tier":"крупный","brand":"Самокат",
      "category":"доставка","audience":"18–34 смешанная","offer":"скидка 30% на первый заказ","cta":"промокод",
      "format":"интеграция в видео","cost":207972,"reach":447500,"clicks":2100,"installs":760,"orders":410,"romi":88,"repeat":False,"demo":True},
    ]
    for d in demo: record(d)
    print("Записано ДЕМО-результатов:", len(demo), "→", LEDGER)
    print("\n=== ЧТО БАЗА ТЕПЕРЬ ЗНАЕТ ===")
    print(strategy_hint("Самокат"))
    w=what_works("Самокат")
    print(f"\n  CPA по авторам: " + ", ".join(f"{r['blogger']} {r['cpa']}₽ (ROMI {r['romi']}%)" for r in load() if r.get("cpa")))
    print("  → Граф пополнен рёбрами РЕЗУЛЬТАТ (blogger -[cpa/romi/offer/cta/format]-> brand)")
    print("\nВывод: со второй кампании «Самокат» стратегия уже не эвристика, а собственная статистика платформы.")
