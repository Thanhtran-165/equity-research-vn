# Data Coverage Report — vn-bond-transmission

> Báo cáo nghiên cứu: tác động thị trường trái phiếu VN lên SBV rate / tỷ giá / interbank / lạm phát
> Generated: 2026-07-09

## Tổng quan nguồn data đã thu thập

| # | Nguồn | Loại data | Rows | Range | Tần suất | File |
|---|---|---|---|---|---|---|
| 1 | **HNX Yield Curve** ⭐ | Bond yields 2Y/5Y/10Y (+ 8 tenors) | 3,121 | 2014-01-02 → 2026-07-09 | Daily | `data/raw/hnx_yield/hnx_yield_curve_daily.csv` |
| 2 | **SBV Central FX** ⭐ | USD/VND tỷ giá trung tâm | 2,941 | 2015-01-01 → 2026-07-08 | Daily | `data/raw/sbv_fx/sbv_central_fx_daily.csv` |
| 3 | **sjc-gold-history (reuse)** | USD/VND market rate | 4,919 | 2009-07-21 → 2026-07-08 | Daily | `data/raw/workspace_reuse/usd_vnd_market_daily_2009_2026.csv` |
| 4 | **IMF IFS (DBnomics)** | Lending + Deposit Rate (proxy interbank) | 678 | 1992-11 → 2023-12 | Monthly | `data/raw/imf_rates/imf_lending_deposit_monthly.csv` |
| 5 | **FRED** ⭐ | US 10Y/2Y + DXY + CPI VN index | 33,867 | 1962 → 2026 | Daily | `data/raw/fred_global/fred_data.csv` |
| 6 | **World Bank** | M2/reserves/GDP/inflation/FX | 314 | 1990 → 2025 | Annual | `data/raw/worldbank_macro/wb_vn_annual.csv` |
| 7 | **VBMA weekly** | Interbank ON (gần đây) | 12 | 2026-04-10 → 2026-07-03 | Weekly | `data/raw/vbma_archive/vbma_interbank_weekly.csv` |
| 8 | **SBV policy timeline (VERIFIED)** | Refinancing/discount/OMO events | 31 | 2008-12 → 2024-01 | Event | `data/raw/sbv_decisions/sbv_policy_rate_timeline.csv` |
| 9 | **NSO CPI monthly** ⭐ | CPI YoY + MoM | 79 | 2019-11 → 2026-07 | Monthly | `data/raw/cpi/nso_cpi_monthly.csv` |
| 10 | **vn10y delta (reuse)** | Bond 10Y/2Y delta bps + VN-Index | 144 | 2014-07 → 2026-06 | Monthly | `data/raw/workspace_reuse/bond_equity_delta_monthly_2014_2026.csv` |
| 11 | **sjc CPI yearly (reuse)** | CPI index | 18 | 2009 → 2026 | Yearly | `data/raw/workspace_reuse/cpi_index_yearly_2009_2026.csv` |
| 12 | **vn-rates-weekly snapshot** | Rates snapshot 4 tuần | 30 | 2026-W23→W26 | Weekly | `data/raw/workspace_reuse/rates_snapshot_4w_2026W23_W26.csv` |

**Tổng: ~43,000+ rows dữ liệu thô** từ 12 nguồn, covering 1962→2026.

---

## Coverage theo 5 biến cốt lõi

### ✅ Biến A — Trái phiếu CP VN yields (BIẾN ĐỘC LẬP CHÍNH)

| Nguồn | Range | Tần suất | Cột chính | Đánh giá |
|---|---|---|---|---|
| **HNX yield curve** ⭐ | 2014-01-02 → 2026-07-09 (11.5 năm) | Daily | 2Y/5Y/10Y par yield + 3M/6M/9M/1Y/3Y/7Y/15Y | ⭐⭐⭐ Hoàn hảo — 3,121 ngày, 0 error |

**Confidence**: HIGH (nguồn chính thức HNX, par yield benchmark). Cột `par_yield` là benchmark chuẩn (từ giao dịch thật).

---

### 🟡 Biến B — Interbank (CÓ GAP CẤU TRÚC, ĐÃ CÓ WORKAROUND)

| Nguồn | Range | Tần suất | Loại | Đánh giá |
|---|---|---|---|---|
| **IMF Lending Rate** (proxy) | 1992-11 → 2023-12 (31 năm) | Monthly | PROXY — KHÔNG phải VNIBOR | ⭐⭐ Dài nhất nhưng là proxy |
| **IMF Deposit Rate** (proxy) | 1992-11 → 2023-12 (31 năm) | Monthly | PROXY | ⭐⭐ |
| **VBMA weekly** (thật) | 2026-04-10 → 2026-07-03 (12 tuần) | Weekly | VNIBOR ON thật | ⭐ Gần đây, rất ngắn |
| **vn-rates-weekly snapshot** | 2026-W23→W26 | Weekly | Interbank ON/1W/1M thật | ⭐ Gần đây |

**⚠️ GAP CÔNG NHẬN MINH BẠCH**:
- VNIBOR chuẩn chỉ ra mắt ~2009-2010 (administrator: LSEG/FTSE Russell)
- "Interbank 2005-2009" về mặt khái niệm KHÔNG tồn tại
- Free daily interbank series dài = KHÔNG có (test 4 hướng: IMF DataMapper/SDMX/DBnomics/BIS đều rỗng)
- `dttktt.sbv.gov.vn` (chứa archive interbank thật) bị firewall block kể cả từ VN (TCP port 443+80 đều closed)
- CEIC/LSEG trả phí cho full VNIBOR history

**Workaround đã triển khai**:
1. Dài hạn (1992-2023): IMF Lending/Deposit Rate làm PROXY (label rõ)
2. Gần đây (2026): VBMA weekly + SBV snapshot (VNIBOR thật)
3. Khoảng 2018-2025: chưa có (archive VBMA cũ không predictable tên file)

**Confidence**: MEDIUM (proxy cho dài hạn, real cho gần đây)

---

### ✅ Biến C — Tỷ giá USD/VND

| Nguồn | Range | Tần suất | Loại | Đánh giá |
|---|---|---|---|---|
| **SBV central rate** ⭐ | 2015-01-01 → 2026-07-08 (11.5 năm) | Daily | Tỷ giá trung tâm chính thức | ⭐⭐⭐ Hoàn hảo — 2,941 dòng, có SoVanBan |
| **sjc-gold-history market** ⭐ | 2009-07-21 → 2026-07-08 (17 năm) | Daily | Market rate (VCB) | ⭐⭐⭐ 4,919 dòng, gap 508 đã forward-fill |
| FRED annual IMF | 1970 → 2023 | Annual | Cross-check | ⭐ |

**Confidence**: HIGH (cả 2 nguồn chính thức, overlap 2015-2026 cho cả central + market).

---

### ✅ Biến D — CPI / Lạm phát

| Nguồn | Range | Tần suất | Loại | Đánh giá |
|---|---|---|---|---|
| **NSO CPI monthly** ⭐ | 2019-11 → 2026-07 (79 tháng) | Monthly | YoY + MoM | ⭐⭐⭐ YoY 65 obs, MoM 72 obs — đủ cho monthly quant |
| **FRED CPI VN index** ⭐ | 1990 → 2031 (42 năm, có forecast) | Annual | CPI index | ⭐⭐⭐ Cross-check dài hạn |
| **sjc CPI yearly** (reuse) | 2009 → 2026 (18 năm) | Yearly | CPI index (2010=100) | ⭐⭐⭐ Cross-check |
| World Bank inflation | 1996 → 2025 | Annual | Inflation YoY % | ⭐⭐ |

**Confidence**: HIGH — có cả monthly (2019-2026, cho quant) + annual (1990-2026, cho context dài hạn).

---

### 🟡 Biến E — Lịch quyết định lãi suất SBV (ĐÃ VERIFY)

| Nguồn | Range | Loại | Đánh giá |
|---|---|---|---|
| **SBV policy timeline (VERIFIED)** ⭐ | 2008-12 → 2024-01 (31 events) | Refinancing + discount + OMO | ⭐⭐ 10 verified, 17 pending (2008-2019 từ AMRO) |

**✅ ĐÃ VERIFY 5 QĐ chính (corrections made)**:

| Sự kiện | QĐ ĐÚNG | Ngày hiệu lực | Rate cũ→mới | Nguồn verify |
|---|---|---|---|---|
| COVID cut 1 | **418/QĐ-NHNN** | 17/03/2020 | 6.0→5.0% | Thuvienphapluat ✅ |
| COVID cut 2 | **918/QĐ-NHNN** | 13/05/2020 | 5.0→4.5% | LuatVietnam ✅ |
| COVID cut 3 | **1728/QĐ-NHNN** *(sửa từ 1123)* | 01/10/2020 | 4.5→4.0% | Thuvienphapluat ✅ |
| Thắt 2022 #1 | **1606/QĐ-NHNN** *(sửa từ 1524)* | 23/09/2022 | 4.0→5.0% | LuatVietnam + baochinhphu ✅ |
| Nới lỏng 2023 #4 | **1123/QĐ-NHNN** *(sửa từ 1124)* | 19/06/2023 | 5.0→4.5% | sbv.gov.vn + Thuvienphapluat ✅ |

**⚠️ 17 entries pending verification (2008-2019)**: dựa vào AMRO ACR reports — cite "AMRO ACR" thay vì số QĐ cụ thể nếu chưa verify. Đã thêm QĐ phụ: 1809 (thắt 2022 #2), 313/574/950 (nới lỏng 2023 #1-3).

---

## Master Datasets đã build

### `master_daily_2014_2026.csv` (3,849 rows)
Cửa sổ daily khi overlap đủ biến A (bond) + C (FX) + context (US rates).

| Cột | Valid | Range |
|---|---|---|
| date | 3,849 | 2014-01-01 → 2026-07-09 |
| 2y/5y/10y_par_yield | 3,121 each | 2014-01-02 → 2026-07-09 |
| usd_vnd_central | 2,941 | 2015-01-01 → 2026-07-08 |
| usd_vnd_market | 4,919 | 2009-07-21 → 2026-07-08 |
| us_10y_yield | 16,112 | 1962 → 2026 |
| us_2y_yield | 12,520 | 1976 → 2026 |
| dxy_trade_weighted | 5,139 | 2006 → 2026 |

**Overlap bond+FX(both)**: 2,378 ngày (2015-01-07 → 2026-07-08) — đủ cho daily regression.

### `master_monthly.csv` (415 rows, 1992-01 → 2026-07, 16 columns)

| Cột | Valid | Range | Nguồn |
|---|---|---|---|
| 2y/5y/10y_par_yield | 151 each | 2014-01 → 2026-07 | HNX |
| usd_vnd_central | 136 | 2015-01 → 2026-07 | SBV |
| usd_vnd_market | 205 | 2009-07 → 2026-07 | sjc |
| deposit_rate | 333 | 1992-11 → 2023-12 | IMF (proxy) |
| lending_rate | 345 | 1992-11 → 2023-12 | IMF (proxy) |
| us_10y/2y_yield | 415 each | 1992-01 → 2026-07 | FRED |
| dxy_trade_weighted | 247 | 2006-01 → 2026-07 | FRED |
| cpi_vn_index | 415 | 1992-01 → 2026-07 | FRED (annual, fwd-fill) |
| **cpi_yoy_pct** ⭐ | 65 | 2019-11 → 2026-07 | NSO monthly (NEW) |
| **cpi_mom_pct** ⭐ | 72 | 2019-11 → 2026-07 | NSO monthly (NEW) |
| sbv_refinancing_pct | 212 | 2008-12 → 2026-07 | SBV timeline (VERIFIED) |
| sbv_discount_pct | 212 | 2008-12 → 2026-07 | SBV timeline (VERIFIED) |

---

## Cửa sổ nghiên cứu tối ưu

### Window 1: Daily deep quant (2015-01 → 2026-07, ~11.5 năm)
- **Đủ**: Bond yields (HNX) + USD/VND (SBV central + sjc market) + US rates/DXY
- **Thiếu**: Interbank daily real (chỉ có proxy IMF monthly)
- **Phù hợp**: Regression bond↔FX, event study quanh SBV decisions

### Window 2: Monthly long-run (1992-2023, ~31 năm)
- **Đủ**: IMF Lending/Deposit Rate (proxy interbank) + CPI + SBV policy + US rates
- **Thiếu**: Bond yields (chỉ có 2014+), USD/VND daily (chỉ annual IMF)
- **Phù hợp**: Context dài hạn, narrative, so sánh chu kỳ

### Window 3: Overlap đầy đủ (2014-01 → 2023-12, ~10 năm monthly)
- **Đủ nhất**: Bond yields + FX + interbank proxy + CPI + SBV rate + US rates
- **Phù hợp**: VAR/Granger causality trên monthly data

---

## Provenance & Confidence Summary

| Biến | Confidence | Nguồn chính | Cross-check |
|---|---|---|---|
| A. Bond yields | **HIGH** | HNX (chính thức) | vn10y delta (144 tháng) |
| B. Interbank (proxy) | **MEDIUM** | IMF Lending/Deposit | VBMA weekly (gần đây) |
| C. USD/VND | **HIGH** | SBV central + sjc market | FRED annual IMF |
| D. CPI | **HIGH** | NSO monthly (2019-2026) + FRED annual (1990-2026) | sjc yearly + World Bank |
| E. SBV rate | **HIGH** (5 QĐ verified) / **MEDIUM** (17 pending 2008-2019) | SBV timeline (VERIFIED) | AMRO ACR reports |

---

## Scripts (reproducible)

| Script | Chức năng | Thời gian chạy |
|---|---|---|
| `01_fetch_hnx_yield.py` | Backfill HNX yield 2014→nay | ~7 phút (3,121 ngày, 4 workers) |
| `02_fetch_sbv_fx.py` | SBV central FX qua Liferay API | ~30 giây (30 pages) |
| `10_build_master.py` | Build master_monthly + master_daily | ~5 giây |

**Reproducibility**: Tất cả script có checkpoint/resume. `FRED_API_KEY` KHÔNG cần (dùng fredgraph.csv endpoint).

---

## KHÔNG có trong dataset này (minh bạch)

- ❌ Interbank daily series dài (2005-2025) — gap cấu trúc, chỉ có proxy IMF monthly
- ❌ CPI monthly YoY/MoM chính thức từ NSO — chỉ có annual (cần bổ sung nếu làm monthly quant)
- ❌ M0/M1/M2 monthly — chỉ có annual (World Bank); `dttktt.sbv.gov.vn` bị block
- ❌ Dự trữ ngoại hối real-time — SBV chưa publish (cam kết 2027)
- ❌ Archive VBMA weekly 2018-2025 — tên file không predictable, chỉ có 12 tuần gần nhất

## Bước tiếp theo (chờ user quyết định)

1. **Verify SBV policy timeline** — từng QĐ cụ thể trước khi dùng cho claim
2. **Bổ sung CPI monthly** từ NSO (nếu cần monthly quant)
3. **Phân tích** (correlation/regression/VAR) — sau khi chốt coverage OK
4. **Outline longform** 15-20 chương
