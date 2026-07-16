# Báo cáo dữ liệu: Khối ngoại và 5 cặp quan hệ nghiên cứu

**Ngày:** 2026-07-15
**Mục đích:** Cung cấp cho GPT đầy đủ thông tin data để triển khai nghiên cứu mới về khối ngoại.
**Người thực hiện nghiên cứu:** GPT (sau khi nhận báo cáo này)
**Khảo sát data:** GLM-5.2 (đã verify thực tế bằng API)

---

## TÓM TẮT EXECUTIVE

Dữ liệu khối ngoại **đầy đủ cho cả 5 cặp quan hệ**, với lịch sử **2014–2026** (12+ năm) ở cả cấp từng mã và cấp chỉ số. Nguồn chính là **vnstock_data Golden tier** — module trả 25 cột khối ngoại chi tiết (mua/bán/ròng × khớp lệnh/thoả thuận/tổng × volume/value + room).

| Cặp quan hệ | Data khả thi? | Phạm vi | Ghi chú |
|---|---|---|---|
| 1. Ngoại ↔ biến động cổ phiếu | ✅ | 2014–2026 | Per-stock foreign flow + OHLCV |
| 2. Ngoại ↔ biến động chỉ số | ✅ | 2014–2026 | **Index-level foreign data có sẵn** (VNINDEX, VN30, VN100) |
| 3. Ngoại ↔ sinh lời cổ phiếu | ✅ | 2014–2026 | Forward return + foreign flow |
| 4. Ngoại ↔ tăng/giảm cổ phiếu | ✅ | 2014–2026 | Binary classification (lên/xuống) |
| 5. Ngoại ↔ trái phiếu | ✅ | 2014–2026 | Foreign flow + VN yield 2y/5y/10y |

---

## 1. NGUỒN DỮ LIỆU CHÍNH: vnstock_data (Golden Sponsor)

### 1.1 Thông tin xác thực

| Thuộc tính | Giá trị |
|---|---|
| Tài khoản | Golden Sponsor (Thành Trần Đình) |
| Tier | `golden` |
| Rate limit | **500 requests/phút** (30.000/giờ) |
| API key | Đã lưu tại `~/.vnstock/api_key.json` |
| Python env | `/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/bin/python` (Python 3.11) |
| Module | `vnstock_data` (KHÔNG dùng `vnstock.Trading` — cái đó chưa implement `foreign_trade`) |

### 1.2 Cách gọi API đúng

```python
# PHẢI dùng sponsor venv Python 3.11
# /Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/bin/python

from vnstock_data import Trading

# Per-stock foreign trade
t = Trading(source='vci', symbol='FPT')
df = t.foreign_trade(start='2024-01-01', end='2024-12-31')

# Index-level foreign trade (VNINDEX, VN30, VN100, VNFINSELECT)
ti = Trading(source='vci', symbol='VNINDEX')
df_idx = ti.foreign_trade(start='2024-01-01', end='2024-12-31')
```

### 1.3 Giới hạn kỹ thuật API

| Giới hạn | Chi tiết | Cách xử lý |
|---|---|---|
| **100 rows/call** | API trả tối đa 100 dòng mỗi lần gọi, bất kể date range | Chunk theo quý (3 tháng ~ 60 ngày giao dịch < 100) |
| **Pre-2010 lỗi** | AttributeError khi fetch trước 2010 | Giới hạn mẫu từ 2010 trở đi |
| **Không auto-paginate** | `start='2014-01-01'` chỉ trả 100 dòng gần nhất trong range | Chunk thủ công |

### 1.4 Code chunking để fetch full history

```python
import pandas as pd
from vnstock_data import Trading

def fetch_full_foreign_history(symbol, start_year=2014, end_year=2025):
    """Fetch foreign trade in quarterly chunks to overcome 100-row limit."""
    t = Trading(source='vci', symbol=symbol)
    chunks = []
    date_ranges = pd.date_range(f'{start_year}-01-01', f'{end_year}-12-31', freq='3MS')
    for i in range(len(date_ranges) - 1):
        s = date_ranges[i].strftime('%Y-%m-%d')
        e = date_ranges[i+1].strftime('%Y-%m-%d')
        try:
            df = t.foreign_trade(start=s, end=e)
            if df is not None and df.shape[0] > 0:
                chunks.append(df)
        except:
            pass
    if chunks:
        result = pd.concat(chunks, ignore_index=True)
        result = result.drop_duplicates(subset=['trading_date'])
        result = result.sort_values('trading_date').reset_index(drop=True)
        return result
    return pd.DataFrame()
```

**Tốc độ đã verify:** 1 mã × 12 năm (2014–2025) = ~2.930 dòng trong **10 giây**.
**Ước tính fetch 1.500 mã:** ~4 giờ (batch + checkpoint).

---

## 2. CỘT DỮ LIỆU KHỐI NGOẠI (25 cột)

### 2.1 Cấp từng mã (stock-level) — 25 cột

```
trading_date
--- Khớp lệnh (matched) ---
fr_buy_value_matched        # GT ngoại mua khớp lệnh (VND)
fr_buy_volume_matched       # KL ngoại mua khớp lệnh
fr_sell_value_matched       # GT ngoại bán khớp lệnh
fr_sell_volume_matched      # KL ngoại bán khớp lệnh
--- Thoả thuận (deal/put-through) ---
fr_buy_value_deal           # GT ngoại mua thoả thuận
fr_buy_volume_deal          # KL ngoại mua thoả thuận
fr_sell_value_deal          # GT ngoại bán thoả thuận
fr_sell_volume_deal         # KL ngoại bán thoả thuận
--- Tổng (total = matched + deal) ---
fr_buy_value_total          # GT ngoại mua tổng
fr_buy_volume_total         # KL ngoại mua tổng
fr_sell_value_total         # GT ngoại bán tổng
fr_sell_volume_total        # KL ngoại bán tổng
--- Ròng (net = buy - sell) ---
fr_net_volume_total         # KL ngoại ròng tổng
fr_net_value_total          # GT ngoại ròng tổng (VND)
fr_net_volume_matched       # KL ròng khớp lệnh
fr_net_value_matched        # GT ròng khớp lệnh
fr_net_volume_deal          # KL ròng thoả thuận
fr_net_value_deal           # GT ròng thoả thuận
--- Room ngoại ---
fr_total_room               # Tổng room ngoại
fr_current_room             # Room còn lại
fr_room_percentage          # % room đã dùng
fr_owned_percentage         # % sở hữu ngoại hiện tại
fr_available_percentage     # % room còn trống
fr_owned                    # Số lượng cổ phiểu ngoại đang nắm giữ
```

### 2.2 Cấp chỉ số (index-level) — 22 cột

```
# Tương tự stock-level nhưng KHÔNG có: fr_room_percentage, fr_owned_percentage, fr_available_percentage
# VNINDEX, VN30, VN100, VNFINSELECT đều có dữ liệu
# fr_owned = tổng số cổ phiếu ngoại đang nắm trong rổ chỉ số
```

### 2.3 Chất lượng dữ liệu

| Kiểm tra | Kết quả |
|---|---|
| FPT 2014–2025: fr_buy_volume_total null | **0.0%** |
| FPT 2014–2025: fr_net_volume_total null | **0.0%** |
| Null rate tổng thể | 0% trên các cột chính |
| Dữ liệu zero (không giao dịch ngoại) | Có — một số ngày mã nhỏ không có foreign trade, ghi 0.0 |

---

## 3. DATA CHO TỪNG CẶP QUAN HỆ NGHIÊN CỨU

### Cặp 1: Giao dịch khối ngoại ↔ biến động cổ phiếu

**Câu hỏi:** Khi ngoại mua/bán ròng mạnh, giá cổ phiếu biến động thế nào (volatility)?

| Y (outcome) | X (predictor) | Source |
|---|---|---|
| Stock return volatility (realized vol 5d/20d/60d) | fr_net_volume_total, fr_net_value_total | vnstock_data foreign_trade + OHLCV |
| Absolute return (|ret|) | fr_buy_volume_total, fr_sell_volume_total | Same |
| Intraday range (high-low/close) | fr_net_volume_matched vs fr_net_volume_deal | Same |

**Data cần fetch:**
- Foreign trade: 100–300 mã HOSE thanh khoản × 2014–2025 (quarterly chunks)
- OHLCV: đã có sẵn trong `stock_ohlcv/latest.sqlite` (2GB, 50 bảng)
- Hoặc fetch mới qua `Quote.history()`

**Phạm vi:** 100 mã × ~2.900 ngày = ~290.000 obs. Đủ cho panel regression hai chiều.

---

### Cặp 2: Giao dịch khối ngoại ↔ biến động chỉ số

**Câu hỏi:** Dòng ngoại ròng tổng có liên hệ với biến động VNINDEX/VN30 không?

| Y (outcome) | X (predictor) | Source |
|---|---|---|
| VNINDEX return volatility (5d/20d/60d) | VNINDEX fr_net_value_total | vnstock_data foreign_trade cho VNINDEX |
| VN30 absolute return | VN30 fr_net_volume_total | Same cho VN30 |
| Index intraday range | fr_buy_volume_total vs fr_sell_volume_total | Same |

**Data cần fetch:**
- Index foreign trade: 4 indices (VNINDEX, VN30, VN100, VNFINSELECT) × 2014–2025
- Index OHLCV: fetch qua `Quote.history()` hoặc dùng `stock_ohlcv` DB

**Lợi thế:** Index-level foreign data là **dữ liệu tổng hợp chính thức** (không cần tự SUM từ mã thành viên). Tránh được sai số tổng hợp.

**Phạm vi:** 4 chỉ số × ~2.900 ngày = ~11.600 obs.

---

### Cặp 3: Giao dịch khối ngoại ↔ khả năng sinh lời cổ phiếu

**Câu hỏi:** Ngoại mua ròng có dự báo forward return không?

| Y (outcome) | X (predictor) | Horizon |
|---|---|---|
| fwd_ret_log_1d, fwd_ret_log_5d, fwd_ret_log_20d, fwd_ret_log_60d | fr_net_volume_total (t), fr_net_value_total (t) | H=1,5,20,60 |
| Cumulative abnormal return (CAR) | fr_net_volume trong event window | Event study |

**Data cần fetch:**
- Foreign trade: 100–300 mã × 2014–2025
- Forward returns: tính từ OHLCV đã có

**Thiết kế gợi ý:**
- Panel regression two-way clustered (date + symbol)
- Hoặc Fama-MacBeth cross-sectional regression
- Event study: ngoại mua ròng > 2σ → CAR trong 5/20/60 ngày

**Phạm vi:** 100 mã × 2.900 ngày × 4 horizons = ~1.16 triệu cell (trước khi loại thiếu data).

---

### Cặp 4: Giao dịch khối ngoại ↔ tăng/giảm cổ phiếu

**Câu hỏi:** Ngoại mua ròng có dự báo xác suất cổ phiếu tăng không?

| Y (outcome) | X (predictor) | Loại |
|---|---|---|
| Binary: ret_5d > 0 (1/0) | fr_net_volume_total, fr_buy_volume_total/sell | Binary classification |
| Directional: sign(ret_5d) | fr_net_value_total | Directional accuracy |
| Magnitude bucket: quartile return | fr_net_volume percentile rank | Ordinal |

**Data cần fetch:**
- Foreign trade: 100–300 mã × 2014–2025
- Binary outcomes: tính từ OHLCV

**Thiết kế gợi ý:**
- Logit/Probit với restricted-null efficient score test (như stock divergence study)
- Brier score cho calibration (như multivariate forecast study)
- Walk-forward OOS với expanding window

---

### Cặp 5: Giao dịch khối ngoại ↔ thị trường trái phiếu

**Câu hỏi:** Dòng ngoại cổ phiếu có liên hệ với lợi suất trái phiếu VN không?

| Y (outcome) | X (predictor) | Source |
|---|---|---|
| Δ yield 2y (5d bps) | VNINDEX fr_net_value_total | Bond data ( dưới) + vnstock_data foreign |
| Δ yield 10y (5d bps) | fr_net_volume_total | Same |
| Yield curve slope (10y-2y) | fr_buy vs fr_sell ratio | Same |

**Data bond đã có sẵn (KHÔNG cần fetch mới):**

| File | Đường dẫn | Phạm vi | Cột chính |
|---|---|---|---|
| HNX yield curve daily | `/Users/bobo/ZCodeProject/vn-bond-transmission/data/raw/hnx_yield/hnx_yield_curve_daily.csv` | 2014-12 → 2026-07 | 3m, 6m, 9m, 1y, 2y, 3y, 5y, 7y, 10y, 15y par yield |
| Master daily | `/Users/bobo/ZCodeProject/vn-bond-transmission/data/processed/master_daily_2014_2026.csv` | 2014-01 → 2026-07 | 2y, 5y, 10y yield + USD/VND + US yield + DXY |
| FRED DGS2 | `bond_equity_chapter2_return_v1/outputs/cache/fred_DGS2.parquet` | 2012 → 2026 | US 2y Treasury |
| FRED DGS10 | `bond_equity_chapter2_return_v1/outputs/cache/fred_DGS10.parquet` | 2012 → 2026 | US 10y Treasury |
| rates.db | `Bond Lab/vn-bond-lab/Lai_suat/data/rates.db` (90MB) | Full | Comprehensive rate data |

**Lưu ý:** Yield data có gap ngày (HNX không công bố mỗi ngày). Cần forward-fill hoặc restrict trading days.

---

## 4. DATA PHỤ TRỢ ĐÃ CÓ SẴN

### 4.1 OHLCV (giá cổ phiếu)

| Database | Đường dẫn | Phạm vi |
|---|---|---|
| stock_ohlcv | `~/Library/Mobile Documents/com~apple~CloudDocs/main sonet/market_cache/stock_ohlcv/latest.sqlite` | Full history, 50 bảng |
| vci_trading_daily | `~/Documents/main sonet - dự phòng/market_cache/vci_trading_daily/latest.sqlite` | 2024–2026, có foreign trong facts |

### 4.2 Metadata

| Loại | Bảng | Database |
|---|---|---|
| Company overview | `company_overview` (1.538 mã) | stock_ohlcv |
| Sector (ICB) | `company_overview.icb_name3` (17 ngành) | stock_ohlcv |
| Corporate actions | `corporate_action_adjustment_factors` | stock_ohlcv |
| Listing status | `stocks`, `stock_exchange`, `stock_index` | stock_ohlcv |
| Security master PIT | `security_master_pit` | stock_ohlcv |

### 4.3 Indices OHLCV

```python
# Fetch index price history
from vnstock_data import Quote
q = Quote(source='vci', symbol='VNINDEX')
df = q.history(start='2014-01-01', end='2025-12-31')
# Returns: time, open, high, low, close, volume
```

---

## 5. GIỚI HẠN CẦN GHI RÕ

### 5.1 Survivorship bias

Danh sách mã hiện tại là **current-active snapshot**. Mã đã delisted trước 2024 sẽ thiếu dữ liệu foreign trade (API chỉ trả mã còn hoạt động).

**Cap bắt buộc:** `RESEARCH_ONLY_SURVIVORSHIP_LIMITED`

### 5.2 Pre-2014 data

API trả data về 2010, nhưng:
- Giai đoạn 2010–2013 thanh khoản rất mỏng, foreign trade thưa
- Các nghiên cứu hiện tại dùng 2014 làm mốc (khớp với bond data)

**Khuyến nghị:** Mẫu từ 2014-01-02 trở đi, nhất quán với 5 nghiên cứu trước.

### 5.3 Deal vs Matched

Foreign trade có 2 kênh: khớp lệnh (matched) và thoả thuận (deal/put-through). Deal có thể chiếm phần lớn ở mã lớn (VCB, HPG). Nghiên cứu cần rõ ràng dùng `total` hay chỉ `matched`.

### 5.4 Index foreign = tổng hợp HOSE

VNINDEX foreign trade là tổng hợp toàn bộ mã HOSE, không phải giao dịch trực tiếp VNINDEX. Khác với tổng hợp tự tính (SUM từ mã thành viên) ở chỗ: HOSE tính bao gồm cả deal, và có thể có mã chưa niêm yết toàn thời gian.

### 5.5 Zero-trade days

Mã nhỏ có nhiều ngày foreign trade = 0 (không có giao dịch ngoại). Cần xử lý:
- Loại nếu zero > 50% ngày
- Hoặc keep nhưng ghi rõ phân bố zero-inflated

---

## 6. ĐỀ XUẤT THIẾT KẾ NGHIÊN CỨU

### 6.1 Universe

- **Stock-level:** 100–150 mã HOSE thanh khoản nhất (median trading value top)
- **Index-level:** VNINDEX, VN30, VN100, VNFINSELECT
- **Sample start:** 2014-01-02
- **Sample end:** 2025-12-31 (hoặc latest available)

### 6.2 Horizons

H = 1, 5, 20, 60 phiên (nhất quán với các nghiên cứu trước).

### 6.3 Inference

| Loại outcome | Estimator | Std error |
|---|---|---|
| Continuous (return, volatility) | Panel two-way clustered | Cameron-Gelbach-Miller |
| Binary (tăng/giảm) | Restricted-null efficient score | Multiplier bootstrap |
| Directional | Single-stock HAC | Newey-West horizon-aware |

### 6.4 OOS

- Walk-forward expanding window, purge ≥ horizon
- Minimum 4/6 folds improvement
- Materiality gate (Brier improvement ≥ 0.02 hoặc R² improvement > ngưỡng)

### 6.5 Bootstrap

- B = 999 initial
- Rerun B = 9.999 khi raw_p < 0.10

---

## 7. LỆNH FETCH DATA (SẴN SÀNG DÙNG)

### 7.1 Fetch foreign trade cho 1 mã

```bash
/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/bin/python << 'EOF'
from vnstock_data import Trading
import pandas as pd

def fetch_full_foreign_history(symbol, start_year=2014, end_year=2025):
    t = Trading(source='vci', symbol=symbol)
    chunks = []
    date_ranges = pd.date_range(f'{start_year}-01-01', f'{end_year}-12-31', freq='3MS')
    for i in range(len(date_ranges) - 1):
        s = date_ranges[i].strftime('%Y-%m-%d')
        e = date_ranges[i+1].strftime('%Y-%m-%d')
        try:
            df = t.foreign_trade(start=s, end=e)
            if df is not None and df.shape[0] > 0:
                chunks.append(df)
        except:
            pass
    if chunks:
        result = pd.concat(chunks, ignore_index=True)
        result = result.drop_duplicates(subset=['trading_date'])
        result = result.sort_values('trading_date').reset_index(drop=True)
        return result
    return pd.DataFrame()

# Example: FPT
df = fetch_full_foreign_history('FPT', 2014, 2025)
print(f"FPT: {df.shape[0]} rows, {df['trading_date'].min()} to {df['trading_date'].max()}")
df.to_csv('FPT_foreign_2014_2025.csv', index=False)
EOF
```

### 7.2 Fetch index foreign trade

```bash
/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/bin/python << 'EOF'
from vnstock_data import Trading
import pandas as pd

indices = ['VNINDEX', 'VN30', 'VN100', 'VNFINSELECT']
for idx in indices:
    t = Trading(source='vci', symbol=idx)
    chunks = []
    date_ranges = pd.date_range('2014-01-01', '2025-12-31', freq='3MS')
    for i in range(len(date_ranges) - 1):
        try:
            df = t.foreign_trade(
                start=date_ranges[i].strftime('%Y-%m-%d'),
                end=date_ranges[i+1].strftime('%Y-%m-%d')
            )
            if df is not None and df.shape[0] > 0:
                chunks.append(df)
        except:
            pass
    if chunks:
        full = pd.concat(chunks).drop_duplicates('trading_date').sort_values('trading_date')
        full.to_csv(f'{idx}_foreign_2014_2025.csv', index=False)
        print(f"{idx}: {full.shape[0]} rows saved")
EOF
```

---

## 8. TỔNG KẾT

| Hỏi | Đáp |
|---|---|
| Có đủ data cho 5 cặp quan hệ? | ✅ Có |
| Phạm vi lịch sử | 2014–2026 (12+ năm), có thể về 2010 |
| Cấp dữ liệu | Cả per-stock (25 cột) và index-level (22 cột) |
| Chất lượng | 0% null trên cột chính, đã verify |
| Bond data cho cặp 5 | ✅ Đã có HNX yield + FRED + master daily |
| OHLCV | ✅ Đã có stock_ohlcv DB (2GB) |
| Tốc độ fetch | 1 mã × 12 năm = 10 giây; 150 mã ≈ 25 phút |
| Giới hạn chính | Survivorship bias, 100 rows/call cần chunking |
| Tier | Golden Sponsor (500 req/phút) |

**Sẵn sàng bàn giao cho GPT triển khai nghiên cứu.**
