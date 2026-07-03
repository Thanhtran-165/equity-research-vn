# Dịch "In Gold We Trust 2026" + Skill `translate-doc` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dịch toàn bộ báo cáo "In Gold We Trust 2026" (464 trang, 29 chương) sang tiếng Việt với độ chính xác thuật ngữ cao, đồng thời xây dựng skill `translate-doc` tổng quát để tái sử dụng.

**Architecture:** Approach Hybrid lặp — dịch chương mẫu → xây skill v1 → dịch batch kiểm chứng → tinh chỉnh skill → dịch nốt → QC toàn cục. Mỗi chương là 1 file Markdown độc lập trong `igwt2026-vi/`. Glossary song ngữ build dần để đảm bảo nhất quán. Skill `translate-doc` tại `~/.zcode/skills/translate-doc/` gồm SKILL.md + 5 reference files.

**Tech Stack:** `pdftotext` (poppler) để trích xuất PDF; Markdown cho output; git cho version control; cú pháp footnote `[^n]` cho chú thích thuật ngữ.

**Spec:** `/Users/bobo/ZCodeProject/docs/superpowers/specs/2026-07-03-translation-skill-design.md`

---

## Quy trình dịch 7 bước (áp dụng cho MỖI chương)

Mỗi task dịch chương đều tuân theo 7 bước dưới đây. Task sẽ gọi cụ thể range trang + tên file. Các bước luôn lặp lại nên được định nghĩa một lần ở đây:

1. **Trích xuất:** `pdftotext -layout -f <start> -l <end> /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf <tmp>` → text thô
2. **Làm sạch:** Tách header/footer (số trang + tiêu đề chương lặp), chèn marker `<!-- p.N -->` mỗi ~2 trang, đánh dấu block biểu đồ/bảng dạng `[CHART: <tiêu đề VN>] Source: <nguồn>`
3. **Xác định thuật ngữ:** Scan chương, đánh dấu thuật ngữ ứng viên, tra `GLOSSARY.md`, ghi nhận thuật ngữ mới
4. **Dịch khối:** Dịch theo paragraph, KHÔNG cắt câu; giữ cấu trúc markdown (heading, list, quote, bold/italic)
5. **QC thuật ngữ:** Rà soát tất cả thuật ngữ nhất quán với glossary; sửa bản dịch lệch về chuẩn
6. **Ghi chú:** Thêm footnote `[^n]: Tên gốc: "..."` cho trích dẫn/signature ratio/khái niệm khó (lần đầu)
7. **Cập nhật glossary:** Bổ sung thuật ngữ mới vào `igwt2026-vi/GLOSSARY.md`

**Quy tắc dịch (xem spec mục 4.2-4.3):**
- Tên riêng người/tổ chức: giữ nguyên (Stöferle, Incrementum, Federal Reserve)
- Thuật ngữ tài chính: dịch Việt chuẩn theo glossary
- Signature ratio: dịch nghĩa + footnote tên Anh (vd: Tỷ lệ Bia Oktoberfest (Oktoberfest Beer Ratio)[^n])
- Số liệu trong văn dịch: dấu phẩy thập phân Việt Nam (`1,5%`); số liệu trong placeholder biểu đồ: giữ format gốc
- Đơn vị: trillion→nghìn tỷ, billion→tỷ, million→triệu

**Cấu trúc header mỗi file chương:**
```markdown
# [Tên chương tiếng Việt]

> **Chương gốc:** "[Tên Anh]" — trang [start]–[end]

[Nội dung dịch theo 7 bước]

<!-- p.N -->  ← marker trang mỗi ~2 trang

[^1]: Tên gốc: "..."
```

---

## PHASE 0 — Setup

### Task 0.1: Khởi tạo git repo + cấu trúc thư mục

**Files:**
- Create: `/Users/bobo/ZCodeProject/.git` (git init)
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/` (dir)
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/GLOSSARY.md`
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/README.md`
- Create: `/Users/bobo/ZCodeProject/.gitignore`

- [ ] **Step 1: Khởi tạo git repo**

```bash
cd /Users/bobo/ZCodeProject && git init
```

- [ ] **Step 2: Tạo .gitignore**

Tạo `/Users/bobo/ZCodeProject/.gitignore` với nội dung:
```
.DS_Store
*.tmp
.playwright-mcp/
```

- [ ] **Step 3: Tạo thư mục output**

```bash
mkdir -p /Users/bobo/ZCodeProject/igwt2026-vi
```

- [ ] **Step 4: Tạo GLOSSARY.md (header bảng)**

Tạo `/Users/bobo/ZCodeProject/igwt2026-vi/GLOSSARY.md`:
```markdown
# Glossary song ngữ — In Gold We Trust 2026

Bảng thuật ngữ build dần qua từng chương. Sắp xếp theo alphabet tiếng Anh.

| Thuật ngữ Anh | Dịch Việt chuẩn | Ghi chú / ngữ cảnh |
|---|---|---|
```

- [ ] **Step 5: Tạo README.md mô tả dự án**

Tạo `/Users/bobo/ZCodeProject/igwt2026-vi/README.md`:
```markdown
# In Gold We Trust 2026 — Bản dịch tiếng Việt

Bản dịch tiếng Việt báo cáo "In Gold We Trust 2026" (20th Anniversary Edition) của Incrementum / Sound Money Capital AG.

## Cấu trúc
- `00-99` — 29 file Markdown, mỗi file 1 chương, đánh số thứ tự đọc
- `GLOSSARY.md` — Glossary thuật ngữ song ngữ Anh-Việt

## Quy ước
- Văn phong học thuật, thuật ngữ dịch thuần Việt
- Thuật ngữ mới có footnote tên gốc ở lần đầu xuất hiện
- `<!-- p.N -->` = số trang gốc trong PDF
- `[CHART: ...]` = placeholder biểu đồ (xem source gốc để xem chi tiết)

## Source
- PDF gốc: `/Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf` (464 trang)
- Spec: `../docs/superpowers/specs/2026-07-03-translation-skill-design.md`
```

- [ ] **Step 6: Commit**

```bash
cd /Users/bobo/ZCodeProject
git add .gitignore igwt2026-vi/GLOSSARY.md igwt2026-vi/README.md
git commit -m "init: cấu trúc dự án dịch IGWT 2026"
```

---

## PHASE 1 — Dịch chương mẫu + rút pitfalls

### Task 1.1: Dịch chương 00 — Foreword & Cover (trang 4-7)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/00-foreword-cover.md`

- [ ] **Step 1: Trích xuất text**

```bash
pdftotext -layout -f 4 -l 7 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p004-007.txt
```

- [ ] **Step 2: Làm sạch + dịch theo 7 bước**

Dịch nội dung: bìa kỷ niệm 20 năm, lời cảm ơn Premium Partners, credits đội ngũ, mục lục, disclaimer. Áp dụng 7 bước. File header:
```markdown
# Lời tựa & Bìa — Kỷ niệm 20 năm

> **Phần gốc:** "Foreword / Cover / TOC / Disclaimer" — trang 4-7
```

- [ ] **Step 3: Cập nhật glossary**

Thêm thuật ngữ mới gặp (vd: "Premium Partners" → "Đối tác Premium", "Sound Money" → "Tiền Lành mạnh" nếu có). Đảm bảo không trùng entry.

- [ ] **Step 4: Commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/00-foreword-cover.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 00 foreword & cover (tr 4-7)"
```

### Task 1.2: Dịch chương 01 — Introduction: Back to the Monetary Future (trang 8-25)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/01-introduction-monetary-future.md`

- [ ] **Step 1: Trích xuất**

```bash
pdftotext -layout -f 8 -l 25 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p008-025.txt
```

- [ ] **Step 2: Làm sạch + dịch theo 7 bước**

Đây là chương cốt lõi, giới thiệu chủ đề "Back to the Monetary Future". Nội dung chính: Key Takeaways, Back to the Future of Trust, sự sụp đổ của Pax Americana. Nhiều trích dẫn nổi tiếng (Victor Hugo, Will Durant, Lyn Alden, Bridgewater) → dịch nghĩa + footnote tác giả. Chú ý thuật ngữ: Pax Americana, Austrian School of Economics, Cantillon effect, malinvestment, time preference, fiat money, subprime, quantitative easing.

Header:
```markdown
# Lời mở đầu: Trở về Tương lai Tiền tệ

> **Chương gốc:** "Introduction: Back to the Monetary Future" — trang 8-25
```

- [ ] **Step 3: Cập nhật glossary**

Bổ sung ít nhất 15 thuật ngữ cốt lõi (Pax Americana, Cantillon effect, malinvestment, time preference, fiat money, Austrian School, subprime, monetary science fiction, hedge fund, etc.).

- [ ] **Step 4: Commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/01-introduction-monetary-future.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 01 introduction (tr 8-25)"
```

### Task 1.3: Ghi chú pitfalls từ chương mẫu

**Files:**
- Create: `/tmp/igwt-pitfalls-phase1.md` (scratch file, dùng cho Task 2.x)

- [ ] **Step 1: Tổng hợp pitfalls**

Sau khi dịch xong 2 chương mẫu, ghi lại các vấn đề gặp phải vào `/tmp/igwt-pitfalls-phase1.md`:
- Pattern header/footer lặp (vd: "Back to the Monetary Future" + số trang ở mỗi trang)
- Cách `pdftotext -layout` xử lý quote box nổi (text trong khung bên cạnh đoạn chính)
- Ký tự đặc biệt: dấu ä, ö, ü, ß (Stöferle), dấu ngoặc kép cong "" ""
- Cách đánh dấu biểu đồ (tiêu đề + Source + caption)
- Trường hợp thuật ngữ khó / đa nghĩa
- Lỗi OCR/format cụ thể

Danh sách này là đầu vào cho skill v1 ở Phase 2.

---

## PHASE 2 — Xây skill `translate-doc` v1

### Task 2.1: Tạo cấu trúc skill + SKILL.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/translate-doc/SKILL.md`
- Create: `/Users/bobo/.zcode/skills/translate-doc/references/` (dir)

- [ ] **Step 1: Tạo thư mục skill**

```bash
mkdir -p /Users/bobo/.zcode/skills/translate-doc/references
```

- [ ] **Step 2: Tạo SKILL.md**

Tạo `/Users/bobo/.zcode/skills/translate-doc/SKILL.md`:
```markdown
---
name: translate-doc
description: Dịch tài liệu tài chính/kỹ thuật (PDF/DOCX/MD) sang tiếng Việt với độ chính xác cao về thuật ngữ và ngữ cảnh. TRIGGER khi user yêu cầu "dịch", "translate", "phiên dịch" tài liệu — đặc biệt báo cáo tài chính, equity research, vĩ mô, kỹ thuật. Đảm bảo nhất quán thuật ngữ qua glossary song ngữ + quy trình 7 bước + QC.
---

# Dịch tài liệu tài chính/kỹ thuật sang tiếng Việt

Skill này dịch tài liệu (PDF/DOCX/MD) sang tiếng Việt với độ chính xác thuật ngữ cao, dùng quy trình 7 bước + glossary song ngữ để đảm bảo nhất quán giữa các chương.

## Khi nào dùng

Khi user yêu cầu dịch tài liệu — đặc biệt tài liệu tài chính (báo cáo đầu tư, equity research, vĩ mô), kỹ thuật, học thuật — sang tiếng Việt. Đặc biệt hữu ích cho tài liệu dài nhiều chương cần nhất quán thuật ngữ.

## Quy trình 7 bước (áp dụng cho MỖI chương/section)

Chi tiết + ví dụ: xem `references/translation_workflow.md`. Tóm tắt:

1. **Trích xuất** — `pdftotext -layout -f <start> -l <end> <pdf> <tmp>` (PDF) hoặc đọc trực tiếp (DOCX/MD)
2. **Làm sạch** — tách header/footer lặp, chèn marker trang `<!-- p.N -->`, đánh dấu block biểu đồ `[CHART: <tiêu đề>] Source: <nguồn>`
3. **Xác định thuật ngữ** — scan, tra glossary, ghi nhận thuật ngữ mới
4. **Dịch khối** — theo paragraph, không cắt câu, giữ cấu trúc markdown
5. **QC thuật ngữ** — rà soát nhất quán với glossary
6. **Ghi chú** — footnote `[^n]: Tên gốc: "..."` cho trích dẫn / signature ratio / khái niệm khó (lần đầu)
7. **Cập nhật glossary** — bổ sung thuật ngữ mới

## Quy ước thuật ngữ

Xem chi tiết `references/terminology_decisions.md`. Tóm tắt:
- Tên riêng người/tổ chức: GIỮ NGUYÊN
- Thuật ngữ tài chính: dịch Việt chuẩn theo glossary
- Signature ratio / câu nói nổi tiếng: dịch nghĩa + footnote tên gốc
- Số liệu: văn dịch Việt hóa format (dấu phẩy thập phân); biểu đồ giữ format gốc

## Output

- 1 file Markdown / chương (đánh số thứ tự 2 chữ số)
- `GLOSSARY.md` dùng chung, build dần
- README.md mô tả dự án

## Reference files

- `references/translation_workflow.md` — chi tiết 7 bước + ví dụ
- `references/glossary_template.md` — template glossary + mẫu tài chính
- `references/quality_checklist.md` — 15 điểm QC
- `references/handling_charts_tables.md` — xử lý biểu đồ/bảng/số liệu
- `references/terminology_decisions.md` — quy tắc ra quyết định thuật ngữ

## Lưu ý

Skill là **flexible** — áp dụng nguyên tắc theo loại tài liệu, không phải checklist máy móc. Điều chỉnh tần suất QC, độ chi tiết footnote theo nhu cầu (học thuật vs. đại chúng).
```

- [ ] **Step 3: Commit**

```bash
cd /Users/bobo/ZCodeProject
# Skill nằm ngoài repo; không commit trực tiếp nhưng ghi nhận
echo "translate-doc skill v1 — SKILL.md created" >> /tmp/skill-progress.log
```

### Task 2.2: Tạo reference translation_workflow.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/translate-doc/references/translation_workflow.md`

- [ ] **Step 1: Viết reference workflow**

Viết file với 7 mục (mỗi bước 1 mục), mỗi mục gồm: mô tả, ví dụ cụ thể từ IGWT (rút từ Phase 1 pitfalls), lỗi thường gặp. Nội dung chính:

- **Bước 1 Trích xuất:** lệnh `pdftotext -layout`, lưu ý range trang phải khớp TOC, PDF scan (không có text layer) cần OCR.
- **Bước 2 Làm sạch:** pattern header lặp (số trang + tiêu đề chương), dùng `<!-- p.N -->` cho marker, định dạng placeholder biểu đồ.
- **Bước 3 Xác định thuật ngữ:** cách scan (grep thuật ngữ Anh phổ biến), cách tra glossary, khi nào ghi nhận "thuật ngữ mới".
- **Bước 4 Dịch khối:** dịch theo paragraph nguyên vẹn, giữ heading level / list / quote / emphasis, xử lý quote box nổi (text bên cạnh đoạn chính).
- **Bước 5 QC thuật ngữ:** checklist nhất quán, xử lý khi phát hiện bản dịch lệch.
- **Bước 6 Ghi chú:** cú pháp `[^n]`, khi nào cần footnote, ví dụ signature ratio + trích dẫn.
- **Bước 7 Cập nhật glossary:** format bảng, tránh trùng entry, sắp xếp ABC.

Nhúng pitfalls thực tế từ `/tmp/igwt-pitfalls-phase1.md` (Task 1.3) vào các mục liên quan.

- [ ] **Step 2: Ghi nhận**

```bash
echo "translate-doc: translation_workflow.md created" >> /tmp/skill-progress.log
```

### Task 2.3: Tạo reference glossary_template.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/translate-doc/references/glossary_template.md`

- [ ] **Step 1: Viết template + mẫu**

Nội dung: (1) Template bảng glossary rỗng, (2) glossary IGWT đã build từ Phase 1 (~15-20 thuật ngữ từ chương 00-01) làm mẫu tham khảo cho tài liệu tài chính tương tự. Ghi chú cách dùng glossary dùng chung qua nhiều chương.

- [ ] **Step 2: Ghi nhận**

```bash
echo "translate-doc: glossary_template.md created" >> /tmp/skill-progress.log
```

### Task 2.4: Tạo reference quality_checklist.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/translate-doc/references/quality_checklist.md`

- [ ] **Step 1: Viết checklist 15 điểm**

15 điểm QC, nhóm theo loại:
- **Nội dung (5):** không bỏ sót đoạn, không thêm/bớt ý, đúng cấu trúc heading, list đầy đủ, quote box không mất
- **Thuật ngữ (4):** nhất quán glossary, thuật ngữ mới đã thêm glossary, footnote đầy đủ, tên riêng giữ nguyên
- **Format (3):** markdown hợp lệ, marker trang đúng, placeholder biểu đồ đúng cú pháp
- **Số liệu (2):** số liệu chính xác, định dạng (dấu thập phân/hàng nghìn) đúng quy ước
- **Ngữ pháp VN (1):** văn phong tự nhiên, không dịch sát chữ gây gượng

Mỗi điểm kèm câu hỏi yes/no để check.

- [ ] **Step 2: Ghi nhận**

```bash
echo "translate-doc: quality_checklist.md created" >> /tmp/skill-progress.log
```

### Task 2.5: Tạo reference handling_charts_tables.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/translate-doc/references/handling_charts_tables.md`

- [ ] **Step 1: Viết hướng dẫn xử lý biểu đồ/bảng**

Nội dung:
- **Biểu đồ (chart):** cú pháp placeholder `[CHART: <tiêu đề VN>]` + dòng `Source: <nguồn>` + caption VN (nếu có). KHÔNG dịch số liệu/trục bên trong. Ví dụ từ IGWT.
- **Bảng số liệu (table):** dịch header cột sang VN, GIỮ NGUYÊN số liệu, dùng markdown table. Ví dụ.
- **Quy ước số liệu:** văn dịch = dấu phẩy thập phân VN; dữ liệu biểu đồ/bảng = giữ format gốc (xem spec 4.3). Đơn vị: trillion→nghìn tỷ, billion→tỷ, million→triệu.
- **Infographic / sidebar:** tóm tắt ý chính thành list bullet, đánh dấu `[INFOGRAPHIC: ...]`.

- [ ] **Step 2: Ghi nhận**

```bash
echo "translate-doc: handling_charts_tables.md created" >> /tmp/skill-progress.log
```

### Task 2.6: Tạo reference terminology_decisions.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/translate-doc/references/terminology_decisions.md`

- [ ] **Step 1: Viết bảng phân loại + flowchart**

Nội dung: bảng phân loại thuật ngữ (tên riêng / thuật ngữ tài chính / signature ratio / trích dẫn / phim-sách / số liệu / tiền tệ) + cách xử lý từng loại (xem spec 4.2). Kèm flowchart text ra quyết định: "Có tên riêng người không? → giữ nguyên. Có trong glossary không? → dùng bản chuẩn. Là signature ratio? → dịch + footnote."

- [ ] **Step 2: Ghi nhận + commit note**

```bash
echo "translate-doc: skill v1 complete (SKILL.md + 5 references)" >> /tmp/skill-progress.log
cd /Users/bobo/ZCodeProject
git add docs/superpowers/specs/2026-07-03-translation-skill-design.md
git commit -m "docs: thêm spec dịch IGWT 2026" 2>/dev/null || true
```

---

## PHASE 3 — Dịch batch Status Quo + Renaissance (chương 02-08) — kiểm chứng skill

### Task 3.1: Dịch chương 02 — Status Quo of Gold (trang 26-35)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/02-status-quo-gold.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước (áp dụng skill v1)**

```bash
pdftotext -layout -f 26 -l 35 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p026-035.txt
```

Header: `# Hiện trạng của Vàng` / `> **Chương gốc:** "The Status Quo of Gold" — trang 26-35`

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/02-status-quo-gold.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 02 status quo of gold (tr 26-35)"
```

### Task 3.2: Dịch chương 03 — Status Quo of Gold Relative to Stocks, Bonds, Commodities (trang 36-45)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/03-status-quo-vs-stocks-bonds.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước**

```bash
pdftotext -layout -f 36 -l 45 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p036-045.txt
```

Header: `# Hiện trạng Vàng so với Cổ phiếu, Trái phiếu và Hàng hóa` / `> **Chương gốc:** "Status Quo of Gold Relative to Stocks, Bonds, and Commodities" — trang 36-45`. Chú ý thuật ngữ: stocks, bonds, commodities, correlation, Sharpe ratio, volatility.

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/03-status-quo-vs-stocks-bonds.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 03 status quo vs stocks/bonds (tr 36-45)"
```

### Task 3.3: Dịch chương 04 — Status Quo of Debt (trang 46-65)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/04-status-quo-debt.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước**

```bash
pdftotext -layout -f 46 -l 65 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p046-065.txt
```

Header: `# Hiện trạng Nợ công` / `> **Chương gốc:** "Status Quo of Debt" — trang 46-65`. Chương dài 20 trang — chia thành section con. Thuật ngữ: sovereign debt, yield curve, debt-to-GDP, fiscal deficit, monetary policy, QE, QT.

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/04-status-quo-debt.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 04 status quo of debt (tr 46-65)"
```

### Task 3.4: Dịch chương 05 — Status Quo of Inflation Dynamics (trang 66-87)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/05-status-quo-inflation.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước**

```bash
pdftotext -layout -f 66 -l 87 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p066-087.txt
```

Header: `# Hiện trạng Động thái Lạm phát` / `> **Chương gốc:** "Status Quo of Inflation Dynamics" — trang 66-87`. Chương dài 22 trang. Thuật ngữ: inflation, deflation, stagflation, CPI, PCE, real interest rate, monetary base, velocity of money.

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/05-status-quo-inflation.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 05 status quo of inflation (tr 66-87)"
```

### Task 3.5: Dịch chương 06 — Status Quo of Gold Demand and Supply (trang 88-103)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/06-status-quo-demand-supply.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước**

```bash
pdftotext -layout -f 88 -l 103 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p088-103.txt
```

Header: `# Hiện trạng Cung cầu Vàng` / `> **Chương gốc:** "The Status Quo of Gold Demand and Gold Supply" — trang 88-103`. Thuật ngữ: central bank purchases, ETF flows, jewelry demand, mining output, recycling, gold reserves.

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/06-status-quo-demand-supply.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 06 status quo demand & supply (tr 88-103)"
```

### Task 3.6: Dịch chương 07 — Status Quo of Gold Conclusion (trang 104-115)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/07-status-quo-conclusion.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước**

```bash
pdftotext -layout -f 104 -l 115 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p104-115.txt
```

Header: `# Hiện trạng Vàng — Kết luận` / `> **Chương gốc:** "The Status Quo of Gold – Conclusion" — trang 104-115`.

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/07-status-quo-conclusion.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 07 status quo conclusion (tr 104-115)"
```

### Task 3.7: Dịch chương 08 — Renaissance of Gold Allocation (trang 116-147)

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/08-renaissance-gold-allocation.md`

- [ ] **Step 1: Trích xuất + dịch theo 7 bước**

```bash
pdftotext -layout -f 116 -l 147 /Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf /tmp/igwt_p116-147.txt
```

Header: `# Sự Phục hưng của Phân bổ Vàng` / `> **Chương gốc:** "The Renaissance of Gold Allocation" — trang 116-147`. Chương dài 32 trang — chương dài nhất trong batch. Thuật ngữ: portfolio allocation, optimal weight, risk parity, 60/40 portfolio, hedge, safe haven.

- [ ] **Step 2: Cập nhật glossary + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/08-renaissance-gold-allocation.md igwt2026-vi/GLOSSARY.md
git commit -m "dịch: chương 08 renaissance gold allocation (tr 116-147)"
```

### Task 3.8: Review skill v1 → tinh chỉnh v1.1

**Files:**
- Modify: `/Users/bobo/.zcode/skills/translate-doc/references/translation_workflow.md`
- Modify: `/Users/bobo/.zcode/skills/translate-doc/references/quality_checklist.md`

- [ ] **Step 1: Đánh giá skill v1**

Sau khi dịch 7 chương (02-08) bằng skill v1, rà soát: bước nào mơ hồ? bước nào thiếu? lỗi lặp lại nào chưa được skill cảnh báo? Ghi vào `/tmp/skill-review-phase3.md`.

- [ ] **Step 2: Cập nhật skill → v1.1**

Sửa `translation_workflow.md` + `quality_checklist.md` dựa trên review. Thêm pitfalls mới phát hiện.

- [ ] **Step 3: Ghi nhận**

```bash
echo "translate-doc: skill v1.1 tuned after Phase 3" >> /tmp/skill-progress.log
```

---

## PHASE 4 — Dịch phần còn lại (chương 09-27 + 99)

Mỗi task = 1 chương. Mỗi task theo cấu trúc: Trích xuất → 7 bước → glossary → commit. Tôi liệt kê đầy đủ; mỗi task áp dụng skill v1.1.

### Gold and Geopolitics (chương 09-12)

### Task 4.1: Dịch chương 09 — Two Systems, One World (trang 148-165)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/09-two-systems-one-world.md`

- [ ] **Step 1:** `pdftotext -layout -f 148 -l 165 ...`. Header: `# Hai Hệ thống, Một Thế giới: Cuộc chiến giành Trật tự Tiền tệ Toàn cầu leo thang`. Thuật ngữ: BRICS, unipolar, multipolar, Petrodollar, sanctions.
- [ ] **Step 2:** Glossary + commit `dịch: chương 09 two systems one world (tr 148-165)`

### Task 4.2: Dịch chương 10 — Shovels, Not Spreadsheets (trang 166-173)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/10-shovels-not-spreadsheets.md`

- [ ] **Step 1:** `pdftotext -layout -f 166 -l 173 ...`. Header: `# Xẻng, Không Phải Bảng tính: Luke Gromen Tranh luận với Craig Tindale`. Đối thoại interview — giữ format Q&A. Tên riêng giữ: Luke Gromen, Craig Tindale.
- [ ] **Step 2:** Glossary + commit `dịch: chương 10 shovels not spreadsheets (tr 166-173)`

### Task 4.3: Dịch chương 11 — Gold and the End of the US Dollar Standard (trang 174-191)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/11-gold-end-us-dollar.md`

- [ ] **Step 1:** `pdftotext -layout -f 174 -l 191 ...`. Header: `# Vàng và Sự kết thúc của Chuẩn USD`. Thuật ngữ: reserve currency, Triffin dilemma, exorbitant privilege, Bretton Woods, Nixon shock.
- [ ] **Step 2:** Glossary + commit `dịch: chương 11 gold end us dollar standard (tr 174-191)`

### Task 4.4: Dịch chương 12 — Gold and the Monetary Analogue of Mackinder's Heartland Theory (trang 192-207)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/12-gold-mackinder-heartland.md`

- [ ] **Step 1:** `pdftotext -layout -f 192 -l 207 ...`. Header: `# Vàng và Tương tự Tiền tệ của Thuyết "Heartland" nền tảng của Mackinder`. Footnote giải thích Heartland Theory. Tên: Halford Mackinder.
- [ ] **Step 2:** Glossary + commit `dịch: chương 12 mackinder heartland (tr 192-207)`

### Gold Panorama (chương 13-19)

### Task 4.5: Dịch chương 13 — Six Vectors of Gold Remonetization (trang 208-223)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/13-six-vectors-remonetization.md`

- [ ] **Step 1:** `pdftotext -layout -f 208 -l 223 ...`. Header: `# Sáu Lực đẩy Tái tiền tệ hóa Vàng`. Cốt lõi — thuật ngữ "remonetization" đã có trong glossary.
- [ ] **Step 2:** Glossary + commit `dịch: chương 13 six vectors remonetization (tr 208-223)`

### Task 4.6: Dịch chương 14 — Back to the Founders: Dr. Shelton (trang 224-233)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/14-back-to-founders-shelton.md`

- [ ] **Step 1:** `pdftotext -layout -f 224 -l 233 ...`. Header: `# Trở về các Quốc phụ: TS. Shelton về Hiến pháp, Vàng và Tương lai USD`. Interview — giữ Q&A. Tên: Judy Shelton.
- [ ] **Step 2:** Glossary + commit `dịch: chương 14 back to founders shelton (tr 224-233)`

### Task 4.7: Dịch chương 15 — Gold Goes Digital (trang 234-243)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/15-gold-goes-digital.md`

- [ ] **Step 1:** `pdftotext -layout -f 234 -l 243 ...`. Header: `# Vàng Kỷ nguyên Số: Token hóa, Hạ tầng Tài chính và Niềm tin`. Thuật ngữ: tokenization, blockchain, stablecoin, DeFi, smart contract.
- [ ] **Step 2:** Glossary + commit `dịch: chương 15 gold goes digital (tr 234-243)`

### Task 4.8: Dịch chương 16 — A Golden Stabilization Op (trang 244-269)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/16-golden-stabilization-op.md`

- [ ] **Step 1:** `pdftotext -layout -f 244 -l 269 ...`. Header: `# Một Chiến dịch "Ổn định" Vàng ngay Trước mắt`. Chương dài 26 trang. Thuật ngữ: gold price suppression, London gold pool, intervention, BIS.
- [ ] **Step 2:** Glossary + commit `dịch: chương 16 golden stabilization op (tr 244-269)`

### Task 4.9: Dịch chương 17 — Psychology Behind Gold's Underallocation (trang 270-285)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/17-psychology-underallocation.md`

- [ ] **Step 1:** `pdftotext -layout -f 270 -l 285 ...`. Header: `# Tâm lý học đằng sau Phân bổ Vàng quá thấp`. Thuật ngữ: behavioral finance, cognitive bias, recency bias, status quo bias, home bias.
- [ ] **Step 2:** Glossary + commit `dịch: chương 17 psychology underallocation (tr 270-285)`

### Task 4.10: Dịch chương 18 — India Gold Ecosystem (trang 286-305)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/18-india-gold-ecosystem.md`

- [ ] **Step 1:** `pdftotext -layout -f 286 -l 305 ...`. Header: `# Ấn Độ — Cấu trúc, Động thái và Tương lai của Hệ sinh thái Vàng lớn nhất Thế giới`. Thuật ngữ đặc thù Ấn Độ: Akshaya Tritiya, Dhanteras, GST, gold monetization scheme. Footnote giải thích lễ hội.
- [ ] **Step 2:** Glossary + commit `dịch: chương 18 india gold ecosystem (tr 286-305)`

### Task 4.11: Dịch chương 19 — Collapse of Commodity Beta (trang 306-327)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/19-collapse-commodity-beta.md`

- [ ] **Step 1:** `pdftotext -layout -f 306 -l 327 ...`. Header: `# Sự sụp đổ của Beta Hàng hóa`. Thuật ngữ: commodity beta, ESG, energy transition, underinvestment, capex.
- [ ] **Step 2:** Glossary + commit `dịch: chương 19 collapse commodity beta (tr 306-327)`

### Performance Gold (chương 20-26)

### Task 4.12: Dịch chương 20 — Bitcoin's Role in the Monetary Future (trang 328-347)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/20-bitcoin-monetary-future.md`

- [ ] **Step 1:** `pdftotext -layout -f 328 -l 347 ...`. Header: `# Vai trò của Bitcoin trong Tương lai Tiền tệ`. Thuật ngữ: Bitcoin, Satoshi Nakamoto, proof of work, halving, digital gold, hashrate.
- [ ] **Step 2:** Glossary + commit `dịch: chương 20 bitcoin monetary future (tr 328-347)`

### Task 4.13: Dịch chương 21 — Silver After the Surge (trang 348-367)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/21-silver-after-surge.md`

- [ ] **Step 1:** `pdftotext -layout -f 348 -l 367 ...`. Header: `# Bạc Sau đợt Tăng giá: Cầu thang lên Thiên đường hay Cao tốc xuống Địa ngục?`. Thuật ngữ: silver, gold-silver ratio, industrial demand, photovoltaic.
- [ ] **Step 2:** Glossary + commit `dịch: chương 21 silver after the surge (tr 348-367)`

### Task 4.14: Dịch chương 22 — AI Is Making its Way into the Mining Sector (trang 368-377)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/22-ai-mining-sector.md`

- [ ] **Step 1:** `pdftotext -layout -f 368 -l 377 ...`. Header: `# Trí tuệ Nhân tạo đang Thâm nhập Ngành Khai khoáng`. Thuật ngữ: AI, machine learning, exploration, autonomous drilling, predictive maintenance.
- [ ] **Step 2:** Glossary + commit `dịch: chương 22 ai mining sector (tr 368-377)`

### Task 4.15: Dịch chương 23 — Innovate or Terminate: Gold Mining Industry (trang 378-389)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/23-innovate-or-terminate.md`

- [ ] **Step 1:** `pdftotext -layout -f 378 -l 389 ...`. Header: `# Đổi mới hay Bị Loại: Về Ngành Khai thác Vàng`. Thuật ngữ: mining, ore grade, all-in sustaining cost (AISC), exploration, depletion.
- [ ] **Step 2:** Glossary + commit `dịch: chương 23 innovate or terminate (tr 378-389)`

### Task 4.16: Dịch chương 24 — Corporate Gold Standard (trang 390-401)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/24-corporate-gold-standard.md`

- [ ] **Step 1:** `pdftotext -layout -f 390 -l 401 ...`. Header: `# Chuẩn Vàng Doanh nghiệp: Tại sao các Công ty Khai thác Vàng-Bạc nên Nắm giữ Kim loại của chính mình`. Thuật ngữ: balance sheet, treasury, hedging, royalty.
- [ ] **Step 2:** Glossary + commit `dịch: chương 24 corporate gold standard (tr 390-401)`

### Task 4.17: Dịch chương 25 — Gold and Silver Miners: Problem Child to Model Student (trang 402-419)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/25-miners-problem-to-model.md`

- [ ] **Step 1:** `pdftotext -layout -f 402 -l 419 ...`. Header: `# Công ty Khai thác Vàng và Bạc: Từ Đứa trẻ Vấn nạn đến Học sinh Gương mẫu`. Thuật ngữ: mining equities, GDX, GDXJ, HUI, leverage to gold price.
- [ ] **Step 2:** Glossary + commit `dịch: chương 25 miners problem to model (tr 402-419)`

### Task 4.18: Dịch chương 26 — Technical Analysis (trang 420-435)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/26-technical-analysis.md`

- [ ] **Step 1:** `pdftotext -layout -f 420 -l 435 ...`. Header: `# Phân tích Kỹ thuật`. Thuật ngữ TA: support, resistance, trendline, moving average, RSI, MACD, Fibonacci, Elliott Wave.
- [ ] **Step 2:** Glossary + commit `dịch: chương 26 technical analysis (tr 420-435)`

### Kết luận + Appendix (chương 27, 99)

### Task 4.19: Dịch chương 27 — Quo Vadis, Aurum? (trang 436-455)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/27-quo-vadis-aurum.md`

- [ ] **Step 1:** `pdftotext -layout -f 436 -l 455 ...`. Header: `# Vàng sẽ đi về đâu?` (footnote: "Quo Vadis, Aurum?" = Latin "Vàng sẽ đi đâu"). Đây là chương kết luận + dự báo — cốt lõi.
- [ ] **Step 2:** Glossary + commit `dịch: chương 27 quo vadis aurum (tr 436-455)`

### Task 4.20: Dịch chương 99 — Appendix: About us + Premium Partner (trang 456-464)

**Files:** Create `/Users/bobo/ZCodeProject/igwt2026-vi/99-appendix-about.md`

- [ ] **Step 1:** `pdftotext -layout -f 456 -l 464 ...`. Header: `# Phụ lục: Về chúng tôi & Đối tác Premium`. Tiểu sử tác giả (Stöferle, Valek), danh sách Premium Partners.
- [ ] **Step 2:** Glossary + commit `dịch: chương 99 appendix about (tr 456-464)`

---

## PHASE 5 — QC toàn cục + hoàn thiện

### Task 5.1: Sắp xếp glossary + kiểm tra trùng lặp

**Files:**
- Modify: `/Users/bobo/ZCodeProject/igwt2026-vi/GLOSSARY.md`

- [ ] **Step 1: Kiểm tra trùng entry**

```bash
cd /Users/bobo/ZCodeProject/igwt2026-vi
grep -E '^\|' GLOSSARY.md | tail -n +2 | awk -F'|' '{print $2}' | sort | uniq -d
```
Nếu có trùng → gộp entry, chọn bản dịch chuẩn.

- [ ] **Step 2: Sắp xếp ABC theo thuật ngữ Anh**

Sắp xếp lại bảng glossary theo alphabet cột 1.

- [ ] **Step 3: Commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/GLOSSARY.md
git commit -m "qc: sắp xếp + khử trùng glossary"
```

### Task 5.2: Quét nhất quán thuật ngữ qua 29 file

**Files:** Read-only check tất cả 29 file chương

- [ ] **Step 1: Trích xuất danh sách thuật ngữ + bản dịch chuẩn**

Đọc `GLOSSARY.md`, build danh sách (thuật ngữ Anh, bản dịch chuẩn).

- [ ] **Step 2: Quét từng file tìm bản dịch lệch**

Với mỗi thuật ngữ, grep các biến thể dịch khác có trong các file chương. Ví dụ với "remonetization" (chuẩn: "tái tiền tệ hóa"), grep tìm các biến thể như "tiền tệ hóa lại", "remonetization" chưa dịch. Nếu phát hiện lệch → sửa về chuẩn.

- [ ] **Step 3: Sửa các file lệch + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/*.md
git commit -m "qc: đồng nhất thuật ngữ qua 29 file chương"
```

### Task 5.3: Kiểm tra cross-reference + markdown hợp lệ

**Files:** Read-only check

- [ ] **Step 1: Kiểm tra footnote `[^n]`**

Mỗi file: đảm bảo mọi `[^n]` trong body có definition `[^n]:` ở cuối file, và ngược lại. Lệnh check:
```bash
cd /Users/bobo/ZCodeProject/igwt2026-vi
for f in *.md; do
  echo "=== $f ==="
  refs=$(grep -oE '\[\^[0-9]+\]' "$f" | grep -v ':' | sort -u)
  defs=$(grep -oE '\[\^[0-9]+\]:' "$f" | sed 's/:$//' | sort -u)
  echo "Refs: $refs"
  echo "Defs: $defs"
done
```

- [ ] **Step 2: Kiểm tra marker trang + placeholder biểu đồ**

```bash
cd /Users/bobo/ZCodeProject/igwt2026-vi
echo "=== markers trang ==="
grep -c '<!-- p\.' *.md
echo "=== placeholders CHART ==="
grep -c '\[CHART:' *.md
```
Đảm bảo mỗi file có marker trang + placeholder biểu đồ hợp lý.

- [ ] **Step 3: Sửa lỗi + commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/*.md
git commit -m "qc: sửa footnote + marker + placeholder" || echo "không có thay đổi"
```

### Task 5.4: Hoàn thiện glossary_template.md của skill với glossary IGWT đầy đủ

**Files:**
- Modify: `/Users/bobo/.zcode/skills/translate-doc/references/glossary_template.md`

- [ ] **Step 1: Copy glossary IGWT hoàn chỉnh vào skill**

Sau Phase 5.1 glossary IGWT đã hoàn chỉnh (~80-120 thuật ngữ). Copy nội dung vào `references/glossary_template.md` làm mẫu tham khảo cho tài liệu tài chính tương lai.

- [ ] **Step 2: Ghi nhận**

```bash
echo "translate-doc: glossary_template.md cập nhật với glossary IGWT đầy đủ" >> /tmp/skill-progress.log
```

### Task 5.5: Báo cáo hoàn thành

**Files:**
- Create: `/Users/bobo/ZCodeProject/igwt2026-vi/COMPLETION_REPORT.md`

- [ ] **Step 1: Viết báo cáo**

Nội dung: tổng quan dự án, thống kê (số chương, số từ, số thuật ngữ glossary), danh sách file, thống kê pitfalls đã đúc kết vào skill, ghi chú sử dụng.

- [ ] **Step 2: Final commit**

```bash
cd /Users/bobo/ZCodeProject
git add igwt2026-vi/COMPLETION_REPORT.md
git commit -m "docs: báo cáo hoàn thành dự án dịch IGWT 2026"
git log --oneline | head -40
```

---

## Self-Review (sau khi viết plan)

**Spec coverage:**
- ✅ Mục 1 (quyết định): tất cả 7 quyết định phản ánh trong tasks
- ✅ Mục 2 (cấu trúc output): Task 0.1 tạo cấu trúc; 29 task chương tạo file; Phase 5 QC
- ✅ Mục 3 (quy trình 7 bước): định nghĩa đầu plan + áp dụng trong mọi task chương
- ✅ Mục 4 (thuật ngữ + glossary): Task 0.1 tạo glossary; mỗi task chương cập nhật; Task 5.1-5.2 QC
- ✅ Mục 5 (skill translate-doc): Task 2.1-2.6 tạo SKILL.md + 5 reference files; Task 3.8 + 5.4 tinh chỉnh
- ✅ Mục 6 (5 phase): Phase 0-5 đầy đủ
- ✅ Mục 7 (rủi ro): xử lý qua QC + marker trang + placeholder

**Placeholder scan:** Không có TBD/TODO mơ hồ. Mỗi task có range trang + tên file cụ thể + commit message.

**Type consistency:** Cấu trúc file nhất quán (header metadata, marker trang, footnote). Glossary dùng chung xuyên suốt. Skill v1 → v1.1 (Task 3.8) → cập nhật glossary_template (Task 5.4) — mạch lạc.

**Scope:** 1 dự án dịch + 1 skill, không quá rộng. 29 chương chia task độc lập, mỗi task commit riêng — phù hợp subagent-driven.
