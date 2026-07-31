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

---

## Lỗi 3 — "Góc nhìn khoản đầu tư" hardcode 800 triệu, không hỏi quy mô vốn

### Tình huống thật
- Phase 6 (dashboard) render section "Góc nhìn khoản đầu tư 800 triệu VND"
- Agent tự chọn 800 triệu — KHÔNG hỏi user
- Skill design KHÔNG có chỗ nào yêu cầu hỏi quy mô vốn
- Mỗi lần chạy có thể ra số khác nhau (không deterministic)

### Vấn đề
- Section "khoản đầu tư" không có ý nghĩa nếu không biết vốn thật của người dùng
- Hardcode 800 triệu không phù hợp cho mọi người (với người có 50 triệu thì 800 triệu là vô nghĩa)

### Cách tránh
```yaml
đề_xuất_sửa_skill:
  phase_0_hoặc_1: 'Hỏi user: "Anh muốn xem góc nhìn với quy mô vốn bao nhiêu VND?"'
  default_nếu_không_chỉ_định: 'Bỏ section này, hoặc dùng 3 mức (100tr / 500tr / 1 tỷ)'
  lưu_vào: 'task-state.json field "investment_amount"'
  phase_6: 'Đọc investment_amount từ task-state → render đúng số'
```

### REQ liên quan
- Không có REQ nào kiểm tra điều này → **cần thêm REQ** hoặc sửa phase 6 spec
- Đây là vấn đề UX/personalization, không phải data correctness

---

## Lỗi 4 — Peer Comparison data từ bộ nhớ agent, không từ API

### Tình huống thật
- Section 9 "Peer Comparison" hiển thị scatter chart với HBC, C4G, FCN, DXG
- P/B, CAGR, vốn hóa của các peer = **agent tự ghi từ bộ nhớ**
- KHÔNG có API call nào fetch peer data
- Text nói "Hòa Bình, Ricons, Coteccons" nhưng chart dùng HBC, C4G, FCN, DXG → không nhất quán
- DXG (Đại Từ Gate) đã hủy niêm yết → data hoàn toàn sai

### Vấn đề
- Peer data **KHÔNG verify được** — không có source
- Có thể chứa ticker đã hủy niêm yết (DXG, HBC)
- P/B, CAGR có thể cũ hoặc sai
- Verifier REQ-022 chỉ check CTD data, **không check peer data** → lọt verifier

### Cách tránh
```yaml
đề_xuất_sửa_skill:
  phase_1: 'Fetch data cho 4-5 peer cùng ngành (P/B, CAGR, market_cap)'
           'Lưu vào verified-dashboard-data.json field "peers"'
  phase_6: 'Render scatter từ DATA.peers (verified), KHÔNG từ bộ nhớ agent'
  verifier: 'REQ-022 mở rộng: check peer data cũng phải có source path'
  
  hoặc_nếu_không_có_API:
    'Bỏ scatter chart, chỉ hiển thị text comparison'
    'KHÔNG render số liệu không có source'
```

### REQ liên quan
- REQ-022 (data accuracy): hiện chỉ check CTD → **cần mở rộng check peer**
- REQ-027 (external claim): peer data là external claim → cần flag source
