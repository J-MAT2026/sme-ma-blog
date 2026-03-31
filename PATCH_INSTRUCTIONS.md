# app.py 修正パッチ手順書
# ================================================
# 修正箇所は3つ。以下の「BEFORE → AFTER」で置換する。
# ================================================

# ============================================
# 修正1: max_tokens 引き上げ（記事途切れ対策）
# ============================================
# 場所: groq_generate() 関数内（約390行目付近）
#
# BEFORE:
#             "max_tokens": 2000,
#
# AFTER:
#             "max_tokens": 3500,


# ============================================
# 修正2: スロット判定を2回に変更（昼刊を廃止）
# ============================================
# 場所: slot_hour 判定部分（約80行目付近）
#
# BEFORE:
# slot_hour = now.hour
# if slot_hour < 11:
#     slot = "morning"
#     slot_jp = "朝刊"
# elif slot_hour < 15:
#     slot = "noon"
#     slot_jp = "昼刊"
# else:
#     slot = "evening"
#     slot_jp = "夕刊"
#
# AFTER:
# slot_hour = now.hour
# if slot_hour < 13:
#     slot = "morning"
#     slot_jp = "朝刊"
# else:
#     slot = "evening"
#     slot_jp = "夕刊"


# ============================================
# 修正3: 企業名抽出 → 証券コード直接抽出に変更
#         （EDINETDB連携修正・最重要）
# ============================================
# 場所: 「各案件を処理」ループ内（約700行目付近）
# company_patterns〜EDINETDB照合ループを丸ごと置換。
#
# 以下の BEFORE ブロック全体を AFTER ブロックで置換する。
#
# === BEFORE（ここから）===
#
#     # 企業名抽出（簡易）
#     company_patterns = [
#         r'([^\s、。「」【】]{2,15}(?:株式会社|ホールディングス|ＨＤ|HD|グループ))',
#         r'((?:株式会社)[^\s、。「」【】]{2,12})',
#         r'([^\s、。「」【】]{3,8}＜\d{4}＞)',
#     ]
#     company_names = []
#     for pat in company_patterns:
#         matches = re.findall(pat, deal["title"])
#         company_names.extend(matches)
#     company_names = list(dict.fromkeys(company_names))[:3]
#     print(f"  企業名: {company_names}")
#
#     # EDINETDB照合
#     companies_data = []
#     financials_all = []
#     text_blocks_all = {}
#     sec_codes = []
#     for cname in company_names[:2]:
#         co = edinetdb_search(cname)
#         if co:
#             ec = co.get("edinet_code","")
#             sc = co.get("sec_code","")
#             fins = edinetdb_financials(ec)
#             ana = edinetdb_analysis(ec)
#             txts = edinetdb_text_blocks(ec)
#             print(f"    EDINETDB: {co.get('name','')} ({ec}) score={ana.get('credit_score','N/A') if ana else 'N/A'}")
#             companies_data.append({"name": co.get("name",""), "edinet_code": ec, "sec_code": sc, "analysis": ana})
#             if fins:
#                 financials_all = fins
#             if txts:
#                 text_blocks_all = txts
#             if sc:
#                 sec_codes.append(sc)
#         time.sleep(0.5)
#
# === BEFORE（ここまで）===
#
#
# === AFTER（ここから）===

#     # 証券コード抽出（タイトルの＜XXXX＞から直接取得）
#     sec_code_matches = re.findall(r'＜(\w{4,5})＞', deal["title"])
#     print(f"  証券コード: {sec_code_matches}")
#
#     # EDINETDB照合（証券コードで検索）
#     companies_data = []
#     financials_all = []
#     text_blocks_all = {}
#     sec_codes = []
#     for scode in sec_code_matches[:2]:
#         co = edinetdb_search(scode)
#         if co:
#             ec = co.get("edinet_code","")
#             sc = co.get("sec_code","")
#             fins = edinetdb_financials(ec)
#             ana = edinetdb_analysis(ec)
#             txts = edinetdb_text_blocks(ec)
#             print(f"    EDINETDB: {co.get('name','')} ({ec}) score={ana.get('credit_score','N/A') if ana else 'N/A'}")
#             companies_data.append({"name": co.get("name",""), "edinet_code": ec, "sec_code": sc, "analysis": ana})
#             if fins:
#                 financials_all = fins
#             if txts:
#                 text_blocks_all = txts
#             if sc:
#                 sec_codes.append(sc)
#         else:
#             print(f"    EDINETDB: {scode} → ヒットなし")
#         time.sleep(0.5)
#
# === AFTER（ここまで）===
