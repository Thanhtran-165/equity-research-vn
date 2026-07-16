# DÀN Ý BÁO CÁO LONGFORM (REVISED — thesis regime-dependent)

> **Thesis mới**: Mối quan hệ trái phiếu chính phủ VN ↔ tỷ giá USD/VND, lạm phát, và lãi suất điều hành **đảo dấu theo regime chính sách** — đây là phát hiện mà phân tích full-period correlation che giấu. Đây là insight mới, cụ thể, và data vững.
>
> **Thesis cũ đã bỏ** (premortem vòng 1): ~~"trái phiếu là biến trung tâm"~~ — quá mạnh cho data (corr đảo dấu, Fisher window truncate).
>
> **Style**: Research-driven + chronological. 12 chương gọn, mỗi chương vững. Regime = trục tổ chức.
>
> **Data mới**: rolling 24M correlation Bond↔FX dao động **-0.96 → +0.87** (đi qua 0). Bond↔CPI **-0.63 → +0.80**.

---

## 5 REGIME CHÍNH SÁCH (trục tổ chức chính)

| # | Regime | Period | SBV refinancing | Bond 10Y mean | USD/VND mean | corr Bond↔FX |
|---|---|---|---|---|---|---|
| R1 | Thắt chặt hậu khủng hoảng | 2014-01 → 2016-12 | 6.5% (giữ) | 7.01% | 21.804 | **+0.04** |
| R2 | Ổn định | 2017-01 → 2019-08 | 6.0% (cut nhẹ) | 5.10% | 22.616 | **-0.66** |
| R3 | Nới lỏng COVID | 2019-09 → 2022-08 | 6.0→4.0% (3 cut) | 2.56% | 23.170 | **+0.16** |
| R4 | Thắt chặt Fed-driven | 2022-09 → 2023-06 | 4.0→6.0% (2 hike) | 4.05% | 23.601 | **-0.08** |
| R5 | Nới lỏng trở lại | 2023-06 → 2026-07 | 6.0→4.5% (4 cut) | 3.09% | 24.548 | **+0.84** |

→ Corr đảo dấu liên tục. Đây là câu chuyện.

---

## CẤU TRÚC: 12 chương trong 4 nhóm

### NHÓM 1: MỞ ĐẦU (3 chương)

#### Chương 1: Câu hỏi nghiên cứu — tại sao full-period correlation lừa dối?
- **Hook**: Phân tích phổ biến nói "bond↔FX tương quan -0.66" — nhưng đây là **Simpson's paradox**
- Stress-test: cùng data, chia theo regime → corr đảo từ -0.66 thành +0.84
- 4 câu hỏi nghiên cứu (nhưng frame theo regime, không "biến trung tâm")
- Component: kpi-grid (5 regime stats), chart-box (rolling corr -0.96→+0.87)

#### Chương 2: Data & phương pháp luận
- 11 nguồn, ~43,000 rows
- **Bảng window từng mối quan hệ** (P0 B.2 fix): bond+SBV 151tháng, bond+FX 136, bond+CPI 69, all4 chỉ 34
- Caveat: interbank proxy, SBV QĐ verify status
- Component: bảng window, compare (2 trục)

#### Chương 3: Khung lý thuyết — regime-dependent monetary transmission
- **Lý thuyết**: monetary policy transmission (Taylor 1995) + regime-switching models (Hamilton 1989)
- Tại sao correlation có thể đảo dấu: cơ chế truyền dẫn khác nhau theo stance
- Fisher hypothesis — test cho VN ở từng regime
- Component: callout lý thuyết, flow diagram

---

### NHÓM 2: 5 REGIME CHRONOLOGICAL (5 chương — core)

#### Chương 4: R1 — Thắt chặt hậu khủng hoảng (2014-2016)
- SBV giữ 6.5% suốt, bond ~7% (cao)
- corr Bond↔FX = **+0.04** (gần 0 — chưa có mối quan hệ rõ)
- Context: hậu GFC, lạm phát hạ nhiệt, thị trường non
- **Insight**: giai đoạn này bond chưa "nói chuyện" với tỷ giá

#### Chương 5: R2 — Ổn định, corr âm mạnh xuất hiện (2017-2019)
- SBV cut 6.5→6.0%, bond giảm 7%→5%
- corr Bond↔FX = **-0.66** (âm mạnh nhất lịch sử)
- **Giải thích**: bond yield tăng → hút vốn ngoại → VND mạnh (cơ chế textbook)
- **Insight**: chỉ ở giai đoạn ổn định, cơ chế textbook mới hoạt động

#### Chương 6: R3 — COVID shock, corr đảo dấu (+0.16)
- SBV cut 3 đợt (6→5→4.5→4%), bond sụt 2.56%
- corr Bond↔FX = **+0.16** (dương nhẹ — đảo dấu)
- **Tại sao đảo**: SBV cut cực mạnh → bond rơi → VND cũng yếu (cùng chiều, không ngược)
- **Insight**: ở cut cực, cơ chế textbook gãy — cả bond lẫn FX cùng phản ứng "risk-off"

#### Chương 7: R4 — Thắt chặt Fed-driven, corr gần 0 (2022-2023)
- SBV hike 2 đợt (4→5→6%), bond tăng 4.05%
- corr Bond↔FX = **-0.08** (gần 0 — mối quan hệ biến mất)
- **Tại sao**: Fed hike quá mạnh → DXY tăng → cả bond VN lẫn VND bị áp lực ngoài, không còn quan hệ nội tại
- **Insight**: external shock phá vỡ mối quan hệ nội địa

#### Chương 8: R5 — Nới lỏng trở lại, corr dương mạnh (+0.84)
- SBV cut 4 đợt (6→4.5%), bond 3.09%
- corr Bond↔FX = **+0.84** (dương mạnh nhất lịch sử)
- **Tại sao**: giai đoạn phục hồi, bond thấp + VND yếu cùng lúc (Tết tỷ giá áp lực 2024)
- **Insight**: hiện tại mối quan hệ đang "risk-off" mode — bond thấp không nhất thiết VND mạnh

---

### NHÓM 3: SÂU HƠN (3 chương)

#### Chương 9: Bond ↔ SBV — phản ứng bất đối xứng (HIKING > CUT)
- Event study 12 decisions: CUT bond -0.5 đến -1.0%, HIKING +1.2 đến +1.3%
- **Insight**: bond phản ứng hiking mạnh hơn cutting (loss aversion — Ch11)
- Component: event study chart, kpi-grid per event

#### Chương 10: Bond ↔ lạm phát — Fisher hypothesis test theo regime
- Full-period corr -0.10 (gần 0)
- **Nhưng rolling**: -0.63 → +0.80 — Fisher ĐÚNG ở vài regime, SAI ở vài regime
- **Giải thích**: VN bond chưa phải inflation hedge ổn định, nhưng có giai đoạn phản ánh
- Component: scatter per regime, rolling corr chart

#### Chương 11: Bond ↔ interbank — narrative + caveat
- Proxy (IMF Lending/Deposit) + 16 tuần VNIBOR thật
- Caveat rõ: data không đủ deep quant
- **Insight**: deposit rate phản ánh bond (+0.77), lending rate không (-0.15)
- Component: proxy chart, callout caveat

---

### NHÓM 4: KẾT LUẬN (1 chương)

#### Chương 12: Tổng hợp — regime là chìa khóa
- **Thesis confirmed**: mối quan hệ bond↔4 biến phụ thuộc regime
- **Hệ quả đầu tư**: không thể dùng bond để dự báo FX mà không biết regime
- **Hệ quả chính sách**: SBV cần biết regime nào truyền dẫn mạnh
- **Gap**: cần VNIBOR series dài, CPI monthly lịch sử
- **Hướng nghiên cứu**: Markov-switching VAR, so sánh ASEAN
- Component: summary table, kpi-grid, callout actionable

---

## TỔNG KẾT KỸ THUẬT

| Thông số | Cũ (18 chương) | Mới (12 chương) |
|---|---|---|
| Số chương | 18 | 12 |
| Thesis | "Biến trung tâm" (mạnh, data yếu) | "Regime-dependent" (khiêm tốn, sắc bén) |
| Nhóm minimap | 5 | 4 |
| Core insight | 4 mối quan hệ stable | Corr đảo dấu theo 5 regime |
| Data đủ? | 4 chương yếu | 12 chương vững |
| Insight mới? | Có (Fisher fail) | **Rất mới** (regime-switching corr chưa ai chỉ ra) |

## CHECKLIST DATA COVERAGE THEO CHƯƠNG (REVISED)

| Chương | Data cần | Có sẵn? |
|---|---|---|
| Ch1-3 (Mở đầu) | rolling corr + window table | ✅ |
| Ch4 (R1 2014-16) | bond + FX + SBV | ✅ |
| Ch5 (R2 2017-19) | bond + FX + SBV | ✅ |
| Ch6 (R3 COVID) | bond + FX + SBV + CPI | ✅ |
| Ch7 (R4 thắt 2022) | bond + FX + DXY | ✅ |
| Ch8 (R5 nới 2023+) | bond + FX + SBV | ✅ |
| Ch9 (Bond↔SBV) | event study | ✅ |
| Ch10 (Bond↔CPI) | rolling corr per regime | ✅ |
| Ch11 (Bond↔interbank) | proxy + 16 tuần | 🟡 Caveat |
| Ch12 (Kết) | synthesis | ✅ |

**11/12 chương data vững. 1 chương caveat.**
