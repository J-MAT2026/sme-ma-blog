import datetime
import os
import feedparser

today = datetime.date.today()

feed = feedparser.parse("https://prtimes.jp/topics/keywords/M%26A/rss")

articles = []

for entry in feed.entries[:5]:
    articles.append(f"- [{entry.title}]({entry.link})")

article_text = "\n".join(articles)

content = f"""
---
title: "今日のM&Aニュース {today}"
date: {today}
---

## 今日のM&Aニュース

{article_text}

"""

os.makedirs("out", exist_ok=True)

filename = f"out/{today}-ma-news.md"

with open(filename,"w") as f:
    f.write(content)
