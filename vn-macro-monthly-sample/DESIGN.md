# Skill: vn-macro-monthly — Design Document

**Mục đích**: Báo cáo vĩ mô Việt Nam hàng tháng (toàn diện) cho 1 người đọc (user).
**Trigger**: On-demand — user kích hoạt khi muốn, tự quyết định ngày chạy.

---

## 1. NGUỒN DỮ LIỆU (5 nguồn chính, 100% miễn phí)

| Nguồn | Provider | Loại | Độ trễ |
|---|---|---|---|
| **PMI** | S&P Global | Press release PDF (free, no account) | ~1 ngày sau cuối tháng |
| **NSO** | Tổng cục Thống kê | Báo cáo KTXH tháng (web) | ~3 ngày |
| **Customs** | Tổng cục Hải quan | Báo cáo XNK (JSP portal, render JS) | ~10 ngày |
| **VBMA** | Hiệp hội TT Trái phiếu | Báo cáo tuần TT tiền tệ & trái phiếu (PDF) | ~3 ngày |
| **VNBA** | Hiệp hội Ngân hàng | Báo cáo tháng KT-TC-TT (PDF, 22 trang) | ~11 ngày |

**URL patterns**:
- PMI: `pmi.spglobal.com/Public/Home/PressRelease/{hash}` → tìm qua WebSearch
- NSO: `nso.gov.vn/bai-top/{YYYY}/{MM}/bao-cao-tinh-hinh-kinh-te-xa-hoi-thang-{...}/`
- Customs: `customs.gov.vn/index.jsp?pageId=4967&tkId={XXXX}` → tìm tkId qua WebSearch (render JS)
- VBMA: `vbma.org.vn/storage/reports/{MonthEn}{Year}/{DDMMYYYY}-{DDMMYYYY} BAO CAO TUAN TTP[N].pdf`
- VNBA: `vnba.org.vn/vi/ban-tin-kinh-te-tai-chinh-tien-te-thang-{M}-va-tuan-1-thang-{M+1}-{Y}-{id}.htm` → lấy link CDN (token expires)

---

## 2. SCOPE — 41 chỉ số, chỉ dữ liệu THÁNG (không quý)

```
Nhóm 1 Kinh tế thực (14) — NSO + Customs + S&P
Nhóm 2 Tiền tệ & Tài chính (12) — VNBA + VBMA
Nhóm 3 Ngành & Cơ cấu (5) — Customs + S&P + NSO
Nhóm 4 Bối cảnh toàn cầu (10) — VNBA
```

### Nhóm 1 — Kinh tế thực (priority order)
1. CPI (mom/yoy/ytd/core) · 2. PMI Manufacturing · 3. IIP · 4. Trade balance · 5. Exports · 6. Imports · 7. FDI disbursed · 8. FDI registered · 9. Retail · 10. Business new · 11. Business exited · 12. Int'l visitors · 13. State investment · 14. State budget

### Nhóm 2 — Tiền tệ & Tài chính (priority order)
1. Interbank rate (ON/1W/2W/1M) · 2. FX central rate · 3. VN-Index · 4. Govt bond yield (1Y/5Y/10Y) · 5. Gold world · 6. Credit · 7. Deposit rate · 8. Lending rate · 9. FX free rate · 10. DXY · 11. Corporate bond issuance · 12. Govt bond issuance

### Nhóm 3 — Ngành & Cơ cấu (priority order)
1. PMI sub-indices · 2. Trade by sector (FDI vs nội địa) · 3. Trade by market · 4. Trade by commodity · 5. FDI by sector

### Nhóm 4 — Bối cảnh toàn cầu (priority order)
1. Fed policy · 2. US economy · 3. Oil prices · 4. Geopolitical risk · 5. 10Y US Treasury yield · 6. ECB/Eurozone · 7. BOJ/Japan · 8. China economy · 9. Policy actions VN · 10. Agriculture snapshot

---

## 3. CORE RULES

### 3.1 Time Consistency Rule ("Nhìn lùi, không nhìn tới")
- Reference Month (RM): tháng kinh tế được báo cáo
- Data Cutoff: cuối ngày cuối cùng của RM (VD 2026-05-31 23:59)
- Lọc theo nguồn:
  - PMI / NSO / Customs → dùng nguyên (đã chốt cuối tháng)
  - VBMA (tuần) → chỉ lấy tuần có ngày KẾT THÚC ≤ cutoff
  - VNBA (tháng) → chỉ lấy phần "tháng X", BỎ phần "tuần 1 tháng X+1"
- KHÔNG có ngoại lệ look-ahead. Báo cáo = thuần 1 tháng.

### 3.2 Frequency Rule
- CHỈ dữ liệu tháng (monthly-only)
- KHÔNG dùng quý (→ bỏ PBT/NIM ngân hàng khỏi scope)

### 3.3 Conflict Resolution Rule
**4 nguyên tắc:**

1. **Primary Source Hierarchy** (theo loại chỉ số):
   - CPI/IIP/FDI/retail/DN/visitors → NSO
   - XNK (chính thức) → Customs
   - Lãi suất/tỷ giá/trái phiếu/tín dụng → VNBA (VBMA bổ sung)
   - Vàng/dầu/hàng hóa TG/kinh tế TG → VNBA
   - PMI → S&P Global

2. **Definition First** — kiểm chứng định nghĩa trước khi so sánh số. Mỗi chỉ số phải có field `definition`. Đa số "xung đột" thực ra là khác định nghĩa (không phải sai dữ liệu).

3. **Acceptable Variance**:
   - <2% → bình thường, dùng primary
   - 2-5% → ghi `conflict_note`, dùng primary
   - >5% → ghi cả 2 số + lý do

4. **When to show both** — chỉ khi chênh >5% VÀ 2 nguồn có định nghĩa rõ ràng khác nhau.

### 3.4 Unit Convention
| Đuôi trường | Đơn vị |
|---|---|
| `_b_vnd` | tỷ VND |
| `_b_usd` | tỷ USD |
| `_vnd` | đồng VND (số nguyên) |
| `_pct` | % (số thập phân 2 chữ) |
| `_k` | nghìn (đơn vị) |
| `_m` | triệu (lượt/người) |
| `usd_oz` | USD/ounce (vàng TG) |
| `usd_bbl` | USD/thùng (dầu) |

- Mỗi trường JSON kết thúc bằng đơn vị
- % tách rõ: `mom_pct` / `yoy_pct` / `ytd_avg_pct`

### 3.5 Data Card schema (áp dụng cho MỌI chỉ số)
```json
{
  "{indicator}": {
    "name_vi": "...",
    "name_en": "...",
    "tier": "group1_real_economy",
    "definition": "...",
    "value": <number>,
    "value_unit": "%",
    "comparisons": {"mom_pct": ..., "yoy_pct": ..., "ytd_avg_pct": ...},
    "source_primary": "NSO",
    "source_secondary": ["VNBA"],
    "signal": "GREEN|YELLOW|RED",
    "note": "...",
    "has_chart": true|false
  }
}
```

---

## 4. WORKFLOW

```
User kích hoạt: /vn-macro-monthly 2026-05
        ↓
[PRE-FLIGHT CHECK] — kiểm tra 5 nguồn có tồn tại không
        ↓
   ┌────┴────┐
   ↓         ↓
 ĐỦ 5/5   THIẾU
   ↓         ↓
 LÀM      DỪNG + báo thiếu nguồn + đề xuất ngày thử lại
 BÁO CÁO   (KHÔNG tạo thư mục → máy sạch)
   ↓
[TẠO THƯ MỤC cache] {project}/vn-macro-monthly/2026-05/
   ↓
[FETCH] — tải 5 nguồn về sources_cache/
   ↓
[PARSE] — pdftotext / WebReader → extract text
   ↓
[EXTRACT] — LLM parse 41 chỉ số theo Data Card schema
   ↓
[APPLY RULES] — Time Rule + Conflict Rule + Unit Convention
   ↓
[CROSS-CHECK] — 6 cặp cross-check giữa các nguồn
   ↓
[BUILD JSON] — report.json (source-of-truth)
   ↓
[APPEND HISTORY] — history.json (cho chart sau này)
   ↓
[RENDER HTML] — report.html (dashboard chuyên nghiệp)
        ↓
   XONG
```

### Pre-flight check — cách check từng nguồn
| Nguồn | Cách check |
|---|---|
| PMI | WebSearch `"Vietnam Manufacturing PMI" [tháng] [năm] site:pmi.spglobal.com` |
| NSO | WebSearch `nso.gov.vn "báo cáo kinh tế xã hội" tháng [M] [Y]` |
| Customs | WebSearch `customs.gov.vn tkId "tháng [M] [Y]"` |
| VBMA | WebSearch `vbma.org.vn "BAO CAO TUAN" [tuần cuối tháng M]` |
| VNBA | WebSearch `vnba.org.vn "tháng [M] và tuần 1 tháng [M+1]"` |

### Đề xuất ngày thử lại (khi bị DỪNG)
- Skill biết lịch release cố định (NSO ~3/M+1, Customs ~10/M+1, VNBA ~11/M+1)
- Output: "Thiếu nguồn X. Thử lại sau ngày [ngày dự kiến release]"

---

## 5. CẤU TRÚC FILE / CACHE (Option C: PDF + text + JSON)

```
{project_dir}/
└── vn-macro-monthly/
    ├── DESIGN.md                   ← tài liệu này
    ├── history.json                ← chuỗi thời gian (append mỗi tháng)
    ├── 2026-05/                    ← 1 kỳ = 1 thư mục (chỉ tạo khi pre-flight PASS)
    │   ├── report.json             ← data structured (source-of-truth)
    │   ├── report.html             ← dashboard cuối cùng cho user đọc
    │   └── sources_cache/
    │       ├── pmi_may.html
    │       ├── nso_may.html
    │       ├── customs_may.txt     ← secondary sources (JSP render JS)
    │       ├── vbma_weekly_25-29may.pdf
    │       ├── vbma_weekly_25-29may.txt
    │       ├── vnba_monthly_may.pdf
    │       └── vnba_monthly_may.txt
    ├── 2026-04/
    │   └── ...
    └── ...
```

**Rules cache**:
- Mọi số liệu trong report.json phải trace được tới 1 file cụ thể trong sources_cache/
- KHÔNG bao giờ xóa cache (bằng chứng)
- File naming cố định: `{source}_{period}.{ext}`

---

## 6. OUTPUT — HTML Dashboard chuyên nghiệp

### Design pattern (4 thành phần)
```
┌─────────────────────────────────────────────────────┐
│ HERO: Tên báo cáo + Verdict (1 dòng)                 │
├─────────────────────────────────────────────────────┤
│ NAV (thanh điều hướng)                               │
│ [Nhóm 1*] [Nhóm 2] [Nhóm 3] [Nhóm 4]  (*mặc định)   │
├─────────────────────────────────────────────────────┤
│ NỘI DUNG 1 NHÓM:                                     │
│ 🔴 TIÊU CỰC (highlight box, 2-3 điểm)               │
│ 🟢 TÍCH CỰC (highlight box, 2-3 điểm)               │
│ 📋 CHI TIẾT (list, priority giảm dần)               │
│   Mỗi item: giá trị • MoM/YoY • flag • [📊 Chart]   │
│   Chart = click to expand (modal/accordion)         │
└─────────────────────────────────────────────────────┘
```

### Quy tắc visual
- Style đồng bộ với skill VN hiện có (`vn-research-dashboard`, `vn-news-digest`)
  - Palette: tím-hồng gradient + glassmorphism
  - Signal flag: 🟢 GREEN / 🟡 YELLOW / 🔴 RED
- Chart = **click to expand** (KHÔNG nhồi thẳng). Modal hoặc accordion.
- Chart Cấp A (~10 chỉ số): sparkline 12 tháng, **tự tích lũy** từ history.json
- Chart Cấp B (còn lại): khi history đủ (>6 tháng) mới có

### Cross-check & Risks/Catalysts (section cuối, ngoài 4 nhóm)
- Cross-checks: bảng 6 cặp đối chiếu verdict (CONFIRMED/DIVERGENCE/MATCHED...)
- Risks (5): level Rất cao / Cao / Trung bình
- Catalysts (5): level tương tự
- Key takeaways (5): bullet points tổng hợp

---

## 7. LỊCH SỬ (HISTORY DB)

### history.json
```json
{
  "series": {
    "cpi_yoy_pct": [
      {"month": "2026-05", "value": 5.60}
    ],
    "pmi": [
      {"month": "2026-05", "value": 52.8}
    ]
  }
}
```

### Rules
- Mỗi lần skill chạy thành công → append entry mới
- **Re-run tháng cũ → ghi đè** (1 tháng chỉ 1 giá trị)
- **Bắt đầu trống** (KHÔNG seed data cũ). Áp dụng cho CẢ `history.json` thật VÀ template sample (`assets/report_template.html`)
- → Dashboard demo sẽ không có nút `[📊]` cho đến khi skill chạy thật 6+ kỳ (feature ngủ chờ data — KHÔNG phải bug)
- Đủ 6+ tháng → có thể vẽ chart Cấp A
- Đủ 12+ tháng → hầu hết chỉ số có chart

---

## 8. CROSS-CHECK PAIRS (6 cặp mặc định)

| # | Cặp | Ý nghĩa |
|---|---|---|
| 1 | PMI NewExportOrders ↔ Customs Exports | Xuất khẩu phục hồi? |
| 2 | PMI InputCosts ↔ NSO CPI | Lạm phát đường lên? |
| 3 | PMI Output ↔ NSO IIP | Sản xuất CN mạnh? |
| 4 | NSO vs Customs trade balance | Sơ bộ vs chính thức |
| 5 | VBMA LNH ↔ VNBA mặt bằng lãi suất | Áp lực thanh khoản VND |
| 6 | VNBA tỷ giá ↔ Customs nhập siêu | Cán cân → tỷ giá |

---

## 9. SAMPLE DATA

- Reference implementation: `may_2026.json` (đã verify, JSON hợp lệ)
- Cache PDF mẫu: `sources/vbma_weekly_march2026.pdf`, `sources/vnba_monthly_may2026.pdf`
- Verdict tháng 5/2026: `NEUTRAL_WITH_CAUTION` (4 áp lực về giá & thanh khoản)

---

## 10. PHỐI HỢP VỚI HỆ SINH THÁI SKILL VN

```
vn-financial-data-collector  (DN cấp)
        ↓
vn-fundamental-analysis     (DN phân tích)
vn-valuation-engine         (DN định giá)
vn-technical-analysis       (DN kỹ thuật)
vn-news-digest              (thời sự 30 ngày)
⭐ vn-macro-monthly ⭐       (VĨ MÔ monthly)  ← SKILL NÀY
        ↓
vn-research-dashboard       (render HTML — share style)
```
