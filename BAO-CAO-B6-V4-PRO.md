# BÁO CÁO BATCH-6 (VẬN HÀNH) — dành cho V4 Pro

Skill `equity-research-vn` (68 REQ) vừa được vá batch-6 — đợt **vận hành** (không phải đợt REQVerifier) dựa trên review tổng quan pipeline của bạn + V4 Flash. Mời nghiệm thu.

## Những gì đã vá theo phát hiện của BẠN

| Fix | Trạng thái | Chi tiết |
|---|---|---|
| **ARC-5** — đồng bộ tên phase | ✅ ĐÃ VÁ | `init_task_state.py`: 10 phase → **9 phase** (bỏ `phase7_verify`/`phase8_deploy` thừa, gộp vào `phase7_deploy`) — đồng bộ với `run_phase.py` PHASES list. REQ-068 giờ đọc đúng phase schema |
| **ARC-7** — bỏ copy requirements.yaml thừa | ✅ ĐÃ VÁ | `init_task_state.py`: xóa `shutil.copy(req_src, req_dst)` — verifier đọc từ SKILL_DIR, không từ WORK_DIR → artifact rác bị dọn |

## Những gì đã vá theo phát hiện của V4 Flash (bạn có thể kiểm tra chéo)

| Fix | Chi tiết |
|---|---|
| **P1** (CRITICAL) — inject template phase 6 | `run_phase.py read_phase_prompt`: tự inject `dashboard_template.html` vào `__TEMPLATE_INLINE_PLACEHOLDER__` — hết "cửa tử" khi chạy qua runner |
| **P2** (HIGH) — REQ-030 freshness giá | Parse `price_fetched_at`, check TẤT CẢ nguồn (overview/financials/task-state/HTML) — 1 nguồn cũ >7 ngày → FAIL |
| **P3+P4** (HIGH) — REQ-068 phase_completion_check (MỚI) | Verifier đọc `phases[*].status` — mọi phase 0-6 phải `completed`. `run_phase` tự ghi status sau verify PASS |

## Bằng chứng nghiệm thu

```
Clean fixture:  66/68 PASS + 2 ⚠️ ADVISORY — REQ-021 PASS, deploy không block
Negative suite: 8/8
Regression:     8/8 mutation đúng kỳ vọng (M1b→G6)
P1 test:        run_phase phase6 → dashboard_template.html được inject ✓
P2 test:        giá cũ 47 ngày trong financials.json → REQ-030 FAIL ✓
P3 test:        skip phase 2 (status=pending) → REQ-068 FAIL ✓
```

Total REQ: **67 → 68** (REQ-068 phase_completion_check mới).

## Yêu cầu nghiệm thu

1. Chạy clean + test_v5_negative.py → 66/68 + 8/8
2. Kiểm ARC-5: `init_task_state.py` giờ 9 phase (không còn phase7_verify/phase8_deploy)
3. Kiểm ARC-7: `.task-state/requirements.yaml` không còn được copy
4. Chạy lại M1→M5 + ARC mutation → vẫn đúng

## Còn lại (ưu tiên thấp, bạn từng xếp thấp)
- ARC-1 (tách module verifier — cần test ≥50% trước), ARC-2 (phase 6 god phase 44 REQ), ARC-3 (thêm test), ARC-4 (task-state schema), ARC-6 (tách REQ khỏi prompt), ARC-8 (env var path)
