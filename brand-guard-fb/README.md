# Brand Guard FB

Tự dò profile Facebook giả mạo thương hiệu — so sánh avatar/cover bằng pHash, chấm điểm rủi ro, sinh bài post cảnh báo + mẫu đơn khiếu nại.

## Quick Start

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb

# Install
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/playwright install chromium

# Copy brand avatar + cover vào config/avatars/
# Edit config/brands.yaml

# QA (compile + test + smoke)
make qa
# or: bash scripts/qa.sh

# Scan (live)
.venv/bin/python -m src.cli --brand chim_cut --alert

# Scan (no network, cache only)
.venv/bin/python -m src.cli --brand chim_cut --no-network

# Inspect cache
.venv/bin/python -m src.cli --inspect-cache
```

## Config

`config/brands.yaml` — định nghĩa brand cần giám sát:

```yaml
brands:
  - id: chim_cut
    display_name: "Chim Cút"
    aliases: ["Chim Cut"]          # biến thể tên kẻ gian dùng
    official_username: chimcutvnindex
    official_page_url: https://www.facebook.com/chimcutvnindex
    avatar_path: ./config/avatars/chim_cut_avatar.jpg
    cover_path: ./config/avatars/chim_cut_cover.png
```

Config validation fail-closed: nếu avatar/cover thiếu, aliases rỗng, URL sai → exit 2.

## CLI Flags

| Flag | Mô tả |
|------|-------|
| `--brand <id>` | Scan 1 brand (mặc định: tất cả) |
| `--alert` | Sinh bài post cảnh báo tiếng Việt |
| `--alert-include-medium` | Bao gồm cả MID trong alert |
| `--generate-complaints` | Sinh đơn Meta IP + SHTT |
| `--no-network` | Chỉ dùng cache, không network |
| `--clear-cache` | Xóa cache trước scan |
| `--use-chrome-profile` | Dùng Chrome profile login FB |
| `--output-dir <dir>` | Output dir cho files (mặc định: .cache/complaints) |
| `--report-json` | Output JSON machine-readable |
| `--inspect-cache` | Xem cache stats |
| `--verbose` | Debug logging |
| `--learn <url>` | Thêm fake vào pattern DB |

## Exit Codes

| Code | Ý nghĩa |
|------|---------|
| 0 | Success |
| 2 | Config/input error |
| 3 | Browser/profile error |
| 4 | Partial failure (quá nhiều fetch fail) |

## Scoring

| Tín hiệu | Trọng số |
|-----------|----------|
| Avatar pHash | 50 |
| Cover pHash | 30 |
| Tên match | 15 |
| Trang mới | 3 |
| URL/username | 2 |

**Bands:** 🔴 HIGH ≥70 | 🟡 MID 40-69 | 🟢 LOW <40

## Cache

- TTL: 7 ngày
- Location: `.cache/page_meta/`
- Brand-namespaced: mỗi entry có `brand_id`
- `--clear-cache` để force re-check
- `--inspect-cache` để xem stats

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Legal Warning

Kết quả là **gợi ý heuristic**. Review bằng chứng thủ công trước khi gửi khiếu nại hoặc hành động pháp lý. Người dùng chịu trách nhiệm về tính chính xác của báo cáo.
