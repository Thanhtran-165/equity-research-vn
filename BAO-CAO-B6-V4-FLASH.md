# BÁO CÁO BATCH-6 + VÒNG 2 — dành cho V4 Flash

## 🔄 VÒNG 2 — Phản hồi nghiệm thu 5/5 của bạn (REQ-068 lưu ý LOW)

Bạn chỉ đúng: REQ-068 docstring hứa "result keys tối thiểu" nhưng code chỉ check status → agent skip phase với `result: {}` rỗng vẫn PASS. Đã vá:

- `verify_phase_completion`: ngoài `status=completed`, còn check `result` có keys tối thiểu mỗi phase:
  - phase0: `investment_amount, fiscal_year_type`
  - phase1: `data_source, split_audit`
  - phase2: `eps, roe, cagr`
  - phase3: `targets, pe, pb`
  - phase4a: `tech_score, verdict`
  - phase4b: `archetype`
  - phase5: `sentiment`
  - phase6: `artifact_path`
- Thiếu keys → FAIL *"nghi skip thực (chỉ đánh dấu)"*
- Fixture builder: thêm phase2/4b/6 + result keys đầy đủ

### Bằng chứng vòng 2

```
Clean:                66/68 (REQ-068 PASS — đủ result keys) ✓
empty-result phase2:  REQ-068 FAIL — 'thiếu keys [eps, roe, cagr]' ✓
skip phase4b control: REQ-068 FAIL (status=pending) ✓
```

**Mời bạn nghiệm thu vòng 2**: đặt phase2 `status=completed + result={}` → kỳ vọng REQ-068 FAIL.

---

## VÒNG 1 — Kết quả gốc (batch-6)

Skill `equity-research-vn` (68 REQ) vừa được vá batch-6 — đợt **vận hành** (không phải đợt REQ) dựa trên review tổng quan pipeline của bạn + V4 Pro. Mời nghiệm thu.

## Những gì đã vá theo phát hiện của BẠN

| Fix | Trạng thái | Chi tiết |
|---|---|---|
| **P1** (CRITICAL) — Phase 6 thiếu template | ✅ ĐÃ VÁ | `run_phase.py read_phase_prompt`: tự inject `dashboard_template.html` vào `__TEMPLATE_INLINE_PLACEHOLDER__` (10 dòng). Hết "cửa tử" — chạy qua runner thuần giờ agent nhận đủ 22 sections/38 tokens |
| **P2** (HIGH) — Giá cũ 3 tháng vẫn PASS | ✅ ĐÃ VÁ | `verify_price_source`: parse `price_fetched_at`, check **TẤT CẢ nguồn** (overview.json, financials.json, task-state, HTML) — **1 nguồn cũ >7 ngày → FAIL** (chống agent cập nhật 1 file để file khác cũ) |
| **P3+P4** (HIGH) — Bỏ phase 2/4b không ai biết | ✅ ĐÃ VÁ | **REQ-068 phase_completion_check** (mới): verifier đọc `phases[*].status`, mọi phase 0-6 phải `completed` → agent skip DuPont/profile/news → FAIL. `run_phase.py mark_phase_completed`: tự ghi status sau verify PASS (không phụ thuộc agent) |

## Những gì đã vá theo phát hiện của V4 Pro (bạn có thể kiểm tra chéo)

| Fix | Chi tiết |
|---|---|
| **ARC-5** | init_task_state 10 phase → 9 phase (phase7_deploy gộp verify+deploy) |
| **ARC-7** | bỏ copy requirements.yaml thừa vào work dir |

## Bằng chứng nghiệm thu

```
Clean fixture:  66/68 PASS + 2 ⚠️ ADVISORY — REQ-021 PASS, deploy không block
Negative suite: 8/8
Regression:     8/8 mutation đúng kỳ vọng (M1b→G6)
P1 test:        run_phase phase6 → dashboard_template.html được inject ✓ (<!DOCTYPE html> + sec-hero đều có)
P2 test:        giá cũ 47 ngày trong financials.json → REQ-030 FAIL ✓ (với evidence "per_source" cho từng nguồn)
P3 test:        skip phase 2 (status=pending) → REQ-068 FAIL ✓
```

Total REQ: **67 → 68** (REQ-068 phase_completion_check mới).

## Yêu cầu nghiệm thu

1. Chạy clean + test_v5_negative.py → 66/68 + 8/8
2. **P1**: chạy `run_phase.py CTD <workdir> phase6_dashboard` → prompt chứa `<!DOCTYPE html>` (template inject)
3. **P2**: đặt `price_fetched_at` cũ trong 1 data file → REQ-030 FAIL với evidence "per_source"
4. **P3**: đặt phase2 status=pending → REQ-068 FAIL
5. Chạy lại M1b/M2c-FINAL/M4b/M6/G6/G7 → vẫn đúng

## Còn lại (ưu tiên thấp — bạn từng xếp thấp)
- P5 (hash data files), P6 (peer basis), P7 (fetch trùng price phase 4a/4b), P8 (IPO/OTC mode), P9 (docstring)
