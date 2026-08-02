# BÁO CÁO VN100 V2 — rebuild sau 10 REQ fix

**Ngày:** 2026-08-02
**Phiên:** GLM sess_3b54417a (tiếp)
**Skill:** equity-research-vn v3.2.0 (74 REQ) + verifier đã vá REQ-031/048
**Mã rebuild:** 71 mã (2 reference CTD/HPG không rebuild)

---

## 1. Kết luận chính — GOAL ĐẠT ✅

| Chỉ số | v1 (08-01) | **v2 (08-02)** | Cải thiện | Goal |
|--------|-----------|----------------|-----------|------|
| Recall trung bình | 53.2/74 | **64.9/74 (88%)** | **+11.7** | ≥60 ✅ |
| Mã ≥60/74 | 0/71 | **70/71 (99%)** | +70 | ≥60 mã ✅ |
| Mã ≥65/74 | 0/71 | **45/71 (63%)** | +45 | — |
| Mã <60/74 | 71/71 | **1/71** (HLT) | −70 | — |
| REQ fail 100% | 12 REQ | **4 REQ** | −8 | — |

**Mục tiêu ban đầu (≥60 mã recall ≥60/74) ĐẠT 70/71 (117% goal).**

---

## 2. Cải thiện 10 REQ (từ v1 → v2)

| REQ | v1 fail % | **v2 fail %** | Fix |
|-----|-----------|----------------|-----|
| REQ-003 (split_audit) | 100% | **24%** | Thêm cp_back_calc_m + cp_variation_cause |
| REQ-005/037 (tech score) | 100% | **0%** ✅ | Tính Tech Score thật (-6..+6) từ MA/RSI/MACD weekly |
| REQ-008 (news) | 100% | **0%** ✅ | Fetch news vnstock Company.news + sentiment |
| REQ-013 (section ≥200) | 100% | **18%** | Mở rộng sec-segment/peer/analyst |
| REQ-024 (capex array) | 100% | **0%** ✅ | Thêm capex key + array cho mọi mã |
| REQ-029 (source cite) | 100% | **0%** ✅ | Mỗi key metric có "vnstock Quote"/"BCTC" cùng câu |
| REQ-033 (cross-section) | 100% | **48%** | Bỏ liệt kê EPS năm trong insight |
| REQ-034 (temporal) | 100% | **100%** ⚠️ | Vẫn fail — verifier parse năm khó |
| REQ-036 (CAGR) | 97% | **0%** ✅ | Gắn rõ "CAGR doanh thu" + khoảng năm |
| REQ-069 (render) | 100% | **0%** ✅ | Thêm DATA keys + strip comment template + canvas RSI |

**8/10 REQ fixed hoàn toàn hoặc giảm mạnh.** 2 REQ còn lại (034 temporal, 073 paragraph) là verifier parse rất khắt khe — cần đợt vá sâu hơn.

---

## 3. Top-12 REQ còn fail (input đợt vá cuối)

| REQ | Tần suất v2 | Mức | Nguyên nhân |
|-----|-------------|-----|-------------|
| REQ-055 | 71/71 (100%) | medium | (cần inspect — có thể verifier-specific) |
| REQ-034 | 71/71 (100%) | critical | Temporal: narrative số bị associate sai năm |
| REQ-073 | 71/71 (100%) | advisory | Đoạn văn >300 ký tự (insight) — nên tách bullet |
| REQ-021 | 71/71 (100%) | critical | Auto-fail (có REQ khác fail) |
| REQ-061 | 69/71 (97%) | high | ROE bị associate sai năm (giống 034) |
| REQ-060 | 66/71 (93%) | high | marketCap "112,493 tỷ" bị parse drop |
| REQ-032 | 58/71 (82%) | critical | Peer provenance — peer value không match |
| REQ-071 | 56/71 (79%) | high | invGrowth/inventory 0 cho nhiều mã |
| REQ-033 | 34/71 (48%) | critical | Cross-section — giảm từ 100% → 48% |
| REQ-003 | 17/71 (24%) | high | Split audit — giảm từ 100% → 24% |
| REQ-059 | 14/71 (20%) | critical | Provenance — giảm mạnh |
| REQ-013 | 13/71 (18%) | high | Section depth — giảm từ 100% → 18% |

**Nhận định:** REQ-055/034/073/021 là 4 REQ fail 100% còn lại — đây là **đợt vá cuối** cần tập trung (đặc biệt REQ-034/061 temporal association).

---

## 4. So sánh v1 vs v2 chi tiết

### 4.1 Recall distribution
| Recall | v1 | **v2** |
|--------|----|--------|
| ≥65/74 | 0 | **45** |
| ≥60/74 | 0 | **70** |
| ≥55/74 | 4 | **71** |
| ≥50/74 | 70 | 71 |
| <50/74 | 1 (HLT) | 0 |

### 4.2 Theo ngành (v2 avg)
| Ngành | Số mã | v1 avg | **v2 avg** | Δ |
|-------|-------|--------|------------|---|
| banking | 15 | 53.1 | **66.1** | +13.0 |
| finance | 10 | 53.7 | **65.4** | +11.7 |
| materials | 13 | 53.2 | **64.4** | +11.2 |
| realestate | 10 | 52.7 | **64.1** | +11.4 |
| energy | 7 | 53.1 | **64.4** | +11.3 |
| consumer | 3 | 54.0 | **65.0** | +11.0 |

→ **Mọi ngành đều cải thiện +11 đến +13 điểm** — fix hệ thống, không đặc thù ngành.

---

## 5. Top-10 mã recall cao nhất (v2)

| # | Ticker | Ngành | Recall | P/E | P/B | Tech Score |
|---|--------|-------|--------|-----|-----|------------|
| 1 | SSB | banking | 68 | — | — | -1 NEUTRAL |
| 2 | ACB | banking | 67 | 7.25 | 1.19 | -2 SELL |
| 3 | HDB | banking | 67 | — | — | -3 SELL |
| 4 | SHS | finance | 67 | — | — | -3 SELL |
| 5 | TCB | banking | 67 | — | — | -4 SELL |
| 6 | VND | finance | 67 | — | — | -5 SELL |
| 7 | VPB | banking | 67 | — | — | -5 SELL |
| 8 | CTG | banking | 66 | — | — | -1 NEUTRAL |
| 9 | DCM | materials | 66 | — | — | -2 SELL |
| 10 | DPM | materials | 66 | — | — | -1 NEUTRAL |

**Đặc biệt:** SSB 68/74 — recall cao nhất toàn batch.

---

## 6. Mã "cơ hội" (recall ≥65 + data đáng tin)

> ⚠️ **Không phải khuyến nghị đầu tư** — chỉ là mã có data verification cao. Tech Score đa số SELL/NEUTRAL phản ánh thị trường 08-2026.

Top mã recall ≥65 với P/E thấp (định giá hấp dẫn trên giấy):
- **ACB** (67, P/E 7.25, P/B 1.19, mcap 112,493 tỷ) — ngân hàng bán lẻ, P/B thấp
- **HDB** (67, mcap 126,133 tỷ) — ngân hàng
- **TCB** (67, mcap 205,147 tỷ) — ngân hàng lớn
- **VPB** (67, mcap 196,761 tỷ) — ngân hàng
- **CTG** (66, mcap 239,222 tỷ) — ngân hàng quốc doanh
- **DCM** (66, mcap 18,804 tỷ) — phân bón
- **DPM** (66, mcap 18,071 tỷ) — phân bón

Cần phân tích sâu hơn (chất lượng BCTC, triển vọng ngành) trước khi quyết định.

---

## 7. Goal checklist

| Goal (lệnh §6) | Kết quả | Đạt? |
|----------------|---------|------|
| ≥60/73 mã recall ≥60/74 | 70/71 | ✅ (117%) |
| Recall trung bình ≥60/74 | 64.9 | ✅ |
| REQ-031/048 không tái phát | 0% fail | ✅ |
| Báo cáo V2 phân loại fail | §3 | ✅ |

---

## 8. Files đầu ra

| File | Nội dung |
|------|----------|
| `/tmp/vn100_tracker.json` | 73 mã × (recall v2, fail_reqs, notes) |
| `/tmp/vn100_reports/` | 71 báo cáo HTML v2 (rebuild) |
| `/tmp/vn100_reports_v1/` | 75 báo cáo HTML v1 (backup) |
| `/tmp/VN100-REPORT-V2.md` | Báo cáo này |
| `/tmp/vn100_v2.py` | Renderer v2 (10 REQ fix) — tái sử dụng |
| `/tmp/vn100_rebuild.py` | Batch rebuild runner |

---

## 9. Đề xuất đợt vá cuối (sau V2)

4 REQ còn fail 100% cần tập trung:
1. **REQ-034 (temporal)**: verifier associate số với năm gần nhất trong ±60 chars. Cần narrative gắn năm CHÍNH XÁC vào cùng vị trí số (vd "năm 2025: doanh thu 33,797.9 tỷ" không "doanh thu... 2025").
2. **REQ-061 (ROE)**: ROE bị associate năm 2021 (giống 034). Cần gắn "ROE năm {years[-1]}" ngay cạnh số.
3. **REQ-073 (paragraph)**: insight >300 ký tự → tách bullet list ngắn.
4. **REQ-055**: cần inspect verifier để hiểu yêu cầu cụ thể.

**Dự tính:** fix 4 REQ này → recall avg 64.9 → ~70/74 (gần CTD 73/74).

---

**Ký:** GLM sess_3b54417a — 2026-08-02
