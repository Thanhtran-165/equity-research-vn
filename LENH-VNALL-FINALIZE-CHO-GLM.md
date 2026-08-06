# LỆNH VNALL FINALIZE: (1) re-render 343 mã industrial · (2) gom chỉ số định giá

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-06
**Điều kiện:** VNALL resector đã xong (628 mã 74/74, 11 ngành). Builder đã thêm nhóm 13 "CÔNG NGHIỆP & SẢN XUẤT" (commit 1667b129d).

---

## 1. CẬP NHẬT BUILDER + PACK (bắt buộc)

```bash
# Lấy bản mới nhất từ repo Thanhtran-165/equity-research-vn:
#   scripts/build_report.py  (map 'industrial' → nhóm 13)
#   references/sector_pack.md (nhóm 13 CÔNG NGHIỆP & SẢN XUẤT)
#   scripts/vnall_dashboard.py (dashboard mới — tham khảo)
cp .../scripts/build_report.py ~/.zcode/skills/equity-research-vn/scripts/build_report.py
cp .../references/sector_pack.md ~/.zcode/skills/equity-research-vn/references/sector_pack.md
```

## 2. VIỆC 1 — Re-render 343 mã "industrial" (nhóm 13 mới)

- 343 mã có `sector == "industrial"` trong `/tmp/vnall_tracker.json` hiện hiển thị nhóm
  "12. NGÀNH KHÁC" — giờ sẽ là "13. CÔNG NGHIỆP & SẢN XUẤT".
- Chạy lại với `--reuse` (không gọi API tài chính, chỉ 1 call news/mã, sleep 15-30s):
  ```bash
  python3 ~/.zcode/skills/equity-research-vn/scripts/build_report.py <TICKER> industrial --reuse
  ```
- Cập nhật tracker (recall/fails mới, giữ sector industrial). Mã mất data → ghi `reuse_data_missing`.

## 3. VIỆC 2 — Gom chỉ số định giá cho dashboard (886 mã có data)

Mỗi mã `done`/`needs_human` có file `/tmp/vn100_<TICKER>/verified-dashboard-data.json`
chứa `pe`, `pb`, `roe`, `marketCap`, `pe5med`, `pe_normalized`. Gom 1 file:

```python
# /tmp/vnall_metrics.py
import json, os
tr = json.load(open('/tmp/vnall_tracker.json'))
out = {}
for t in tr['tickers']:
    if t['status'] == 'NO_DATA':
        continue
    p = f"/tmp/vn100_{t['ticker']}/verified-dashboard-data.json"
    if not os.path.exists(p):
        out[t['ticker']] = {'missing': True}
        continue
    d = json.load(open(p))
    out[t['ticker']] = {
        'sector': t.get('sector'), 'status': t['status'], 'recall': t.get('recall'),
        'pe': d.get('pe'), 'pb': d.get('pb'), 'pe5med': d.get('pe5med'),
        'pe_normalized': d.get('pe_normalized'), 'roe': (d.get('roe') or [None])[-1],
        'mcap_bn': d.get('marketCap'), 'price': d.get('price'),
    }
json.dump(out, open('/tmp/vnall_metrics.json', 'w'), ensure_ascii=False)
print('metrics:', len(out))
```

Báo cáo: số mã gom được / thiếu file.

## 4. BÁO CÁO (file `/tmp/VNALL-REPORT-FINALIZE.md`)

1. Việc 1: số mã industrial re-render thành công, trước-sau recall (nhóm 13 phải không gây fail mới).
2. Việc 2: số mã gom metrics, số mã thiếu file.
3. Cập nhật 1 dòng tổng: tổng 74/74 sau tất cả (kỳ vọng ≥628).

## 5. LƯU Ý

- KHÔNG sửa builder/renderer. `--reuse` lỗi → copy stack trace vào báo cáo.
- KHÔNG chạy lại fetch cho mã mất data.
- Xong → ZCode làm dashboard nâng cấp (thêm cột định giá P/E, P/B) từ `/tmp/vnall_metrics.json`.

**Ký:** ZCode — 2026-08-06
