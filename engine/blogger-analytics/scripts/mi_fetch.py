#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marketing Intelligence — content fetcher. Достаёт ТЕКСТЫ последних постов из t.me/s/<channel>
(+ просмотры/дата), чтобы AI-слой мог оценить Brand Safety, тематики, рекламную насыщенность,
конкурентов и качество интеграций — то, чего нет у агрегаторов метрик.

Работает там, где контент доступен: Telegram (тут), YouTube (заголовки/описания через Data API),
RuTube (public JSON). На TikTok без логина ленты нет → MI недоступен (честно).

Usage: python3 mi_fetch.py <channel> [channel2 ...]  → JSON {channel, posts:[{text,views,date,is_ad_hint}]}
"""
from __future__ import annotations
import json, re, sys, os
from html import unescape
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import telegram

AD_HINTS=re.compile(r"(реклама|erid|партнёр|партнер|промокод|скидк|по промокоду|#реклама|ссылк[аи] в|"
                    r"оформить|регистрируйся|переходи|успей|акци|дарим|розыгрыш)", re.I)

def strip(html_frag):
    t=re.sub(r"<br\s*/?>","\n",html_frag)
    t=re.sub(r"<[^>]+>","",t)
    return unescape(t).strip()

def fetch_posts(slug):
    html=telegram.fetch(slug)
    if not html: return []
    # каждый пост: текстовый блок + просмотры + дата
    texts=re.findall(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.S)
    views=re.findall(r'tgme_widget_message_views">([^<]+)<', html)
    dates=re.findall(r'<time[^>]*datetime="([^"]+)"', html)
    posts=[]
    for i,tx in enumerate(texts):
        txt=strip(tx)
        if not txt: continue
        posts.append({"text":txt[:600], "views":views[i] if i<len(views) else None,
                      "date":dates[i] if i<len(dates) else None,
                      "is_ad_hint":bool(AD_HINTS.search(txt))})
    return posts

if __name__=="__main__":
    out={}
    for slug in sys.argv[1:] or ["vsezpif"]:
        p=fetch_posts(slug)
        out[slug]={"channel":slug,"n":len(p),"ad_hints":sum(1 for x in p if x["is_ad_hint"]),"posts":p}
        print(f"{slug}: {len(p)} постов, ad-hints {out[slug]['ad_hints']}", file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False))
