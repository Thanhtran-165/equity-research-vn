# Tổng hợp hiện trạng dữ liệu khối ngoại (Foreign Investor Flow)

**Ngày khảo sát:** 2026-07-15
**Mục đích:** Đánh giá nguồn dữ liệu khối ngoại hiện có, giới hạn, và khi nào nên mở nghiên cứu mới.

---

## 1. Kết luận ngắn

Có dữ liệu khối ngoại mua/bán ròng **đầy đủ ở cấp từng mã cổ phiếu**, nhưng chỉ trong **phạm vi 2 năm (2024-01-02 → 2026-01-08)**. Không có dữ liệu ở cấp index. Dữ liệu chất lượng cao: 100% non-null, 50+ cột chi tiết.

**Chưa đủ để mở nghiên cứu mới ngay** vì 2 năm là quá ngắn cho OOS nghiêm ngặt. Nên dùng khi mở rộng được lịch sử về 2014 trở đi.

---

## 2. Nguồn dữ liệu

### Nguồn chính (đã có sẵn)

| Thuộc tính | Giá trị |
|---|---|
| Database | `vci_trading_daily/latest.sqlite` |
| Đường dẫn | `/Users/bobo/Documents/main sonet - dự phòng/market_cache/vci_trading_daily/latest.sqlite` |
| Kích thước | 2.531 MB |
| Bảng chính | `vci_trading_daily_facts` |
| Số dòng | 726.982 |
| Số mã duy nhất | 1.578 |
| Phạm vi ngày | 2024-01-02 → 2026-01-08 |
| Resolution | Daily (1D) |
| Nguồn gốc | VCI GraphQL `TickerPriceHistory` |
| Collector script | `market/src/vci_trading_daily_facts_db.py` |

### Nguồn dự phòng

| Database | Đường dẫn | Có foreign? |
|---|---|---|
| `stock_ohlcv/latest.sqlite` | `market_cache/stock_ohlcv/` | ❌ Chỉ có `foreigner_percentage` (ownership %, không phải flow) |
| `vietnam_stocks.db` | `Báo cáo tài chính/` | ❌ Không có foreign trade flow |

---

## 3. Cột dữ liệu khối ngoại có sẵn

Bảng `vci_trading_daily_facts` có **50+ cột khối ngoại** cho mỗi mã, mỗi ngày. Đầy đủ 100% non-null trên toàn bộ 726.982 dòng.

### Nhóm cột chính

**Khối lượng (Volume):**
- `fr_buy_volume_matched` — KL ngoại mua khớp lệnh
- `fr_sell_volume_matched` — KL ngoại bán khớp lệnh
- `fr_buy_volume_deal` — KL ngoại mua thoả thuận
- `fr_sell_volume_deal` — KL ngoại bán thoả thuận
- `fr_buy_volume_total` — KL ngoại mua tổng
- `fr_sell_volume_total` — KL ngoại bán tổng

**Giá trị (Value, VND):**
- `fr_buy_value_matched` / `fr_sell_value_matched`
- `fr_buy_value_deal` / `fr_sell_value_deal`
- `fr_buy_value_total` / `fr_sell_value_total`

**Ròng (Net):**
- `fr_net_volume_total` — KL ròng (mua − bán)
- `fr_net_value_total` — GT ròng (VND)
- `fr_net_volume_matched` / `fr_net_value_matched`
- `fr_net_volume_deal` / `fr_net_value_deal`

**Room ngoại:**
- `fr_total_room` — Tổng room
- `fr_current_room` — Room còn lại
- `fr_available_percentage` — % room còn trống
- `fr_room_percentage` — % room đã dùng
- `fr_owned_percentage` — % sở hữu ngoại hiện tại

### Mức độ đầy đủ

| Kiểm tra | Kết quả |
|---|---|
| FPT: `fr_buy_volume_total` non-null | 360/360 (100%) |
| FPT: `fr_net_volume_total` non-null | 360/360 (100%) |
| Toàn bộ DB: `fr_buy_volume_total` non-null | 726.982/726.982 (100%) |
| Toàn bộ DB: `fr_net_volume_total` non-null | 726.982/726.982 (100%) |

---

## 4. Phân loại mã theo sàn

| Phân loại | Số mã | Số dòng |
|---|---|---|
| HOSE 3 ký tự (ACP, FPT, VCB...) | 1.427 | 654.879 |
| HOSE 4–6 ký tự | trong "OTHER" | 63.133 |
| Index (VNINDEX, VN30...) | 18 | 8.970 |

**Lưu ý quan trọng:** 18 "index" symbols (VNA, VNB, VNC...) là ETF/fund codes, **không phải VNINDEX/VN30**. VNINDEX và VN30 là chỉ số tính toán, không phải mã giao dịch — **không có foreign buy/sell trực tiếp**.

---

## 5. Giới hạn nghiêm trọng

### Giới hạn 1: Chỉ có 2 năm dữ liệu

```
2024:  339.930 rows,  1.554 symbols
2025:  385.450 rows,  1.578 symbols
2026:    1.602 rows,    401 symbols (chỉ đến 2026-01-08)
```

**Hệ quả:** Không đủ cho nghiên cứu yêu cầu OOS dài hạn. Các nghiên cứu hiện tại trong ResearchLab đều dùng mẫu từ 2014 trở đi. 2 năm data khối ngoại không khớp chuẩn này.

### Giới hạn 2: Không có dữ liệu cấp index

VNINDEX, VN30, VN100 là chỉ số — không giao dịch trực tiếp, không có dòng ngoại mua/bán riêng. Muốn phân tích "ngoại ròng → VNINDEX", phải **tổng hợp từ tất cả mã thành viên**:

```sql
SELECT trading_date,
       SUM(fr_net_value_total) as market_net_foreign_value
FROM vci_trading_daily_facts
GROUP BY trading_date
```

Đây là **xấp xỉ thị trường**, không phải số liệu chính thức của HOSE (HOSE công bố tổng 외 ròng riêng, có thể chênh vài % do xử lý thoả thuận).

### Giới hạn 3: vnstock API không hỗ trợ

| API | Trạng thái |
|---|---|
| `vnstock.Trading.foreign_trade()` (v3.5.1) | ❌ NotImplementedError ở cả VCI và KBS |
| `vnstock.Trading.foreign_trade()` (v4.0.4) | ❌ Vẫn chưa implement |
| `vnstock.Trading.price_board()` | ✅ Có foreign live, nhưng **chỉ snapshot hôm nay**, không lịch sử |
| VCI GraphQL `TickerPriceHistory` (direct) | ⚠️ Collector script từng chạy được, nhưng test độc lập trả `{}` rỗng |

---

## 6. Cách mở rộng lịch sử (khi cần)

### Đã có sẵn

Collector script `vci_trading_daily_facts_db.py` đã fetch được 2024–2026. Chạy `--incremental` sẽ cập nhật về trước:

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/main\ sonet/market
python3 src/vci_trading_daily_facts_db.py snapshot \
    --start 2014-01-01 --end 2023-12-31
```

### Rủi ro

1. **VCI GraphQL có thể không trả data trước 2024** — cần test lại với session đúng.
2. **Rate limit** — fetch 1.500 mã × 10 năm = ~375.000 dòng, cần checkpoint.
3. **Survivorship bias** — mã đã delisted trước 2024 sẽ thiếu.

---

## 7. Đề xuất hướng nghiên cứu (khi có data đủ)

### Khả thi ngay với data 2024–2026

| Nghiên cứu | Mô tả | OOS khả thi? |
|---|---|---|
| Ngoại ròng mã → return cổ phiếu (1–20 phiên) | Panel regression fr_net_volume → forward_return | ⚠️ 2 năm, OOS ngắn |
| Tập trung dòng ngoại → đảo chiều | Top-N mã ngoại mua/bán mạnh → VNINDEX | ⚠️ Tổng hợp, không chính thức |
| Room ngoại → tốc độ giải | fr_current_room depletion → giá | ✅ Cross-sectional |
| Phân kỳ giá–ngoại ròng | Giá giảm + ngoại mua ròng → hồi phục? | ⚠️ 2 năm |

### Cần mở rộng lịch sử trước

| Nghiên cứu | Lý do cần dài hơn |
|---|---|
| Ngoại ròng → VNINDEX (Granger) | Cần chu kỳ gấu/bò khác nhau |
| So sánh dòng ngoại qua các chế độ thị trường | 2 năm chỉ 1 chế độ |
| Xây chỉ báo ngoại ròng vận hành | Cần OOS nhiều giai đoạn |

### Không khả thi với dữ liệu hiện tại

| Nghiên cứu | Lý do |
|---|---|
| Foreign flow cấp index chính thức | Index không giao dịch, không có foreign trực tiếp |
| Dòng ngoại trong chu kỳ gấu 2011–2012, 2022 | Chưa fetch data về trước |

---

## 8. Khi nào nên mở nghiên cứu mới

**Khuyến nghị:** Mở nghiên cứu khi **đồng thời** thoả:

1. ✅ Đã mở rộng dữ liệu khối ngoại về 2014 tối thiểu (10+ năm)
2. ✅ Đã giải quyết được VCI GraphQL session để fetch lịch sử
3. ✅ Có ít nhất 1 chu kỳ gấu+bò đầy đủ trong mẫu

Với data hiện tại (2 năm), nghiên cứu sẽ phải cap `RESEARCH_ONLY_SHORT_HISTORY` — giới hạn tương tự `RESEARCH_ONLY_SURVIVORSHIP_LIMITED` mà các báo cáo hiện tại đang dùng.

---

## Phụ lục: Lệnh kiểm tra nhanh

```sql
-- Xem dữ liệu khối ngoại của 1 mã
SELECT trading_date, symbol, close,
       fr_buy_volume_total, fr_sell_volume_total,
       fr_net_volume_total, fr_net_value_total
FROM vci_trading_daily_facts
WHERE symbol = 'FPT'
ORDER BY trading_date DESC LIMIT 10;

-- Tổng hợp ngoại ròng toàn thị trường theo ngày
SELECT trading_date,
       SUM(fr_net_value_total) as market_net_foreign,
       SUM(fr_buy_value_total) as total_buy,
       SUM(fr_sell_value_total) as total_sell
FROM vci_trading_daily_facts
WHERE trading_date >= '2025-12-01'
GROUP BY trading_date ORDER BY trading_date DESC;

-- Top mã ngoại mua ròng trong 1 ngày
SELECT symbol, fr_net_volume_total, fr_net_value_total
FROM vci_trading_daily_facts
WHERE trading_date = '2026-01-08'
ORDER BY fr_net_volume_total DESC LIMIT 20;
```
