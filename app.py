import feedparser
import datetime
import os
import re
import json
import requests
from bs4 import BeautifulSoup

# ======================
# APIキー
# ======================
PEXELS_API_KEY     = os.environ.get("PEXELS_API_KEY", "")
EDINETDB_API_KEY   = os.environ.get("EDINETDB_API_KEY", "")
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")

EDINETDB_BASE = "https://edinetdb.jp/v1"
EDINETDB_HEADERS = {
    "Authorization": f"Bearer {EDINETDB_API_KEY}",
    "X-API-Key": EDINETDB_API_KEY,
    "Content-Type": "application/json",
}

# ======================
# キーワード
# ======================
ma_keywords = [
    "買収", "子会社化", "株式取得", "事業譲渡", "合併",
    "資本提携", "出資", "M&A", "TOB", "MBO", "株式交換",
    "第三者割当", "公開買付", "経営統合", "持分取得",
    "完全子会社", "グループ入り", "傘下", "吸収合併",
]
ma_strong_patterns = [
    "公開買付", "TOB", "MBO", "株式交換", "吸収合併",
    "株式移転", "会社分割", "事業譲渡", "経営統合",
    "完全子会社化", "子会社化に関する", "株式取得に関する",
    "資本業務提携", "資本提携に関する",
]
ng_keywords = [
    "採用", "募集", "イベント", "セミナー", "転職", "インターン",
    "プレスリリース配信", "サービス開始", "リリース開始", "新サービス",
    "アップデート", "キャンペーン", "新機能", "リニューアル",
    "四半期報告", "有価証券報告", "内部統制報告", "確認書",
    "株主総会", "招集通知", "定時株主", "臨時株主",
    "配当予想", "配当金", "記念配当",
    "業績予想の修正", "業績修正", "業績予想修正",
    "自己株式の取得", "自己株式取得状況", "自己株式消却",
    "決算短信", "決算説明",
    "代表取締役", "役員人事", "人事異動",
    # 新株予約権・自己株式系のノイズ
    "新株予約権", "ASR", "行使価額修正", "大量行使",
    "ストックオプション", "転換社債", "社債",
    # その他ノイズ
    "為替差益", "為替差損", "減損", "特別損失", "特別利益",
]

# ======================
# フィード
# ======================
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
def fetch_pexels_image(category, seed):
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
        return f"https://picsum.photos/seed/{seed * 13}/800/450"
    try:
        page = (seed % 3) + 1
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=5&page={page}&orientation=landscape"
        resp = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, timeout=10)
        data = resp.json()
        photos = data.get("photos", [])
        if photos:
            return photos[seed % len(photos)]["src"]["large"]
    except Exception as e:
        print(f"  Pexels取得エラー: {e}")
    return f"https://picsum.photos/seed/{seed * 13}/800/450"

def make_image_url(category, seed):
    return fetch_pexels_image(category, seed)

# ======================
# M&A記事フィルタ
# ======================
def is_ma_article(title, summary):
    text = title + " " + summary
    if any(k in text for k in ng_keywords):
        return False
    if any(p in title for p in ma_strong_patterns):
        return True
    matched = sum(1 for k in ma_keywords if k in text)
    if matched >= 2:
        return True
    title_match = any(k in title for k in ma_keywords)
    summary_match = any(k in summary for k in ma_keywords)
    if title_match and summary_match:
        return True
    return False

# ======================
# EDINETDB：企業名からEDINETコード取得
# ======================
def search_company_edinet(company_name):
    if not EDINETDB_API_KEY or not company_name:
        return None
    try:
        resp = requests.get(
            f"{EDINETDB_BASE}/companies/search",
            params={"q": company_name, "limit": 3},
            headers=EDINETDB_HEADERS,
            timeout=10
        )
        print(f"    EDINETDB検索 [{company_name}] status={resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            # レスポンス構造をログ出力
            print(f"    レスポンスキー: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            data = result.get("data", result.get("results", result.get("companies", [])))
            if data and len(data) > 0:
                return data[0]
        else:
            print(f"    エラーレスポンス: {resp.text[:200]}")
    except Exception as e:
        print(f"  EDINETDB検索エラー({company_name}): {e}")
    return None

# ======================
# EDINETDB：財務データ取得
# ======================
def get_financials(edinet_code):
    if not EDINETDB_API_KEY:
        return None
    try:
        resp = requests.get(
            f"{EDINETDB_BASE}/companies/{edinet_code}/financials",
            params={"years": 3},
            headers=EDINETDB_HEADERS,
            timeout=10
        )
        return resp.json().get("data", [])
    except Exception as e:
        print(f"  EDINETDB財務取得エラー: {e}")
    return None

# ======================
# EDINETDB：財務分析・AI所見取得
# ======================
def get_analysis(edinet_code):
    if not EDINETDB_API_KEY:
        return None
    try:
        resp = requests.get(
            f"{EDINETDB_BASE}/companies/{edinet_code}/analysis",
            headers=EDINETDB_HEADERS,
            timeout=10
        )
        return resp.json().get("data", {})
    except Exception as e:
        print(f"  EDINETDB分析取得エラー: {e}")
    return None

# ======================
# 記事タイトルから企業名を抽出
# ======================
def extract_company_names(title):
    """タイトルから買収側・被買収側の企業名を抽出（簡易版）"""
    companies = []
    # 「〇〇が△△を買収」「〇〇による△△の子会社化」パターン
    patterns = [
        r'([^\s、。「」【】]+(?:株式会社|ホールディングス|HD|グループ))',
        r'([^\s、。「」【】]{2,10}(?:社|Corp|Inc))',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, title)
        companies.extend(matches)
    # 重複除去・上限3社
    return list(dict.fromkeys(companies))[:3]

# ======================
# Claude APIで分析コメント生成
# ======================
def generate_analysis_comment(article, companies_data):
    if not ANTHROPIC_API_KEY:
        return ""
    if not companies_data:
        return ""

    # プロンプト構築
    company_info = ""
    for cd in companies_data:
        if not cd:
            continue
        name = cd.get("name", "")
        financials = cd.get("financials", [])
        analysis = cd.get("analysis", {})

        fin_text = ""
        for fy in financials[:2]:  # 直近2年
            rev = fy.get("revenue")
            oi = fy.get("operating_income")
            ni = fy.get("net_income")
            if rev:
                fin_text += f"FY{fy.get('fiscal_year')}: 売上{rev/1e8:.0f}億円"
                if oi:
                    fin_text += f" 営業利益{oi/1e8:.0f}億円"
                if ni:
                    fin_text += f" 純利益{ni/1e8:.0f}億円"
                fin_text += "\n"

        score = analysis.get("credit_score", "N/A") if analysis else "N/A"
        ai_view = analysis.get("ai_comment", "") if analysis else ""

        company_info += f"""
【{name}】
財務スコア: {score}/100
{fin_text}
EDINETDB AI所見: {ai_view[:200] if ai_view else "なし"}
"""

    if not company_info.strip():
        return ""

    prompt = f"""以下のM&Aニュースと当事者企業の財務データをもとに、専門家視点の分析コメントを200字程度で書いてください。
事業戦略との整合性、財務的な観点（買収余力・収益性）、今後の展望を含めてください。
箇条書きではなく、流れるような文章で記述してください。

【M&Aニュース】
{article['title']}
{article['summary']}

【当事者企業の財務情報】
{company_info}

分析コメント（200字程度）："""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        result = resp.json()
        return result["content"][0]["text"].strip()
    except Exception as e:
        print(f"  Claude API エラー: {e}")
        return ""

# ======================
# RSS取得
# ======================
print("RSSフィードを取得中...")

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

# フォールバック
if len(articles) < 5:
    print("記事が少ないためフォールバック取得中...")
    for url in feeds_google:
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
# ピックアップ5件 + EDINETDB財務分析
# ======================
featured = articles[:5]
all_headlines = articles
featured_data = []

for i, a in enumerate(featured, 1):
    pro_title = make_professional_title(a, i)
    img_url = make_image_url(a["category"], i * 13 + abs(hash(a["title"])) % 99)

    # 企業名抽出 → EDINETDB照合
    analysis_comment = ""
    if EDINETDB_API_KEY:
        company_names = extract_company_names(a["title"])
        print(f"  [{i}] 企業名抽出: {company_names}")
        companies_data = []
        for cname in company_names[:2]:  # API節約のため上位2社まで
            company = search_company_edinet(cname)
            if company:
                edinet_code = company.get("edinet_code")
                print(f"    → {cname} = {edinet_code} ({company.get('name')})")
                financials = get_financials(edinet_code)
                analysis = get_analysis(edinet_code)
                companies_data.append({
                    "name": company.get("name", cname),
                    "edinet_code": edinet_code,
                    "financials": financials or [],
                    "analysis": analysis or {},
                })

        # Claude APIで分析コメント生成
        if companies_data and ANTHROPIC_API_KEY:
            print(f"    → Claude APIで分析コメント生成中...")
            analysis_comment = generate_analysis_comment(a, companies_data)
            print(f"    → 生成完了({len(analysis_comment)}字)")

    featured_data.append({
        "rank": i,
        "pro_title": pro_title,
        "link": a["link"],
        "summary": a["summary"],
        "category": a["category"],
        "image": img_url,
        "analysis": analysis_comment,
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

page_summary = f"本日（{today_jp}）のM&Aニュースを厳選。注目5案件の財務分析付き詳報と、全{len(all_headlines)}件のヘッドラインをお届けします。"

# ======================
# 本文生成
# ======================
body = "## 本日の注目5案件\n\n"
for f in featured_data:
    body += f"### {f['rank']}. {f['pro_title']}\n\n"
    body += f"**カテゴリ：** {f['category']}\n\n"
    if f['summary']:
        body += f"{f['summary']}\n\n"
    if f['analysis']:
        body += f"**📊 財務分析・専門家コメント**\n\n{f['analysis']}\n\n"
    body += f"[元記事を読む]({f['link']})\n\n---\n\n"

body += "## 本日の全M&Aヘッドライン\n\n"
for i, a in enumerate(all_headlines, 1):
    body += f"{i}. [{a['title']}]({a['link']})\n"

# ======================
# YAML生成
# ======================
featured_yaml = ""
for f in featured_data:
    safe_title = f['pro_title'].replace('"', "'")
    safe_summary = f['summary'].replace('"', "'")[:100]
    safe_analysis = f['analysis'].replace('"', "'").replace('\n', ' ')[:200] if f['analysis'] else ""
    featured_yaml += "  - rank: " + str(f["rank"]) + "\n"
    featured_yaml += '    title: "' + safe_title + '"\n'
    featured_yaml += '    link: "' + f["link"] + '"\n'
    featured_yaml += '    summary: "' + safe_summary + '"\n'
    featured_yaml += '    category: "' + f["category"] + '"\n'
    featured_yaml += '    image: "' + f["image"] + '"\n'
    featured_yaml += '    analysis: "' + safe_analysis + '"\n'

headlines_yaml = ""
for a in all_headlines[:30]:
    safe_title = a["title"].replace('"', "'")
    headlines_yaml += "  - title: " + '"' + safe_title + '"\n'
    headlines_yaml += "    link: " + '"' + a["link"] + '"\n'
    headlines_yaml += "    category: " + '"' + a["category"] + '"\n'

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
