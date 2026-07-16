# Plan: Tạo skill `frontend-polish` — dispatcher chọn skill MengTo theo ngữ cảnh

## Mục tiêu
Tạo 1 skill ZCode tên `frontend-polish` đóng vai trò "vòng nghiệm thu cuối" cho frontend. Skill là **thuần dispatcher**: đọc task → quét catalog 73 skill MengTo → tự chọn 3–5 skill phù hợp nhất → load vào context → áp dụng. Không thêm logic audit riêng.

## Kiến trúc

```
/Users/bobo/.zcode/skills/frontend-polish/
├── SKILL.md                         # dispatcher logic + routing catalog
├── agents/openai.yaml               # UI metadata
└── references/
    └── catalog.md                   # 73 skill: name + description + category + sub-theme

/Users/bobo/.zcode/skills/_mengto-skills/    # clone nguyên repo MengTo (external shared folder, dấu _)
└── agent-skills/{codex,media,ui,web-design}/<skill>/SKILL.md
```

Lý do tách `_mengto-skills/` ra ngoài: đó là tài sản của người khác (MIT license), tách bạch với logic skill của bạn, dễ `git pull` update khi MengTo có skill mới mà không đụng code của bạn. Pattern này khớp với `_viz-shared/` đã có sẵn của bạn.

## Quy trình dispatcher (logic trong SKILL.md)

1. **Nhận task** + xác định loại output (dashboard / báo cáo / landing page / animation / 3D...)
2. **Đọc** `references/catalog.md` (~10K tokens) — chứa 73 dòng dạng bảng: `name | category | sub-theme | description`
3. **Chọn 3–5 skill** phù hợp nhất theo ma trận routing (cho sẵn trong SKILL.md):
   - Báo cáo/dashboard tài chính → `editorial-tech`, `beautiful-shadows`, `gsap`, `tailwindcss`
   - Landing page → `landing-page`, `pricing-page`, `css-border-gradient`, `marquee-loop`
   - Có 3D/WebGL → `threejs`, `globe-gl`, `cobejs`
   - Animation cuộn → `animation-on-scroll`, `cinematic-gsap-lenis-motion-system`
   - Phong cách tối giản → `dark-glass-clean-layout`, `mesh-gradient-dark-blue-clean`
4. **Load SKILL.md** của từng skill đã chọn từ `../_mengto-skills/agent-skills/<cat>/<skill>/SKILL.md`
5. **Áp dụng** theo workflow của mỗi skill (chỉ đổi 1–2 thứ / lần)
6. **Báo cáo** skill nào đã áp dụng + kết quả

## Các file cụ thể sẽ tạo

### 1. Clone repo MengTo → `_mengto-skills/`
```bash
git clone https://github.com/MengTo/Skills.git /Users/bobo/.zcode/skills/_mengto-skills
```
Sau đó xoá `.git/` để không thành nested repo (skill folder không nên chứa `.git` riêng — ngoại trừ `vn-rates-weekly`/`vn-macro-monthly` đã có sẵn).

### 2. `frontend-polish/SKILL.md` (~150 dòng)
Frontmatter:
```yaml
---
name: frontend-polish
description: Nghiệm thu & hoàn thiện frontend — dispatcher chọn 3-5 skill từ thư viện MengTo (73 skill web-design) phù hợp ngữ cảnh rồi áp dụng. Use khi user nói "polish frontend", "làm đẹp web", "nghiệm thu UI", "audit frontend", "hoàn thiện dashboard/báo cáo HTML", "make it pretty", hoặc trước khi deploy 1 trang HTML/dashboard. Cốt lõi = routing catalog + progressive disclosure (chỉ load skill cần dùng).
---
```
Body (tiếng Việt + English terms, theo style `equity-research-vn`):
- `## Cách dùng` — 1 câu: "Cho skill đường dẫn tới file HTML/folder frontend cần polish"
- `## Workflow` — 6 bước dispatcher ở trên
- `## Routing matrix` — bảng ánh xạ loại-output → skill gợi ý (anchor, không ép cứng — AI được linh hoạt chọn thêm)
- `## Progress reporting` — format báo cáo skill nào đã áp dụng
- `## Lưu ý` — "chỉ load skill khi cần, đừng load cả 73", "MengTo skill là reference, không sửa"

### 3. `frontend-polish/references/catalog.md` (~73 dòng bảng)
Bảng 4 cột sinh bằng cách scan frontmatter của 73 SKILL.md:
```
| name | category | sub-theme | description (Use when...) |
|------|----------|-----------|---------------------------|
| landing-page | web-design | conversion | Use when designing a high-converting landing page... |
| beautiful-shadows | web-design | css-treatments | Use when compact cards... |
| gsap | web-design | motion | ... |
...
```
Sub-theme lấy từ README của MengTo (web-design được nhóm sẵn: conversion, motion, webgl, css-treatments, layout, visual-moods).

### 4. `frontend-polish/agents/openai.yaml`
```yaml
interface:
  display_name: Frontend Polish
  short_description: Nghiệm thu frontend — dispatcher chọn skill MengTo phù hợp
  default_prompt: "Polish frontend tại [PATH/URL] — chọn skill phù hợp rồi áp dụng"
```

## Build sequence (8 task)

1. Clone MengTo → `_mengto-skills/`, xoá `.git/`
2. Viết script Python tạm: scan toàn bộ `SKILL.md` trong `_mengto-skills/`, xuất ra `catalog.md` (dạng bảng)
3. Chạy script → sinh `references/catalog.md`
4. Viết `frontend-polish/SKILL.md` (frontmatter + workflow + routing matrix)
5. Viết `frontend-polish/agents/openai.yaml`
6. Chạy `quick_validate.py frontend-polish` để kiểm tra
7. Xoá script tạm (không giữ lại trong skill)
8. Forward-test: bảo 1 subagent "polish [1 file HTML thực tế của user, vd HPG_Financial_Dashboard.html]" → xem nó có tự chọn đúng skill + load + áp dụng không

## Rủi ro & cách xử lý
- **Rủi ro**: catalog quá dài → xử lý bằng cách tách catalog ra `references/` (progressive disclosure), SKILL.md chỉ giữ routing matrix gọn
- **Rủi ro**: AI load nhầm skill → routing matrix trong SKILL.md làm anchor, nhưng cho phép linh hoạt
- **Rủi ro**: MengTo update repo → user chỉ cần `git pull` trong `_mengto-skills/` rồi chạy lại script sinh catalog
- **Lưu ý license**: repo MengTo là MIT → được phép dùng/sửa, chỉ cần giữ attribute (catalog sẽ ghi nguồn)