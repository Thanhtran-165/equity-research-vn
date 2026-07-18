# Spec — Main Street vs Wall Street · Giai đoạn R (Content Research Foundation)

- **Ngày**: 2026-07-18
- **Dự án**: Website scrollytelling editorial "Main Street vs Wall Street"
- **Phạm vi**: Giai đoạn R — nghiên cứu & biên tập nội dung cho 18 chương
- **Bài nguồn**: 18 phần "Main Street và Wall Street" do người dùng cung cấp (file đính kèm)
- **Prompt nguồn**: `pasted-text-20260718-155453-f76a4ade.txt` (prompt tổng 1700+ dòng)
- **Tình trạng**: Đã duyệt qua brainstorm 6 section
- **Tiếp theo sau spec**: `writing-plans` skill tạo implementation plan

---

## 1. Bối cảnh và chiến lược tổng thể

### 1.1. Sản phẩm cuối cùng

Một website scrollytelling editorial 18 chương về mối quan hệ giữa Main Street (nền kinh tế thực) và Wall Street (hệ thống tài chính), theo phong cách Financial Times / Bloomberg Graphics / Reuters Graphics. Có Hero, presentation mode, 15 thành phần tương tác, design system riêng, deploy Vercel.

### 1.2. Tại sao chia giai đoạn

Prompt tổng (1700+ dòng, 22 section) mô tả một sản phẩm chuyên nghiệp tương đương một dự án FT/Bloomberg Graphics nhiều tuần. Một agent đơn lẻ không thể làm đầy đủ và chất lượng trong một lần. Chia giai đoạn giúp:

- Người dùng **thấy sản phẩm sớm** và điều hướng nếu sai tone.
- Mỗi giai đoạn có **nghiệm thu riêng** (build pass, deploy được, content verified).
- Tách hai loại công việc khác nhau (research content vs build UI) để chất lượng cao hơn.

### 1.3. Bốn giai đoạn

| Giai đoạn | Nội dung | Spec |
|---|---|---|
| **R** (spec này) | Research content — 18 chương, claims, sources, glossary, methodology | Đây |
| **A** | Build Hero + chương 1–6 + design system + presentation mode cơ bản | Spec sau |
| **B** | Build chương 7–14 (split-screen, rebalancing machine, 3 case study Mỹ–Nhật–TQ) | Spec sau |
| **C** | Build chương 15–18 (pyramid, risk map, who-wins matrix, checklist) + polish + QA + deploy | Spec sau |

### 1.4. Các quyết định đã chốt trong brainstorm

| Quyết định | Chốt | Lý do |
|---|---|---|
| Phạm vi | 4 giai đoạn R→A→B→C | Thấy sản phẩm sớm, nghiệm thu từng giai đoạn |
| Hướng design (cho A) | Direction B — Modern Dataviz | Navy đậm + cam đất + giấy ấm; tiện biểu đồ, có chiều sâu kỹ thuật |
| Layout Hero (cho A) | Layout C — Asymmetric | Text trái + mini-diagram dòng vốn phải; tạo promise product |
| Scrollytelling pattern (cho A) | Hybrid per-chapter | Mỗi chương chọn pattern phù hợp (sticky-scroll hoặc inline-flow) |
| Tech stack (cho A) | Next.js 15 App Router, static export | Match cấu trúc `app/` trong prompt, SEO/metadata sẵn |
| Mức kiểm chứng | Deep research (Mức 3) | Tách thành Giai đoạn R để chất lượng |
| Approach R | Theo chương tuần tự | Nghiệm thu từng chương, bám luồng câu chuyện |

---

## 2. Mục tiêu và phạm vi Giai đoạn R

### 2.1. Mục tiêu

Xây dựng nền tảng nội dung đầy đủ cho toàn bộ 18 chương, là **đầu vào bắt buộc** cho Giai đoạn A/B/C build UI. Sản phẩm là các file JSON + markdown được tổ chức chặt chẽ, có nguồn xác thực, không bịa đặt.

### 2.2. Trong phạm vi (in scope)

- Trích xuất toàn bộ luận điểm từ bài nguồn 18 phần.
- Mỗi luận điểm gắn nhãn `fact | mechanism | interpretation`.
- Search & verify nguồn chính thức cho các mốc lịch sử quan trọng.
- Viết `content/chXX.json` đầy đủ cho 18 chương (mở đầu, luận điểm, cơ chế, visual plan, ví dụ, phản biện, takeaway).
- Đề xuất visual plan per-chapter (loại diagram, dữ liệu cần, interaction pattern).
- Glossary các thuật ngữ.
- Methodology document.
- Special insights (theo prompt Section VIII — 8 insights).
- Phản biện (theo prompt Section XIX — 10 phản biện).

### 2.3. Ngoài phạm vi (out of scope)

- Bất kỳ dòng code UI nào (thuộc Giai đoạn A/B/C).
- SVG/Diagram implementation.
- Number-crunching mới từ raw dataset (chỉ dùng số liệu đã published).
- Biên tập lại văn phong (giữ tinh thần bài nguồn).
- Build, deploy, QA frontend.

### 2.4. Stop condition

Nếu không tìm được nguồn chính thức cho một claim định lượng → claim được đánh dấu `status: "author-view"` với note giải thích. **Không bao giờ bịa source.**

---

## 3. Kiến trúc nội dung

### 3.1. Cấu trúc thư mục cuối Giai đoạn R

```
content/
├─ index.json                    ← 18 chương index (chapter nav, sitemap)
├─ claims.json                   ← ~100–150 claims
├─ sources.json                  ← ~50–80 nguồn
├─ glossary.json                 ← 30–50 thuật ngữ
├─ methodology.md                ← cách phân loại + verify claim
├─ progress.md                   ← nghiệm thu chương
├─ insights.md                   ← 8 special insights (prompt Section VIII)
├─ counterpoints.md              ← 10 phản biện (prompt Section XIX)
└─ chapters/
   ├─ ch01.json
   ├─ ch02.json
   ├─ ...
   └─ ch18.json

RESEARCH-REPORT.md                ← tóm tắt cuối (ở root repo)
```

### 3.2. Schema `content/chXX.json`

Mỗi chương là một file JSON với schema thống nhất:

```json
{
  "id": "ch06",
  "number": 6,
  "slug": "chu-ky-lanh-manh-va-bong-bong",
  "title": "Chu kỳ lành mạnh và chu kỳ bong bóng",
  "summary": "1–2 câu tóm tắt cho chapter nav.",
  "opening_question": "Khi giá tài sản tăng, đó là thịnh vượng hay dấu hiệu bong bóng?",
  "sections": [
    {
      "type": "prose",
      "label": "Luận điểm",
      "content": "Đoạn văn luận điểm chính..."
    },
    {
      "type": "mechanism",
      "label": "Cơ chế",
      "content": "Giải thích cơ chế kinh tế...",
      "claim_refs": ["CLM-045", "CLM-046"]
    },
    {
      "type": "visual_plan",
      "visual_id": "ch06-cycle-toggle",
      "visual_type": "sticky-toggle-diagram",
      "description": "Hai sơ đồ chu kỳ side-by-side, toggle Healthy/Bubble.",
      "data_needed": "illustrative-mechanism",
      "claim_refs": ["CLM-045"]
    },
    {
      "type": "example",
      "label": "Ví dụ",
      "content": "..."
    },
    {
      "type": "counterpoint",
      "content": "Phản biện: chu kỳ không hoàn toàn tự động..."
    },
    {
      "type": "takeaway"
    }
  ],
  "takeaway": "Chu kỳ lành mạnh neo ở dòng tiền. Chu kỳ bong bóng neo ở giá tài sản.",
  "visual_plans": [
    {
      "id": "ch06-cycle-toggle",
      "type": "sticky-toggle",
      "priority": "primary",
      "is_centerpiece": true,
      "data_needed": "illustrative-mechanism",
      "description": "..."
    }
  ],
  "claim_refs": ["CLM-045", "CLM-046", "CLM-047"],
  "chapter_pattern": "sticky-scroll",
  "reading_time_min": 4
}
```

#### Bảng trường `content/chXX.json`

| Trường | Loại | Bắt buộc | Ý nghĩa |
|---|---|---|---|
| `id` | string | ✓ | `chXX` duy nhất |
| `number` | int | ✓ | Số chương 1–18 |
| `slug` | string | ✓ | URL-safe slug tiếng Việt không dấu |
| `title` | string | ✓ | Tiêu đề chương |
| `summary` | string | ✓ | Tóm tắt 1–2 câu cho chapter nav |
| `opening_question` | string | ✓ | Câu hỏi mở đầu (theo prompt XVIII) |
| `sections` | array | ✓ | Mảng các section (xem dưới) |
| `takeaway` | string | ✓ | Câu kết luận nổi bật của chương |
| `visual_plans` | array | ✓ | Visual cần build ở A/B/C |
| `claim_refs` | array | ✓ | ID claim trong claims.json |
| `chapter_pattern` | enum | ✓ | `sticky-scroll` \| `inline-flow` \| `hybrid` |
| `reading_time_min` | int | ✓ | Ước tính thời gian đọc |

#### Các `type` của section

| `type` | Ý nghĩa |
|---|---|
| `prose` | Đoạn văn luận điểm |
| `mechanism` | Giải thích cơ chế kinh tế |
| `visual_plan` | Đề xuất visual (chưa implement) |
| `example` | Ví dụ cụ thể |
| `counterpoint` | Phản biện |
| `takeaway` | Kết luận nổi bật |

#### `chapter_pattern` — phân bổ Hybrid đã chốt

- `sticky-scroll`: chương có visual trung tâm dính màn hình.
- `inline-flow`: chương thiên lập luận, visual xen kẽ đoạn văn.
- `hybrid`: kết hợp cả hai trong cùng chương.

Phân bổ dự kiến (sẽ chốt cuối trong content):
- **sticky**: chương 1, 6, 11, 12, 13, 14 (visual trung tâm rõ).
- **inline**: chương 2, 3, 7, 9, 10, 15, 16, 17, 18.
- **hybrid**: chương 4, 5, 8.

### 3.3. Schema `content/index.json`

```json
{
  "project": "main-street-vs-wall-street",
  "version": "1.0",
  "language": "vi",
  "total_chapters": 18,
  "chapters": [
    {
      "id": "ch01",
      "number": 1,
      "slug": "hai-nua-cua-nen-kinh-te",
      "title": "Hai nửa của nền kinh tế",
      "summary": "...",
      "chapter_pattern": "sticky-scroll",
      "visual_count": 1,
      "reading_time_min": 3,
      "file": "chapters/ch01.json"
    }
  ]
}
```

---

## 4. Schema claims.json và sources.json

### 4.1. `claims.json`

Mỗi claim là một entry:

```json
{
  "id": "CLM-001",
  "chapter": "ch01",
  "claim": "Main Street là nền kinh tế thực — nơi hàng hóa, dịch vụ, việc làm và thu nhập được tạo ra.",
  "type": "fact",
  "status": "verified",
  "sources": ["SRC-FED-MAINSTREET", "SRC-BIS-GLOSSARY"],
  "note": "Định nghĩa chuẩn. Main Street là metaphor cho real economy.",
  "source_quote": "Main Street refers to the real economy..."
}
```

#### Trường bắt buộc

| Trường | Giá trị | Ý nghĩa |
|---|---|---|
| `id` | `CLM-XXX` | ID duy nhất, tham chiếu từ content.json |
| `chapter` | `chXX` | Chương chứa claim |
| `claim` | text tiếng Việt | Nội dung luận điểm |
| `type` | `fact` \| `mechanism` \| `interpretation` | 3 nhãn nội bộ theo prompt Section IV |
| `status` | `verified` \| `qualified` \| `disputed` \| `author-view` | Trạng thái kiểm chứng |
| `sources` | mảng `SRC-*` | Tham chiếu tới sources.json (có thể rỗng nếu author-view) |
| `note` | text | Giới hạn, caveat, hoặc giải thích |
| `source_quote` | text | Trích dẫn gốc (nếu có) để UI show trong panel nguồn |

#### 3 `type` claim (theo prompt Section IV)

- **`fact`** — dữ kiện có thể kiểm chứng.
- **`mechanism`** — cơ chế kinh tế được giải thích.
- **`interpretation`** — diễn giải hoặc quan điểm của tác giả.

#### 4 `status` kiểm chứng

- **`verified`** — có ít nhất 1 nguồn chính thức hỗ trợ trực tiếp (IMF, Fed, BIS, BEA...).
- **`qualified`** — đúng trong điều kiện nhất định, nguồn có nhưng cần caveat.
- **`disputed`** — có tranh luận học thuật, trình bày cả hai góc nhìn.
- **`author-view`** — quan điểm/diễn giải của tác giả, không có nguồn chính thức trực tiếp. **Không bịa nguồn** cho claim này.

### 4.2. `sources.json`

Registry nguồn:

```json
{
  "id": "SRC-FRED-CSHPLR",
  "publisher": "S&P CoreLogic Case-Shiller",
  "publisher_short": "Case-Shiller (FRED)",
  "title": "S&P/Case-Shiller U.S. National Home Price Index",
  "url": "https://fred.stlouisfed.org/series/CSUSHPINSA",
  "publisher_type": "official",
  "accessed_at": "2026-07-18",
  "license": "Public domain (FRED)",
  "topics": ["us-housing", "asset-prices"],
  "language": "en"
}
```

#### `publisher_type` để UI phân loại

| Loại | Ví dụ |
|---|---|
| `official` | Fed, BIS, BEA, NBS, BoJ, PBOC, BLS |
| `international` | IMF, World Bank, OECD, BIS cross-country |
| `academic` | Nghiên cứu peer-review (vd: Richard Koo, Nomura) |
| `media-quality` | Financial Times, Bloomberg, Reuters (chỉ verify sự kiện) |
| `authoritative-book` | Sách nhà kinh tế uy tín |

### 4.3. Nguyên tắc kiểm chứng (anti-fabrication)

1. Mọi URL trong `sources.json` phải **thực sự tồn tại** — WebSearch/WebFetch verify trước khi nhập.
2. Không gán phát biểu cho IMF/Fed/PBOC nếu không tìm thấy document gốc.
3. Mỗi claim định lượng phải có ít nhất 1 source `official` hoặc `international`.
4. Nếu không tìm được source phù hợp → claim xuống `author-view`, không fake status `verified`.
5. Số liệu minh họa (vd: Allocation Shift 70/30) **không** là claim, được ghi trong visual_plan với `data_needed: "illustrative-mechanism"`.

---

## 5. Kế hoạch verify cho 3 case study

Chương 12 (TQ), 13 (Nhật), 14 (Mỹ) là phần khó nhất. Dưới đây là checklist verify.

### 5.1. Chương 14 — Mỹ

| Mốc | Số liệu cần | Nguồn mục tiêu |
|---|---|---|
| Trước 2008: tín dụng nhà + securitization | Nợ hộ gia đình/GDP, MBS outstanding | FRED (HDTGPDUSQ), SIFMA |
| 2008–09: GFC | S&P 500 rơi ~57% (10/2007–3/2009), GDP suy thoái | FRED SP500, BEA |
| Sau 2008: deleveraging hộ gia đình | Nợ hộ gia đình/GDP giảm ~100% (2007) → ~75% (2020) | FRED HDTGPDUSQ |
| Dodd-Frank Act | 2010, stress tests, capital ratios | Federal Reserve, Congress.gov |
| Phục hồi tài sản (QE) | S&P 500 từ đáy 3/2009 → peak; Case-Shiller | FRED SP500, CSUSHPINSA |
| Phục hồi việc làm | Tỷ lệ thất nghiệp peak 10% (10/2009) | BLS LNS14000000 |
| Đầu tư hạ tầng | CHIPS Act 2022, IRA 2022 | Congress.gov, White House archives |

### 5.2. Chương 13 — Nhật Bản

| Mốc | Số liệu cần | Nguồn mục tiêu |
|---|---|---|
| Bong bóng 1980s | Nikkei peak 38,915 (12/1989); giá đất六大都市 | BoJ, Japan Real Estate Institute |
| Sụp đổ 1990–91 | Nikkei rơi >50% trong 1990; "Lost Decade" | BoJ, IMF Japan studies |
| Nợ xấu ngân hàng | NPL ratio peak ~8% (2001–02) | BoJ, FSA Japan |
| Balance sheet recession | Khái niệm Richard Koo | Richard Koo, "The Holy Grail of Macroeconomics" |
| Giảm phát kéo dài | CPI YoY âm nhiều năm 1999–2012 | BoJ, FRED JPNCPIALLMINMEI |
| Tiền lương trì trệ | Real wage index flat 1997–2012 | MLS Hello Work, OECD |
| GDP thấp | Tăng trưởng ~1%/năm | Cabinet Office Japan, FRED |

### 5.3. Chương 12 — Trung Quốc

| Mốc | Số liệu cần | Nguồn mục tiêu |
|---|---|---|
| Cú sốc chứng khoán 2015 | Shanghai Composite peak 5,166 (6/2015) → ~3,000 (8/2015) | NBS, Bloomberg, CSRC |
| "thoát hư hướng thực" 2016 | "脱虚向实" trong Financial Work Conference 7/2017 | Xinhua, PBOC |
| Giảm đòn bẩy 2017–2020 | Shadow banking assets; nợ phi tài chính/GDP | BIS, PBOC China Financial Stability Report |
| Ba lằn ranh đỏ (BĐS) 8/2020 | Thông tư PBOC 8/2020; Evergrande default 12/2021 | PBOC, Reuters, IMF Article IV |
| Kiểm soát internet platform | Alibaba fining 4/2021, $2.8B | SAMR, Reuters |
| Sản xuất tiên tiến | EV output, battery share, semiconductor policy | CAAM, IEA, MIIT |
| Xu hướng gần đây | GDP growth, property investment decline | NBS quarterly |

### 5.4. Phản biện bắt buộc (cho cả 3 case study)

Mỗi case study phải có 1–2 phản biện với claim `status: "disputed"` và ít nhất 2 nguồn đại diện 2 góc nhìn:

- **Mỹ**: "Mỹ không thực sự rời bỏ tài chính hóa — Fed balance sheet vẫn lớn, giá tài sản phục hồi trước hộ gia đình."
- **Nhật**: "Tranh luận về nguyên nhân giảm phát — balance sheet recession (Koo) vs. monetary policy failure vs. demographics."
- **TQ**: "Tranh luận về chi phí chuyển đổi — tăng trưởng chậm, криз BĐS, vs. lợi ích dài hạn."

### 5.5. Phương pháp verify chung

1. **WebSearch + WebFetch** để check mỗi mốc.
2. Ưu tiên URL từ domain chính thức: `.gov`, `imf.org`, `bis.org`, `worldbank.org`, `fred.stlouisfed.org`, `boj.or.jp`, `pbc.gov.cn`, `stats.gov.cn`.
3. Nếu domain chính thức không có số liệu chính xác → dùng **media-quality** (FT, Bloomberg, Reuters) có trích dẫn số liệu từ nguồn chính thức.
4. Nếu vẫn không tìm được → claim xuống `author-view`, note rõ "Không tìm được nguồn chính thức xác minh số liệu cụ thể; trình bày theo diễn giải tác giả."
5. **Không tự suy luận** hoặc nội suy số liệu.

---

## 6. Workflow thực thi theo chương (Approach 1)

### 6.1. Quy trình 4 bước cho mỗi chương

```
Bước 1: Trích claims
  • Đọc đoạn chương tương ứng trong bài nguồn 18 phần.
  • Trích 5–12 claims, mỗi claim gắn type tạm: fact | mechanism | interpretation.

Bước 2: Verify nguồn
  • Với mỗi claim:
    - fact/mechanism định lượng → WebSearch + WebFetch check domain chính thức.
    - interpretation thuần túy → gán status author-view (không cần verify).
  • Cập nhật sources.json.

Bước 3: Viết content/chXX.json
  • Đầy đủ: opening_question, sections (prose, mechanism, visual_plan, counterpoint), takeaway, visual_plans, claim_refs.

Bước 4: Nghiệm thu chương
  • Đếm claims verify/qual/disputed/author-view.
  • Kiểm không có citation giả.
  • Kiểm visual_plans đầy đủ.
  • Cập nhật progress.md.
```

### 6.2. Thứ tự ưu tiên chương (độ khó tăng dần)

Không bắt buộc tuần tự 1→18. Khuyến nghị theo 3 pha:

| Pha | Chương | Đặc điểm | Lý do ưu tiên |
|---|---|---|---|
| **Pha 1 — Khái niệm** | 1, 2, 3, 11, 15 | Khái niệm nền, ít số liệu | Làm nóng quy trình, dễ verify |
| **Pha 2 — Cơ chế** | 4, 5, 6, 7, 8, 9, 10, 16, 17, 18 | Cơ chế học thuyết | Phần lớn nội dung, chạy nhanh |
| **Pha 3 — Case study** | 12, 13, 14 | Research lịch sử nặng | Làm cuối khi workflow đã ổn định |

### 6.3. File nghiệm thu `progress.md`

```markdown
# Research Progress

## Đã hoàn thành
- [x] Chương 1 — Hai nửa nền kinh tế (12 claims, 8 verified, 4 author-view)

## Đang tiến hành
- [ ] Chương 2 — Khi lợi nhuận tài sản hấp dẫn hơn sản xuất

## Còn lại
- [ ] Chương 3–18
```

### 6.4. Tốc độ dự kiến

- **Pha 1** (5 chương khái niệm): ~10–15 tool-calls/chương.
- **Pha 2** (10 chương cơ chế): ~12–18 tool-calls/chương.
- **Pha 3** (3 case study): ~25–40 tool-calls/chương.

Tổng cộng Giai đoạn R hoàn thành trong 1–2 phiên làm việc dài.

---

## 7. Special insights và phản biện (theo prompt Section VIII & XIX)

### 7.1. 8 special insights (`insights.md`)

| # | Insight | Chương liên kết |
|---|---|---|
| 1 | Tài chính hóa không chỉ là quy mô ngành tài chính | Chương 2, 4 |
| 2 | Giá tài sản vừa là kết quả, vừa là nguyên nhân | Chương 6, 7 |
| 3 | Không phải mọi đầu tư vào tài sản đều là đầu cơ | Chương 8, 16 |
| 4 | Phi tài chính hóa không đồng nghĩa thị trường giảm mãi | Chương 8, 14 |
| 5 | Tái cân bằng là cuộc chiến phân bổ tổn thất | Chương 10, 16 |
| 6 | Độ đau chuyển pha phụ thuộc bảng cân đối | Chương 10, 13 |
| 7 | Main Street hiện đại không chỉ là nhà máy | Chương 1, 15, 17 |
| 8 | Wall Street có thể tài trợ quay về Main Street | Chương 8, 15 |

### 7.2. 10 phản biện (`counterpoints.md`)

Phần "Những điều mô hình Main Street–Wall Street không giải thích hết":

1. Tài sản tăng không nhất thiết đồng nghĩa bong bóng.
2. Thị trường chứng khoán tăng có thể phản ánh lợi nhuận và đổi mới.
3. Sản xuất hiện đại có nhiều tài sản vô hình.
4. Ngành tài chính có thể tạo ra giá trị thực.
5. Vốn đầu cơ đôi khi cung cấp thanh khoản và chấp nhận rủi ro.
6. Bất bình đẳng không chỉ đến từ tài chính hóa.
7. Chính sách ưu tiên sản xuất có thể dẫn tới đầu tư dư thừa.
8. Giảm tài chính hóa quá mạnh có thể làm giảm khả năng huy động vốn.
9. Không có tỷ lệ Main Street–Wall Street tối ưu cho mọi quốc gia.
10. Case study TQ/Nhật/Mỹ không thể so sánh hoàn toàn trực tiếp.

Mỗi phản biện là 1 claim `status: "disputed"` với ít nhất 2 nguồn.

---

## 8. Tiêu chuẩn nghiệm thu Giai đoạn R

| # | Tiêu chuẩn | Cách kiểm chứng |
|---|---|---|
| 1 | 18 file `content/chapters/chXX.json` đầy đủ | `ls content/chapters/*.json \| wc -l` = 18 |
| 2 | `content/index.json` có đủ 18 chương | Đọc file |
| 3 | `claims.json` có 100–150 claim | Đếm entry |
| 4 | Mỗi claim có đủ 7 trường bắt buộc | JSON schema validation |
| 5 | `sources.json` có 50–80 nguồn | Đếm entry |
| 6 | Mọi URL trong sources.json thực sự tồn tại | WebFetch ngẫu nhiên 10 URL |
| 7 | Không có citation giả | Manual review |
| 8 | Mỗi chương có ít nhất 1 visual_plan | Đọc content/chXX.json |
| 9 | 3 case study (12, 13, 14) có ≥5 claim `verified` mỗi chương | Lọc theo status |
| 10 | Glossary có ≥30 thuật ngữ | Đếm entry |
| 11 | `methodology.md` giải thích cách phân loại claim + verify | Đọc file |
| 12 | `progress.md` đánh dấu 18/18 chương hoàn thành | Đọc file |

---

## 9. Sản phẩm bàn giao cuối Giai đoạn R

```
content/
├─ index.json
├─ claims.json
├─ sources.json
├─ glossary.json
├─ methodology.md
├─ progress.md
├─ insights.md
├─ counterpoints.md
└─ chapters/
   └─ ch01.json ... ch18.json

RESEARCH-REPORT.md  ← ở root repo
```

### `RESEARCH-REPORT.md` chứa

- Số claim theo status (verified / qualified / disputed / author-view).
- Top 10 nguồn được dùng nhiều nhất.
- 8 special insights phát hiện trong research.
- 10 phản biện đã trình bày.
- Known limitations.
- Khuyến nghị cho Giai đoạn A (Hero + chương 1–6 build).

---

## 10. Known limitations

1. **Số liệu chính xác có thể không khớp 100%** giữa các nguồn (vd: tỷ lệ nợ/GDP khác nhau giữa BIS, IMF, PBOC vì phương pháp tính khác). Sẽ ghi rõ nguồn cụ thể + ngày truy cập.

2. **Một số claim không thể verify hoàn toàn** → status `author-view`. Đặc biệt:
   - Các nhận định chính trị/chính sách.
   - Các dự báo/kỳ vọng tương lai.
   - Các quan điểm thuần diễn giải.

3. **Tranh luận học thuật có nhiều trường phái** — một số claim sẽ `disputed` với 2 nguồn đại diện, không thể đầy đủ mọi góc nhìn.

4. **Ngôn ngữ nguồn**: NBS/PBOC thường tiếng Trung, BoJ tiếng Nhật. Sẽ dùng phiên bản tiếng Anh khi có (BoJ, IMF country reports), nếu chỉ tiếng Trung/Nhật thì ghi rõ.

5. **Số liệu đến hiện tại**: dữ liệu cập nhật đến ngày truy cập (2026-07-18), không dự báo.

6. **Không phải paper học thuật**: đây là nền tảng nội dung cho website editorial, không phải meta-analysis peer-review. Mục tiêu là "trung thực với nguồn" chứ không phải "tiên học thuật".

---

## 11. Chuyển giao cho Giai đoạn A

Khi Giai đoạn R hoàn thành, Giai đoạn A sẽ nhận:

| File | Dùng cho |
|---|---|
| `content/chapters/ch01.json` → `ch06.json` | Dữ liệu UI cho 6 chương đầu |
| `claims.json` + `sources.json` | Render panel nguồn/nhãn Fact/Mechanism/Interpretation |
| `glossary.json` | Glossary drawer |
| `methodology.md` | Trang `/methodology` |
| `insights.md` + `counterpoints.md` | Section riêng trong site |
| `RESEARCH-REPORT.md` | Dữ liệu cho `README.md` và báo cáo cuối |

Giai đoạn A sẽ viết spec riêng sau khi Giai đoạn R nghiệm thu xong.

---

## 12. Tóm tắt

Spec này định nghĩa **Giai đoạn R** — giai đoạn research content cho website Main Street vs Wall Street. Sản phẩm là các file JSON + markdown tổ chức chặt chẽ, có nguồn xác thực, làm đầu vào bắt buộc cho Giai đoạn A/B/C build UI. Workflow theo chương tuần tự, ưu tiên Pha 1 (khái niệm) → Pha 2 (cơ chế) → Pha 3 (case study). Tiêu chuẩn nghiệm thu 12 điều. Không bịa nguồn, không citation giả.

**Bước tiếp theo**: invoke `writing-plans` skill để tạo implementation plan chi tiết cho Giai đoạn R.
