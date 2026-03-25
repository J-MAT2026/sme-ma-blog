import feedparser
import datetime
import os
import re
import requests
from bs4 import BeautifulSoup

# ======================
# キーワード
# ======================
ma_keywords = [
    "買収", "子会社化", "株式取得", "事業譲渡", "合併",
    "資本提携", "出資", "M&A", "TOB", "MBO", "株式交換",
    "第三者割当", "公開買付", "経営統合", "持分取得",
    "完全子会社", "グループ入り", "傘下", "吸収合併",
]

# TDnet特有のM&Aタイトルパターン（これにマッチすれば確実にM&A）
ma_strong_patterns = [
    "公開買付", "TOB", "MBO", "株式交換", "吸収合併",
    "株式移転", "会社分割", "事業譲渡", "経営統合",
    "完全子会社化", "子会社化に関する", "株式取得に関する",
    "資本業務提携", "資本提携に関する",
]

ng_keywords = [
    # 採用・広報系
    "採用", "募集", "イベント", "セミナー", "転職", "インターン",
    "プレスリリース配信", "サービス開始", "リリース開始", "新サービス",
    "アップデート", "キャンペーン", "新機能", "リニューアル",
    # TDnetノイズ（M&Aと無関係な適時開示）
    "四半期報告", "有価証券報告", "内部統制報告", "確認書",
    "株主総会", "招集通知", "定時株主", "臨時株主",
    "配当予想", "配当金", "記念配当",
    "業績予想の修正", "業績修正", "業績予想修正",
    "自己株式の取得", "自己株式取得状況", "自己株式消却",
    "決算短信", "決算説明",
    "代表取締役", "役員人事", "人事異動",
]

# ソース別にフィードを定義（優先度順）
feeds_tdnet = [
    "https://webapi.yanoshin.jp/webapi/tdnet/list/recent.rss",
]
feeds_prtimes = [
    "https://prtimes.jp/index.rdf",
]
feeds_google = [
    "https://news.google.com/rss/search?q=M%26A+買収+子会社化&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=TOB+公開買付+経営統合&hl=ja&gl=JP&ceid=JP:ja",
]
feeds = feeds_tdnet + feeds_prtimes + feeds_google

articles = []
seen = set()

# ======================
# 要約
# ======================
def make_summary(text):
    if not text:
        return ""
    try:
        soup = BeautifulSoup(text, "html.parser")
        clean = soup.get_text()
    except Exception:
        clean = text
    clean = clean.replace("\n", " ").strip()
    if len(clean) > 150:
        return clean[:150] + "..."
    return clean

# ======================
# 業種カテゴリ判定
# ======================
def detect_category(text):
    categories = {
        "IT・テクノロジー": ["IT", "テック", "DX", "AI", "ソフトウェア", "SaaS", "クラウド", "システム", "デジタル", "アプリ", "ネット"],
        "金融・保険": ["銀行", "保険", "証券", "金融", "ファンド", "投資", "リース", "信託", "再保険"],
        "医療・ヘルスケア": ["医療", "製薬", "病院", "ヘルスケア", "バイオ", "医薬", "クリニック"],
        "製造・素材": ["製造", "メーカー", "素材", "化学", "鉄鋼", "部品", "工場"],
        "不動産・建設": ["不動産", "建設", "住宅", "マンション", "ゼネコン", "土地"],
        "食品・飲食": ["食品", "飲食", "レストラン", "カフェ", "食料", "外食", "農業", "牛角", "大戸屋"],
        "小売・流通": ["小売", "流通", "EC", "物流", "商社", "卸売", "スーパー"],
        "エネルギー": ["エネルギー", "電力", "ガス", "再生可能", "太陽光", "石油"],
        "メディア・エンタメ": ["メディア", "エンタメ", "出版", "放送", "ゲーム", "映画", "音楽"],
    }
    for category, keywords in categories.items():
        if any(k in text for k in keywords):
            return category
    return "M&A総合"

# ======================
# 専門家風タイトル生成
# ======================
def make_professional_title(article, rank):
    title = article["title"]
    category = article["category"]

    amount_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?(?:億|兆|万)?円)', title)
    amount = amount_match.group(1) if amount_match else ""

    if "TOB" in title:
        action = "TOBによる完全子会社化"
    elif "MBO" in title:
        action = "経営陣によるMBO"
    elif "合併" in title:
        action = "合併統合"
    elif "資本提携" in title:
        action = "戦略的資本提携"
    elif "子会社化" in title or "完全子会社" in title:
        action = "完全子会社化"
    elif "出資" in title:
        action = "資本参加・出資"
    else:
        action = "M&A"

    prefixes = [
        f"【独自分析】{category}セクターの再編加速：",
        f"【注目案件】{action}が示す業界構造変化：",
        f"【市場動向】{category}におけるM&A戦略の深層：",
        f"【詳報】{action}の背景と今後の展望：",
        f"【速報】{category}の大型{action}：",
    ]

    prefix = prefixes[(rank - 1) % len(prefixes)]
    short = title.split("　")[0].split(" ")[0][:25]
    if amount:
        return f"{prefix}{short}（{amount}規模）"
    return f"{prefix}{short}"

# ======================
# 画像URL（Pexels API）
# ======================
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

def fetch_pexels_image(category, seed):
    """Pexels APIからカテゴリ別画像URLを取得"""
    query_map = {
        "IT・テクノロジー":   "technology office business",
        "金融・保険":        "finance business meeting",
        "医療・ヘルスケア":   "healthcare medical",
        "製造・素材":        "manufacturing factory industry",
        "不動産・建設":      "real estate building architecture",
        "食品・飲食":        "food restaurant business",
        "小売・流通":        "retail logistics warehouse",
        "エネルギー":        "energy industry power",
        "メディア・エンタメ": "media technology office",
        "M&A総合":          "business meeting handshake",
    }
    query = query_map.get(category, "business meeting")

    if not PEXELS_API_KEY:
        print("  ⚠️ PEXELS_API_KEY が未設定。フォールバック画像を使用")
        return f"https://picsum.photos/seed/{seed * 13}/800/450"

    try:
        page = (seed % 3) + 1
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=5&page={page}&orientation=landscape"
        resp = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, timeout=10)
        data = resp.json()
        photos = data.get("photos", [])
        if photos:
            idx = seed % len(photos)
            return photos[idx]["src"]["large"]
    except Exception as e:
        print(f"  Pexels取得エラー: {e}")

    # フォールバック
    return f"https://picsum.photos/seed/{seed * 13}/800/450"

def make_image_url(category, seed):
    return fetch_pexels_image(category, seed)

# ======================
# RSS取得
# ======================
print("RSSフィードを取得中...")

def is_ma_article(title, summary):
    """M&A記事かどうかを判定する（強化版）"""
    text = title + " " + summary

    # NGキーワードがあれば即除外
    if any(k in text for k in ng_keywords):
        return False

    # 強パターンにマッチすれば即採用（TDnet向け）
    if any(p in title for p in ma_strong_patterns):
        return True

    # 通常キーワードは2つ以上マッチで採用（ノイズ低減）
    matched = sum(1 for k in ma_keywords if k in text)
    if matched >= 2:
        return True

    # タイトルだけで1つマッチ＋summaryでも1つマッチ
    title_match = any(k in title for k in ma_keywords)
    summary_match = any(k in summary for k in ma_keywords)
    if title_match and summary_match:
        return True

    return False

for url in feeds:
    try:
        print(f"  取得: {url}")
        feed = feedparser.parse(url)
        print(f"  → {len(feed.entries)} 件取得")
        for entry in feed.entries[:50]:
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "")

            if not title:
                continue
            if not is_ma_article(title, summary):
                continue
            if title not in seen:
                seen.add(title)
                category = detect_category(title + " " + summary)
                articles.append({
                    "title": title,
                    "link": link,
                    "summary": make_summary(summary),
                    "category": category,
                })
    except Exception as e:
        print(f"  エラー: {e}")

print(f"フィルタ後: {len(articles)} 件")

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
                    category = detect_category(title + " " + summary)
                    articles.append({
                        "title": title,
                        "link": link,
                        "summary": make_summary(summary),
                        "category": category,
                    })
        except Exception as e:
            print(f"  フォールバックエラー: {e}")

# ======================
# 日付生成
# ======================
now = datetime.datetime.now()
date_str = now.strftime("%Y-%m-%d %H:%M:%S +0900")
today_str = now.strftime("%Y-%m-%d")
today_jp = now.strftime("%Y年%m月%d日")

# ======================
# ピックアップ5件
# ======================
featured = articles[:5]
all_headlines = articles

featured_data = []
for i, a in enumerate(featured, 1):
    pro_title = make_professional_title(a, i)
    img_url = make_image_url(a["category"], i * 13 + abs(hash(a["title"])) % 99)
    featured_data.append({
        "rank": i,
        "pro_title": pro_title,
        "link": a["link"],
        "summary": a["summary"],
        "category": a["category"],
        "image": img_url,
    })

# ======================
# メインタイトル
# ======================
if featured_data:
    cats = list(dict.fromkeys([f["category"] for f in featured_data]))[:2]
    cat_str = "・".join(cats)
    main_title = f"{today_jp}のM&A動向：{cat_str}を中心に主要{min(len(articles), 10)}件を解説"
else:
    main_title = f"{today_jp}のM&Aニュース｜主要案件と市場動向"

page_summary = f"本日（{today_jp}）のM&Aニュースを厳選。注目5案件の分析と、全{len(all_headlines)}件のヘッドラインをお届けします。"

# ======================
# 本文生成
# ======================
body = "## 本日の注目5案件\n\n"
for f in featured_data:
    body += f"### {f['rank']}. {f['pro_title']}\n\n"
    body += f"**カテゴリ：** {f['category']}\n\n"
    if f['summary']:
        body += f"{f['summary']}\n\n"
    body += f"[元記事を読む]({f['link']})\n\n---\n\n"

body += "## 本日の全M&Aヘッドライン\n\n"
for i, a in enumerate(all_headlines, 1):
    body += f"{i}. [{a['title']}]({a['link']})\n"

# ======================
# featured YAMLブロック
# ======================
featured_yaml = ""
for f in featured_data:
    safe_title = f['pro_title'].replace('"', "'")
    safe_summary = f['summary'].replace('"', "'")[:100]
    featured_yaml += f'  - rank: {f["rank"]}\n'
    featured_yaml += f'    title: "{safe_title}"\n'
    featured_yaml += f'    link: "{f["link"]}"\n'
    featured_yaml += f'    summary: "{safe_summary}"\n'
    featured_yaml += f'    category: "{f["category"]}"\n'
    featured_yaml += f'    image: "{f["image"]}"\n'

# ======================
# headlines YAMLブロック
# ======================
headlines_yaml = ""
for a in all_headlines[:30]:
    safe_title = a["title"].replace('"', "'")
    safe_link = a["link"]
    safe_cat = a["category"]
    headlines_yaml += "  - title: \"" + safe_title + "\"\n"
    headlines_yaml += "    link: \"" + safe_link + "\"\n"
    headlines_yaml += "    category: \"" + safe_cat + "\"\n"

# ======================
# ファイル出力
# ======================
content = f"""---
title: "{main_title}"
date: {date_str}
summary: "{page_summary}"
featured:
{featured_yaml}headlines:
{headlines_yaml}---

{body}
"""

os.makedirs("_posts", exist_ok=True)
filename = f"_posts/{today_str}-ma-news.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 出力完了: {filename}（ピックアップ{len(featured_data)}件 / 全{len(all_headlines)}件）")
