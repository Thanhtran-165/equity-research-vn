# Spec: Dịch "In Gold We Trust 2026" + Xây dựng skill dịch tổng quát

- **Ngày:** 2026-07-03
- **Nguồn:** `/Users/bobo/Downloads/In-Gold-We-Trust-2026-Full.pdf` (464 trang, 52 MB, PDF 1.7)
- **Mục tiêu kép:**
  1. Dịch toàn bộ báo cáo "In Gold We Trust 2026" (IGWT) sang tiếng Việt với độ chính xác cao về ngữ cảnh và thuật ngữ.
  2. Thông qua quá trình dịch, xây dựng skill `translate-doc` tổng quát — tái sử dụng cho mọi tài liệu tài chính/kỹ thuật.

## 1. Quyết định thiết kế (đã chốt với user)

| Yếu tố | Quyết định |
|---|---|
| Ngôn ngữ đích | Tiếng Việt |
| Phạm vi | Toàn bộ 464 trang |
| Mục đích | Nghiên cứu / học thuật (văn phong học thuật, thuật ngữ chính xác, có chú thích kỹ thuật) |
| Định dạng output | Markdown theo chương (1 file/chương) |
| Xử lý thuật ngữ | Dịch thuần Việt; glossary song ngữ để đảm bảo nhất quán |
| Loại skill | Tổng quát (dùng cho mọi tài liệu tài chính/kỹ thuật) |
| Approach | Hybrid lặp (dịch mẫu → viết skill v1 → dịch batch → tinh chỉnh skill → dịch nốt) |

## 2. Cấu trúc dự án & output

```
/Users/bobo/ZCodeProject/
├── igwt2026-vi/                              # Bản dịch tiếng Việt
│   ├── GLOSSARY.md                           # Glossary song ngữ (build dần)
│   ├── 00-foreword-cover.md                  # trang 4-7
│   ├── 01-introduction-monetary-future.md    # trang 8-25
│   ├── 02-status-quo-gold.md                 # trang 26-35
│   ├── 03-status-quo-vs-stocks-bonds.md      # trang 36-45
│   ├── 04-status-quo-debt.md                 # trang 46-65
│   ├── 05-status-quo-inflation.md            # trang 66-87
│   ├── 06-status-quo-demand-supply.md        # trang 88-103
│   ├── 07-status-quo-conclusion.md           # trang 104-115
│   ├── 08-renaissance-gold-allocation.md     # trang 116-147
│   ├── 09-two-systems-one-world.md           # trang 148-165
│   ├── 10-shovels-not-spreadsheets.md        # trang 166-173
│   ├── 11-gold-end-us-dollar.md              # trang 174-191
│   ├── 12-gold-mackinder-heartland.md        # trang 192-207
│   ├── 13-six-vectors-remonetization.md      # trang 208-223
│   ├── 14-back-to-founders-shelton.md        # trang 224-233
│   ├── 15-gold-goes-digital.md              # trang 234-243
│   ├── 16-golden-stabilization-op.md         # trang 244-269
│   ├── 17-psychology-underallocation.md      # trang 270-285
│   ├── 18-india-gold-ecosystem.md            # trang 286-305
│   ├── 19-collapse-commodity-beta.md         # trang 306-327
│   ├── 20-bitcoin-monetary-future.md         # trang 328-347
│   ├── 21-silver-after-surge.md              # trang 348-367
│   ├── 22-ai-mining-sector.md               # trang 368-377
│   ├── 23-innovate-or-terminate.md           # trang 378-389
│   ├── 24-corporate-gold-standard.md         # trang 390-401
│   ├── 25-miners-problem-to-model.md         # trang 402-419
│   ├── 26-technical-analysis.md              # trang 420-435
│   ├── 27-quo-vadis-aurum.md                 # trang 436-455
│   └── 99-appendix-about.md                  # trang 456-464
└── docs/superpowers/specs/
    └── 2026-07-03-translation-skill-design.md  (file này)
```

Skill được lưu tại `~/.zcode/skills/translate-doc/` (xem mục 5).

### Quy ước đặt tên file

- Đánh số thứ tự 2 chữ số để sort đúng thứ tự đọc.
- Slug giữ **tiếng Anh gốc** (để dễ map ngược với source PDF khi cần đối chiếu), nhưng nội dung file dịch **thuần Việt**.
- File `99-appendix-about.md` gộp phần "About us" + "Premium Partner" + trang bìa cuối.

### Cấu trúc bên trong mỗi file chương

```markdown
# [Tên chương tiếng Việt]

> **Chương gốc:** "[Tên Anh gốc]" — trang [start]–[end]
> **Tác giả chương:** [nếu có]

## Tóm tắt要点 (Key Takeaways)
...

## [Tiêu đề section tiếng Việt]
[Nội dung dịch]

<!-- p.10 -->          ← đánh dấu số trang gốc, định kỳ mỗi ~2 trang
...

[^1]: Tên gốc: "..."   ← footnote tên thuật ngữ/trích dẫn gốc
```

## 3. Quy trình dịch 7 bước (áp dụng cho mỗi chương)

Đây là quy trình lõi; sẽ được trình bày chi tiết trong skill `translate-doc`.

1. **Trích xuất** — `pdftotext -layout -f <start> -l <end>` theo range trang chương → text thô.
2. **Làm sạch** — tách bỏ header (số trang + tiêu đề chương lặp lại ở mỗi trang), chèn marker số trang gốc dạng HTML comment `<!-- p.N -->` mỗi ~2 trang, đánh dấu block biểu đồ/bảng dưới dạng placeholder có cấu trúc.
3. **Xác định thuật ngữ** — scan chương, đánh dấu thuật ngữ ứng viên cần tra glossary + ghi nhận thuật ngữ mới chưa có trong glossary.
4. **Dịch khối** — dịch theo khối đoạn (paragraph), KHÔNG cắt câu giữa chừng. Giữ nguyên cấu trúc markdown (heading level, list, quote block, bold/italic).
5. **QC thuật ngữ** — rà soát toàn bộ thuật ngữ đã dùng nhất quán với `GLOSSARY.md`. Nếu phát hiện bản dịch lệch, sửa về dạng chuẩn.
6. **Ghi chú** — thêm footnote `[^n]: Tên gốc: "..."` cho: trích dẫn câu nói nổi, signature ratio (lần đầu xuất hiện), người/tên riêng khi cần làm rõ.
7. **Cập nhật glossary** — bổ sung thuật ngữ mới phát hiện trong chương vào `GLOSSARY.md`.

## 4. Xử lý thuật ngữ & glossary song ngữ

### 4.1 Glossary dùng chung

Vị trí: `igwt2026-vi/GLOSSARY.md`. Bắt đầu rỗng, build dần qua từng chương. Cấu trúc bảng:

| Thuật ngữ Anh | Dịch Việt chuẩn | Ghi chú / ngữ cảnh |
|---|---|---|
| gold remonetization | sự tái tiền tệ hóa vàng | khái niệm cốt lõi báo cáo |
| de-dollarization | sự phi đô la hóa | |
| monetary base | cơ sở tiền tệ | |
| fiat money | tiền pháp định | tiền do nhà nước phát hành, không có vàng backing |
| Cantillon effect | hiệu ứng Cantillon | giữ tên riêng người |
| Pax Americana | Trật tự Pax Americana | giữ Latin; "Pax" = hòa bình |
| malinvestment | đầu tư sai lệch | thuật ngữ trường phái Áo |
| time preference | ưu tiên thời gian | trường phái Áo |
| Oktoberfest Beer Ratio | Tỷ lệ Bia Oktoberfest | signature ratio, dịch nghĩa + footnote tên Anh |

### 4.2 Quy tắc dịch phân loại

| Loại | Xử lý | Ví dụ |
|---|---|---|
| Tên riêng người | Giữ nguyên | Ronald-Peter Stöferle, Satoshi Nakamoto, Marty McFly |
| Tên tổ chức/thương hiệu | Giữ nguyên | Bridgewater, Incrementum, Federal Reserve |
| Tên thuật ngữ tài chính | Dịch Việt chuẩn theo glossary; footnote tên Anh ở lần đầu nếu khái niệm khó | tiền pháp định (fiat money)¹ |
| Signature ratio của IGWT | Dịch nghĩa tiếng Việt + footnote tên Anh ở lần đầu | Tỷ lệ Bia Oktoberfest (Oktoberfest Beer Ratio) |
| Trích dẫn câu nói nổi tiếng | Dịch nghĩa; ghi tác giả + footnote tên gốc nếu là câu chơi chữ | "Tương lai có nhiều cái tên..." — Victor Hugo |
| Tên phim/sách | Dịch tựa Việt phổ biến nếu có; nếu không, giữ gốc + footnote | Back to the Future (Trở Về Tương Lai) |
| Số liệu / đơn vị tiền | Giữ nguyên | $4,623, USD 9 nghìn tỷ, 600% |
| Tên tiền tệ | Giữ mã chuẩn | USD, EUR, GBP, VND |

### 4.3 Quy ước số liệu

- Dấu thập phân trong **văn dịch**: dấu phẩy (Việt Nam) — `1,5%` không phải `1.5%`, `4.623` USD → `4,623` USD (lưu ý: đây là dấu thập phân, không phải hàng nghìn).
- **Số liệu trong placeholder biểu đồ/bảng** (block `[CHART:...]` và bảng số): giữ nguyên format gốc của source (dấu chấm thập phân, dấu phẩy hàng nghìn) để tránh sai lệch dữ liệu khi đối chiếu; chỉ dịch nhãn trục/tiêu đề. Quy tắc: văn dịch → Việt hóa format; dữ liệu biểu đồ → giữ nguyên.
- Đơn vị lớn: "nghìn tỷ" (trillion), "tỷ" (billion), "triệu" (million). Ví dụ `9trn USD` → `9 nghìn tỷ USD`.
- Phạm vi số: `$670–$4,623`.

## 5. Cấu trúc skill `translate-doc` (tổng quát)

Vị trí: `~/.zcode/skills/translate-doc/`. Skill loại **flexible** (nguyên tắc áp dụng, không phải checklist cố định).

```
~/.zcode/skills/translate-doc/
├── SKILL.md                          # Quy trình dịch chính
└── references/
    ├── translation_workflow.md       # Chi tiết 7 bước + ví dụ cụ thể
    ├── glossary_template.md          # Template glossary song ngữ + mẫu IGWT
    ├── quality_checklist.md          # Checklist QC (15 điểm)
    ├── handling_charts_tables.md     # Cách xử lý biểu đồ / bảng / số liệu
    └── terminology_decisions.md      # Quy tắc ra quyết định thuật ngữ theo phân loại
```

### Frontmatter

```yaml
---
name: translate-doc
description: Dịch tài liệu tài chính/kỹ thuật (PDF/DOCX/MD) sang tiếng Việt với độ chính xác cao về thuật ngữ và ngữ cảnh. TRIGGER khi user yêu cầu "dịch", "translate", "phiên dịch" tài liệu — đặc biệt báo cáo tài chính, equity research, vĩ mô, kỹ thuật. Đảm bảo nhất quán thuật ngữ qua glossary song ngữ + quy trình 7 bước + QC.
---
```

### Nội dung SKILL.md (đại cương)

- Khi nào dùng skill
- Quy trình 7 bước (tóm tắt; chi tiết trong `references/translation_workflow.md`)
- Quy ước đặt tên file output + cấu trúc thư mục
- Liên kết tới 5 reference files
- Lưu ý: skill là flexible — áp dụng nguyên tắc, không phải checklist máy móc. Điều chỉnh theo loại tài liệu.

### Mục đích từng reference file

- **translation_workflow.md** — diễn giải chi tiết từng bước trong 7 bước, kèm ví dụ cụ thể từ IGWT (trích xuất → làm sạch → dịch → QC). File dài nhất.
- **glossary_template.md** — template bảng glossary + glossary IGWT đã build (≈80–120 thuật ngữ) để dùng làm reference cho tài liệu tài chính tương tự.
- **quality_checklist.md** — 15 điểm QC: nhất quán thuật ngữ, đúng cấu trúc markdown, không bỏ sót đoạn, footnote đầy đủ, số liệu chính xác, đánh dấu trang, v.v.
- **handling_charts_tables.md** — cách xử lý: placeholder biểu đồ (`[CHART: <tiêu đề>] Source: <nguồn>`), dịch tiêu đề trục, giữ số liệu gốc, bảng số liệu đánh dấu cột.
- **terminology_decisions.md** — bảng phân loại thuật ngữ (mục 4.2) + flowchart ra quyết định dịch/giữ nguyên.

## 6. Thứ tự thực thi (Approach Hybrid lặp)

```
Phase 0 — Setup
  ├─ Tạo cây thư mục igwt2026-vi/
  ├─ Tạo GLOSSARY.md rỗng (chỉ header bảng)
  ├─ Trích xuất TOC PDF đã xác nhận range trang
  └─ Tạo README.md trong igwt2026-vi/ mô tả dự án

Phase 1 — Dịch chương mẫu (00 + 01: Foreword + Introduction)
  ├─ Áp dụng 7 bước thủ công
  ├─ Ghi nhận pitfalls / thuật ngữ đặc thù gặp phải
  └─ Cập nhật GLOSSARY.md với thuật ngữ từ 2 chương này

Phase 2 — Viết skill translate-doc v1
  ├─ SKILL.md + 5 reference files
  ├─ Đưa pitfalls từ Phase 1 vào translation_workflow.md
  └─ Đưa glossary IGWT vào glossary_template.md

Phase 3 — Dịch batch Status Quo + Renaissance (chương 02-08) → kiểm chứng skill
  ├─ Áp dụng skill v1
  ├─ Ghi nhận nơi skill còn mơ hồ / thiếu sót
  └─ Tinh chỉnh skill → v1.1

Phase 4 — Dịch phần còn lại (chương 09-27 + 99)
  ├─ Geopolitics (09-12)
  ├─ Gold Panorama (13-19)
  ├─ Performance Gold (20-26)
  └─ Quo Vadis + Appendix (27, 99)

Phase 5 — QC toàn cục
  ├─ Quét nhất quán thuật ngữ qua tất cả 29 file
  ├─ Hoàn thiện GLOSSARY.md (sắp xếp ABC)
  ├─ Kiểm tra cross-reference giữa chương
  └─ Báo cáo hoàn thành
```

Mỗi phase báo tiến độ cho user. Mỗi chương lưu file riêng — user có thể soát từng file.

## 7. Rủi ro & giải pháp

| Rủi ro | Giải pháp |
|---|---|
| PDF 464 trang, dịch lâu | Chia 29 file, dịch từng chương độc lập, không phải làm lại từ đầu nếu lỗi |
| `pdftotext` có thể lệch layout biểu đồ | Đánh dấu biểu đồ bằng placeholder, không cố dịch nội dung bên trong biểu đồ |
| Thuật ngữ mới phát sinh không có trong glossary | Cập nhật GLOSSARY.md sau mỗi chương; QC toàn cục Phase 5 |
| Trùng lặp thuật ngữ dịch khác nhau giữa chương | Glossary dùng chung + bước QC thuật ngữ (bước 5) trong mỗi chương |
| Trích dẫn câu nói nổi tiếng khó dịch giữ sắc thái | Dịch nghĩa + footnote tên gốc; ưu tiên truyền đạt ý hơn là dịch sát chữ |
| Cú pháp `[^n]` footnote có thể không render đúng mọi markdown viewer | Dùng cú pháp chuẩn; kiểm tra render ở cuối |

## 8. Tiêu chí hoàn thành (Definition of Done)

- [ ] 29 file Markdown trong `igwt2026-vi/` — mỗi chương 1 file, đúng range trang
- [ ] `GLOSSARY.md` hoàn chỉnh (≈80–120 thuật ngữ), sắp xếp ABC
- [ ] Skill `translate-doc` tại `~/.zcode/skills/translate-doc/` gồm SKILL.md + 5 reference files
- [ ] Mỗi file chương: đúng cấu trúc (header metadata, đánh dấu trang, footnote)
- [ ] QC toàn cục Phase 5 hoàn tất — không còn thuật ngữ dịch lệch
- [ ] README.md trong `igwt2026-vi/` mô tả dự án + hướng dẫn đọc
