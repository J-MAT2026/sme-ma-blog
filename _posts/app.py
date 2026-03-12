import datetime
import os

today = datetime.date.today()

content = f"""
---
title: "今日のM&Aニュース {today}"
date: {today}
---

本日のM&Aニュースまとめです。

・中小企業M&A  
・事業承継  
・買収ニュース

自動生成記事です。
"""

os.makedirs("out", exist_ok=True)

filename = f"out/{today}-daily-ma.md"

with open(filename,"w") as f:
    f.write(content)
