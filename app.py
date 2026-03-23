import feedparser
import datetime
import os
import requests
from bs4 import BeautifulSoup

# ======================
# M&A確定キーワード
# ======================

ma_keywords = [
"買収","企業買収","会社買収",
"子会社化","完全子会社化",
"株式取得","持分取得",
"事業譲渡","会社分割",
"吸収合併","新設合併",
"事業承継",
"資本提携","業務提携",
"グループ入り","傘下入り"
]

# ======================
# NGワード（ノイズ除去）
# ======================

ng_keywords = [
"採用","募集","イベント","セミナー",
"インタビュー","お知らせ","キャンペーン"
]

feeds = [
"https://news.google.com/rss/search?q=企業買収&hl=ja&gl=JP&ceid=JP:ja",
"https://news.google.com/rss/search?q=事業譲渡&hl=ja&gl=JP&ceid=JP:ja",
"https://prtimes.jp/topics/keywords/M%26A/rss"
]

articles = []
seen = set()

# ======================
# 要約生成
# ======================

def make_summary(text):
    return text[:80] + "..."

# ======================
# RSS取得
# ======================

for url in feeds:

    feed = feedparser.parse(url)

    for entry in feed.entries[:10]:

        title = entry.title
        link = entry.link
        summary = entry.summary if "summary" in entry else ""

        text = title + summary

        # M&A判定
text = (entry.title + entry.summary).lower()

if not any(k.lower() in text for k in ma_keywords):
    continue

        # ノイズ除去
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
# 企業サイトスクレイピング
# ======================

company_sites = [
"https://www.fc.alsok.co.jp/news/",
"https://www.nihon-ma.co.jp/news/"
]

for site in company_sites:

    try:
        html = requests.get(site, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a"):

            title = a.get_text(strip=True)
            href = a.get("href")

            if not title or not href:
                continue

            if not any(k in title for k in ma_keywords):
                continue

            if href.startswith("/"):
                href = site.rstrip("/") + href

            if title not in seen:
                seen.add(title)

                articles.append({
                    "title": title,
                    "link": href,
                    "summary": "企業公式リリース"
                })

    except:
        pass

# ======================
# 記事生成
# ======================

today = datetime.date.today()

content = f"""---
title: "今日のM&Aニュース {today}"
date: {today}
summary: "本日のM&Aニュースまとめ"
---

## 今日のM&Aニュース

"""

for a in articles[:50]:
    content += f"- [{a['title']}]({a['link']})\n  - {a['summary']}\n\n"

os.makedirs("_posts", exist_ok=True)

filename = f"_posts/{today}-ma-news.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)
