#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Graph — «бриллиант» платформы. Не таблицы, а СВЯЗИ: бренд ↔ блогер ↔ тематика ↔
площадка ↔ промокод ↔ (в будущем) результат кампании. Ценность не в цифрах, а в рёбрах графа.

Сейчас засеивается из Marketing Intelligence (реально извлечённые бренды/промокоды/тематики) + плана.
Когда пойдут кампании — Learning Engine добавит рёбра (blogger)-[РЕЗУЛЬТАТ CPA/ROMI]->(brand).

Usage: python3 knowledge_graph.py   → строит webui/graph.json + демо-запросы
"""
from __future__ import annotations
import json, re, os
WEB = os.environ.get("CREATOR_WEBUI_DIR", "webui")  # папка с data.json и graph.json
D=json.load(open(f"{WEB}/data.json",encoding="utf-8"))
nodes={}; edges=[]
def node(nid,typ,label=None):
    nodes.setdefault(nid,{"id":nid,"type":typ,"label":label or nid})
    return nid
def edge(a,b,rel,meta=None): edges.append({"from":a,"to":b,"rel":rel,**({"meta":meta} if meta else {})})

PROMO=re.compile(r"\b[A-ZА-Я]{3,}\d{1,3}\b")
def clean_brand(s): return re.sub(r"\s*\(.*?\)\s*"," ",s).strip()

for b in D["bloggers"]:
    if not b.get("score"): continue
    bl=node("blogger:"+b["name"], "blogger", b["name"])
    node("platform:"+b["platform"],"platform",b["platform"]); edge(bl,"platform:"+b["platform"],"НА")
    mi=b.get("mi")
    if not mi: continue
    for br in mi.get("competitors",[]):
        cb=clean_brand(br)
        node("brand:"+cb,"brand",cb); edge(bl,"brand:"+cb,"РЕКЛАМИРОВАЛ",{"raw":br})
    for t in mi.get("topics",[]):
        node("topic:"+t["name"][:40],"topic",t["name"]); edge(bl,"topic:"+t["name"][:40],"ТЕМА",{"share":t["share_pct"]})
    note=mi.get("integration_quality",{}).get("note","")+" "+mi.get("ad_load",{}).get("frequency_note","")
    for code in set(PROMO.findall(note)):
        node("promo:"+code,"promo",code); edge(bl,"promo:"+code,"ПРОМОКОД")
    node("safety:"+mi["brand_safety"]["overall"],"safety",mi["brand_safety"]["overall"]); edge(bl,"safety:"+mi["brand_safety"]["overall"],"BRAND_SAFETY")

G={"nodes":list(nodes.values()),"edges":edges}
json.dump(G, open(f"{WEB}/graph.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- запросы к графу ----
def out(bl,rel): return [nodes[e["to"]]["label"] for e in edges if e["from"]==bl and e["rel"]==rel]
def inn(nid,rel): return [nodes[e["from"]]["label"] for e in edges if e["to"]==nid and e["rel"]==rel]

print(f"Граф: {len(nodes)} узлов, {len(edges)} рёбер")
print(" по типам:", {t:sum(1 for n in nodes.values() if n['type']==t) for t in set(n['type'] for n in nodes.values())})
print("\n— Демо-запросы —")
print("Бренды demo_creator:", out("blogger:demo_creator","РЕКЛАМИРОВАЛ"))
print("Промокоды demo_creator:", out("blogger:demo_creator","ПРОМОКОД"))
wb=[n for n in nodes if "brand:Wildberries" in n]
if wb: print("Кто рекламировал Wildberries:", inn(wb[0],"РЕКЛАМИРОВАЛ"))
print("Бренды Евгений Воронин:", out("blogger:Евгений Воронин","РЕКЛАМИРОВАЛ")[:4])
# mermaid субграф demo_creator
sub=[e for e in edges if e["from"]=="blogger:demo_creator"][:8]
print("\nmermaid (demo_creator):")
print("graph LR")
for e in sub: print(f'  demo_creator -->|{e["rel"]}| {nodes[e["to"]]["label"][:22]}')
print(f"\nsaved {WEB}/graph.json")
