#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation Engine — «что будет, если…» ДО запуска. Не прогноз («12 000 переходов»), а ДЕЛЬТЫ:
убрать/заменить блогера, долить бюджет → как меняются охват, CPM, стоимость и вероятность KPI.
Это уже не подбор, а оптимизация медиаплана.

Модель вероятности KPI — прозрачная эвристика (помечена): чем хуже стоимость контакта, тем ниже
шансы уложиться в KPI → Δprob ≈ −0.65 × ΔCPM%. Когда Learning Engine накопит реальные CPA/ROMI,
эвристика заменяется моделью на своих данных.

Usage: python3 simulation.py
"""
from __future__ import annotations
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import recommend
WEB = os.environ.get("CREATOR_WEBUI_DIR", "webui")  # папка с data.json и graph.json

def metrics(picks):
    cost=sum(p["cost"] for p in picks); reach=sum(p["reach"] for p in picks)
    cpm=round(cost/reach*1000,1) if reach else None
    cpv=round(cost/reach,3) if reach else None
    return {"n":len(picks),"cost":cost,"reach":reach,"cpm":cpm,"cpv":cpv}

def prob_delta(base_cpm, new_cpm):
    """ЭВРИСТИКА (не факт): хуже CPM → ниже шанс KPI. Ограничена ±100%: вероятность
    не может измениться сильнее, чем на всю себя (баг: раньше выдавала −138%)."""
    if not base_cpm or not new_cpm: return None
    d=(new_cpm-base_cpm)/base_cpm*100
    return max(-100.0, min(100.0, round(-0.65*d,1)))

def fmt(m): return f"{m['n']} авт. · охват {m['reach']:,} · CPM {m['cpm']} ₽ · бюджет {m['cost']:,} ₽".replace(",", " ")
def delta(a,b,unit="",pct=True):
    d=b-a; s=f"{'+' if d>=0 else ''}{d:,.0f}{unit}".replace(",", " ")
    if pct and a: s+=f" ({'+' if d>=0 else ''}{d/a*100:.0f}%)"
    return s

def scenario_remove(picks, name):
    new=[p for p in picks if p["name"]!=name]
    return new, [p for p in picks if p["name"]==name][0]

def scenario_replace(picks, name, cand):
    new=[p for p in picks if p["name"]!=name]
    new.append({"name":cand["name"],"platform":cand["platform"],"cost":cand["plan"]["cost"],
                "reach":recommend.expected_reach(cand)[0],"cpv":None})
    return new

def best_additions(pool, picks, budget_extra):
    taken={p["name"] for p in picks}
    cands=[]
    for c in pool:
        if c["name"] in taken or not c.get("score") or c["plan"].get("rkn") is False: continue
        r,_=recommend.expected_reach(c); cost=c["plan"]["cost"]
        if not r or not cost or cost>budget_extra: continue
        cands.append({"name":c["name"],"platform":c["platform"],"cost":cost,"reach":r,"eff":r/cost})
    cands.sort(key=lambda x:-x["eff"])
    out,spent=[],0
    for c in cands:
        if spent+c["cost"]<=budget_extra: out.append(c); spent+=c["cost"]
    return out,spent

if __name__=="__main__":
    pool=json.load(open(f"{WEB}/data.json",encoding="utf-8"))["bloggers"]
    brief={"budget":500000,"goal":"installs","geo_cities":["Спб","Мск","Казань"],
           "platforms":["TikTok","Telegram","YouTube"],"target_cpv":1.5,"max_bloggers":10}
    rec=recommend.recommend(pool,brief); picks=rec["picks"]
    base=metrics(picks)
    print("=== БАЗОВЫЙ МЕДИАПЛАН ===")
    print(" ", fmt(base))
    print("  (охват TikTok — оценка, лента за логином; вероятность KPI — эвристика, не факт)\n")

    # 1) убрать
    victim=max(picks,key=lambda p:p["cost"])["name"]
    new,removed=scenario_remove(picks,victim); m=metrics(new)
    print(f"=== ЕСЛИ УБРАТЬ «{victim}» ===")
    print(f"  Охват    {delta(base['reach'],m['reach'])}")
    print(f"  CPM      {base['cpm']} → {m['cpm']} ₽ ({delta(base['cpm'],m['cpm'],pct=True).split('(')[-1][:-1]})")
    print(f"  Бюджет   {delta(base['cost'],m['cost'],' ₽')}")
    pd=prob_delta(base['cpm'],m['cpm']); print(f"  Вероятность KPI  {'+' if pd and pd>=0 else ''}{pd}%  [эвристика]\n")

    # 2) заменить
    cand=next((c for c in pool if c.get("score") and c["name"] not in {p['name'] for p in picks}
               and c["platform"]=="TikTok" and c["plan"].get("rkn") is not False), None)
    if cand:
        new=scenario_replace(picks,victim,cand); m=metrics(new)
        print(f"=== ЕСЛИ ЗАМЕНИТЬ «{victim}» → «{cand['name']}» ===")
        print(f"  Охват    {delta(base['reach'],m['reach'])}")
        print(f"  CPM      {base['cpm']} → {m['cpm']} ₽")
        print(f"  Экономия {delta(base['cost'],m['cost'],' ₽')}")
        pd=prob_delta(base['cpm'],m['cpm']); print(f"  Вероятность KPI  {'+' if pd and pd>=0 else ''}{pd}%  [эвристика]\n")

    # 3) долить бюджет
    extra=80000
    add,spent=best_additions(pool,picks,extra)
    if add:
        new=picks+[{"name":a["name"],"platform":a["platform"],"cost":a["cost"],"reach":a["reach"],"cpv":None} for a in add]
        m=metrics(new)
        print(f"=== ЕСЛИ ДОЛИТЬ +{extra:,} ₽ ===".replace(",", " "))
        print(f"  Лучшее применение: добавить {len(add)} авт. ({', '.join(a['name'] for a in add)}) за {spent:,} ₽".replace(",", " "))
        print(f"  Охват    {delta(base['reach'],m['reach'])}")
        print(f"  CPM      {base['cpm']} → {m['cpm']} ₽")
        pd=prob_delta(base['cpm'],m['cpm']); print(f"  Вероятность KPI  {'+' if pd and pd>=0 else ''}{pd}%  [эвристика]")
        print("  Альтернатива «поднять частоту у лучших» требует данных Learning Engine (пока нет реальных CPA) → честно не считаем.")
