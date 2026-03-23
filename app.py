import feedparser
import datetime
import os
import requests
from bs4 import BeautifulSoup

# ======================
# キーワード
# ======================

ma_keywords = [
"買収","企業買収","子会社化","株式取得",
"事業譲渡","合併","資本提携","出資"
]

ng_keywords = [
"採用","募集","イベント","セミナー"
]

feeds = [
"https://news.google.com/rss/search?q=企業買収&hl=ja&gl=JP&ceid=JP:ja",
"https://prtimes.jp/topics/keywords/M%26A/rss"
]

articles = []
seen = set()

# ======================
# 要約（改良）
# ======================

def make_summary(text):
    if not text:
        return ""
    return text.replace("\n", "")[:120] + "..."

# ======================
# RSS取得
# ======================

for url in feeds:
    feed = feedparser.parse(url)

    for entry in feed.entries[:20]:
        title = entry.title
        link = entry.link
        summary = entry.summary if hasattr(entry, "summary") else ""

        text = (title + summary)

        if not any(k in text for k in ma_keywords):
            continue

        if any(k in text for k in ng_keywords):
            continue

        if title not in seen:
            seen.add(title)

            articles.append({
                "title": title,
                "link": link,
                "summary": make_summary(summary)
            })

# ======================
# 記事少ない対策
# ======================

if len(articles) < 5:
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": ""
            })

# ======================
# タイトル生成（重要）
# ======================

now = datetime.datetime.now()
date_str = now.strftime("%Y-%m-%d %H:%M:%S +0900")
today_str = now.strftime("%Y-%m-%d")

main_title = f"M&Aニュースまとめ（{today}）主要案件を解説"

# 👉 ここが超重要
page_summary = "本日のM&Aニュースを厳選してまとめ。買収・資本提携など重要トピックを短時間で把握できます。"

# ======================
# 本文生成（メディア風）
# ======================

body = "## 今日の注目M&Aニュース\n\n"

for a in articles[:10]:
    body += f"### {a['title']}\n"
    body += f"{a['summary']}\n\n"
    body += f"[記事を読む]({a['link']})\n\n---\n\n"

# ======================
# 出力（修正版）
# ======================

content = f"""---
title: "{main_title}"
date: {date_str}
summary: "{page_summary}"
---

{body}
"""

os.makedirs("_posts", exist_ok=True)

filename = f"_posts/{today_str}-ma-news.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)
