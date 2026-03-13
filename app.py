import feedparser
import datetime
import os

# -------------------------
# M&A確定ワード
# -------------------------

ma_keywords = [

"買収",
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
"業務提携"

]

# -------------------------
# 除外ワード
# -------------------------

ng_words = [

"研究",
"考察",
"解説",
"入門",
"戦略",
"まとめ",
"勉強",
"ブログ",
"note",
"コラム"

]

# -------------------------
# RSS
# -------------------------

feeds = [

"https://news.google.com/rss/search?q=M%26A&hl=ja&gl=JP&ceid=JP:ja",
"https://news.google.com/rss/search?q=企業買収&hl=ja&gl=JP&ceid=JP:ja",
"https://news.google.com/rss/search?q=事業譲渡&hl=ja&gl=JP&ceid=JP:ja",

"https://prtimes.jp/topics/keywords/M%26A/rss",
"https://prtimes.jp/topics/keywords/事業承継/rss"

]

articles = []
seen = set()

for url in feeds:

    feed = feedparser.parse(url)

    for entry in feed.entries[:5]:

        title = entry.title
        link = entry.link

        # NGワード除外
        if any(w in title for w in ng_words):
            continue

        # M&Aワード必須
        if not any(k in title for k in ma_keywords):
            continue

        if title not in seen:

            seen.add(title)

            articles.append(
                f"- [{title}]({link})"
            )

today = datetime.date.today()

content = f"""---
title: "今日のM&Aニュース {today}"
date: {today}
---

## 今日のM&Aニュース

{chr(10).join(articles[:60])}
"""

os.makedirs("_posts", exist_ok=True)

filename = f"_posts/{today}-ma-news.md"

with open(filename,"w",encoding="utf-8") as f:
    f.write(content)
