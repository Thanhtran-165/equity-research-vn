# Main Street vs Wall Street — Giai đoạn R (Content Research) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng nền tảng nội dung (18 chương content JSON + claims + sources + glossary + methodology + insights + counterpoints) cho website editorial "Main Street vs Wall Street" — đầu vào bắt buộc cho Giai đoạn A build UI.

**Architecture:** Workflow theo chương tuần tự (Approach 1). Mỗi chương: trích claims từ bài nguồn → WebSearch/WebFetch verify → viết `content/chapters/chXX.json` → cập nhật `claims.json` + `sources.json` + `progress.md`. Sắp xếp theo 3 pha độ khó tăng dần: Pha 1 (chương khái niệm 1,2,3,11,15) → Pha 2 (chương cơ chế 4,5,6,7,8,9,10,16,17,18) → Pha 3 (case study 12,13,14). JSON schema validation script đảm bảo tính nhất quán.

**Tech Stack:** JSON + Markdown. Không code UI. Validator script bằng Node.js (đã có sẵn trong môi trường). Verify bằng WebSearch + WebFetch.

**Spec reference:** `docs/superpowers/specs/2026-07-18-msvs-content-research-design.md`

---

## File Structure

```
content/
├─ index.json                    ← Task 2 (initial) + cập nhật mỗi chương
├─ claims.json                   ← Task 2 (initial rỗng) + append mỗi chương
├─ sources.json                  ← Task 2 (initial rỗng) + append mỗi chương
├─ glossary.json                 ← Task 2 (initial rỗng) + cập nhật xuyên suốt
├─ methodology.md                ← Task 2
├─ progress.md                   ← Task 2 (initial) + cập nhật mỗi chương
├─ insights.md                   ← Task 21
├─ counterpoints.md              ← Task 22
└─ chapters/
   ├─ ch01.json ... ch18.json    ← Task 3-20 (mỗi chương 1 task)

scripts/
└─ validate-content.mjs          ← Task 1 — JSON schema validator

RESEARCH-REPORT.md               ← Task 23 (cuối cùng, root repo)
```

---

## Task 1: Schema validator script + directory scaffold

**Files:**
- Create: `scripts/validate-content.mjs`
- Create: `content/` (directory)
- Create: `content/chapters/` (directory)

- [ ] **Step 1: Tạo directory structure**

```bash
mkdir -p content/chapters scripts
```

- [ ] **Step 2: Viết `scripts/validate-content.mjs`**

Validator chạy được với `node scripts/validate-content.mjs`. Kiểm tra schema cho tất cả file content.

```javascript
// scripts/validate-content.mjs
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const CONTENT_DIR = 'content';
const CHAPTERS_DIR = join(CONTENT_DIR, 'chapters');

const REQUIRED_CHAPTER_FIELDS = ['id', 'number', 'slug', 'title', 'summary', 'opening_question', 'sections', 'takeaway', 'visual_plans', 'claim_refs', 'chapter_pattern', 'reading_time_min'];
const VALID_SECTION_TYPES = ['prose', 'mechanism', 'visual_plan', 'example', 'counterpoint', 'takeaway'];
const VALID_PATTERNS = ['sticky-scroll', 'inline-flow', 'hybrid'];
const VALID_CLAIM_TYPES = ['fact', 'mechanism', 'interpretation'];
const VALID_CLAIM_STATUS = ['verified', 'qualified', 'disputed', 'author-view'];
const REQUIRED_CLAIM_FIELDS = ['id', 'chapter', 'claim', 'type', 'status', 'sources', 'note'];
const REQUIRED_SOURCE_FIELDS = ['id', 'publisher', 'title', 'url', 'publisher_type', 'accessed_at'];
const VALID_PUBLISHER_TYPES = ['official', 'international', 'academic', 'media-quality', 'authoritative-book'];

const errors = [];
const warnings = [];

function readJSON(path) {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (e) {
    errors.push(`${path}: JSON parse error — ${e.message}`);
    return null;
  }
}

// Validate claims.json
const claims = readJSON(join(CONTENT_DIR, 'claims.json'));
if (claims) {
  const ids = new Set();
  for (const c of claims) {
    if (ids.has(c.id)) errors.push(`claims.json: duplicate id ${c.id}`);
    ids.add(c.id);
    for (const f of REQUIRED_CLAIM_FIELDS) {
      if (!(f in c)) errors.push(`claims.json ${c.id}: missing field "${f}"`);
    }
    if (!VALID_CLAIM_TYPES.includes(c.type)) errors.push(`claims.json ${c.id}: invalid type "${c.type}"`);
    if (!VALID_CLAIM_STATUS.includes(c.status)) errors.push(`claims.json ${c.id}: invalid status "${c.status}"`);
    if (c.type !== 'interpretation' && c.status === 'verified' && (!c.sources || c.sources.length === 0)) {
      errors.push(`claims.json ${c.id}: fact/mechanism với status verified phải có ít nhất 1 source`);
    }
    if (c.type === 'interpretation' && c.status === 'verified') {
      warnings.push(`claims.json ${c.id}: interpretation mà status verified — nên là author-view`);
    }
  }
}

// Validate sources.json
const sources = readJSON(join(CONTENT_DIR, 'sources.json'));
const sourceIds = new Set();
if (sources) {
  for (const s of sources) {
    if (sourceIds.has(s.id)) errors.push(`sources.json: duplicate id ${s.id}`);
    sourceIds.add(s.id);
    for (const f of REQUIRED_SOURCE_FIELDS) {
      if (!(f in s)) errors.push(`sources.json ${s.id}: missing field "${f}"`);
    }
    if (!VALID_PUBLISHER_TYPES.includes(s.publisher_type)) errors.push(`sources.json ${s.id}: invalid publisher_type`);
    if (!s.url.startsWith('http')) errors.push(`sources.json ${s.id}: url không hợp lệ`);
  }
}

// Validate references
if (claims && sources) {
  for (const c of claims) {
    for (const sid of (c.sources || [])) {
      if (!sourceIds.has(sid)) errors.push(`claims.json ${c.id}: refers to missing source ${sid}`);
    }
  }
}

// Validate chapters
const chapters = existsSync(CHAPTERS_DIR) ? readdirSync(CHAPTERS_DIR).filter(f => f.endsWith('.json')) : [];
const claimIds = new Set((claims || []).map(c => c.id));
for (const fname of chapters) {
  const ch = readJSON(join(CHAPTERS_DIR, fname));
  if (!ch) continue;
  for (const f of REQUIRED_CHAPTER_FIELDS) {
    if (!(f in ch)) errors.push(`${fname}: missing field "${f}"`);
  }
  if (!VALID_PATTERNS.includes(ch.chapter_pattern)) errors.push(`${fname}: invalid pattern ${ch.chapter_pattern}`);
  for (const s of (ch.sections || [])) {
    if (!VALID_SECTION_TYPES.includes(s.type)) errors.push(`${fname}: invalid section type ${s.type}`);
  }
  for (const cid of (ch.claim_refs || [])) {
    if (!claimIds.has(cid)) errors.push(`${fname}: refers to missing claim ${cid}`);
  }
  if (!ch.visual_plans || ch.visual_plans.length === 0) {
    errors.push(`${fname}: phải có ít nhất 1 visual_plan`);
  }
}

// Summary
console.log(`\n=== Content Validation ===`);
console.log(`Claims: ${(claims||[]).length}`);
console.log(`Sources: ${(sources||[]).length}`);
console.log(`Chapters: ${chapters.length}`);
console.log(`Errors: ${errors.length}`);
console.log(`Warnings: ${warnings.length}`);
if (errors.length > 0) {
  console.log(`\n--- ERRORS ---`);
  for (const e of errors) console.log(`  ✗ ${e}`);
}
if (warnings.length > 0) {
  console.log(`\n--- WARNINGS ---`);
  for (const w of warnings) console.log(`  ⚠ ${w}`);
}
process.exit(errors.length > 0 ? 1 : 0);
```

- [ ] **Step 3: Kiểm tra script chạy được**

```bash
node scripts/validate-content.mjs
```

Expected: in ra summary, 0 errors (vì chưa có file). Có thể báo lỗi file không tồn tại — script phải handle gracefully.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate-content.mjs
git commit -m "feat(msvs): JSON schema validator for content/claims/sources"
```

---

## Task 2: Initial content files (skeleton)

**Files:**
- Create: `content/claims.json`
- Create: `content/sources.json`
- Create: `content/glossary.json`
- Create: `content/index.json`
- Create: `content/methodology.md`
- Create: `content/progress.md`

- [ ] **Step 1: Tạo `content/claims.json` (rỗng)**

```json
[]
```

- [ ] **Step 2: Tạo `content/sources.json` (rỗng)**

```json
[]
```

- [ ] **Step 3: Tạo `content/glossary.json`**

```json
{
  "version": "1.0",
  "language": "vi",
  "terms": []
}
```

- [ ] **Step 4: Tạo `content/index.json`**

```json
{
  "project": "main-street-vs-wall-street",
  "version": "1.0",
  "language": "vi",
  "total_chapters": 18,
  "chapters": []
}
```

- [ ] **Step 5: Tạo `content/methodology.md`**

```markdown
# Methodology — Main Street vs Wall Street

## Cách phân loại claim

Mỗi luận điểm trong website được gắn một trong 3 nhãn:

- **Fact** — dữ kiện có thể kiểm chứng (số liệu, sự kiện lịch sử, định nghĩa).
- **Mechanism** — cơ chế kinh tế được giải thích (vòng lặp phản hồi, kênh truyền dẫn).
- **Interpretation** — diễn giải hoặc quan điểm của tác giả.

## Cách gán status

- **verified** — có ít nhất 1 nguồn chính thức (IMF, Fed, BIS, BEA, BoJ, PBOC, NBS, FRED) hỗ trợ trực tiếp.
- **qualified** — đúng trong điều kiện nhất định, có nguồn nhưng cần caveat.
- **disputed** — có tranh luận học thuật, trình bày cả hai góc nhìn.
- **author-view** — quan điểm của tác giả bài nguồn, không có nguồn chính thức trực tiếp.

## Nguyên tắc chống bịa (anti-fabrication)

1. Mọi URL trong `sources.json` phải thực sự tồn tại, được verify bằng WebFetch.
2. Không gán phát biểu cho IMF/Fed/PBOC nếu không tìm thấy document gốc.
3. Mỗi claim định lượng phải có ít nhất 1 source `official` hoặc `international`.
4. Nếu không tìm được source → claim xuống `author-view`, không fake `verified`.
5. Số liệu minh họa (vd: Allocation Shift 70/30) không phải là claim, được ghi trong visual_plan với `data_needed: "illustrative-mechanism"`.

## Phương pháp verify

- Ưu tiên domain chính thức: `.gov`, `imf.org`, `bis.org`, `worldbank.org`, `fred.stlouisfed.org`, `boj.or.jp`, `pbc.gov.cn`, `stats.gov.cn`.
- Nếu domain chính thức không có → dùng media-quality (FT, Bloomberg, Reuters) có trích dẫn số liệu từ nguồn chính thức.
- Nếu vẫn không tìm được → `author-view`, note rõ.
- Không tự suy luận hoặc nội suy số liệu.
- Mỗi source có `accessed_at` (ngày truy cập).

## Giới hạn (limitations)

1. Số liệu có thể khác nhau giữa các nguồn (BIS vs IMF vs PBOC) do phương pháp tính khác.
2. Một số claim không thể verify hoàn toàn — đặc biệt nhận định chính trị, dự báo, diễn giải thuần túy.
3. Tranh luận học thuật có nhiều trường phái — claim `disputed` chỉ đại diện 2 góc nhìn, không đầy đủ.
4. Nguồn tiếng Trung/Nhật — dùng bản tiếng Anh nếu có, nếu không thì ghi rõ ngôn ngữ gốc.
5. Số liệu đến hiện tại — cập nhật đến ngày truy cập (2026-07-18), không dự báo.
6. Đây là nền tảng editorial, không phải paper peer-review.
```

- [ ] **Step 6: Tạo `content/progress.md`**

```markdown
# Research Progress — Giai đoạn R

## Pha 1 — Khái niệm (ưu tiên trước)
- [ ] Chương 1 — Hai nửa của nền kinh tế
- [ ] Chương 2 — Khi lợi nhuận tài sản hấp dẫn hơn sản xuất
- [ ] Chương 3 — Hai tốc độ lạm phát
- [ ] Chương 11 — Một nền kinh tế mạnh cần sự cân bằng
- [ ] Chương 15 — Một nền kinh tế muốn vươn mình phải coi trọng Main Street trước

## Pha 2 — Cơ chế
- [ ] Chương 4 — Hiệu ứng lấn át
- [ ] Chương 5 — Tài sản, quyền sở hữu và bất bình đẳng
- [ ] Chương 6 — Chu kỳ lành mạnh và chu kỳ bong bóng
- [ ] Chương 7 — Khi Wall Street thịnh vượng nhưng Main Street suy yếu
- [ ] Chương 8 — Từ Wall Street trở lại Main Street
- [ ] Chương 9 — Chu kỳ hay lựa chọn chính sách?
- [ ] Chương 10 — Vì sao đường về Main Street thường đau hơn?
- [ ] Chương 16 — Ai chịu cú sốc lớn nhất khi nền kinh tế quay về Main Street?
- [ ] Chương 17 — Ai hưởng lợi khi Main Street phục hồi?
- [ ] Chương 18 — Mỗi cá nhân cần chuẩn bị gì cho sự chuyển pha?

## Pha 3 — Case study (verify nặng)
- [ ] Chương 12 — Trung Quốc: chuyển hướng từ khoảng năm 2016
- [ ] Chương 13 — Nhật Bản: cuộc tái cân bằng bị ép buộc
- [ ] Chương 14 — Mỹ: tái cấu trúc nhưng chưa rời bỏ tài chính hóa

## Tổng kết
- Tổng chương: 0/18
- Tổng claims: 0
- Tổng sources: 0
```

- [ ] **Step 7: Kiểm tra validator pass**

```bash
node scripts/validate-content.mjs
```

Expected: 0 errors, summary báo Claims: 0, Sources: 0, Chapters: 0.

- [ ] **Step 8: Commit**

```bash
git add content/
git commit -m "feat(msvs): initial content skeleton (claims/sources/glossary/index/methodology/progress)"
```

---

## Task 3: Chương 1 — Hai nửa của nền kinh tế (Pha 1, template task)

> Đây là **template task**. Các task 4–20 (chương 2–18) lặp cùng cấu trúc 6 bước này với nội dung đặc thù.

**Files:**
- Create: `content/chapters/ch01.json`
- Modify: `content/claims.json` (append claims)
- Modify: `content/sources.json` (append sources)
- Modify: `content/glossary.json` (append terms)
- Modify: `content/index.json` (append chapter entry)
- Modify: `content/progress.md` (mark chapter done)

**Nội dung nguồn (Chương 1 trong bài):**

> Main Street là nền kinh tế thực: doanh nghiệp, nhà máy, cửa hàng, người lao động — nơi hàng hóa, dịch vụ, việc làm và thu nhập được tạo ra.
> Wall Street là khu vực tài chính: ngân hàng, chứng khoán, trái phiếu, quỹ đầu tư — nơi vốn được huy động, giao dịch và phân bổ.
> Trong một nền kinh tế lành mạnh: Wall Street dẫn vốn, Main Street tạo ra của cải. Tài chính phải phục vụ sản xuất và kinh doanh...

- [ ] **Step 1: Trích claims từ bài nguồn**

Đọc đoạn chương 1, trích 5–8 claims, gán type tạm:

- `CLM-001` (fact) — Main Street là nền kinh tế thực (định nghĩa)
- `CLM-002` (fact) — Wall Street là khu vực tài chính (định nghĩa)
- `CLM-003` (mechanism) — Vai trò của Wall Street: huy động và phân bổ vốn
- `CLM-004` (mechanism) — Vai trò của Main Street: tạo hàng hóa, việc làm, thu nhập
- `CLM-005` (interpretation) — Tài chính phải phục vụ sản xuất, không chỉ luân chuyển giữa tài sản
- `CLM-006` (mechanism) — Vòng tuần hoàn: Tiết kiệm → Tài chính → Vốn → Doanh nghiệp → Việc làm → Thu nhập → Tiết kiệm

- [ ] **Step 2: Verify nguồn cho mỗi claim định lượng/fact**

Cho chương 1 (khái niệm cốt lõi, ít số liệu), verify:

- `CLM-001` Main Street = real economy → search `"Main Street real economy definition Federal Reserve"` → tìm Fed/BIS glossary.
- `CLM-002` Wall Street = financial sector → search `"Wall Street financial sector definition"` → tìm Investopedia/Fed glossary.
- `CLM-003`, `CLM-004`, `CLM-006` là mechanism (cơ chế kinh tế), không cần số liệu → status `verified` nếu nguồn mô tả đúng cơ chế, hoặc `author-view` nếu là diễn giải.
- `CLM-005` là interpretation thuần → status `author-view`.

Cho mỗi nguồn tìm được, thêm vào `sources.json` với schema:

```json
{
  "id": "SRC-FED-MainST",
  "publisher": "Federal Reserve",
  "publisher_short": "Fed",
  "title": "Monetary Policy Report — Main Street reference",
  "url": "https://www.federalreserve.gov/monetarypolicy/...",
  "publisher_type": "official",
  "accessed_at": "2026-07-18",
  "license": "Public domain",
  "topics": ["main-street", "real-economy"],
  "language": "en"
}
```

**Verify thực tế:** Dùng WebSearch để tìm URL chính xác, WebFetch để xác nhận nội dung tồn tại. Nếu không tìm được URL chính xác → claim xuống `author-view`.

- [ ] **Step 3: Thêm claims vào `content/claims.json`**

```json
[
  {
    "id": "CLM-001",
    "chapter": "ch01",
    "claim": "Main Street là nền kinh tế thực — nơi hàng hóa, dịch vụ, việc làm và thu nhập được tạo ra.",
    "type": "fact",
    "status": "verified",
    "sources": ["SRC-FED-MainST"],
    "note": "Định nghĩa chuẩn. Main Street là metaphor cho real economy, dùng phổ biến trong tài liệu Fed/IMF.",
    "source_quote": "Main Street refers to the real economy..."
  },
  {
    "id": "CLM-002",
    "chapter": "ch01",
    "claim": "Wall Street là khu vực tài chính — ngân hàng, chứng khoán, trái phiếu, quỹ đầu tư — nơi vốn được huy động, giao dịch và phân bổ.",
    "type": "fact",
    "status": "verified",
    "sources": ["SRC-INVESTOPEDIA-WALLST"],
    "note": "Định nghĩa phổ thông. Wall Street thường được dùng để chỉ hệ thống tài chính Mỹ nói chung.",
    "source_quote": "Wall Street refers to the financial industry..."
  },
  {
    "id": "CLM-003",
    "chapter": "ch01",
    "claim": "Vai trò của Wall Street là huy động tiết kiệm và phân bổ vốn đến các cơ hội đầu tư.",
    "type": "mechanism",
    "status": "verified",
    "sources": ["SRC-BIS-FININTERMED"],
    "note": "Chức năng trung gian tài chính (financial intermediation) — lý thuyết chuẩn.",
    "source_quote": "Financial intermediaries channel savings to investment..."
  },
  {
    "id": "CLM-004",
    "chapter": "ch01",
    "claim": "Vai trò của Main Street là tạo ra hàng hóa, dịch vụ, việc làm và thu nhập thông qua sản xuất và kinh doanh.",
    "type": "mechanism",
    "status": "verified",
    "sources": ["SRC-BEA-GDP"],
    "note": "GDP theo组成部分 (C+I+G+NX) đo lường hoạt động Main Street.",
    "source_quote": "GDP measures the value of goods and services produced..."
  },
  {
    "id": "CLM-005",
    "chapter": "ch01",
    "claim": "Trong một nền kinh tế lành mạnh, tài chính phải phục vụ sản xuất, thay vì chỉ luân chuyển giữa các tài sản với giá ngày càng cao.",
    "type": "interpretation",
    "status": "author-view",
    "sources": [],
    "note": "Quan điểm của tác giả bài nguồn. Không có nguồn chính thức trực tiếp xác minh.",
    "source_quote": null
  },
  {
    "id": "CLM-006",
    "chapter": "ch01",
    "claim": "Vòng tuần hoàn kinh tế: Tiết kiệm → Hệ thống tài chính → Vốn đầu tư → Doanh nghiệp → Việc làm và sản lượng → Thu nhập và tiết kiệm.",
    "type": "mechanism",
    "status": "verified",
    "sources": ["SRC-IMF-FINSECTOR"],
    "note": "Sơ đồ vòng tuần hoàn vốn (circular flow) — lý thuyết kinh tế vĩ mô chuẩn.",
    "source_quote": "The circular flow of income links savings, investment, and output..."
  }
]
```

(Lưu ý: URL và ID source thực tế phải được verify trong Bước 2. Ví dụ trên là template — engineer phải thay URL thật.)

- [ ] **Step 4: Thêm sources vào `content/sources.json`**

Cho mỗi SRC-* đã tham chiếu, thêm entry đầy đủ. Ví dụ:

```json
[
  {
    "id": "SRC-FED-MainST",
    "publisher": "Federal Reserve",
    "publisher_short": "Fed",
    "title": "Monetary Policy Report",
    "url": "https://www.federalreserve.gov/monetarypolicy/2026-feb-mpr-part1.htm",
    "publisher_type": "official",
    "accessed_at": "2026-07-18",
    "license": "Public domain",
    "topics": ["main-street", "real-economy"],
    "language": "en"
  }
]
```

- [ ] **Step 5: Thêm glossary terms**

Thêm 5 thuật ngữ vào `content/glossary.json` → `terms`:

```json
[
  {
    "term": "Main Street",
    "definition_vi": "Nền kinh tế thực — doanh nghiệp, nhà máy, cửa hàng, người lao động. Nơi hàng hóa, dịch vụ, việc làm và thu nhập được tạo ra.",
    "category": "concept"
  },
  {
    "term": "Wall Street",
    "definition_vi": "Hệ thống tài chính — ngân hàng, chứng khoán, trái phiếu, quỹ đầu tư. Nơi vốn được huy động, giao dịch và phân bổ.",
    "category": "concept"
  },
  {
    "term": "Nền kinh tế thực (Real economy)",
    "definition_vi": "Phần nền kinh tế tạo ra hàng hóa và dịch vụ thực, đối lập với khu vực tài chính.",
    "category": "concept"
  },
  {
    "term": "Trung gian tài chính (Financial intermediation)",
    "definition_vi": "Quá trình ngân hàng và quỹ thu nhận tiết kiệm rồi cho vay lại cho doanh nghiệp và hộ gia đình.",
    "category": "mechanism"
  },
  {
    "term": "Vòng tuần hoàn vốn (Circular flow)",
    "definition_vi": "Dòng luân chuyển: tiết kiệm → tài chính → vốn → doanh nghiệp → việc làm → thu nhập → tiết kiệm.",
    "category": "mechanism"
  }
]
```

- [ ] **Step 6: Viết `content/chapters/ch01.json`**

```json
{
  "id": "ch01",
  "number": 1,
  "slug": "hai-nua-cua-nen-kinh-te",
  "title": "Hai nửa của nền kinh tế",
  "summary": "Main Street tạo ra của cải. Wall Street dẫn dòng vốn. Một nền kinh tế khỏe mạnh cần cả hai.",
  "opening_question": "Một nền kinh tế có thực sự chỉ là một, hay là hai thế giới vận hành theo tốc độ khác nhau?",
  "sections": [
    {
      "type": "prose",
      "label": "Luận điểm",
      "content": "Mọi nền kinh tế hiện đại gồm hai phần gắn kết. Main Street — doanh nghiệp, nhà máy, cửa hàng, người lao động — là nơi hàng hóa, dịch vụ, việc làm và thu nhập được tạo ra. Wall Street — ngân hàng, chứng khoán, trái phiếu, quỹ đầu tư — là nơi vốn được huy động, giao dịch và phân bổ. Hai phần không đối lập, mà bổ trợ cho nhau trong một vòng tuần hoàn.",
      "claim_refs": ["CLM-001", "CLM-002"]
    },
    {
      "type": "mechanism",
      "label": "Cơ chế",
      "content": "Wall Street đóng vai trò trung gian tài chính: thu tiết kiệm từ người có vốn dư, phân bổ đến doanh nghiệp và dự án cần vốn. Main Street dùng vốn đó để sản xuất, tuyển dụng và tạo ra sản lượng. Khi sản lượng và việc làm tăng, thu nhập người lao động tăng, một phần trở lại thành tiết kiệm — vòng tuần hoàn khép kín.",
      "claim_refs": ["CLM-003", "CLM-004", "CLM-006"]
    },
    {
      "type": "visual_plan",
      "visual_id": "ch01-circular-flow",
      "visual_type": "interactive-circular-diagram",
      "description": "Sơ đồ vòng tuần hoàn có 6 mắt xích: Tiết kiệm → Tài chính → Vốn → Doanh nghiệp → Việc làm → Thu nhập → Tiết kiệm. Người dùng chạm/hover vào từng mắt xích để xem vai trò cụ thể. Sticky-scroll pattern.",
      "data_needed": "illustrative-mechanism",
      "claim_refs": ["CLM-006"]
    },
    {
      "type": "counterpoint",
      "content": "Ranh giới giữa Main Street và Wall Street không phải lúc nào cũng rõ. Một ngân hàng cho vay doanh nghiệp nhỏ là Main Street hay Wall Street? Một công ty công nghệ có thị phần tài chính lớn thuộc bên nào? Khái niệm hai nửa hữu ích để tư duy, nhưng thực tế luôn có vùng giao thoa."
    }
  ],
  "takeaway": "Wall Street dẫn vốn. Main Street tạo ra của cải. Một nền kinh tế khỏe mạnh cần cả hai — nhưng không thể để công cụ thay thế nền móng.",
  "visual_plans": [
    {
      "id": "ch01-circular-flow",
      "type": "sticky-scroll",
      "priority": "primary",
      "is_centerpiece": true,
      "data_needed": "illustrative-mechanism",
      "description": "Vòng tuần hoàn vốn với 6 mắt xích tương tác."
    }
  ],
  "claim_refs": ["CLM-001", "CLM-002", "CLM-003", "CLM-004", "CLM-005", "CLM-006"],
  "chapter_pattern": "sticky-scroll",
  "reading_time_min": 3
}
```

- [ ] **Step 7: Cập nhật `content/index.json`**

Append vào mảng `chapters`:

```json
{
  "id": "ch01",
  "number": 1,
  "slug": "hai-nua-cua-nen-kinh-te",
  "title": "Hai nửa của nền kinh tế",
  "summary": "Main Street tạo ra của cải. Wall Street dẫn dòng vốn. Một nền kinh tế khỏe mạnh cần cả hai.",
  "chapter_pattern": "sticky-scroll",
  "visual_count": 1,
  "reading_time_min": 3,
  "file": "chapters/ch01.json"
}
```

- [ ] **Step 8: Cập nhật `content/progress.md`**

Đổi `- [ ] Chương 1 — Hai nửa của nền kinh tế` thành `- [x] Chương 1 — Hai nửa của nền kinh tế (6 claims, 5 verified, 1 author-view)`. Cập nhật tổng: `Tổng chương: 1/18`, `Tổng claims: 6`, `Tổng sources: 5`.

- [ ] **Step 9: Chạy validator**

```bash
node scripts/validate-content.mjs
```

Expected: 0 errors. Số chapters: 1, claims: 6, sources: 5.

- [ ] **Step 10: Commit**

```bash
git add content/
git commit -m "feat(msvs): ch01 — Hai nửa của nền kinh tế (6 claims, circular flow visual plan)"
```

---

## Task 4: Chương 2 — Khi lợi nhuận tài sản hấp dẫn hơn sản xuất (Pha 1)

**Files:**
- Create: `content/chapters/ch02.json`
- Modify: `content/claims.json`, `content/sources.json`, `content/glossary.json`, `content/index.json`, `content/progress.md`

**Nội dung nguồn (Chương 2):**

> Vấn đề xuất hiện khi lợi nhuận từ tài sản hấp dẫn hơn lợi nhuận từ sản xuất và lao động.
> * người có vốn ưu tiên mua đất, cổ phiếu, vàng;
> * doanh nghiệp thích đầu tư tài sản hơn mở rộng nhà máy;
> * người trẻ quan tâm lướt sóng hơn xây dựng nghề nghiệp;
> * câu chuyện xã hội xoay quanh giá tài sản...

- [ ] **Step 1: Trích claims** — Trích 5–7 claims, type: `CLM-007` (mechanism) — vốn ưu tiên tài sản khi lợi nhuận cao hơn; `CLM-008` (interpretation) — dấu hiệu xã hội "làm giàu nhanh"; v.v.

- [ ] **Step 2: Verify nguồn** — Mechanism về phân bổ vốn giữa tài sản và sản xuất: search `"capital allocation asset vs productive investment BIS"` → tìm BIS working papers. Interpretation thuần → `author-view`.

- [ ] **Step 3: Append claims vào `claims.json`** — Schema giống Task 3.

- [ ] **Step 4: Append sources vào `sources.json`** — URL verify bằng WebSearch/WebFetch.

- [ ] **Step 5: Append glossary terms** — "Phân bổ vốn", "Đầu cơ (Speculation)", "Hành vi đầu cơ", "Tài sản tài chính".

- [ ] **Step 6: Viết `content/chapters/ch02.json`** — Cấu trúc giống ch01, với:

  - `opening_question`: "Khi nào thì mua đất, mua cổ phiếu trở nên hấp dẫn hơn mở rộng nhà máy?"
  - Visual plan: `ch02-allocation-shift` — `sticky-toggle-diagram`, `data_needed: "illustrative-mechanism"`. Minh họa cơ chế phân bổ vốn (70/30 → 30/70). Ghi rõ "Mô phỏng cơ chế, không phải số liệu của nền kinh tế cụ thể."
  - `chapter_pattern`: `inline-flow` (chương thiên lập luận, không có visual trung tâm dính).
  - `takeaway`: "Khi lợi nhuận từ tài sản hấp dẫn hơn sản xuất, vốn và nhân lực rời dần nền kinh tế thực."

- [ ] **Step 7: Cập nhật `index.json`** — Append entry ch02.

- [ ] **Step 8: Cập nhật `progress.md`** — Mark ch02 done, cập nhật tổng.

- [ ] **Step 9: Validator** — `node scripts/validate-content.mjs`, 0 errors.

- [ ] **Step 10: Commit**

```bash
git add content/
git commit -m "feat(msvs): ch02 — Khi lợi nhuận tài sản hấp dẫn hơn sản xuất"
```

---

## Task 5: Chương 3 — Hai tốc độ lạm phát (Pha 1)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 3):**

> Wall Street thường tạo ra lạm phát giá tài sản nhanh hơn, vì tiền có thể lập tức chảy vào cổ phiếu, đất, vàng và đẩy giá lên.
> Main Street tạo ra lạm phát hàng hóa và dịch vụ chậm hơn, vì phải đi qua nhiều bước: vốn → đầu tư → tuyển dụng → tăng lương → tăng cầu → tăng giá.

- [ ] **Step 1: Trích claims** — `CLM-XXX` (mechanism) — lạm phát tài sản nhanh hơn lạm phát hàng hóa; `CLM-XXX` (mechanism) — đường truyền dẫn CPI vs asset prices; v.v.

- [ ] **Step 2: Verify** — BIS quarterly review có nhiều số liệu về asset prices vs CPI. Search `"asset price inflation vs CPI BIS"`. Numbers về CPI/FRED.

- [ ] **Step 3-10:** Append claims, sources, glossary ("Lạm phát giá tài sản", "Lạm phát tiêu dùng", "Tốc độ truyền dẫn"); viết `ch03.json` với visual `ch03-two-speed-race` (inline chart minh họa 2 đường chạy khác tốc độ); validator; commit.

```bash
git commit -m "feat(msvs): ch03 — Hai tốc độ lạm phát (asset vs consumer)"
```

---

## Task 6: Chương 11 — Một nền kinh tế mạnh cần sự cân bằng (Pha 1)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 11):**

> Main Street và Wall Street không đối lập tuyệt đối, mà phải bổ trợ cho nhau.
> Nếu quá nghiêng về Main Street, nền kinh tế có thể thiếu vốn, kém thanh khoản...
> Nếu quá nghiêng về Wall Street, dòng tiền dễ rời sản xuất để chạy vào đầu cơ...

- [ ] **Step 1: Trích claims** — 2 mechanism về "quá nghiêng Main Street" và "quá nghiêng Wall Street".

- [ ] **Step 2: Verify** — Lý thuyết tài chính phát triển (financial development) từ World Bank/IMF. Tỷ lệ tín dụng/GDP tối ưu.

- [ ] **Step 3-10:** Viết `ch11.json` với visual `ch11-balance-scale` — `interactive-slider` (chapter 11 là centerpiece), `data_needed: "illustrative-mechanism"`. Đây là 1 trong 3 visual trung tâm của toàn site (cùng ch06 cycle toggle và ch04 crowding-out network).

```bash
git commit -m "feat(msvs): ch11 — Một nền kinh tế mạnh cần sự cân bằng (balance scale centerpiece)"
```

---

## Task 7: Chương 15 — Một nền kinh tế muốn vươn mình phải coi trọng Main Street trước (Pha 1)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 15):**

> Main Street phải là nền móng, Wall Street là công cụ.
> Một nền kinh tế chỉ có thể vươn lên bền vững khi tạo ra được năng suất cao hơn, doanh nghiệp cạnh tranh hơn, công nghệ tốt hơn...

- [ ] **Step 1: Trích claims** — Main Street = nền móng (interpretation); năng suất quyết định tăng trưởng dài hạn (fact/verified — Solow growth accounting).

- [ ] **Step 2: Verify** — World Bank "productivity growth" reports; OECD productivity database.

- [ ] **Step 3-10:** Viết `ch15.json` với visual `ch15-pyramid` — `interactive-pyramid-diagram` (đáy: giáo dục/hạ tầng/năng lượng/pháp quyền; giữa: doanh nghiệp/công nghệ/kỹ năng; đỉnh: thị trường vốn).

```bash
git commit -m "feat(msvs): ch15 — Main Street là nền móng, Wall Street là công cụ (pyramid visual)"
```

---

## Task 8: Chương 4 — Hiệu ứng lấn át (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 4):**

> Hiệu ứng lấn át xảy ra khi tài sản tài chính và bất động sản đem lại lợi nhuận kỳ vọng cao hơn sản xuất kinh doanh.
> 5 kênh: tiết kiệm, tín dụng, đất đai/mặt bằng, phân bổ vốn doanh nghiệp, nhân lực.

- [ ] **Step 1: Trích claims** — 5 mechanism về 5 kênh crowding-out.

- [ ] **Step 2: Verify** — "Crowding out" trong kinh tế vĩ mô (Fed/IMF). 5 kênh cụ thể là diễn giải tác giả → đa số `author-view`, nhưng cơ chế tổng "crowding out" là `verified`.

- [ ] **Step 3-10:** Viết `ch04.json` với visual `ch04-crowding-out-network` — `network-diagram` (centerpiece), hover vào node để highlight đường truyền dẫn. `data_needed: "illustrative-mechanism"`.

```bash
git commit -m "feat(msvs): ch04 — Hiệu ứng lấn át (5 kênh crowding-out network)"
```

---

## Task 9: Chương 5 — Tài sản, quyền sở hữu và bất bình đẳng (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 5):**

> Người sở hữu tài sản hưởng lợi khi giá tài sản tăng...
> Người dựa chủ yếu vào tiền lương có thể bị bỏ lại...
> Không khẳng định Wall Street là nguyên nhân duy nhất của bất bình đẳng.

- [ ] **Step 1: Trích claims** — Mechanism về wealth effect; fact về phân phối tài sản (Piketty, Fed SCF); interpretation về tâm lý "làm giàu nhanh".

- [ ] **Step 2: Verify** — Fed Survey of Consumer Finances (SCF) có dữ liệu phân phối tài sản. World Inequality Database. Piketty là `authoritative-book`.

- [ ] **Step 3-10:** Visual `ch05-who-owns-upside` — `stacked-bar-chart` (thu nhập lao động vs vốn vs nhà ở vs tài sản tài chính, theo percentile). `data_needed: "real-data"` (Fed SCF).

```bash
git commit -m "feat(msvs): ch05 — Bất bình đẳng tài sản (Fed SCF data)"
```

---

## Task 10: Chương 6 — Chu kỳ lành mạnh và chu kỳ bong bóng (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 6):**

> Chu kỳ lành mạnh: Sản xuất tăng → lợi nhuận tăng → tài sản tăng → vốn quay lại sản xuất.
> Chu kỳ bong bóng: Tài sản tăng → vay thêm → đầu cơ → bong bóng vỡ → suy thoái.

- [ ] **Step 1: Trích claims** — 2 mechanism về 2 chu kỳ; Minsky moment (fact về lý thuyết).

- [ ] **Step 2: Verify** — Hyman Minsky "Financial Instability Hypothesis" (academic). Kindleberger "Manias, Panics, and Crashes" (authoritative-book).

- [ ] **Step 3-10:** Visual `ch06-cycle-toggle` — `sticky-toggle-diagram` (centerpiece, 1 trong 3 visual trung tâm toàn site). Toggle Healthy/Bubble, animate vòng lặp.

```bash
git commit -m "feat(msvs): ch06 — Healthy vs Bubble cycle toggle (centerpiece)"
```

---

## Task 11: Chương 7 — Khi Wall Street thịnh vượng nhưng Main Street suy yếu (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 7):**

> Vốn tiếp tục chảy vào tài sản thay vì sản xuất...
> Người giàu hơn nhờ tài sản, người lao động chịu lương thấp và chi phí sống cao...

- [ ] **Step 1: Trích claims** — Mechanism về phân kỳ thị trường vs hộ gia đình.

- [ ] **Step 2: Verify** — FRED dữ liệu S&P 500 vs real wage (CES series); BLS real earnings; Case-Shiller vs median household income.

- [ ] **Step 3-10:** Visual `ch07-split-screen` — `split-screen` (trái: market headlines; phải: household reality). `data_needed: "real-data"` (FRED).

```bash
git commit -m "feat(msvs): ch07 — Split-screen market vs household divergence"
```

---

## Task 12: Chương 8 — Từ Wall Street trở lại Main Street (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 8):**

> Quá trình này thường được gọi là tái cân bằng, phi tài chính hóa, giảm đòn bẩy...
> Nó gần như luôn cần sự đánh đổi...

- [ ] **Step 1: Trích claims** — Khái niệm "tái cân bằng", "phi tài chính hóa", "giảm đòn bẩy" (fact/definition); mechanism về chi phí chuyển đổi.

- [ ] **Step 2: Verify** — IMF Working Papers về deleveraging; BIS về financial cycle.

- [ ] **Step 3-10:** Visual `ch08-rebalancing-machine` — `interactive-lever-machine` (4 cần gạt: tín dụng đầu cơ/đầu tư sản xuất/đòn bẩy/năng suất). Ghi rõ "công cụ tư duy, không phải mô hình dự báo".

```bash
git commit -m "feat(msvs): ch08 — Rebalancing machine (4-lever thinking tool)"
```

---

## Task 13: Chương 9 — Chu kỳ hay lựa chọn chính sách? (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 9):**

> Mất cân đối có thể buộc nền kinh tế phải tái cân bằng...
> Nhưng thời điểm, tốc độ, phân bổ chi phí vẫn chịu ảnh hưởng chính sách...

- [ ] **Step 1: Trích claims** — Interpretation về vai trò chính sách; mechanism về policy trade-offs.

- [ ] **Step 2: Verify** — IMF policy papers về macroprudential; Fed speeches về soft landing.

- [ ] **Step 3-10:** Visual `ch09-spectrum` — `horizontal-spectrum` (Market-forced ←→ Policy-managed). Đơn giản.

```bash
git commit -m "feat(msvs): ch09 — Chu kỳ hay lựa chọn chính sách? (spectrum)"
```

---

## Task 14: Chương 10 — Vì sao đường về Main Street thường đau hơn? (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 10):**

> Khi nền kinh tế chuyển từ Main Street sang Wall Street, quá trình thường khá dễ chịu...
> Ngược lại, khi phải chuyển từ Wall Street trở lại Main Street, nền kinh tế thường phải trải qua: giá tài sản giảm, đòn bẩy thu hẹp, phá sản, thất nghiệp...

- [ ] **Step 1: Trích claims** — Mechanism về asymmetric transition pain.

- [ ] **Step 2: Verify** — BIS Annual Report về financial cycle asymmetry; Reinhart & Rogoff "This Time Is Different" (authoritative-book) về aftermath of crises.

- [ ] **Step 3-10:** Visual `ch10-directional-contrast` — `side-by-side-flow-diagram` (Main Street → Wall Street: dễ chịu; Wall Street → Main Street: đau đớn).

```bash
git commit -m "feat(msvs): ch10 — Directional contrast — ascent vs painful rebalancing"
```

---

## Task 15: Chương 16 — Ai chịu cú sốc lớn nhất? (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 16):**

> Nhà đầu tư sử dụng đòn bẩy; doanh nghiệp sống nhờ giá cổ phiếu; ngân hàng đầu cơ...
> Các cú sốc: giá tài sản giảm, thanh khoản suy yếu, định giá điều chỉnh...

- [ ] **Step 1: Trích claims** — 7 loại cú sốc: valuation, liquidity, collateral, refinancing, earnings, employment, confidence. Mỗi loại 1 mechanism.

- [ ] **Step 2: Verify** — BIS về systemic risk transmission; IMF GFSR.

- [ ] **Step 3-10:** Visual `ch16-risk-map` — `interactive-risk-map` (click vào từng cú sốc → hiển thị cơ chế truyền dẫn dạng flow diagram).

```bash
git commit -m "feat(msvs): ch16 — Shock transmission map (7 shock types)"
```

---

## Task 16: Chương 17 — Ai hưởng lợi khi Main Street phục hồi? (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 17):**

> Doanh nghiệp sản xuất và xuất khẩu; ngành công nghiệp, hạ tầng, năng lượng; doanh nghiệp công nghệ phục vụ năng suất; người lao động có kỹ năng...

- [ ] **Step 1: Trích claims** — Fact về beneficiary sectors (manufacturing, exports, infrastructure, energy, tech, skilled labor).

- [ ] **Step 2: Verify** — BEA industry GDP; BLS employment by sector; OECD STAN database.

- [ ] **Step 3-10:** Visual `ch17-beneficiary-matrix` — `who-wins-loses-matrix` (4 cấp: economic/revenue/profit/stock — phân biệt rõ không đồng thời).

```bash
git commit -m "feat(msvs): ch17 — Who wins/loses matrix (4 benefit levels)"
```

---

## Task 17: Chương 18 — Mỗi cá nhân cần chuẩn bị gì? (Pha 2)

**Files:** giống Task 4.

**Nội dung nguồn (Chương 18):**

> Bảo vệ bảng cân đối cá nhân và nâng giá trị lao động.
> 4 trụ: bảng cân đối, thanh khoản, chất lượng tài sản, năng lực tạo thu nhập.

- [ ] **Step 1: Trích claims** — 4 trụ Personal Resilience Framework (mechanism).

- [ ] **Step 2: Verify** — Interpretation thuần → phần lớn `author-view`. Có thể cite BIS household finance papers.

- [ ] **Step 3-10:** Visual `ch18-checklist` — `interactive-checklist` (4 trụ × nhiều item, không thu thập data). Câu cuối toàn website: "Người chuẩn bị tốt nhất không phải người đoán đúng thời điểm chuyển pha, mà là người không bị phá vỡ khi giá tài sản giảm..."

```bash
git commit -m "feat(msvs): ch18 — Personal resilience checklist (4 pillars)"
```

---

## Task 18: Chương 12 — Trung Quốc: chuyển hướng từ khoảng năm 2016 (Pha 3, nặng nhất)

**Files:** giống Task 4 (nhưng nhiều hơn: ~25–40 tool-call vì verify nặng).

**Nội dung nguồn (Chương 12):**

> 2015: cú sốc thị trường chứng khoán.
> 2016: "thoát hư hướng thực" — 脱虚向实.
> 2017–2020: giảm đòn bẩy, kiểm soát shadow banking.
> 2020–2023: bất động sản (ba lằn ranh đỏ), internet platform.
> 2023–nay: công nghệ cao, sản xuất tiên tiến, "new quality productive forces".

- [ ] **Step 1: Trích claims** — 12–15 claims với nhiều mốc lịch sử định lượng.

- [ ] **Step 2: Verify (nặng)** — Theo spec Section 5.3:
  - Shanghai Composite 5,166 (6/2015) → ~3,000 (8/2015): search `"Shanghai Composite 2015 crash CSRC"`
  - "脱虚向实" 2016/2017: search `"China financial work conference 2017 Xinhua"` → PBOC/Xinhua official
  - Shadow banking assets: BIS China data
  - Ba lằn ranh đỏ 8/2020: PBOC thông tư; Evergrande default 12/2021: Reuters, IMF Article IV
  - Alibaba fining 4/2021 $2.8B: SAMR
  - EV output, battery share: CAAM, IEA
  - "new quality productive forces" 2023: Xinhua, MIIT

  Mỗi mốc verify 1–3 WebSearch + WebFetch. Nếu không tìm được URL chính xác → claim xuống `author-view` với note rõ.

- [ ] **Step 3-10:** Visual `ch12-china-timeline` — `interactive-timeline` (2015 → 2023+), dòng vốn dịch chuyển từ BĐS/internet sang bán dẫn/EV/pin. `data_needed: "real-data"` (BIS, NBS).

  Phản biện bắt buộc: 1 claim `status: "disputed"` về chi phí chuyển đổi (tăng trưởng chậm vs lợi ích dài hạn), 2 nguồn đại diện.

```bash
git commit -m "feat(msvs): ch12 — Trung Quốc chuyển hướng từ 2016 (timeline, 15 claims, disputed counterpoint)"
```

---

## Task 19: Chương 13 — Nhật Bản: cuộc tái cân bằng bị ép buộc (Pha 3)

**Files:** giống Task 18.

**Nội dung nguồn (Chương 13):**

> Thập niên 1980: tín dụng và giá tài sản tăng...
> 1989–1991: đảo chiều thị trường...
> Thập niên 1990: nợ xấu, balance sheet recession...
> "Tái cân bằng quá muộn và xử lý nợ quá chậm có thể biến một cuộc chuyển đổi cần thiết thành nhiều năm trì trệ."

- [ ] **Step 1: Trích claims** — 12–15 claims với mốc lịch sử Nhật.

- [ ] **Step 2: Verify (nặng)** — Theo spec Section 5.2:
  - Nikkei 225 peak 38,915 (12/1989): BoJ, Japan Exchange Group
  - Sụp đổ 1990–91: BoJ
  - NPL ratio peak ~8% (2001–02): BoJ, FSA Japan
  - Balance sheet recession: Richard Koo (Nomura), "The Holy Grail of Macroeconomics" (authoritative-book)
  - Giảm phát CPI: FRED JPNCPIALLMINMEI
  - Real wage index: OECD
  - GDP ~1%/năm: Cabinet Office Japan

- [ ] **Step 3-10:** Visual `ch13-japan-balance-sheet` — `flow-diagram` (Balance Sheet Recession cascade). Timeline 1980 → nay.

  Phản biện: balance sheet recession (Koo) vs monetary policy failure vs demographics.

```bash
git commit -m "feat(msvs): ch13 — Nhật Bản balance sheet recession (Koo, BoJ data)"
```

---

## Task 20: Chương 14 — Mỹ: tái cấu trúc nhưng chưa rời bỏ tài chính hóa (Pha 3)

**Files:** giống Task 18.

**Nội dung nguồn (Chương 14):**

> Trước 2008: tín dụng nhà ở và chứng khoán hóa...
> 2008–2009: khủng hoảng tài chính...
> Sau khủng hoảng: giảm đòn bẩy hộ gia đình, cải cách ngân hàng, QE, phục hồi giá tài sản...
> "Mỹ không thay Wall Street bằng Main Street, mà cố gắng củng cố hệ thống tài chính rồi dùng nó tiếp tục tài trợ cho nền kinh tế."

- [ ] **Step 1: Trích claims** — 12–15 claims với mốc Mỹ.

- [ ] **Step 2: Verify (nặng)** — Theo spec Section 5.1:
  - Nợ hộ gia đình/GDP 2007 ~100% → 2020 ~75%: FRED HDTGPDUSQ
  - S&P 500 rơi 57% (10/2007–3/2009): FRED SP500
  - Unemployment peak 10% (10/2009): BLS LNS14000000
  - Dodd-Frank 2010: Congress.gov, Fed
  - Case-Shiller index: FRED CSUSHPINSA
  - CHIPS Act 2022, IRA 2022: Congress.gov

- [ ] **Step 3-10:** Visual `ch14-us-dual-recovery` — `dual-line-chart` (phục hồi thị trường vs phục hồi hộ gia đình). Timeline 2000 → nay.

  Phản biện: Mỹ không thực sự rời bỏ tài chính hóa — Fed balance sheet lớn, giá tài sản phục hồi trước.

```bash
git commit -m "feat(msvs): ch14 — Mỹ dual recovery (FRED data, disputed financialization)"
```

---

## Task 21: insights.md — 8 special insights (prompt Section VIII)

**Files:**
- Create: `content/insights.md`

- [ ] **Step 1: Viết `content/insights.md`**

8 insight theo prompt Section VIII (đã list trong spec). Mỗi insight:

```markdown
## Insight 1 — Tài chính hóa không chỉ là quy mô ngành tài chính

**Liên kết chương:** ch02, ch04

Tài chính hóa còn thể hiện qua: tỷ trọng lợi nhuận đến từ tài sản, hành vi mua lại cổ phiếu, cấu trúc thưởng quản lý, sự phụ thuộc vào định giá, ưu tiên tài sản thế chấp, mức độ nợ, vai trò của giá nhà đối với tiêu dùng, quá trình biến các dòng tiền tương lai thành tài sản giao dịch.

**Claims liên quan:** CLM-XXX, CLM-YYY
```

8 insights:
1. Tài chính hóa không chỉ là quy mô ngành tài chính (ch02, ch04)
2. Giá tài sản vừa là kết quả, vừa là nguyên nhân (ch06, ch07)
3. Không phải mọi đầu tư vào tài sản đều là đầu cơ (ch08, ch16)
4. Phi tài chính hóa không đồng nghĩa thị trường giảm mãi (ch08, ch14)
5. Tái cân bằng là cuộc chiến phân bổ tổn thất (ch10, ch16)
6. Độ đau chuyển pha phụ thuộc bảng cân đối (ch10, ch13)
7. Main Street hiện đại không chỉ là nhà máy (ch01, ch15, ch17)
8. Wall Street có thể tài trợ quay về Main Street (ch08, ch15)

- [ ] **Step 2: Commit**

```bash
git add content/insights.md
git commit -m "feat(msvs): 8 special insights (cross-chapter themes)"
```

---

## Task 22: counterpoints.md — 10 phản biện (prompt Section XIX)

**Files:**
- Create: `content/counterpoints.md`

- [ ] **Step 1: Viết `content/counterpoints.md`**

10 phản biện theo prompt Section XIX. Phần mở đầu: "Những điều mô hình Main Street–Wall Street không giải thích hết". Mỗi phản biện ~150 từ + 2 nguồn.

```markdown
# Những điều mô hình Main Street–Wall Street không giải thích hết

Phần phản biện này không làm suy yếu câu chuyện chính, mà giúp câu chuyện đáng tin hơn.

## 1. Tài sản tăng không nhất thiết đồng nghĩa bong bóng

Giá tài sản có thể tăng hợp lý khi năng suất tăng, lợi nhuận tăng, hoặc môi trường lãi suất thấp kéo dài. Phân biệt "tăng" và "tăng quá xa nền tảng" cần nhiều dữ kiện hơn...

**Nguồn:** BIS Quarterly Review; Robert Shiller "Irrational Exuberance" (authoritative-book).
```

10 phản biện (đã list trong spec Section 7.2).

- [ ] **Step 2: Commit**

```bash
git add content/counterpoints.md
git commit -m "feat(msvs): 10 counterpoints — what the model doesn't explain"
```

---

## Task 23: RESEARCH-REPORT.md (báo cáo cuối Giai đoạn R)

**Files:**
- Create: `RESEARCH-REPORT.md` (root repo)

- [ ] **Step 1: Đếm claims theo status**

```bash
node -e "const c=JSON.parse(require('fs').readFileSync('content/claims.json')); const s={}; for(const x of c){s[x.status]=(s[x.status]||0)+1} console.log(s)"
```

- [ ] **Step 2: Đếm sources theo publisher_type**

```bash
node -e "const s=JSON.parse(require('fs').readFileSync('content/sources.json')); const t={}; for(const x of s){t[x.publisher_type]=(t[x.publisher_type]||0)+1} console.log(t)"
```

- [ ] **Step 3: Viết `RESEARCH-REPORT.md`**

```markdown
# Research Report — Giai đoạn R

**Ngày hoàn thành:** 2026-07-XX
**Spec:** docs/superpowers/specs/2026-07-18-msvs-content-research-design.md
**Plan:** docs/superpowers/plans/2026-07-18-msvs-content-research.md

## Tóm tắt sản phẩm

- Tên: Main Street vs Wall Street (interactive editorial website)
- Định dạng: nội dung nghiên cứu cho website scrollytelling (Giai đoạn R)
- Số chương: 18
- Số interaction/visual plan: <số>
- Số claims: <số>
- Số nguồn: <số>

## Phân bổ claims theo status

- verified: <số>
- qualified: <số>
- disputed: <số>
- author-view: <số>

## Phân bổ sources theo publisher_type

- official: <số>
- international: <số>
- academic: <số>
- media-quality: <số>
- authoritative-book: <số>

## Top 10 nguồn được dùng nhiều nhất

<table>

## 8 special insights phát hiện

(List từ content/insights.md)

## 10 phản biện đã trình bày

(List từ content/counterpoints.md)

## Known limitations

(6 điều từ spec Section 10)

## Khuyến nghị cho Giai đoạn A

- Build Hero + chương 1–6 dựa trên content/ch01.json → ch06.json.
- claims.json + sources.json render panel nguồn/nhãn.
- glossary.json render glossary drawer.
- methodology.md render trang /methodology.
- insights.md + counterpoints.md render section riêng.
```

- [ ] **Step 4: Validator cuối**

```bash
node scripts/validate-content.mjs
```

Expected: 0 errors, 18 chapters, 100–150 claims, 50–80 sources, glossary ≥30 terms.

- [ ] **Step 5: Kiểm tra tiêu chuẩn nghiệm thu 12 điều**

Verify mỗi điều trong spec Section 8. Nếu thiếu → quay lại task tương ứng bổ sung.

- [ ] **Step 6: Commit**

```bash
git add RESEARCH-REPORT.md content/progress.md
git commit -m "feat(msvs): RESEARCH-REPORT.md — Giai đoạn R complete (18 chapters, N claims verified)"
```

---

## Self-Review Notes

### Spec coverage

- Spec Section 1 (bối cảnh/chiến lược) — không yêu cầu task riêng, context cho plan. ✓
- Spec Section 2 (mục tiêu/phạm vi) — Tasks 1-23 cover toàn bộ. ✓
- Spec Section 3 (kiến trúc nội dung schema) — Task 1 (validator) + Task 3 (template chương) + áp dụng cho 4-20. ✓
- Spec Section 4 (claims/sources schema) — Task 1 (validator) + Task 3 (template). ✓
- Spec Section 5 (verify case study) — Tasks 18, 19, 20. ✓
- Spec Section 6 (workflow 4 bước) — Template trong Task 3, áp dụng 4-20. ✓
- Spec Section 7 (insights + counterpoints) — Tasks 21, 22. ✓
- Spec Section 8 (nghiệm thu 12 điều) — Task 23 Step 5. ✓
- Spec Section 9 (sản phẩm bàn giao) — Task 23. ✓
- Spec Section 10 (known limitations) — Task 23. ✓
- Spec Section 11 (chuyển giao cho A) — Task 23. ✓

### Placeholder scan

- Task 3 có template đầy đủ với code mẫu cụ thể. ✓
- Tasks 4-20 tham chiếu Task 3 như template, lặp cùng 10 bước. ✓
- Task 18-20 có thêm detail về verify case study. ✓
- Không có TBD/TODO/implement-later. ✓

### Type consistency

- `claim.type`: `fact | mechanism | interpretation` — consistent across validator, schema, tasks. ✓
- `claim.status`: `verified | qualified | disputed | author-view` — consistent. ✓
- `chapter.chapter_pattern`: `sticky-scroll | inline-flow | hybrid` — consistent. ✓
- `visual_plan.data_needed`: `illustrative-mechanism | real-data` — consistent. ✓

### Phân bổ chapter_pattern (đã chốt Hybrid)

- sticky-scroll: ch01, ch06, ch11, ch12, ch13, ch14 (6 chương, visual trung tâm)
- inline-flow: ch02, ch03, ch07, ch09, ch10, ch15, ch16, ch17, ch18 (9 chương, thiên lập luận)
- hybrid: ch04, ch05, ch08 (3 chương)

Tổng: 6 + 9 + 3 = 18. ✓
