---
name: brand-guard-fb
description: Detect fake Facebook fanpages/profiles impersonating user's brand by avatar + cover photo pHash matching. Outputs a markdown report with risk scores and generates Vietnamese warning post + Meta IP / SHTT Vietnam takedown complaint templates. Use when user reports brand impersonation on Facebook, wants proactive brand protection monitoring, says "fanpage bị giả mạo", "trang Facebook giả", "tìm profile fake Chim Cút", or needs takedown templates for IP infringement.
---

# Brand Guard FB

Tự dò profile Facebook giả mạo thương hiệu (theo avatar + cover photo pHash), chấm điểm rủi ro, và sinh bài post cảnh báo tiếng Việt.

## Khi nào dùng

- Bị lập profile/fanpage giả mạo thương hiệu trên Facebook.
- Muốn giám sát theo yêu cầu (không chạy định kỳ).
- Cần bài post cảnh báo + mẫu đơn khiếu nại Meta/SHTT.

## Logic phát hiện

```
LỚP 1 — Discovery (tìm profile):
  Vào /public/<brand-name> trên Facebook → list profile có display name match

LỚP 2 — Verification (chấm điểm):
  So sánh avatar pHash + cover pHash với brand chính chủ
  - Avatar identical (Hamming=0) → 50 điểm
  - Cover identical (Hamming=0)  → 30 điểm
  - Tên match alias              → 15 điểm
  - Tổng ≥ 70                    → 🔴 CAO → tự sinh alert post
```

**Pattern kẻ gian skill bắt được:**
- Tạo profile mới hoặc dùng profile có sẵn
- Đổi display name gần giống brand (bỏ dấu: "Chim Cut" thay "Chim Cút")
- Coppy avatar + cover từ fanpage chính chủ

## Cách dùng

### 1. Setup (chỉ 1 lần — đã làm xong cho Chim Cút)

Đảm bảo `config/brands.yaml` đã điền brand info. Các trường bắt buộc:
- `display_name`, `aliases[]` — tên chính + biến thể (bỏ dấu, viết liền, đảo)
- `official_username`, `official_page_url` — fanpage chính chủ
- `avatar_path`, `cover_path` — path tới ảnh avatar + cover chính chủ

### 2. Chạy (lệnh chính)

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
source .venv/bin/activate
python -m src.cli --brand chim_cut --alert --sleep-between 2.0
```

### 3. Output

- **Báo cáo markdown** trong stdout: bảng phân nhóm 🔴 CAO / 🟡 TRUNG / 🟢 THẤP
- **Bài post cảnh báo** tiếng Việt (nếu có `--alert`): copy đăng lên fanpage
- **File đơn Meta IP + SHTT** (nếu có `--generate-complaints`): tại `.cache/complaints/`

## Các flag

- `--brand <id>` — chỉ scan 1 brand trong config (vd `chim_cut`)
- `--alert` — sinh bài post cảnh báo tiếng Việt (copy đăng fanpage)
- `--alert-include-medium` — liệt kê cả profile 🟡 TRUNG trong post
- `--generate-complaints` — sinh thêm file đơn Meta IP + SHTT cho trang 🔴
- `--signatory-name/title/email` — thông tin người ký đơn (cho --generate-complaints)
- `--no-network` — chỉ dùng cache, không gọi network
- `--sleep-between <s>` — sleep giữa các fetch (mặc định 2.0s)
- `--use-chrome-profile` / `--connect-chrome` — dùng session login FB (tùy chọn nâng cao)

## Workflow khuyến nghị

**Hàng tuần / khi có báo cáo fake mới:**
```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
source .venv/bin/activate
python -m src.cli --brand chim_cut --alert
```
→ Copy post từ output → đăng lên fanpage Chim Cút.

**Khi muốn khiếu nại chính thức Meta/SHTT:**
```bash
python -m src.cli --brand chim_cut --alert --generate-complaints \
  --signatory-name "Tên bạn" \
  --signatory-title "Page Admin" \
  --signatory-email "email@chimcut.vn"
```
→ Mở file đơn tại `.cache/complaints/` → điền chỗ `[YOUR ...]` → nộp.

## Luật chấm điểm (5 tín hiệu, tổng 100)

| Tín hiệu | Trọng số | Lớp |
|---|---|---|
| Avatar pHash | 50 | Verification (quyết định) |
| Cover pHash | 30 | Verification (quyết định) |
| Tên | 15 | Discovery (filter) |
| Trang mới | 3 | Bonus |
| Username/URL | 2 | Bonus |

**Phân loại:** 🔴 CAO ≥70 (sinh đơn+alert), 🟡 TRUNG 40-69, 🟢 THẤP <40.
**Verified page** → total=0 (chính chủ).
**URL chính chủ** → total=0 (whitelist).

## Lưu ý

- **Không** scraping cần đăng nhập — avatar + cover public đều thấy được.
- **Không** vi phạm ToS Facebook rõ ràng.
- Kết quả là **gợi ý heuristic** — review tay trước khi hành động pháp lý.
- Skill tự mở ephemeral browser riêng (không xung đột Chrome chính).

## Spec & Plan

- Spec: `docs/superpowers/specs/2026-07-05-brand-guard-fb-design.md`
- Plan: `docs/superpowers/plans/2026-07-05-brand-guard-fb.md`
