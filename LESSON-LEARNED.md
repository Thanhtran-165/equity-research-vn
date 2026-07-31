# Lesson Learned — equity-research-vn

> **Đọc file này TRƯỚC khi chạy pipeline.** 2 lỗi thực tế đã gặp, kèm cách tránh.

---

## Lỗi 1 — VCI source API down, pipeline chết

### Tình huống thật
- `Vnstock().stock(symbol='CTD', source='VCI')` → `KeyError: 'data'`
- `source='KBS'` → `404 Not Found`
- `source='MSN'` → không hỗ trợ trong bản này
- → Pipeline không fetch data → không chạy được

### Cách tránh
```python
# ĐỪNG chỉ dùng 1 API. Thử theo thứ tự:
try:
    # Ưu tiên 1: vnstock_data sponsor gold (ổn định nhất)
    from vnstock_data import Finance
    f = Finance(source='VCI', symbol='CTD')
    inc = f.income_statement()  # KHÔNG có param 'lang'
    bs = f.balance_sheet()
    cf = f.cash_flow()
except:
    # Fallback 2: Vnstock community
    from vnstock import Vnstock
    vs = Vnstock().stock(symbol='CTD', source='VCI')
    inc = vs.finance.income_statement(period='year', lang='en')
```

### Lưu ý quan trọng
- `vnstock_data.Finance` và `vnstock.Vnstock` là **2 API khác nhau** — method khác nhau
- `Finance.__init__` cần `(source='VCI', symbol='CTD')` — positional, không keyword-only
- `Finance.income_statement()` — KHÔNG nhận param `lang`
- `Vnstock().finance.income_statement(period='year', lang='en')` — CÓ param `lang`
- Nếu VCI down hoàn toàn → sponsor gold vẫn có thể hoạt động (khác endpoint)

---

## Lỗi 2 — Source pack thủ công thiếu field → REQ-025 FAIL

### Tình huống thật
- vnstock API lỗi → em tạo source pack thủ công
- `fundamental_sponsor.json` ghi `equity: 0` cho mọi năm (quên lấy từ balance_sheet)
- → PB = price / (equity/shares) = price / 0 → `PB = null`
- → REQ-025 (valuation recompute) FAIL
- → REQ-021 (no deploy if FAIL) cascade FAIL
- → Verifier **bắt đúng** — harness hoạt động chính xác

### Root cause
Data equity **CÓ** trong `balance_sheet_sponsor.csv` (8.2-9.4 nghìn tỷ), nhưng em không copy vào `fundamental_sponsor.json`.

### Cách tránh
```yaml
checklist_source_pack_thủ_công:
  TRƯỚC KHI CHẠY, verify fundamental_sponsor.json có ĐỦ fields:
  
  required_fields_per_year:
    - revenue         # doanh thu (bắt buộc)
    - net_profit      # lợi nhuận sau thuế (bắt buộc)
    - equity          # VỐN CHỦ SỞ HỮU (bắt buộc — hay quên!)
    - total_assets    # tổng tài sản (bắt buộc)
    - cost_of_sales   # giá vốn (cho margin)
    - capex           # chi phí vốn (nếu có)
  
  required_meta:
    - years: [2021, 2022, 2023, 2024, 2025]  # LIST, ĐÚNG 5 năm
    - data: { "2021": {...}, ... }            # DICT keyed by year
    - shares_outstanding_b: 0.6038            # tỷ cổ phiếu

  format_chú_ý:
    years_phải_là: 'LIST [2021, 2022, ...]'  # KHÔNG PHẢI dict
    data_phải_là: 'DICT {"2021": {...}}'      # KHÔNG PHẢI list
    năm_phải_đúng: 'CHÍNH XÁC 5 năm (không 8, không 3)'
```

### Quick pre-check script
```python
import json, sys

fs = json.load(open(sys.argv[1] + '/fundamental_sponsor.json'))
years = fs.get('years', [])
data = fs.get('data', {})

errors = []
if not isinstance(years, list) or len(years) != 5:
    errors.append(f"years phải là list 5 phần tử, got: {type(years)} {years}")
if not isinstance(data, dict):
    errors.append(f"data phải là dict, got: {type(data)}")

for y in years:
    yd = data.get(str(y), {})
    for field in ['revenue', 'net_profit', 'equity', 'total_assets']:
        v = yd.get(field, 0)
        if not v or v == 0:
            errors.append(f"{y}.{field} = {v} — CÓ THỂ THIẾU DATA")

if errors:
    print("⚠️ SOURCE PACK CÓ VẤN ĐỀ:")
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("✓ Source pack OK — đủ fields cho 5 năm")
```

---

## Tổng kết

| Lỗi | Nguyên nhân | Cách tránh | Verifier bắt được? |
|---|---|---|---|
| API down | Pipeline chỉ dùng 1 nguồn | Fallback sponsor gold → community | Không (pipeline chết trước verifier) |
| REQ-025 PB=null | Source pack thiếu equity | Pre-check fields + lấy equity từ CSV | **Có** (verifier bắt đúng) |

**Giá trị harness:** Lỗi 2 chứng minh verifier hoạt động đúng — nếu PB sai, nó FAIL và chặn deploy, không cho PASS giả.
