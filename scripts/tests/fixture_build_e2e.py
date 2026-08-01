#!/usr/bin/env python3
"""Dựng fixture E2E cho verifier: CTD với data thật (forensic) + report tổng hợp.
Chạy:  python3 fixture_build_e2e.py
Sau đó: python3 ../independent_verifier.py CTD /tmp/ervn_e2e/CTD/CTD_Complete_Report.html
Kỳ vọng: 67/67 PASS (100% recall) — regression test cho V5 wave.
"""
import json, os, math, random, datetime, shutil

FIX = "/tmp/ervn_e2e/CTD"
SRC = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/forensic-audit-v1.0.1b-runs/CTD/data"

shutil.rmtree("/tmp/ervn_e2e", ignore_errors=True)
os.makedirs(FIX + "/data", exist_ok=True)
os.makedirs(FIX + "/.task-state", exist_ok=True)
os.makedirs(FIX + "/source-pack", exist_ok=True)

# 1) data files thật
for f in ("financials.json", "balance_sheet.json", "cash_flow.json"):
    shutil.copy(os.path.join(SRC, f), os.path.join(FIX, "data", f))

fin = json.load(open(os.path.join(FIX, "data", "financials.json")))
bs = json.load(open(os.path.join(FIX, "data", "balance_sheet.json")))
cf = json.load(open(os.path.join(FIX, "data", "cash_flow.json")))
PRICE = 71700.0
SHARES = 111823220.0
CAPEX = {y: abs(float(cf["Purchases of fixed assets and other long term assets"][y])) / 1e9 for y in "2021 2022 2023 2024 2025".split()}
BVPS = float(fin["equity_ty"]["2025"]) * 1e9 / SHARES
GRAHAM = math.sqrt(22.5 * float(fin["eps_vnd"]["2025"]) * BVPS)
MC_TY = PRICE * SHARES / 1e9
ROE25 = float(fin["npatmi_ty"]["2025"]) / float(fin["equity_ty"]["2025"]) * 100
NM25 = float(fin["npatmi_ty"]["2025"]) / float(fin["revenue_ty"]["2025"]) * 100
YOY_REV = float(fin["revenue_ty"]["2025"]) / float(fin["revenue_ty"]["2024"]) - 1
YOY_NPAT = float(fin["npatmi_ty"]["2025"]) / float(fin["npatmi_ty"]["2024"]) - 1
CAGR = (float(fin["revenue_ty"]["2025"]) / float(fin["revenue_ty"]["2021"])) ** 0.25 - 1
PE = PRICE / float(fin["eps_vnd"]["2025"])
PB = PRICE / BVPS
TODAY = datetime.date.today()
print(f"BVPS={BVPS:.0f} GRAHAM={GRAHAM:.0f} MC={MC_TY:.1f}tỷ ROE={ROE25:.2f}% NM={NM25:.2f}% "
      f"YoY_REV={YOY_REV*100:.1f}% YoY_NPAT={YOY_NPAT*100:.1f}% CAGR={CAGR*100:.1f}% PE={PE:.2f} PB={PB:.2f}")

# 2) data/overview.json
json.dump({"current_price": PRICE, "issue_share": SHARES, "price_fetched_at": f"{TODAY.isoformat()}T09:00:00"},
          open(FIX + "/data/overview.json", "w"), indent=2, ensure_ascii=False)

# 3) data/peers.json
peers = {"source": "vnstock_data_sponsor_gold",
         "peers": [{"ticker": "HBC", "pe": 15.2, "pb": 0.8, "cagr_3y": -15.0, "market_cap_b": 1200},
                   {"ticker": "C4G", "pe": 8.5, "pb": 1.2, "cagr_3y": 10.0, "market_cap_b": 800},
                   {"ticker": "FCN", "pe": 10.5, "pb": 1.0, "cagr_3y": 5.0, "market_cap_b": 1500}]}
json.dump(peers, open(FIX + "/data/peers.json", "w"), indent=2, ensure_ascii=False)

# 4) news_digest.json (root — theo verify_news_window)
articles = [
    {"title": "Coteccons trúng thầu dự án lớn tại TP.HCM trong quý vừa qua", "url": "https://cafef.vn/coteccons-trung-thau-du-an-lon-20260715.html",
     "source": "cafef.vn", "date": (TODAY - datetime.timedelta(days=3)).isoformat(), "category": "biz"},
    {"title": "Ngành xây dựng hồi phục nhờ giải ngân đầu tư công kỳ vọng tăng", "url": "https://vnexpress.net/nganh-xay-dung-hoi-phuc-20260718.html",
     "source": "vnexpress.net", "date": (TODAY - datetime.timedelta(days=7)).isoformat(), "category": "sector"},
    {"title": "Coteccons công bố kế hoạch kinh doanh năm tài chính mới", "url": "https://vietstock.vn/coteccons-cong-bo-ke-hoach-20260725.html",
     "source": "vietstock.vn", "date": (TODAY - datetime.timedelta(days=12)).isoformat(), "category": "disclosure"},
]
json.dump({"fetched_at": TODAY.isoformat(), "window_days": 30, "articles": articles},
          open(FIX + "/news_digest.json", "w"), indent=2, ensure_ascii=False)

# 5) data/technical_active.json
json.dump({"tech_score": 3, "verdict": "BUY", "last_close": PRICE, "source": "price_weekly.json"},
          open(FIX + "/data/technical_active.json", "w"), indent=2, ensure_ascii=False)

# 6) company_profile.json
json.dump({"ticker": "CTD", "company_name": "Coteccons Construction", "sector": "Xây dựng"},
          open(FIX + "/company_profile.json", "w"), indent=2, ensure_ascii=False)

# 7) price_daily.json + price_weekly.json (synthetic deterministic)
random.seed(42)
prices = []
p = 70000.0
for i in range(130):
    p *= (1 + random.uniform(-0.015, 0.015))
    prices.append(round(p, 0))
# ép giá cuối = PRICE
prices[-1] = PRICE
json.dump([{"date": (TODAY - datetime.timedelta(days=130 - i)).isoformat(), "close": v} for i, v in enumerate(prices)],
          open(FIX + "/data/price_daily.json", "w"), indent=2)
wk = [{"date": (TODAY - datetime.timedelta(weeks=52 - i)).isoformat(), "close": prices[i * 2]} for i in range(52)]
json.dump(wk, open(FIX + "/data/price_weekly.json", "w"), indent=2)

# 8) source-pack CSVs (cho REQ-059 spot-check + REQ-062 period integrity)
import csv
income_rows = [["report_period", "ticker", "Net sales", "Attributable to parent company", "EPS basic"],
               ["year", "CTD", "9077920000000", "24110000000", "323"],
               ["year", "CTD", "14538690000000", "20790000000", "280"],
               ["year", "CTD", "16529940000000", "187920000000", "2267"],
               ["year", "CTD", "22905860000000", "371400000000", "3729"],
               ["year", "CTD", "30699049000000", "781350000000", "7736"]]
with open(FIX + "/source-pack/income_statement_sponsor.csv", "w", newline="") as f:
    csv.writer(f).writerows(income_rows)
bal_rows = [["report_period", "ticker", "Total assets", "Owner's equity"],
            ["year", "CTD", "13924612376531", "8247560732814"],
            ["year", "CTD", "18967071946667", "8213962257245"],
            ["year", "CTD", "21651893357725", "8407432424176"],
            ["year", "CTD", "27076862120048", "8688770305789"],
            ["year", "CTD", "34442241560980", "9385337105554"]]
with open(FIX + "/source-pack/balance_sheet_sponsor.csv", "w", newline="") as f:
    csv.writer(f).writerows(bal_rows)
cash_rows = [["report_period", "ticker", "Purchases of fixed assets"],
             ["year", "CTD", "47079581566"], ["year", "CTD", "194756167542"],
             ["year", "CTD", "415208683881"], ["year", "CTD", "439083556695"],
             ["year", "CTD", "622700306796"]]
with open(FIX + "/source-pack/cash_flow_sponsor.csv", "w", newline="") as f:
    csv.writer(f).writerows(cash_rows)

# 9) task-state.json
task_state = {
    "ticker": "CTD",
    "investment_amount": 800000000,
    "fiscal_year_type": "calendar",
    "phases": {
        "phase0_sponsor": {"status": "completed", "result": {"tier": "golden", "periods": 41, "sponsor_ok": True,
                                                             "investment_amount": 800000000, "fiscal_year_type": "calendar",
                                                             "api_source": "vnstock_data_sponsor_gold", "version": "vnstock==3.5.1"}},
        "phase1_data": {"status": "completed", "result": {"data_source": "sponsor", "periods": 41,
                                                          "years": [2021, 2022, 2023, 2024, 2025],
                                                          "price_fetched_at": f"{TODAY.isoformat()}T09:00:00",
                                                          "fiscal_year_type": "calendar",
                                                          "split_audit": {"cp_consistent": True, "method": "back-calc CP=LNST/EPS"}}},
        "phase2_fundamental": {"status": "completed", "result": {"eps": fin["eps_vnd"]["2025"], "roe": round(ROE25, 2),
                                                                  "cagr": round(CAGR, 1)}},
        "phase3_valuation": {"status": "completed", "result": {
            "pe": round(PE, 2), "pb": round(PB, 2), "ev_ebitda": None, "ps": None, "pcf": None,
            "dcf_per_share": 82000, "dcf_note": None, "graham_number": round(GRAHAM, 0),
            "converge_median": 82000, "verdict": "UNDERVALUED",
            "targets": {"pe_method": 85000, "pb_method": 80000, "analyst": 82000, "dcf_alt": 82000}}},
        "phase4a_tech_active": {"status": "completed", "result": {"tech_score": 3, "verdict": "BUY",
                                                                  "last_close": PRICE, "rsi14": None, "ma50": None}},
        "phase4b_tech_profile": {"status": "completed", "result": {"archetype": "cyclical_contractor",
                                                                   "volatility": "medium", "drawdown_52w": -28.5}},
        "phase5_news": {"status": "completed", "result": {"total_news": 3, "sentiment": {"positive": 2, "negative": 0, "neutral": 1},
                                                          "sentiment_score": 67, "categories": {"biz": 1, "sector": 1, "disclosure": 1}}},
        "phase6_dashboard": {"status": "completed", "result": {"artifact_path": FIX + "/CTD_Complete_Report.html"}},
    },
    "artifact_path": FIX + "/CTD_Complete_Report.html",
}
json.dump(task_state, open(FIX + "/.task-state/task-state.json", "w"), indent=2, ensure_ascii=False)

# 10) verified-dashboard-data.json
contract = {
    "company": "Coteccons Construction Joint Stock Company",
    "ticker": "CTD", "price": PRICE, "shares": SHARES, "market_cap": PRICE * SHARES,
    "periods": [2021, 2022, 2023, 2024, 2025],
    "financials": {"years": [2021, 2022, 2023, 2024, 2025],
                   "revenue": [9077.92, 14538.69, 16529.94, 22905.86, 30699.1],
                   "netProfit": [24.11, 20.79, 187.92, 371.4, 781.35],
                   "eps": [323, 280, 2267, 3729, 7736],
                   "totalAssets": [13924.62, 18967.07, 21651.89, 27076.86, 34442.24],
                   "equity": [8247.56, 8213.96, 8407.43, 8688.77, 9385.34],
                   "capex": [round(CAPEX[y], 2) for y in "2021 2022 2023 2024 2025".split()]},
    "valuation": {"pe": round(PE, 2), "pb": round(PB, 2), "price": PRICE},
    "technical": {"mode": "ACTIVE", "tech_score": 3, "scale_min": -6, "scale_max": 6, "verdict": "BUY",
                  "source_file": "technical_active.json", "verified": True},
    "company_profile": {"ticker": "CTD", "company_name": "Coteccons Construction", "sector": "Xây dựng"},
    "references": [{"id": i, "title": f"BCTC kiểm toán {y}", "date": str(y + 1), "url": "(standard)"}
                   for i, y in enumerate([2021, 2022, 2023, 2024, 2025])] + 
                  [{"id": i, "title": "Báo cáo ngành xây dựng", "date": "2026", "url": "https://fiingroup.vn"} for i in range(6, 11)],
    "_provenance": {"built_at": f"{TODAY.isoformat()}T10:00:00", "source": "build_data_contract.py from source-pack CSVs",
                    "unit": "tỷ VND (financials arrays); VND (price, eps)", "verification_status": "verified"},
}
json.dump(contract, open(FIX + "/verified-dashboard-data.json", "w"), indent=2, ensure_ascii=False)

# 11) Report HTML
def sec(sid, title, body, extra=""):
    return f'<section id="{sid}" class="section"><div class="section-title"><h2>{title}</h2></div>{extra}{body}</section>'

hero = sec("sec-hero", "Hero",
    "<p>CTD — Coteccons Construction | Giá hiện tại <b>71.700 VND</b> (theo vnstock) | "
    "Doanh thu: <b>30.699 tỷ</b> (năm 2025, theo BCTC) | Vốn hóa <b>8.018 tỷ</b> (theo giá đóng cửa)</p>")
exec_ = sec("sec-exec", "TL;DR",
    "<p>Split-adjusted: Bẫy 5B đã được cross-check — cổ phiếu lưu hành nhất quán (theo BCTC). "
    "Doanh thu đạt <b>30.699 tỷ đồng</b> trong năm 2025, tăng 34% so với năm 2024 (theo BCTC kiểm toán). "
    "Lợi nhuận sau thuế đạt <b>781 tỷ đồng</b> trong năm 2025 (theo BCTC). ROE <b>8.3%</b> (tính từ BCTC). "
    "P/E <b>9.3x</b>, P/B <b>0.85x</b> (theo vnstock). EPS đạt <b>7.736 đồng</b> (năm 2025, theo BCTC). "
    "Triển vọng tích cực và khả quan nhờ hồi phục ngành xây dựng, kỳ vọng tăng trưởng doanh thu tiếp tục nhờ đầu tư công.</p>")
biz = sec("sec-biz", "Mô hình kinh doanh",
    "<p>Coteccons là nhà thầu xây dựng với năng lực thi công dân dụng và hạ tầng (theo công bố của công ty). "
    "Doanh thu chủ yếu từ mảng xây dựng, khách hàng gồm chủ đầu tư bất động sản và khu công nghiệp. "
    "Năng lực quản lý dự án và chuỗi cung ứng vật tư là lợi thế cạnh tranh chính của công ty theo đánh giá của ban lãnh đạo. "
    "Công ty đang mở rộng thị trường ra khu vực miền Trung và miền Bắc, tận dụng làn sóng đầu tư hạ tầng quốc gia.</p>")
industry = sec("sec-industry", "Ngành",
    "<p>Ngành xây dựng đang hồi phục nhờ giải ngân đầu tư công và nguồn vốn bất động sản dần được khơi thông. "
    "Theo báo cáo của FiinGroup, thị trường xây dựng hạ tầng có triển vọng tích cực trong các năm tới. "
    "Cạnh tranh ngành tập trung ở nhóm nhà thầu lớn có năng lực tài chính và kỹ thuật. "
    "Chi phí vật liệu đầu vào biến động là yếu tố tác động chính đến biên lợi nhuận của các nhà thầu trong ngành (theo báo cáo ngành FiinGroup năm 2025).</p>")
history = sec("sec-history", "5 năm",
    "<p>Trong giai đoạn 5 năm gần nhất, hoạt động kinh doanh của Coteccons cải thiện rõ rệt qua từng năm "
    "với quy mô doanh thu tăng gấp hơn ba lần so với năm 2021 (nguồn: BCTC kiểm toán từng năm). "
    "Lợi nhuận sau thuế giai đoạn 2023-2025 phục hồi mạnh sau giai đoạn khó khăn 2021-2022, phản ánh việc "
    "tái cấu trúc danh mục hợp đồng và cải thiện quản trị rủi ro của công ty theo báo cáo thường niên.</p>")
segment = sec("sec-segment", "Segment",
    "<p>Mảng xây dựng là trọng tâm doanh thu của Coteccons (theo BCTC). Mảng bất động sản khu công nghiệp "
    "đang được phát triển dần và kỳ vọng đóng góp thêm trong trung hạn theo kế hoạch của công ty. "
    "Công ty tập trung khai thác thị trường phía Nam, nơi có nhiều dự án nhà ở và khu công nghiệp lớn đang triển khai.</p>")
thesis = sec("sec-thesis", "Thesis",
    "<p>Luận điểm đầu tư: ngành hồi phục nhờ đầu tư công, backlog của công ty cải thiện qua các quý, "
    "biên lợi nhuận ròng <b>2.5%</b> (tính từ BCTC 2025) còn dư địa tăng khi giá vật liệu ổn định. "
    "Cổ phiếu giao dịch tại P/E <b>9.3x</b> (theo vnstock) phản ánh mức định giá chưa cao so với tiềm năng tăng trưởng lợi nhuận giai đoạn tới.</p>")
val = sec("sec-valuation", "Định giá",
    "<p>Định giá theo BCTC và vnstock: P/E <b>9.3x</b>, P/B <b>0.85x</b>. "
    "Giá hợp lý theo nhiều phương pháp ước tính khoảng <b>82.000 đồng</b> (theo DCF và PE-implied). "
    "Phương pháp DCF dựa trên giả định dòng tiền tăng trưởng ổn định, phương pháp so sánh P/E dựa trên "
    "mức bội số trung bình của nhóm ngành theo vnstock. Các mức giá này là ước tính phân tích, "
    "không phải cam kết giá giao dịch thực tế trên thị trường chứng khoán.</p>"
    "<div class=\"val-card\"><span class=\"price\">82.000</span><span class=\"price\">85.000</span><span class=\"price\">80.000</span></div>")
peer = sec("sec-peer", "Peer Comparison",
    "<p>So sánh peer (nguồn: peers.json từ vnstock): HBC P/E <b>15.2x</b>, C4G P/B <b>1.2x</b>, FCN P/E <b>10.5x</b>. "
    "Các peer có quy mô nhỏ hơn CTD về vốn hóa, phản ánh vị thế của Coteccons trong nhóm nhà thầu niêm yết.</p>")
bs_sec = sec("sec-bs", "BS & FCF",
    "<p>Tổng tài sản 2025 đạt <b>34.442 tỷ đồng</b> (theo BCTC). Vốn chủ sở hữu 2025 đạt <b>9.385 tỷ đồng</b> (theo BCTC). "
    "Cấu trúc tài sản chủ yếu là khoản phải thu khách hàng và hàng tồn kho, phù hợp với đặc thù ngành xây dựng. "
    "Hệ số nợ/vốn chủ sở hữu duy trì ở mức kiểm soát được theo đánh giá của ban lãnh đạo.</p>")
risk = sec("sec-risk", "Rủi ro",
    "<p>Rủi ro giảm giá: max drawdown 52 tuần của cổ phiếu là <b>-28.5%</b> (theo data giá vnstock). "
    "Rủi ro biến động giá vật liệu xây dựng và thiếu hụt nguồn lao động có thể ảnh hưởng tiến độ thi công. "
    "Rủi ro cạnh tranh từ các nhà thầu khác trong đấu thầu các dự án lớn. Rủi ro thanh khoản cổ phiếu ở mức trung bình thấp.</p>")
view33 = sec("sec-33k", "Góc nhìn khoản đầu tư",
    "<p>Góc nhìn khoản đầu tư <b>800 triệu đồng</b> (theo quy mô vốn người dùng cung cấp): với giá <b>71.700 đồng</b>, "
    "nhà đầu tư có thể phân bổ vào khoảng 11.000 cổ phiếu CTD. Danh mục nên đa dạng hóa và giữ tỷ trọng hợp lý theo khẩu vị rủi ro cá nhân.</p>")
scenario = sec("sec-scenario", "Kịch bản",
    "<p>Kịch bản cơ sở: giá hợp lý <b>82.000 đồng</b> (ước tính từ DCF và PE-implied). "
    "Kịch bản tích cực: <b>90.000 đồng</b> (giả định biên lợi nhuận cải thiện nhanh hơn kỳ vọng). "
    "Kịch bản tiêu cực: <b>60.000 đồng</b> (rủi ro backlog giảm do cạnh tranh). Mỗi kịch bản là giả định phân tích, không phải cam kết.</p>")
checklist = sec("sec-checklist", "Checklist",
    "<ul><li>Đã đối chiếu số liệu tài chính với BCTC kiểm toán.</li><li>Đã kiểm tra tăng vốn và chia tách cổ phiếu.</li>"
    "<li>Đã đối chiếu giá với nguồn dữ liệu vnstock.</li><li>Đã trích dẫn nguồn cho các số liệu chính.</li>"
    "<li>Các khuyến nghị chỉ mang tính tham khảo, không phải lời khuyên đầu tư.</li></ul>")
ins1 = sec("sec-insight-1", "Insight 1",
    "<p>Insight 1 — Quy mô doanh thu bứt phá: Doanh thu tăng trưởng <b>34%</b> trong năm 2025 so với năm 2024 (theo BCTC), "
    "đạt 30.699 tỷ đồng nhờ backlog tích lũy từ giai đoạn trước được triển khai. Điều này cho thấy chu kỳ tăng trưởng "
    "của công ty vẫn đang tiếp diễn khi ngành xây dựng hồi phục và các dự án mới được ký kết liên tục trong các quý gần đây. "
    "Với nền tảng khách hàng đa dạng gồm chủ đầu tư khu công nghiệp, nhà ở và hạ tầng, cùng năng lực thi công "
    "lớn hàng đầu thị trường, công ty có dư địa duy trì tốc độ tăng trưởng trong các năm tới theo đánh giá của "
    "ban lãnh đạo và kế hoạch kinh doanh được công bố tại ĐHCĐ thường niên vừa qua.</p>")
ins2 = sec("sec-insight-2", "Insight 2",
    "<p>Insight 2 — Lợi nhuận phục hồi: Lợi nhuận sau thuế tăng <b>110%</b> trong năm 2025 so với năm 2024 (theo BCTC), "
    "đạt 781 tỷ đồng, phản ánh hiệu quả tái cấu trúc chi phí và cải thiện quản trị rủi ro hợp đồng của công ty. "
    "Biên lợi nhuận ròng 2.5% tuy còn thấp so với đỉnh lịch sử nhưng đang đi đúng quỹ đạo phục hồi qua từng quý. "
    "Nếu giá vật liệu ổn định và tiến độ thi công thuận lợi, biên lợi nhuận có thể tiếp tục cải thiện trong các "
    "quý tới theo kế hoạch kinh doanh và định hướng của ban lãnh đạo được trình bày tại buổi gặp nhà đầu tư gần nhất.</p>")
ins3 = sec("sec-insight-3", "Insight 3",
    "<p>Insight 3 — Tăng trưởng kép: CAGR doanh thu giai đoạn 2021-2025 đạt <b>35.6%</b> (tính từ BCTC), "
    "là mức tăng trưởng ấn tượng so với mặt bằng chung của ngành xây dựng trong cùng giai đoạn. "
    "Tốc độ này nhờ quy mô nền nhỏ của năm 2021 (doanh thu năm đó chỉ 9.078 tỷ, theo BCTC) và sự phục hồi "
    "mạnh của thị trường bất động sản phía Nam trong giai đoạn sau. "
    "Nhà đầu tư cần lưu ý rằng tăng trưởng quá khứ không đảm bảo tăng trưởng tương lai, và mức CAGR cao một phần "
    "đến từ hiệu ứng nền thấp theo phân tích của bộ phận nghiên cứu, do đó cần theo dõi chất lượng backlog "
    "và khả năng ký mới hợp đồng trong các quý tiếp theo để đánh giá tính bền vững của tăng trưởng.</p>")
tech = sec("sec-tech", "Technical",
    "<p>Tech Score <b>3/6</b>. Verdict: <span data-verdict=\"BUY\">BUY</span>. "
    "RSI(14) đang ở vùng trung tính, MACD chưa cho tín hiệu rõ ràng, giá đang giao dịch trên đường MA50. "
    "Khối lượng giao dịch duy trì ổn định trong các phiên gần đây.</p>")
techp = sec("sec-tech-profile", "Profile",
    "<p>Phân tích kỹ thuật mang tính tham khảo. Nội dung không phải là khuyến nghị mua/bán cổ phiếu và "
    "không cấu thành lời khuyên đầu tư. Nhà đầu tư nên tự đánh giá và tham vấn chuyên gia trước khi quyết định. "
    "Các chỉ báo kỹ thuật được tính từ dữ liệu giá lịch sử và không dự báo được các biến động bất thường của thị trường.</p>")
analyst = sec("sec-analyst", "Analyst",
    "<p>Chưa ghi nhận khuyến nghị mới từ các tổ chức phân tích trong 30 ngày qua (theo công bố công khai). "
    "Khuyến nghị của các tổ chức khác nhau có thể dựa trên giả định và phương pháp định giá khác nhau, "
    "nhà đầu tư cần tự kiểm chứng trước khi sử dụng.</p>")
glossary = sec("sec-glossary", "Thuật ngữ",
    "<p>P/E: giá trên lợi nhuận mỗi cổ phiếu. P/B: giá trên giá trị sổ sách mỗi cổ phiếu. "
    "ROE: tỷ suất lợi nhuận trên vốn chủ sở hữu. CAGR: tốc độ tăng trưởng kép hằng năm. "
    "EPS: lợi nhuận trên mỗi cổ phiếu. Backlog: giá trị hợp đồng chưa thực hiện. "
    "Drawdown: mức sụt giảm từ đỉnh đến đáy của giá cổ phiếu trong một giai đoạn.</p>")
refs = "\n".join(
    [f'<li id="ref-{i}">BCTC kiểm toán {y} của Coteccons Construction — công bố năm {y+1} (nguồn chuẩn, theo SSC)</li>' for i, y in enumerate([2021, 2022, 2023, 2024, 2025])] +
    [f'<li id="ref-{i}">Báo cáo ngành xây dựng {2026 if i % 2 else 2025} của FiinGroup — truy cập 2026</li>' for i in range(6, 11)])
src_sec = sec("sec-source", "Nguồn",
    f"<ol>{refs}</ol><p class=\"faint\">Nguồn dữ liệu chính: BCTC kiểm toán, vnstock (dữ liệu giá), công bố của công ty. Số liệu 2026 là ước tính.</p>")

charts_html = ""
charts_js = ""
chart_defs = [
    ("chart-1", "revenue", "Doanh thu"), ("chart-2", "netProfit", "Lợi nhuận"),
    ("chart-3", "eps", "EPS"), ("chart-4", "capex", "Capex"),
    ("chart-5", "totalAssets", "Tổng tài sản"), ("chart-6", "equity", "Vốn chủ sở hữu"),
]
for cid, key, label in chart_defs:
    charts_html += f'<div class="chart-wrap"><canvas id="{cid}"></canvas></div>'
    charts_js += f'new Chart($("{cid}"), {{type: "bar", data: {{labels: DATA.years, datasets: [{{label: "{label}", data: DATA.{key}}}]}}}});'
for i in range(7, 11):
    charts_html += f'<div class="chart-wrap"><canvas id="chart-{i}"></canvas></div>'
    charts_js += f'new Chart($("chart-{i}"), {{type: "line", data: {{labels: DATA.years, datasets: [{{label: "Series", data: DATA.revenue}}]}}}});'

data_js = f"""const DATA = {{
  "years": [2021, 2022, 2023, 2024, 2025],
  "revenue": [9077.92, 14538.69, 16529.94, 22905.86, 30699.1],
  "netProfit": [24.11, 20.79, 187.92, 371.4, 781.35],
  "netIncome": [24.11, 20.79, 187.92, 371.4, 781.35],
  "eps": [323, 280, 2267, 3729, 7736],
  "totalAssets": [13924.62, 18967.07, 21651.89, 27076.86, 34442.24],
  "equity": [8247.56, 8213.96, 8407.43, 8688.77, 9385.34],
  "liabilities": [{', '.join(str(round(bs["Total Assets"][str(y)] - fin["equity_ty"][str(y)], 2)) for y in '2021 2022 2023 2024 2025'.split())}],
  "capex": [{', '.join(str(round(CAPEX[y], 2)) for y in '2021 2022 2023 2024 2025'.split())}],
  "price": 71700,
  "price_fetched_at": "{TODAY.isoformat()}T09:00:00",
  "max_drawdown_52w": -28.5,
  "techRSI": [40, 45, 38, 52, 48, 35, 42, 50, 55, 47, 39, 44, 51, 48, 36, 43, 49, 53, 41, 46, 38, 50, 44, 37, 48, 52, 45, 40, 47, 43, 39, 51, 46, 42, 48, 55, 41, 37, 49, 44, 50, 38, 46, 43, 52, 40, 48, 35, 45, 50, 42, 47]
}};
document.addEventListener("DOMContentLoaded", function () {{ {charts_js} }});"""

html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>CTD — Coteccons Construction | Báo cáo phân tích</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/jquery@3"></script>
<style>.tbl{{border-collapse:collapse;width:100%}}.tbl td,.tbl th{{border:1px solid #444;padding:4px}}[ref-id]{{display:none}}</style>
</head>
<body>
{hero}
{exec_}
{biz}
{industry}
{history}
{segment}
{thesis}
{val}
{peer}
{bs_sec}
{risk}
{view33}
{scenario}
{checklist}
{ins1}
{ins2}
{ins3}
{tech}
{techp}
{analyst}
{glossary}
{src_sec}
{charts_html}
<script>
{data_js}
</script>
</body>
</html>"""

with open(FIX + "/CTD_Complete_Report.html", "w") as f:
    f.write(html)

print("Fixture built at", FIX)
print("GRAHAM:", round(GRAHAM, 0), "| PE:", round(PE, 2), "| PB:", round(PB, 2))
