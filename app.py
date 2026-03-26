#!/usr/bin/env python3
"""
J-MAT Daily M&A News Generator
- 案件抽出: maonline.jp / nihon-ma.co.jp / marr.jp
- 記事生成: Gemini API (一次情報ベース)
- 財務分析: EDINETDB + matplotlib グラフ生成
- 更新: 1日3回 (9:01 / 13:01 / 17:01 JST)
"""
import datetime, os, re, json, time, base64, io, hashlib
import requests
from bs4 import BeautifulSoup

# ======================
# APIキー
# ======================
PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY", "")
EDINETDB_API_KEY = os.environ.get("EDINETDB_API_KEY", "")
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")

EDINETDB_BASE    = "https://edinetdb.jp/v1"
EDINETDB_HEADERS = {"X-API-Key": EDINETDB_API_KEY}
GEMINI_URL       = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# ======================
# 経産省業種分類（主要のみ）
# ======================
METI_INDUSTRY_MAP = {
    "農業": ["農業", "農産", "農協"],
    "林業": ["林業", "木材", "製材"],
    "漁業": ["漁業", "水産", "養殖"],
    "鉱業": ["鉱業", "採掘", "石炭"],
    "食料品製造業": ["食品", "飲料", "食料", "菓子", "乳業", "製糖", "缶詰"],
    "繊維工業": ["繊維", "紡績", "織物", "アパレル", "縫製"],
    "化学工業": ["化学", "薬品", "化粧品", "塗料", "接着剤"],
    "医薬品製造業": ["製薬", "医薬品", "バイオ", "創薬"],
    "鉄鋼業": ["鉄鋼", "製鉄", "鉄板", "特殊鋼"],
    "非鉄金属製造業": ["非鉄金属", "アルミ", "銅", "亜鉛"],
    "機械器具製造業": ["機械", "産業機械", "工作機械", "ロボット"],
    "電気機械器具製造業": ["電機", "電気機器", "半導体", "電子部品"],
    "情報通信機械器具製造業": ["通信機器", "スマートフォン", "PC"],
    "自動車・同附属品製造業": ["自動車", "カーパーツ", "車体"],
    "建設業": ["建設", "ゼネコン", "工事", "土木", "建築"],
    "電気・ガス・熱供給・水道業": ["電力", "ガス", "エネルギー", "電気"],
    "通信業": ["通信", "電話", "携帯", "インターネット", "ISP"],
    "放送業": ["放送", "テレビ", "ラジオ", "メディア"],
    "情報サービス業": ["IT", "ソフトウェア", "SaaS", "クラウド", "DX", "システム", "AI"],
    "インターネット附随サービス業": ["EC", "ネット", "プラットフォーム", "フィンテック"],
    "運輸業": ["運輸", "物流", "配送", "トラック", "航空", "海運", "倉庫"],
    "卸売業": ["卸売", "商社", "流通"],
    "小売業": ["小売", "スーパー", "コンビニ", "百貨店", "ドラッグストア"],
    "銀行業": ["銀行", "信託", "信用金庫"],
    "証券・商品先物取引業": ["証券", "先物", "FX"],
    "保険業": ["保険", "損保", "生保"],
    "その他金融業": ["ファンド", "リース", "ファクタリング", "投資"],
    "不動産業": ["不動産", "住宅", "マンション", "賃貸", "REIT"],
    "宿泊業": ["ホテル", "旅館", "宿泊"],
    "飲食サービス業": ["飲食", "レストラン", "カフェ", "外食", "フードサービス"],
    "医療業": ["病院", "クリニック", "医療", "診療"],
    "介護・社会福祉業": ["介護", "福祉", "高齢者"],
    "教育・学習支援業": ["教育", "学習", "学校", "塾"],
    "娯楽業": ["ゲーム", "エンタメ", "映画", "音楽", "アミューズメント"],
    "廃棄物処理業": ["廃棄物", "ごみ処理", "リサイクル", "環境処理", "廃液", "産廃", "一般廃棄物"],
    "警備・メンテナンス業": ["メンテナンス", "保守", "点検", "警備", "施設管理", "ビル管理"],
    "消防・防災設備業": ["消防", "防災", "防火", "スプリンクラー"],
    "広告・マーケティング業": ["広告", "マーケティング", "PR", "プロモーション", "リスティング", "SNS広告"],
    "人材サービス業": ["人材", "派遣", "採用", "HR", "転職"],
    "教育・学習支援業": ["教育", "学習", "学校", "塾", "スクール", "保育", "学童"],
    "サービス業（他に分類されないもの）": ["サービス", "コンサル", "その他"],
}

def detect_meti_industry(text):
    for industry, keywords in METI_INDUSTRY_MAP.items():
        if any(k in text for k in keywords):
            return industry
    return "サービス業（他に分類されないもの）"

# ======================
# 日時
# ======================
now = datetime.datetime.now()
date_str   = now.strftime("%Y-%m-%d %H:%M:%S +0900")
today_str  = now.strftime("%Y-%m-%d")
today_jp   = now.strftime("%Y年%m月%d日")
slot_hour  = now.hour
if slot_hour < 11:
    slot = "morning"
    slot_jp = "朝刊"
elif slot_hour < 15:
    slot = "noon"
    slot_jp = "昼刊"
else:
    slot = "evening"
    slot_jp = "夕刊"

print(f"=== J-MAT {today_jp} {slot_jp} ===")

# ======================
# 案件抽出：3サイトのスクレイピング（タイトル・URL・概要のみ）
# ======================
HEADERS_SCRAPE = {
    "User-Agent": "Mozilla/5.0 (compatible; J-MAT-bot/1.0)",
    "Accept-Language": "ja,en;q=0.9",
}

def scrape_maonline():
    """M&A Online: M&A速報一覧からタイトル・URL取得"""
    deals = []
    try:
        r = requests.get("https://maonline.jp/news", headers=HEADERS_SCRAPE, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href*='/news/']")[:40]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 10:
                continue
            url = href if href.startswith("http") else "https://maonline.jp" + href
            deals.append({"title": title, "url": url, "source": "maonline"})
    except Exception as e:
        print(f"  maonline scrape error: {e}")
    return deals

def scrape_nihonma():
    """日本M&Aセンター: ニュースからタイトル・URL取得"""
    deals = []
    try:
        r = requests.get("https://www.nihon-ma.co.jp/news/", headers=HEADERS_SCRAPE, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href*='/news/']")[:40]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 10:
                continue
            url = href if href.startswith("http") else "https://www.nihon-ma.co.jp" + href
            deals.append({"title": title, "url": url, "source": "nihonma"})
    except Exception as e:
        print(f"  nihonma scrape error: {e}")
    return deals

def scrape_marr():
    """MARR Online: トピックスからタイトル・PDF URL取得"""
    deals = []
    try:
        r = requests.get("https://www.marr.jp/genre/topics/news/", headers=HEADERS_SCRAPE, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a")[:60]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 10:
                continue
            if not any(k in href for k in ["/topics/", "/news/", ".pdf"]):
                continue
            url = href if href.startswith("http") else "https://www.marr.jp" + href
            deals.append({"title": title, "url": url, "source": "marr"})
    except Exception as e:
        print(f"  marr scrape error: {e}")
    return deals

# ======================
# M&Aキーワードフィルタ
# ======================
MA_STRONG = ["公開買付", "TOB", "MBO", "株式交換", "吸収合併", "会社分割",
             "完全子会社化", "子会社化", "経営統合", "事業譲渡", "資本業務提携",
             "買収", "M&A", "合併", "出資", "資本参加"]
MA_NG     = ["採用", "セミナー", "イベント", "募集", "決算短信", "配当",
             "自己株式", "役員", "人事", "株主総会"]

def is_ma_deal(title):
    if any(k in title for k in MA_NG):
        return False
    return any(k in title for k in MA_STRONG)

# ======================
# 重複排除（タイトル類似度）
# ======================
def normalize(t):
    return re.sub(r'[　\s【】「」『』〈〉（）()［］\[\]]', '', t).lower()

def deduplicate(deals):
    seen_norm = {}
    result = []
    for d in deals:
        n = normalize(d["title"])
        key = n[:20]
        if key not in seen_norm:
            seen_norm[key] = True
            result.append(d)
    return result

# ======================
# TDnet適時開示PDF取得
# ======================
def fetch_tdnet_disclosure(company_name):
    """TDnet yanoshin APIから企業の最新適時開示を取得"""
    try:
        r = requests.get(
            "https://webapi.yanoshin.jp/webapi/tdnet/list/recent.rss",
            timeout=10
        )
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")
        for item in items[:100]:
            title_tag = item.find("title")
            link_tag  = item.find("link")
            if not title_tag or not link_tag:
                continue
            title = title_tag.get_text()
            link  = link_tag.get_text()
            # 企業名の一部が含まれるか
            short = company_name[:4]
            if short in title and any(k in title for k in MA_STRONG):
                return {"title": title, "url": link}
    except Exception as e:
        print(f"  TDnet fetch error: {e}")
    return None

def fetch_tdnet_pdf_text(company_name_short):
    """TDnetからM&A関連の適時開示PDFを取得してテキスト抽出"""
    try:
        # yanoshin APIで最新適時開示を検索
        r = requests.get(
            "https://webapi.yanoshin.jp/webapi/tdnet/list/recent.rss",
            timeout=10
        )
        soup_rss = BeautifulSoup(r.text, "xml")
        for item in soup_rss.find_all("item")[:200]:
            title_tag = item.find("title")
            link_tag  = item.find("link")
            if not title_tag or not link_tag:
                continue
            title = title_tag.get_text()
            link  = link_tag.get_text()
            # 企業名 + M&Aキーワードでマッチ
            if company_name_short[:3] in title and any(k in title for k in MA_STRONG):
                # PDFリンクを直接取得
                pdf_url = link
                if "rd.php" in link:
                    # リダイレクト先を取得
                    rr = requests.get(link, headers=HEADERS_SCRAPE, 
                                     timeout=10, allow_redirects=True)
                    pdf_url = rr.url
                print(f"    TDnet PDF発見: {title[:40]}")
                return {"url": pdf_url, "title": title, "text": extract_pdf_text(pdf_url)}
    except Exception as e:
        print(f"    TDnet RSS error: {e}")
    return None

def extract_pdf_text(pdf_url):
    """PDFからテキストを抽出（pdfminer不使用・シンプル版）"""
    try:
        r = requests.get(pdf_url, headers=HEADERS_SCRAPE, timeout=15)
        if r.status_code != 200:
            return ""
        # バイナリからテキストを抽出（簡易版）
        content = r.content
        # PDFの生テキストを正規表現で抽出
        text_parts = re.findall(rb'\(([^)]{4,200})\)', content)
        extracted = []
        for part in text_parts:
            try:
                t = part.decode('utf-8', errors='ignore')
                if re.search(r'[ぁ-んァ-ン一-龥]', t):  # 日本語含む
                    extracted.append(t)
            except:
                pass
        result = " ".join(extracted[:100])
        if len(result) > 100:
            return result[:2000]
    except Exception as e:
        print(f"    PDF extract error: {e}")
    return ""

def fetch_press_release(deal_url, company_name=""):
    """公式プレスリリース取得（TDnet PDF優先）"""
    from urllib.parse import urljoin
    press_url = deal_url
    press_text = ""

    # ① TDnet適時開示PDFを優先取得
    if company_name:
        tdnet = fetch_tdnet_pdf_text(company_name)
        if tdnet and tdnet.get("text"):
            return {"url": tdnet["url"], "text": tdnet["text"]}
        elif tdnet:
            press_url = tdnet["url"]

    # ② maonlineページからTDnetリンクを探す
    try:
        r = requests.get(deal_url, headers=HEADERS_SCRAPE, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")

        # TDnet/IRリンクを探す
        for a in soup.find_all("a", href=True):
            href = a.get("href","")
            if any(k in href for k in ["release.tdnet", "tdnet.info", ".pdf"]):
                press_url = href if href.startswith("http") else urljoin(deal_url, href)
                if ".pdf" in press_url:
                    text = extract_pdf_text(press_url)
                    if text:
                        return {"url": press_url, "text": text}
                break

        # ③ ページテキストをフォールバックとして使用
        for tag in soup(["script","style","nav","footer","header","aside"]):
            tag.decompose()
        article = soup.find("article") or soup.find(attrs={"class": re.compile(r"article|news|content")})
        raw = article.get_text(separator="\n") if article else soup.get_text(separator="\n")
        press_text = re.sub(r'\n{3,}', '\n\n', raw).strip()[:2000]
    except Exception as e:
        print(f"    fetch_press_release error: {e}")

    return {"url": press_url, "text": press_text}

# ======================
# EDINETDB
# ======================
def edinetdb_search(name):
    if not EDINETDB_API_KEY or not name:
        return None
    try:
        r = requests.get(f"{EDINETDB_BASE}/search",
                         params={"q": name[:10]},
                         headers=EDINETDB_HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                return data[0]
    except Exception as e:
        print(f"  EDINETDB search error: {e}")
    return None

def edinetdb_financials(edinet_code):
    if not EDINETDB_API_KEY:
        return []
    try:
        r = requests.get(f"{EDINETDB_BASE}/companies/{edinet_code}/financials",
                         params={"years": 5},
                         headers=EDINETDB_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception as e:
        print(f"  EDINETDB financials error: {e}")
    return []

def edinetdb_analysis(edinet_code):
    if not EDINETDB_API_KEY:
        return {}
    try:
        r = requests.get(f"{EDINETDB_BASE}/companies/{edinet_code}/analysis",
                         headers=EDINETDB_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", {})
    except Exception as e:
        print(f"  EDINETDB analysis error: {e}")
    return {}

def edinetdb_text_blocks(edinet_code):
    """有報テキスト（事業計画・中期経営計画）"""
    if not EDINETDB_API_KEY:
        return {}
    try:
        r = requests.get(f"{EDINETDB_BASE}/companies/{edinet_code}/text-blocks",
                         headers=EDINETDB_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", {})
    except Exception as e:
        print(f"  EDINETDB text-blocks error: {e}")
    return {}

# ======================
# 株価取得（Yahoo Finance Japan）
# ======================
def fetch_stock_price(sec_code):
    """Yahoo Finance JapanからCSVで株価取得"""
    if not sec_code:
        return []
    try:
        code = sec_code.zfill(4) + ".T"
        end   = int(now.timestamp())
        start = int((now - datetime.timedelta(days=365*5)).timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1mo&period1={start}&period2={end}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = r.json()
        result_data = data.get("chart", {}).get("result", [])
        if not result_data:
            return []
        timestamps = result_data[0].get("timestamp", [])
        quote = result_data[0].get("indicators", {}).get("quote", [])
        if not quote or not timestamps:
            return []
        closes = quote[0].get("close", [])
        prices = []
        for t, c in zip(timestamps, closes):
            if c is None:
                continue
            dt = datetime.datetime.fromtimestamp(t)
            prices.append({"date": dt.strftime("%Y-%m"), "close": round(c, 1)})
        return prices[-60:]  # 直近60ヶ月
    except Exception as e:
        print(f"  stock price fetch error: {e}")
    return []

# ======================
# グラフ生成（matplotlib）
# ======================
def generate_charts(financials, stock_prices, company_name):
    """PL/BSグラフ＋株価チャートをbase64 PNG で返す"""
    charts = {}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mtick
        # 日本語フォント設定
        import subprocess
        subprocess.run(["apt-get", "install", "-y", "-q", "fonts-noto-cjk"], 
                      capture_output=True)
        import matplotlib.font_manager as fm
        fm._load_fontmanager(try_read_cache=False)
        # Noto Sans CJK JPを優先、なければIPAex
        for fname in ["Noto Sans CJK JP", "IPAexGothic", "DejaVu Sans"]:
            if any(fname in f.name for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = fname
                break

        # --- PL/BS 棒グラフ ---
        if financials:
            years = [str(f.get("fiscal_year","")) for f in financials]
            rev   = [f.get("revenue",0) or 0 for f in financials]
            oi    = [f.get("operating_income",0) or 0 for f in financials]
            ni    = [f.get("net_income",0) or 0 for f in financials]

            # 億円換算
            rev = [v/1e8 for v in rev]
            oi  = [v/1e8 for v in oi]
            ni  = [v/1e8 for v in ni]

            x = range(len(years))
            width = 0.28

            fig, ax = plt.subplots(figsize=(8,4))
            ax.bar([i-width for i in x], rev, width, label="売上高", color="#2563eb", alpha=0.85)
            ax.bar([i       for i in x], oi,  width, label="営業利益", color="#16a34a", alpha=0.85)
            ax.bar([i+width for i in x], ni,  width, label="純利益", color="#dc2626", alpha=0.85)
            ax.set_xticks(list(x))
            ax.set_xticklabels([f"FY{y}" for y in years], fontsize=9)
            ax.set_ylabel("億円", fontsize=9)
            ax.set_title(f"{company_name} PL推移", fontsize=11)
            ax.legend(fontsize=8)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v,_: f"{v:,.0f}"))
            ax.grid(axis="y", alpha=0.3)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120)
            plt.close(fig)
            charts["pl"] = base64.b64encode(buf.getvalue()).decode()

        # --- 株価折れ線チャート ---
        if stock_prices:
            dates  = [p["date"] for p in stock_prices]
            prices = [p["close"] for p in stock_prices]

            fig, ax = plt.subplots(figsize=(8,3))
            ax.plot(range(len(dates)), prices, color="#7c3aed", linewidth=1.8)
            ax.fill_between(range(len(dates)), prices, alpha=0.1, color="#7c3aed")

            # X軸：年のみ表示
            tick_idx = [i for i,d in enumerate(dates) if d.endswith("-01") or i==0]
            ax.set_xticks(tick_idx)
            ax.set_xticklabels([dates[i][:4] for i in tick_idx], fontsize=8)
            ax.set_ylabel("円", fontsize=9)
            ax.set_title(f"{company_name} 株価推移", fontsize=11)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v,_: f"{v:,.0f}"))
            ax.grid(alpha=0.3)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120)
            plt.close(fig)
            charts["stock"] = base64.b64encode(buf.getvalue()).decode()

    except Exception as e:
        print(f"  chart generation error: {e}")

    return charts

# ======================
# Gemini APIで記事生成
# ======================
def gemini_generate(prompt):
    if not GEMINI_API_KEY:
        return ""
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1500,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }
        r = requests.post(GEMINI_URL, json=payload, timeout=30)
        result = r.json()
        # candidatesが存在しない場合のフォールバック
        candidates = result.get("candidates", [])
        if not candidates:
            print(f"  Gemini: candidatesなし (promptFeedback={result.get('promptFeedback',{})})")
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""
        return parts[0].get("text", "").strip()
    except Exception as e:
        print(f"  Gemini API error: {e}")
    return ""

def generate_article(deal, press_text, financials, analysis, text_blocks):
    """Geminiでオリジナル記事を生成"""

    fin_summary = ""
    if financials:
        latest = financials[-1] if isinstance(financials, list) else financials
        rev = latest.get("revenue",0) or 0
        oi  = latest.get("operating_income",0) or 0
        ni  = latest.get("net_income",0) or 0
        fin_summary = f"直近売上高: {rev/1e8:.0f}億円 / 営業利益: {oi/1e8:.0f}億円 / 純利益: {ni/1e8:.0f}億円"

    biz_plan = ""
    # text_blocksがlistの場合はdictに変換
    if isinstance(text_blocks, list):
        tb_dict = {}
        for item in text_blocks:
            if isinstance(item, dict):
                tb_dict.update(item)
        text_blocks = tb_dict
    if isinstance(text_blocks, dict) and text_blocks:
        for key in ["business_strategy","management_policy","mid_term_plan","risks"]:
            val = text_blocks.get(key,"")
            if val:
                biz_plan += val[:500]
                break

    credit = analysis.get("credit_score","") if analysis else ""
    ai_view = analysis.get("ai_comment","") if analysis else ""

    # プレスリリーステキストがある場合のプロンプト
    if press_text and len(press_text) > 100:
        info_section = f"【適時開示・プレスリリース】\n{press_text[:1000]}"
    else:
        info_section = "【注】一次情報なし。案件タイトルと財務データのみで分析。"

    prompt = f"""あなたはM&A専門メディアJ-MATの記者です。以下の案件について日本語で記事を書いてください。

【案件名】{deal['title']}
{info_section}
【財務情報】{fin_summary if fin_summary else 'データなし'} 財務スコア:{credit if credit else 'N/A'}/100
【有報の事業計画】{biz_plan[:300] if biz_plan else 'データなし'}

次の4セクション形式で出力してください（各セクション100-200字）：

## 案件概要
（買い手・売り手・スキーム・取引規模を簡潔に）

## 戦略的背景
（なぜこの買収か、業界環境、シナジー）

## 事業計画との整合性
（中期計画・M&A方針との関連、具体的数値があれば引用）

## J-MAT総合評価
（この案件の注目ポイント・今後の展望）"""

    return gemini_generate(prompt)

def generate_analysis_comment(deal, financials, text_blocks, companies):
    """財務分析コメントをGeminiで生成"""
    if not financials and not text_blocks:
        return ""

    fin_text = ""
    for f in financials[:5]:
        fy  = f.get("fiscal_year","")
        rev = (f.get("revenue",0) or 0) / 1e8
        oi  = (f.get("operating_income",0) or 0) / 1e8
        ni  = (f.get("net_income",0) or 0) / 1e8
        fin_text += f"FY{fy}: 売上{rev:.0f}億 営業利益{oi:.0f}億 純利益{ni:.0f}億\n"

    biz_plan = ""
    if isinstance(text_blocks, list):
        tb_dict = {}
        for item in text_blocks:
            if isinstance(item, dict):
                tb_dict.update(item)
        text_blocks = tb_dict
    if isinstance(text_blocks, dict) and text_blocks:
        for key in ["mid_term_plan","business_strategy","management_policy"]:
            val = text_blocks.get(key,"")
            if val:
                biz_plan = val[:800]
                break

    company_names = " / ".join([c.get("name","") for c in companies if c])

    prompt = f"""M&A専門アナリストとして、以下の財務データをもとに分析コメントを200-300字で書いてください。

案件: {deal['title']}
対象企業: {company_names}
直近財務:
{fin_text if fin_text else 'データなし'}
事業計画: {biz_plan[:400] if biz_plan else 'データなし'}

【分析の観点】
1. 中期経営計画のM&A数値目標との整合性
2. 財務的な買収余力（自己資本・純有利子負債）
3. 買収後の業績への影響見通し

専門家視点で簡潔に論述してください。"""

    return gemini_generate(prompt)

# ======================
# Pexels画像取得
# ======================
def fetch_pexels_image(industry, seed):
    query_map = {
        "情報サービス業":          "technology office business",
        "銀行業":                  "finance bank building",
        "保険業":                  "insurance business meeting",
        "医薬品製造業":            "pharmaceutical laboratory",
        "食料品製造業":            "food manufacturing factory",
        "建設業":                  "construction building",
        "不動産業":                "real estate property",
        "電気・ガス・熱供給・水道業": "energy power plant",
        "運輸業":                  "logistics transportation",
        "小売業":                  "retail store shopping",
        "飲食サービス業":          "restaurant food service",
        "医療業":                  "hospital healthcare medical",
        "自動車・同附属品製造業":   "automotive manufacturing",
        "電気機械器具製造業":      "electronics semiconductor",
    }
    query = query_map.get(industry, "business merger acquisition")
    if not PEXELS_API_KEY:
        return f"https://picsum.photos/seed/{seed}/800/450"
    try:
        r = requests.get(
            f"https://api.pexels.com/v1/search?query={query}&per_page=5&page={(seed%3)+1}&orientation=landscape",
            headers={"Authorization": PEXELS_API_KEY}, timeout=10
        )
        photos = r.json().get("photos",[])
        if photos:
            return photos[seed % len(photos)]["src"]["large"]
    except Exception as e:
        print(f"  Pexels error: {e}")
    return f"https://picsum.photos/seed/{seed}/800/450"

# ======================
# メイン処理
# ======================
print("案件抽出中...")
raw_deals = []
raw_deals += scrape_maonline()
time.sleep(2)
raw_deals += scrape_nihonma()
time.sleep(2)
raw_deals += scrape_marr()

print(f"  取得: {len(raw_deals)}件")
ma_deals = [d for d in raw_deals if is_ma_deal(d["title"])]
ma_deals = deduplicate(ma_deals)
print(f"  M&Aフィルタ後: {len(ma_deals)}件")

if not ma_deals:
    print("案件なし。終了します。")
    exit(0)

# ======================
# 各案件を処理
# ======================
articles = []
featured_data = []
headline_data = []

for i, deal in enumerate(ma_deals[:20]):
    print(f"\n[{i+1}] {deal['title'][:50]}")

    # タイトルから企業名を簡易抽出してTDnet検索キーに使用
    title_cn = re.sub(r'＜[^＞]+＞', '', deal["title"]).strip()
    cn_short = title_cn[:6]
    press = fetch_press_release(deal["url"], company_name=cn_short)
    press_text = press.get("text","")
    press_url  = press.get("url", deal["url"])
    time.sleep(1)

    # 業種判定
    industry = detect_meti_industry(deal["title"] + " " + press_text[:200])

    # 企業名抽出（簡易）
    company_patterns = [
        r'([^\s、。「」【】]{2,15}(?:株式会社|ホールディングス|ＨＤ|HD|グループ))',
        r'((?:株式会社)[^\s、。「」【】]{2,12})',
        r'([^\s、。「」【】]{3,8}＜\d{4}＞)',
    ]
    company_names = []
    for pat in company_patterns:
        matches = re.findall(pat, deal["title"])
        company_names.extend(matches)
    company_names = list(dict.fromkeys(company_names))[:3]
    print(f"  企業名: {company_names}")

    # EDINETDB照合
    companies_data = []
    financials_all = []
    text_blocks_all = {}
    sec_codes = []

    for cname in company_names[:2]:
        co = edinetdb_search(cname)
        if co:
            ec   = co.get("edinet_code","")
            sc   = co.get("sec_code","")
            fins = edinetdb_financials(ec)
            ana  = edinetdb_analysis(ec)
            txts = edinetdb_text_blocks(ec)
            print(f"  EDINETDB: {co.get('name','')} ({ec}) score={ana.get('credit_score','N/A') if ana else 'N/A'}")
            companies_data.append({"name": co.get("name",""), "edinet_code": ec, "sec_code": sc, "analysis": ana})
            if fins:
                financials_all = fins
            if txts:
                text_blocks_all = txts
            if sc:
                sec_codes.append(sc)
        time.sleep(0.5)

    # 株価取得（最初の上場企業）
    stock_prices = []
    if sec_codes:
        stock_prices = fetch_stock_price(sec_codes[0])

    # グラフ生成
    charts = {}
    main_company = companies_data[0]["name"] if companies_data else deal["title"][:10]
    if financials_all or stock_prices:
        charts = generate_charts(financials_all, stock_prices, main_company)

    # Geminiで記事生成（ピックアップ5件のみ）
    article_body = ""
    analysis_comment = ""
    if i < 5:
        print(f"  Gemini記事生成中...")
        article_body = generate_article(deal, press_text, financials_all,
                                        companies_data[0].get("analysis",{}) if companies_data else {},
                                        text_blocks_all)
        if financials_all:
            analysis_comment = generate_analysis_comment(deal, financials_all, text_blocks_all, companies_data)
        time.sleep(1)

    # 画像
    seed = abs(hash(deal["title"])) % 100
    img_url = fetch_pexels_image(industry, seed)

    # プロタイトル生成
    if "TOB" in deal["title"] or "公開買付" in deal["title"]:
        action = "TOBによる完全子会社化"
    elif "MBO" in deal["title"]:
        action = "MBOによる非公開化"
    elif "合併" in deal["title"]:
        action = "合併統合"
    elif "事業譲渡" in deal["title"]:
        action = "事業譲渡"
    elif "資本業務提携" in deal["title"]:
        action = "資本業務提携"
    else:
        action = "M&A"

    pro_title = f"【{industry}】{deal['title'][:40]}"

    art = {
        "rank":             i + 1,
        "title":            deal["title"],
        "pro_title":        pro_title,
        "url":              deal["url"],
        "press_url":        press_url,
        "source":           deal["source"],
        "industry":         industry,
        "image":            img_url,
        "article_body":     article_body,
        "analysis_comment": analysis_comment,
        "charts":           charts,
        "companies":        companies_data,
        "has_financials":   bool(financials_all),
    }

    if i < 5:
        featured_data.append(art)
    headline_data.append(art)

# ======================
# 記事ページ（_posts）生成
# ======================
os.makedirs("_posts", exist_ok=True)
os.makedirs("assets/charts", exist_ok=True)

# チャート画像をファイル保存
for art in featured_data:
    slug = hashlib.md5(art["title"].encode()).hexdigest()[:8]
    for chart_type, b64data in art.get("charts",{}).items():
        fname = f"assets/charts/{today_str}-{slot}-{slug}-{chart_type}.png"
        with open(fname, "wb") as f:
            f.write(base64.b64decode(b64data))
        art[f"chart_{chart_type}_path"] = f"/{fname}"
        print(f"  チャート保存: {fname}")

# メイン記事（今回のスロット）
filename = f"_posts/{today_str}-{slot}-ma-news.md"

# featured YAML
featured_yaml = ""
for f in featured_data:
    safe_title    = f["pro_title"].replace('"',"'")
    safe_press    = f["press_url"].replace('"',"'")
    safe_industry = f["industry"].replace('"',"'")
    safe_analysis = f["analysis_comment"].replace('"',"'").replace('\n',' ')[:300] if f["analysis_comment"] else ""
    chart_pl      = f.get("chart_pl_path","")
    chart_stock   = f.get("chart_stock_path","")

    featured_yaml += f'  - rank: {f["rank"]}\n'
    featured_yaml += f'    title: "{safe_title}"\n'
    featured_yaml += f'    link: "{safe_press}"\n'
    featured_yaml += f'    image: "{f["image"]}"\n'
    featured_yaml += f'    industry: "{safe_industry}"\n'
    featured_yaml += f'    analysis: "{safe_analysis}"\n'
    featured_yaml += f'    chart_pl: "{chart_pl}"\n'
    featured_yaml += f'    chart_stock: "{chart_stock}"\n'

# headlines YAML
headlines_yaml = ""
for h in headline_data:
    safe_t = h["title"].replace('"',"'")
    safe_u = h["press_url"]
    safe_i = h["industry"].replace('"',"'")
    headlines_yaml += f'  - title: "{safe_t}"\n'
    headlines_yaml += f'    link: "{safe_u}"\n'
    headlines_yaml += f'    industry: "{safe_i}"\n'

# ページタイトル
main_title   = f"{today_jp}のM&A動向{slot_jp}：注目5案件を財務分析付きで解説"
page_summary = f"本日{slot_jp}のM&Aニュース。TDnet・公式プレスリリースをもとにGeminiが分析。財務データ・株価チャート付き。"

# 本文
body = f"## {slot_jp}の注目5案件\n\n"
for art in featured_data:
    body += f"### {art['rank']}. {art['pro_title']}\n\n"
    body += f"**業種分類（経産省）：** {art['industry']}\n\n"
    if art["article_body"]:
        body += art["article_body"] + "\n\n"
    if art["analysis_comment"]:
        body += f"---\n**📊 財務分析コメント**\n\n{art['analysis_comment']}\n\n"
    if art.get("chart_pl_path"):
        body += f"![PL推移チャート]({art['chart_pl_path']})\n\n"
    if art.get("chart_stock_path"):
        body += f"![株価推移チャート]({art['chart_stock_path']})\n\n"
    body += f"[📄 公式リリースを読む]({art['press_url']})\n\n---\n\n"

body += "## 本日の全M&Aヘッドライン\n\n"
for h in headline_data:
    body += f"- [{h['title']}]({h['press_url']}) （{h['industry']}）\n"

content = f"""---
title: "{main_title}"
date: {date_str}
summary: "{page_summary}"
slot: "{slot}"
featured:
{featured_yaml}headlines:
{headlines_yaml}---

{body}
"""

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ 完了: {filename}")
print(f"   ピックアップ: {len(featured_data)}件 / ヘッドライン: {len(headline_data)}件")
