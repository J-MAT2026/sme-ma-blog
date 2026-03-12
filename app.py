import datetime
import os
import feedparser

today = datetime.date.today()

feed = feedparser.parse("https://prtimes.jp/topics/keywords/M%26A/rss")

articles = []

for entry in feed.entries[:5]:
    articles.append(f"- [{entry.title}]({entry.link})")

article_text = "\n".join(articles)

content = f"""---
title: "今日のM&Aニュース {today}"
date: {today}
---

{article_text}
"""

filename = f"_posts/{today}-ma-news.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)
