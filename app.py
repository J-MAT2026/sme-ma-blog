import feedparser
import datetime
import os
import requests
from bs4 import BeautifulSoup

# ======================
# M&Aキーワード
# ======================

ma_keywords = [

"買収",
"企業買収",
"会社買収",
"子会社化",
"完全子会社化",
"株式取得",
"持分取得",
"事業譲渡",
"会社分割",
"吸収合併",
"新設合併",
"事業承継",
"資本提携",
"業務提携",
"グループ入り",
"傘下入り"

]

# ======================
# 除外サイト
# ======================

ng_sites = [

"note.com",
"linkedin.com",
"wantedly",
"qiita",
"zenn.dev",
"speakerdeck",
"medium.com"

]

# ======================
# RSSソース
# ======================

feeds = [

"https://news.google.com/rss/search?q=企業買収&hl=ja&gl=JP&ceid=JP:ja",
"https://news.google.com/rss/search?q=事業譲渡&hl=ja&gl=JP&ceid=JP:ja",
"https://news.google.com/rss/search?q=子会社化&hl=ja&gl=JP&ceid=JP:ja",
"https://news.google.com/rss/search?q=事業承継&hl=ja&gl=JP&ceid=JP:ja",

"https://prtimes.jp/topics/keywords/M%26A/rss",
"https://prtimes.jp/topics/keywords/事業承継/rss",
"https://prtimes.jp/topics/keywords/資本提携/rss"

]

articles = []
seen = set()

# ======================
# RSS取得
# ======================

for url in feeds:

    feed = feedparser.parse(url)

    for entry in feed.entries[:20]:

        title = entry.title
        link = entry.link
        summary = entry.summary if "summary" in entry else ""

        text = title + summary

        # M&Aキーワード判定
        if not any(k in text for k in ma_keywords):
            continue

        # ノイズサイト除外
        if any(site in link for site in ng_sites):
            continue

        if title not in seen:

            seen.add(title)

            articles.append(
                f"- [{title}]({link})"
            )


# ======================
# 企業NEWSスクレイピング
# ======================

company_news_sites = [

"https://www.fc.alsok.co.jp/news/",
"https://www.nihon-ma.co.jp/news/",
"https://www.strike.co.jp/news/",
"https://batonz.jp/news/"

]

for site in company_news_sites:

    try:

        html = requests.get(site,timeout=10).text
        soup = BeautifulSoup(html,"html.parser")

        links = soup.find_all("a")

        for a in links:

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

                articles.append(
                    f"- [{title}]({href})"
                )

    except:
        pass


# ======================
# 記事生成
# ======================

today = datetime.date.today()

content = f"""---
title: "今日のM&Aニュース {today}"
date: {today}
---

## 今日のM&Aニュース

{chr(10).join(articles[:100])}
"""

os.makedirs("_posts", exist_ok=True)

filename = f"_posts/{today}-ma-news.md"

with open(filename,"w",encoding="utf-8") as f:
    f.write(content)
