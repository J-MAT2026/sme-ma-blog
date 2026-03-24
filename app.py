import feedparser
import datetime
import os
import requests
from bs4 import BeautifulSoup

# ======================
# キーワード
# ======================
ma_keywords = [
    "買収", "企業買収", "子会社化", "株式取得",
    "事業譲渡", "合併", "資本提携", "出資", "M&A", "TOB", "MBO"
]
ng_keywords = [
    "採用", "募集", "イベント", "セミナー", "転職"
]

feeds = [
    "https://news.google.com/rss/search?q=M%26A+買収&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=企業買収+合併&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=資本提携+出資&hl=ja&gl=JP&ceid=JP:ja",
    "https://prtimes.jp/topics/keywords/M%26A/rss",
    "https://prtimes.jp/topics/keywords/%E8%B2%B7%E5%8F%8E/rss",
]

articles = []
seen = set()

# ======================
# 要約
# ======================
def make_summary(text):
    if not text:
        return ""
    # HTMLタグを除去
    try:
        soup = BeautifulSoup(text, "html.parser")
        clean = soup.get_text()
    except Exception:
        clean = text
    clean = clean.replace("\n", " ").strip()
    if len(clean) > 120:
        return clean[:120] + "..."
    return clean

# ======================
# RSS取得
# ======================
print("RSSフィードを取得中...")

for url in feeds:
    try:
        print(f"  取得: {url}")
        feed = feedparser.parse(url)
        print(f"  → {len(feed.entries)} 件取得")
        for entry in feed.entries[:30]:
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "")
            text = title + " " + summary

            if not any(k in text for k in ma_keywords):
                continue
            if any(k in text for k in ng_keywords):
                continue
            if title and title not in seen:
                seen.add(title)
                articles.append({
                    "title": title,
                    "link": link,
                    "summary": make_summary(summary)
                })
    except Exception as e:
        print(f"  エラー: {e}")

print(f"フィルタ後: {len(articles)} 件")

# ======================
# 記事少ない対策
# ======================
if len(articles) < 5:
    print("記事が少ないためフォールバック取得中...")
    for url in feeds[:2]:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = getattr(entry, "title", "")
                link = getattr(entry, "link", "")
                summary = getattr(entry, "summary", "")
                if title and title not in seen:
                    seen.add(title)
                    articles.append({
                        "title": title,
                        "link": link,
                        "summary": make_summary(summary)
                    })
        except Exception as e:
            print(f"  フォールバックエラー: {e}")

# ======================
# タイトル・日付生成
# ======================
now = datetime.datetime.now()
date_str = now.strftime("%Y-%m-%d %H:%M:%S +0900")
today_str = now.strftime("%Y-%m-%d")  # ← バグ修正: today → today_str

main_title = f"M&Aニュースまとめ（{today_str}）主要案件を解説"
page_summary = "本日のM&Aニュースを厳選してまとめ。買収・資本提携など重要トピックを短時間で把握できます。"

# ======================
# 本文生成
# ======================
body = "## 今日の注目M&Aニュース\n\n"

if not articles:
    body += "本日は該当するM&Aニュースが見つかりませんでした。\n"
else:
    for a in articles[:10]:
        body += f"### {a['title']}\n\n"
        if a['summary']:
            body += f"{a['summary']}\n\n"
        body += f"[記事を読む]({a['link']})\n\n---\n\n"

# ======================
# ファイル出力
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

print(f"✅ 出力完了: {filename}（記事数: {len(articles[:10])}件）")
