---
name: brand-guard-fb
description: Detect fake Facebook fanpages/profiles impersonating user's brand by avatar + cover photo pHash matching. Outputs a markdown report with risk scores and generates Vietnamese warning post + Meta IP / SHTT Vietnam takedown complaint templates. Use when user reports brand impersonation on Facebook, wants proactive brand protection monitoring, says "fanpage bị giả mạo", "trang Facebook giả", "tìm profile fake Chim Cút", or needs takedown templates for IP infringement.
---

# Brand Guard FB

Tự dò profile Facebook giả mạo thương hiệu (theo avatar + cover photo pHash), chấm điểm rủi ro, và sinh bài post cảnh báo tiếng Việt.

## Setup

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/playwright install chromium
```

Copy avatar + cover thật vào `config/avatars/`. Edit `config/brands.yaml`.

Config fail-closed: nếu avatar/cover thiếu, aliases rỗng, URL sai → exit 2.

## QA (1 lệnh)

```bash
make qa        # compile + test + no-network smoke
# or:
bash scripts/qa.sh
```

## Run Modes

### No-network (cache only — safe, no Facebook calls)
```bash
.venv/bin/python -m src.cli --brand chim_cut --no-network
```
Re-score cached profiles. In ra cache stats: valid + stale count.

### Live scan (mặc định — không login)
```bash
.venv/bin/python -m src.cli --brand chim_cut --alert
```
Dùng `/public/<name>` directory + search engine dorks. Mở ephemeral browser.

### Live scan với Chrome profile (login FB — mạnh hơn)
```bash
# Yêu cầu: đóng Chrome hoàn toàn (Cmd+Q)
.venv/bin/python -m src.cli --brand chim_cut --alert --use-chrome-profile --sleep-between 3
```
Dùng FB search bar (Graph Search) → bắt được stolen_profile_renamed.
**Caveat:** Profile copy có thể không decrypt được FB cookies cross-browser. Nếu lỗi, dùng Browser MCP login trực tiếp.

## Cache Management

```bash
# Inspect cache stats
.venv/bin/python -m src.cli --inspect-cache

# Inspect cho 1 brand
.venv/bin/python -m src.cli --brand chim_cut --inspect-cache

# Clear cache (force re-check)
.venv/bin/python -m src.cli --brand chim_cut --clear-cache
```

- TTL: 7 ngày
- Cache namespace theo `brand_id` — không cross-contamination
- Avatar local files persistent (slug = SHA1 hash URL)

## Interpreting Results

| Band | Score | Ý nghĩa |
|------|-------|---------|
| 🔴 HIGH | ≥70 | Avatar/cover khớp mạnh (pHash distance ≤4) — rất có thể giả mạo |
| 🟡 MID | 40-69 | Tên giống + avatar một phần khớp — cần kiểm tra thêm |
| 🟢 LOW | <40 | Chỉ tên giống, avatar khác — ít rủi ro |

**⚠️ Alert post phân biệt rõ:**
- HIGH → "🔴 XÁC NHẬN" (avatar khớp)
- MID → "🟡 NGHI VẤN" (cần kiểm tra)
- Không gọi MID là "đã xác nhận"

## Flags

- `--brand <id>` — scan 1 brand (mặc định: tất cả)
- `--alert` — sinh bài post cảnh báo
- `--alert-include-medium` — bao gồm MID
- `--generate-complaints` — đơn Meta IP + SHTT
- `--no-network` — cache only
- `--clear-cache` — xóa cache
- `--use-chrome-profile` — session login FB
- `--output-dir <dir>` — output dir (mặc định: .cache/complaints)
- `--report-json` — JSON output cho automation
- `--inspect-cache` — cache stats
- `--verbose` — debug logging
- `--learn <url>` — thêm fake vào pattern DB

## Exit Codes

- 0: success
- 2: config/input error
- 3: browser/profile error
- 4: partial failure

## Legal Warning

Kết quả là gợi ý heuristic. Review bằng chứng thủ công trước khi hành động pháp lý. Người dùng chịu trách nhiệm về tính chính xác.

## Tests

```bash
.venv/bin/python -m pytest -q
```
