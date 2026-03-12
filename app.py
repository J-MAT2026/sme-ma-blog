import feedparser
import datetime
import os

keywords = [

"M&A","企業買収","企業売却","会社売却","会社買収",
"企業統合","経営統合",

"買収","買収へ","買収発表",
"子会社化","完全子会社化","子会社取得",
"株式取得","株式取得へ","持分取得","経営権取得",

"売却","事業売却","会社売却",
"持分売却","株式売却","資産売却",

"資本提携","業務提携","資本業務提携",
"戦略提携","アライアンス",

"出資","追加出資","増資","第三者割当",
"ベンチャー投資","VC投資","PEファンド",

"事業譲渡","会社分割","吸収合併","新設合併",
"統合","カーブアウト",

"事業承継","後継者問題","中小企業M&A","事業承継M&A",

"グループ入り","傘下入り","子会社に","買収合意","買収検討"

]

feeds = []

for word in keywords:
    feeds.append(
        f"https://news.google.com/rss/search?q={word}&hl=ja&gl=JP&ceid=JP:ja"
    )

feeds += [

"https://prtimes.jp/topics/keywords/M%26A/rss",
"https://prtimes.jp/topics/keywords/事業承継/rss",
"https://prtimes.jp/topics/keywords/資本提携/rss"

]

articles = []
seen = set()

for url in feeds:

    feed = feedparser.parse(url)

    for entry in feed.entries[:3]:

        title = entry.title
        link = entry.link

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

{chr(10).join(articles[:80])}
"""

os.makedirs("_posts", exist_ok=True)

filename = f"_posts/{today}-ma-news.md"

with open(filename,"w",encoding="utf-8") as f:
    f.write(content)
