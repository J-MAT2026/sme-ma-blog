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
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
GROQ_URL         = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL       = "llama-3.3-70b-versatile"  # 無料・高速・高品質

# ======================
# 経産省業種分類（優先度順・キーワード拡充）
# ※ 上から順にマッチするため、具体的な業種を先に配置
# ======================
METI_INDUSTRY_MAP = [
    ("医薬品製造業",         ["製薬", "医薬品", "バイオ", "創薬", "新薬", "治験", "睡眠障害"]),
    ("医療業",               ["病院", "クリニック", "医療", "診療", "歯科", "医療法人"]),
    ("介護・社会福祉業",     ["介護", "福祉", "高齢者", "デイサービス", "保育園", "学童"]),
    ("廃棄物処理業",         ["廃棄物", "ごみ処理", "リサイクル", "環境処理", "廃液", "産廃", "一般廃棄物", "焼却"]),
    ("消防・防災設備業",     ["消防", "防災", "防火", "スプリンクラー", "防災社"]),
    ("食料品製造業",         ["食品", "飲料", "食料", "菓子", "乳業", "製糖", "缶詰", "水産加工", "醸造"]),
    ("飲食サービス業",       ["飲食", "レストラン", "カフェ", "外食", "フードサービス", "食堂", "居酒屋"]),
    ("建設業",               ["建設", "ゼネコン", "工事", "土木", "建築", "リフォーム", "設備工事"]),
    ("木材・木製品製造業",   ["木材", "製材", "集成材", "合板", "建材", "造作材", "木構造"]),
    ("鉄鋼業",               ["鉄鋼", "製鉄", "鉄板", "特殊鋼"]),
    ("非鉄金属製造業",       ["非鉄金属", "アルミ", "銅", "亜鉛", "貴金属", "金銀"]),
    ("機械器具製造業",       ["機械", "産業機械", "工作機械", "ロボット", "バルブ", "ポンプ", "流体制御", "真空"]),
    ("電気機械器具製造業",   ["電機", "電気機器", "半導体", "電子部品", "熱交換器"]),
    ("自動車・同附属品製造業", ["自動車", "カーパーツ", "車体"]),
    ("化学工業",             ["化学", "薬品", "化粧品", "塗料", "接着剤", "スキンケア", "コスメ"]),
    ("繊維工業",             ["繊維", "紡績", "織物", "アパレル", "縫製", "衣料品"]),
    ("広告・マーケティング業", ["広告", "マーケティング", "PR", "プロモーション", "リスティング", "SNS広告"]),
    ("人材サービス業",       ["人材", "派遣", "採用", "HR", "転職", "求人", "キャリア", "進路"]),
    ("教育・学習支援業",     ["教育", "学習", "学校", "塾", "スクール", "進学"]),
    ("情報サービス業",       ["IT", "ソフトウェア", "SaaS", "クラウド", "DX", "システム開発", "AI", "SIer", "受託開発"]),
    ("インターネット附随サービス業", ["EC", "ネット通販", "プラットフォーム", "フィンテック", "Shopify", "ECサイト"]),
    ("通信業",               ["通信", "電話", "携帯", "ISP"]),
    ("放送業",               ["放送", "テレビ", "ラジオ"]),
    ("電気・ガス・熱供給・水道業", ["電力", "ガス", "エネルギー", "発電", "水力発電"]),
    ("運輸業",               ["運輸", "物流", "配送", "トラック", "航空", "海運", "倉庫"]),
    ("卸売業",               ["卸売", "商社", "流通", "輸入卸"]),
    ("小売業",               ["小売", "スーパー", "コンビニ", "百貨店", "ドラッグストア", "OA機器販売"]),
    ("不動産業",             ["不動産", "住宅", "マンション", "賃貸", "REIT"]),
    ("銀行業",               ["銀行", "信託", "信用金庫", "持株会社設立"]),
    ("証券・商品先物取引業", ["証券", "先物", "FX"]),
    ("保険業",               ["保険", "損保", "生保"]),
    ("その他金融業",         ["ファンド", "リース", "ファクタリング", "投資", "MBO", "TOB"]),
    ("宿泊業",               ["ホテル", "旅館", "宿泊"]),
    ("娯楽業",               ["ゲーム", "エンタメ", "映画", "音楽", "アミューズメント", "カラオケ"]),
    ("警備・メンテナンス業", ["メンテナンス", "保守", "点検", "警備", "施設管理", "ビル管理"]),
    ("農業",                 ["農業", "農産", "農協", "農場"]),
    ("林業",                 ["林業"]),
    ("漁業",                 ["漁業", "養殖"]),
    ("鉱業",                 ["鉱業", "採掘", "石炭"]),
    ("サービス業（他に分類されないもの）", ["コンサル"]),
]

def detect_meti_industry(text):
    """業種を検出（優先度リストの上から順にマッチ）"""
    for industry, keywords in METI_INDUSTRY_MAP:
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
def groq_generate(prompt):
    """Groq APIで記事・分析コメントを生成（無料・高速）"""
    if not GROQ_API_KEY:
        print("  Groq API: APIキー未設定")
        return ""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "あなたはM&A専門メディアのシニアアナリストです。正確で簡潔な日本語で出力してください。Markdown形式で出力し、余計なメタコメントや注釈は一切含めないでください。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.4,
        }
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=45)
        result = r.json()
        if "error" in result:
            print(f"  Groq error: {result['error'].get('message','')[:100]}")
            return ""
        choices = result.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "").strip()
            return clean_llm_output(text)
    except Exception as e:
        print(f"  Groq API error: {e}")
    return ""

def clean_llm_output(text):
    """LLM出力のクリーンアップ"""
    if not text:
        return ""
    # ゴミテキスト・コードブロック記号の除去
    text = re.sub(r'```[\w]*\n?', '', text)
    text = re.sub(r'_v\d+\b', '', text)
    text = re.sub(r'\*\*注[：:]?\*\*.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'【?注[）\)]?】?.*$', '', text, flags=re.MULTILINE)
    # PMI の誤った展開を修正
    text = re.sub(r'PMI\s*[\(（]\s*Performance\s+Metrics?\s+and\s+Indicators?\s*[\)）]',
                  'PMI（Post Merger Integration：買収後統合）', text, flags=re.IGNORECASE)
    text = re.sub(r'PMI\s*[\(（]\s*ポストマージン統合\s*[\)）]',
                  'PMI（Post Merger Integration：買収後統合）', text)
    # 連続改行の整理
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    # 先頭の空行を削除
    text = text.strip()
    return text

# 後方互換のためエイリアスを定義
def claude_generate(prompt):
    return groq_generate(prompt)

def gemini_generate(prompt, retry=1):
    return groq_generate(prompt)

def generate_article(deal, press_text, financials, analysis, text_blocks):
    """LLMでプロ水準のM&A分析記事を生成（一次情報ベース）"""

    # --- 財務サマリー構築 ---
    fin_summary = ""
    if financials:
        for f in financials[-3:]:  # 直近3年分
            fy  = f.get("fiscal_year","")
            rev = (f.get("revenue",0) or 0) / 1e8
            oi  = (f.get("operating_income",0) or 0) / 1e8
            ni  = (f.get("net_income",0) or 0) / 1e8
            ta  = (f.get("total_assets",0) or 0) / 1e8
            eq  = (f.get("equity",0) or 0) / 1e8
            fin_summary += f"FY{fy}: 売上{rev:.1f}億円 / 営業利益{oi:.1f}億円 / 純利益{ni:.1f}億円 / 総資産{ta:.1f}億円 / 純資産{eq:.1f}億円\n"

    # --- 事業計画テキスト ---
    biz_plan = ""
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

    # --- プレスリリース情報 ---
    if press_text and len(press_text) > 100:
        info_section = f"【適時開示・プレスリリース本文】\n{press_text[:1500]}"
    else:
        info_section = "【注】適時開示PDFの取得不可。タイトル情報のみで分析してください。"

    # --- タイトルから数値情報を抽出（プレスリリースがない場合の補完） ---
    title_nums = re.findall(r'[\d,]+(?:万|億|百万)?円?', deal['title'] + " " + (press_text[:500] if press_text else ""))
    nums_info = f"テキスト内の数値: {', '.join(title_nums[:10])}" if title_nums else ""

    prompt = f"""あなたはM&A専門メディア「J-MAT」のシニアアナリストです。
一次情報に基づき、プロの投資家・経営者が読む分析記事を執筆してください。

【案件名】{deal['title']}
{info_section}
{f'【買い手の財務データ（直近3年）】{chr(10)}{fin_summary}' if fin_summary else '【財務データ】EDINETから取得できず。プレスリリース内の数値を使用してください。'}
{f'【信用スコア】{credit}/100' if credit else ''}
{f'【中期経営計画・事業方針】{biz_plan[:400]}' if biz_plan else ''}
{nums_info}

以下の4セクションで出力してください。Markdown見出し（##）で区切ること。
※ プレスリリースに記載の具体的数値（取得価額、売上高、営業利益、純資産、取得比率、取得日など）を可能な限り引用すること。
※ 数値が不明な場合は「非公表」と明記し、推測で補わないこと。

## 案件概要
（買い手・売り手の正式名称、証券コード、スキーム（株式取得/事業譲渡/TOB等）、取得比率、取得価額、取得予定日を整理。売り手の直近業績（売上高・営業利益・純資産）があれば必ず記載。）

## 戦略的背景
（買い手がこの買収を行う理由を一次情報から分析。業界の構造変化、対象企業の強み・ポジション、期待されるシナジー効果を具体的に論述。）

## 事業計画との整合性
（中期経営計画でのM&A方針・数値目標との整合性。過去のM&A実績との比較。財務的な買収余力（自己資本比率等）への言及。データがない場合はその旨を明記。）

## J-MAT総合評価
（本案件の戦略的意義を総括。買収プレミアムの妥当性、PMI（買収後統合）の課題、今後のウォッチポイントを専門家目線で指摘。）"""

    return gemini_generate(prompt)

def generate_analysis_comment(deal, financials, text_blocks, companies, press_text=""):
    """財務分析コメントをLLMで生成（EDINETDB不要のフォールバック対応）"""

    fin_text = ""
    for f in financials[:5]:
        fy  = f.get("fiscal_year","")
        rev = (f.get("revenue",0) or 0) / 1e8
        oi  = (f.get("operating_income",0) or 0) / 1e8
        ni  = (f.get("net_income",0) or 0) / 1e8
        eq  = (f.get("equity",0) or 0) / 1e8
        fin_text += f"FY{fy}: 売上{rev:.1f}億 営業利益{oi:.1f}億 純利益{ni:.1f}億 純資産{eq:.1f}億\n"

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

    # プレスリリースから数値を抽出
    press_nums = ""
    if press_text:
        nums = re.findall(r'(?:売上高|営業利益|純利益|純資産|取得価額|取得価格)[\s:：は]*[\d,\.]+(?:万|百万|億)?円?', press_text[:1500])
        if nums:
            press_nums = "プレスリリース記載の数値: " + " / ".join(nums[:8])

    # バリュエーション指標を算出
    valuation = calc_valuation(deal['title'], press_text)
    val_text = format_valuation(valuation)

    prompt = f"""M&A専門アナリストとして、以下のデータに基づき財務分析コメントを書いてください。

【案件】{deal['title']}
【対象企業】{company_names if company_names else '不明'}
{f'【EDINET財務データ（直近5年）】{chr(10)}{fin_text}' if fin_text else '【EDINET財務データ】取得不可'}
{f'【中期経営計画】{biz_plan[:400]}' if biz_plan else ''}
{press_nums}
{val_text}

【出力ルール】
- 300〜400字で出力
- 必ず以下4点に言及すること：
  ① バリュエーション評価（EV/売上高倍率、EV/EBITDA倍率、PBR等の算出可能な指標を計算し、業界水準との比較を行う。算出できない場合はその旨を明記）
  ② 買い手の財務的な買収余力（データがあれば自己資本比率・ネットDEレシオに言及、なければプレスリリースの数値を使用）
  ③ 売り手の収益性（営業利益率・売上規模から妥当性を評価）
  ④ 今後の注目点（PMI・のれん計上・業績への影響見通し）
- 数値は一次情報からの引用のみ。不明な場合は「開示情報からは確認できない」と明記
- 「〜と考えられる」等の推量表現を適切に使い、断定を避ける"""

    return gemini_generate(prompt)

# ======================
# バリュエーション分析
# ======================
def parse_japanese_number(text):
    """日本語の数値表現を数値に変換（例: '93億6800万' → 9368000000）"""
    if not text:
        return None
    text = text.replace(',', '').replace(' ', '').strip()
    total = 0
    # 兆
    m = re.search(r'([\d\.]+)\s*兆', text)
    if m: total += float(m.group(1)) * 1e12
    # 億
    m = re.search(r'([\d\.]+)\s*億', text)
    if m: total += float(m.group(1)) * 1e8
    # 百万
    m = re.search(r'([\d\.]+)\s*百万', text)
    if m: total += float(m.group(1)) * 1e6
    # 万
    m = re.search(r'([\d\.]+)\s*万', text)
    if m: total += float(m.group(1)) * 1e4
    if total > 0:
        return total
    # 純粋な数値（円単位）
    m = re.search(r'([\d\.]+)', text)
    if m:
        val = float(m.group(1))
        if val > 0:
            return val
    return None

def extract_financial_numbers(text):
    """プレスリリーステキストから財務数値を抽出"""
    result = {}
    patterns = {
        'acquisition_price': [
            r'取得価額[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
            r'買収価[額格][はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
            r'([\d,\.]+(?:億|百万|万)円?)(?:で[取買]得|で買収)',
        ],
        'revenue': [
            r'売上高[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
            r'売上[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
        ],
        'operating_income': [
            r'営業利益[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
        ],
        'net_assets': [
            r'純資産[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
        ],
        'net_income': [
            r'純利益[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
            r'当期純利益[はが\s:：]*約?([\d,\.]+(?:兆|億|百万|万)?円?)',
        ],
    }
    for key, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, text)
            if m:
                val = parse_japanese_number(m.group(1))
                if val and val > 0:
                    result[key] = val
                    break
    return result

def calc_valuation(title, press_text):
    """取得価額と財務数値からバリュエーション指標を算出"""
    text = title + " " + (press_text or "")
    nums = extract_financial_numbers(text)
    valuation = {"raw": nums}

    ap = nums.get('acquisition_price')
    rev = nums.get('revenue')
    oi = nums.get('operating_income')
    na = nums.get('net_assets')
    ni = nums.get('net_income')

    if ap and rev and rev > 0:
        valuation['ev_revenue'] = round(ap / rev, 2)
    if ap and oi and oi > 0:
        valuation['ev_ebitda_approx'] = round(ap / oi, 1)  # EBITDA≒営業利益の近似
    if ap and na and na > 0:
        valuation['pbr'] = round(ap / na, 2)
    if ap and ni and ni > 0:
        valuation['per'] = round(ap / ni, 1)
    if rev and oi and rev > 0:
        valuation['op_margin'] = round(oi / rev * 100, 1)

    return valuation

def format_valuation(val):
    """バリュエーション指標をプロンプト用テキストに整形"""
    lines = []
    raw = val.get('raw', {})

    if raw.get('acquisition_price'):
        lines.append(f"取得価額: {raw['acquisition_price']/1e8:.1f}億円")
    if raw.get('revenue'):
        lines.append(f"売り手売上高: {raw['revenue']/1e8:.1f}億円")
    if raw.get('operating_income'):
        lines.append(f"売り手営業利益: {raw['operating_income']/1e8:.1f}億円")
    if raw.get('net_assets'):
        lines.append(f"売り手純資産: {raw['net_assets']/1e8:.1f}億円")

    if val.get('ev_revenue'):
        lines.append(f"EV/売上高倍率: {val['ev_revenue']}x")
    if val.get('ev_ebitda_approx'):
        lines.append(f"EV/EBITDA倍率(近似): {val['ev_ebitda_approx']}x")
    if val.get('pbr'):
        lines.append(f"PBR: {val['pbr']}x")
    if val.get('per'):
        lines.append(f"PER: {val['per']}x")
    if val.get('op_margin'):
        lines.append(f"営業利益率: {val['op_margin']}%")

    if lines:
        return "【バリュエーション分析（自動算出）】\n" + "\n".join(lines)
    return "【バリュエーション分析】取得価額または財務数値が非公表のため算出不可"

# ======================
# 業種別画像取得（Pexels API 改善版）
# ======================
INDUSTRY_IMAGE_QUERIES = {
    "情報サービス業":           ["software development office", "server room technology", "coding programming screen"],
    "インターネット附随サービス業": ["ecommerce online shopping", "digital platform website", "smartphone app mobile"],
    "通信業":                   ["5G telecommunication tower", "fiber optic cable network", "satellite communication"],
    "建設業":                   ["construction site crane", "building architecture modern", "civil engineering bridge"],
    "不動産業":                 ["modern apartment building", "commercial real estate office", "property architecture city"],
    "医薬品製造業":             ["pharmaceutical laboratory research", "medicine pills capsules", "biotech lab scientist"],
    "医療業":                   ["hospital medical equipment", "healthcare clinic interior", "doctor medical professional"],
    "食料品製造業":             ["food factory production line", "food manufacturing quality", "beverage production facility"],
    "飲食サービス業":           ["restaurant kitchen cooking", "japanese restaurant interior", "cafe dining table food"],
    "機械器具製造業":           ["industrial machinery factory", "manufacturing automation robot", "precision engineering metal"],
    "電気機械器具製造業":       ["semiconductor chip closeup", "electronics manufacturing pcb", "circuit board technology"],
    "化学工業":                 ["chemical laboratory flask", "cosmetics beauty products", "paint color industrial"],
    "広告・マーケティング業":   ["digital marketing analytics", "advertising creative agency", "social media marketing"],
    "人材サービス業":           ["job interview business meeting", "career recruitment office", "handshake business deal"],
    "教育・学習支援業":         ["classroom education students", "online learning laptop", "university campus building"],
    "その他金融業":             ["stock market finance graph", "investment fund portfolio", "financial district skyline"],
    "銀行業":                   ["bank building architecture", "financial services office", "banking digital transaction"],
    "小売業":                   ["retail store shopping mall", "supermarket grocery aisle", "shop display merchandise"],
    "卸売業":                   ["warehouse logistics boxes", "wholesale distribution center", "cargo container shipping"],
    "運輸業":                   ["logistics truck highway", "cargo ship port container", "warehouse forklift operation"],
    "廃棄物処理業":             ["recycling facility plant", "waste management environmental", "green energy sustainable"],
    "木材・木製品製造業":       ["timber lumber woodwork", "sawmill wood processing", "wooden furniture crafting"],
    "繊維工業":                 ["textile fabric manufacturing", "fashion apparel clothing", "sewing machine production"],
    "娯楽業":                   ["gaming entertainment technology", "amusement park attraction", "concert music event"],
    "警備・メンテナンス業":     ["building maintenance facility", "security guard monitoring", "cleaning service professional"],
    "消防・防災設備業":         ["fire safety equipment", "fire extinguisher sprinkler", "emergency safety system"],
    "介護・社会福祉業":         ["elderly care nursing home", "childcare nursery playground", "welfare community support"],
    "宿泊業":                   ["luxury hotel lobby interior", "resort accommodation travel", "japanese ryokan traditional"],
    "鉄鋼業":                   ["steel factory molten metal", "iron manufacturing industrial", "metal fabrication welding"],
    "非鉄金属製造業":           ["aluminum metal processing", "mining mineral extraction", "precious metals gold"],
    "自動車・同附属品製造業":   ["automotive assembly line", "car manufacturing robot", "electric vehicle technology"],
    "電気・ガス・熱供給・水道業": ["power plant energy generation", "wind turbine renewable", "hydroelectric dam water"],
    "農業":                     ["agriculture farming field", "harvest crop tractor", "greenhouse farming organic"],
    "保険業":                   ["insurance protection umbrella", "family safety security", "business risk management"],
    "証券・商品先物取引業":     ["stock exchange trading floor", "financial chart analysis", "wall street finance"],
    "放送業":                   ["television broadcast studio", "media production camera", "news anchor journalism"],
    "林業":                     ["forest logging timber", "tree plantation forestry"],
    "漁業":                     ["fishing boat ocean sea", "fish market seafood fresh"],
    "鉱業":                     ["mining excavation quarry", "coal mine underground"],
    "サービス業（他に分類されないもの）": ["business office corporate", "professional consulting meeting", "modern workspace coworking"],
}

def fetch_pexels_image(industry, seed):
    """Pexels APIで業種に関連する高品質画像を取得"""
    queries = INDUSTRY_IMAGE_QUERIES.get(industry, ["business corporate office"])
    query = queries[seed % len(queries)]

    if not PEXELS_API_KEY:
        # APIキー未設定時はPicsum（ランダム写真）にフォールバック
        return f"https://picsum.photos/seed/{seed}/800/450"
    try:
        r = requests.get(
            f"https://api.pexels.com/v1/search?query={query}&per_page=10&page=1&orientation=landscape&size=medium",
            headers={"Authorization": PEXELS_API_KEY}, timeout=10
        )
        photos = r.json().get("photos", [])
        if photos:
            # seedを使って同じ業種でも毎回違う画像を選択
            idx = seed % len(photos)
            return photos[idx]["src"]["large"]
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

    # バリュエーション算出（全案件で実施）
    valuation = calc_valuation(deal['title'], press_text)

    # LLM生成はランキング後に実施するため、ここではスキップ
    article_body = ""
    analysis_comment = ""

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

    pro_title = f"【{industry}】{deal['title']}"

    art = {
        "rank":             i + 1,
        "title":            deal["title"],
        "pro_title":        pro_title,
        "url":              deal["url"],
        "press_url":        press_url,
        "press_text":       press_text,
        "source":           deal["source"],
        "industry":         industry,
        "image":            img_url,
        "article_body":     article_body,
        "analysis_comment": analysis_comment,
        "valuation":        valuation,
        "charts":           charts,
        "companies":        companies_data,
        "financials":       financials_all,
        "text_blocks":      text_blocks_all,
        "has_financials":   bool(financials_all),
    }

    headline_data.append(art)

# ======================
# ピックアップ5件のランキング（スコアリング）
# 優先度: ① 取得価額が公表 → ② 金額が大きい → ③ 話題性（TOB/MBO/大手企業）
# ======================
def calc_deal_score(art):
    """案件のピックアップ優先度スコアを算出"""
    score = 0
    val = art.get("valuation", {})
    raw = val.get("raw", {})
    title = art.get("title", "")

    # ① 取得価額が公表されている（最優先、+1000点）
    ap = raw.get("acquisition_price", 0)
    if ap > 0:
        score += 1000
        # 金額が大きいほど加点（億円単位で対数スコア）
        import math
        score += min(int(math.log10(max(ap, 1)) * 50), 500)

    # ② 売り手の財務数値が判明している（+200点）
    if raw.get("revenue"):
        score += 200
    if raw.get("operating_income"):
        score += 100

    # ③ 話題性の高いスキーム（+300点）
    if "TOB" in title or "公開買付" in title:
        score += 300
    elif "MBO" in title:
        score += 250
    elif "経営統合" in title or "合併" in title:
        score += 200
    elif "完全子会社化" in title:
        score += 150

    # ④ 大手企業・有名企業の関与（証券コード付き = 上場企業）
    if "＜" in title and "＞" in title:
        score += 50

    # ⑤ LLM記事が生成されている
    if art.get("article_body"):
        score += 100

    return score

# 全案件をスコアリングしてソート
for art in headline_data:
    art["_score"] = calc_deal_score(art)

ranked = sorted(headline_data, key=lambda x: x["_score"], reverse=True)
featured_data = ranked[:5]

# ランクを振り直す
for i, art in enumerate(featured_data):
    art["rank"] = i + 1
    print(f"  ピックアップ#{i+1}: [score={art['_score']}] {art['pro_title'][:50]}")

# featured以外のheadlineにもrank情報をクリア
for art in headline_data:
    if art not in featured_data:
        art["rank"] = 0

# ======================
# ピックアップ5件のLLM記事・分析コメント生成
# ======================
print("\n=== ピックアップ5件のLLM記事生成 ===")
for art in featured_data:
    print(f"\n  [{art['rank']}] {art['pro_title'][:50]}")

    print(f"  LLM記事生成中...")
    art["article_body"] = generate_article(
        {"title": art["title"], "url": art["url"]},
        art.get("press_text", ""),
        art.get("financials", []),
        art["companies"][0].get("analysis", {}) if art.get("companies") else {},
        art.get("text_blocks", {})
    )

    print(f"  LLM分析コメント生成中...")
    art["analysis_comment"] = generate_analysis_comment(
        {"title": art["title"]},
        art.get("financials", []),
        art.get("text_blocks", {}),
        art.get("companies", []),
        art.get("press_text", "")
    )
    time.sleep(1)

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
page_summary = f"本日{slot_jp}のM&Aニュース。TDnet・公式プレスリリースをもとにAIが分析。財務データ・株価チャート付き。"

# 本文
body = f"## {slot_jp}の注目5案件\n\n"
for art in featured_data:
    body += f"### {art['rank']}. {art['pro_title']}\n\n"
    body += f"**業種分類（経産省）：** {art['industry']}\n\n"
    if art["article_body"]:
        body += art["article_body"] + "\n\n"
    # バリュエーション分析テーブル
    val = art.get("valuation", {})
    val_rows = []
    if val.get("raw", {}).get("acquisition_price"):
        val_rows.append(f"| 取得価額 | {val['raw']['acquisition_price']/1e8:.1f}億円 |")
    if val.get("ev_revenue"):
        val_rows.append(f"| EV/売上高倍率 | {val['ev_revenue']}x |")
    if val.get("ev_ebitda_approx"):
        val_rows.append(f"| EV/EBITDA（近似） | {val['ev_ebitda_approx']}x |")
    if val.get("pbr"):
        val_rows.append(f"| PBR | {val['pbr']}x |")
    if val.get("per"):
        val_rows.append(f"| PER | {val['per']}x |")
    if val.get("op_margin"):
        val_rows.append(f"| 営業利益率 | {val['op_margin']}% |")
    if val_rows:
        body += "**📈 バリュエーション分析**\n\n"
        body += "| 指標 | 値 |\n|:---|:---|\n"
        body += "\n".join(val_rows) + "\n\n"
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
