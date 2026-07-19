---
name: vn-research-dashboard
description: Xây dựng Financial HTML/equity research dashboard cho cổ phiếu Việt Nam từ dữ liệu đã phân tích. Hỗ trợ dashboard tài chính, narrative publication, claim graph, counterpoint, centerpiece, Reader/Research mode, progressive disclosure, Chart.js, responsive, print/PDF và QA.
---

# VN Research Dashboard — Financial HTML Narrative

Skill tạo báo cáo Financial HTML dạng single-page, deploy được, có hai lớp song song:

- **Analytical layer:** KPI, bảng, Chart.js, định giá, technical, news, scenario/sensitivity.
- **Narrative layer:** chapter question, claim graph, counterpoint, narrative centerpiece, Reader/Research mode và progressive disclosure.

Mục tiêu: người đọc phổ thông hiểu được mạch lập luận; người đọc chuyên môn kiểm tra được claim, nguồn, công thức và uncertainty trên cùng một HTML.

## Điều kiện tiên quyết

Ưu tiên dùng output từ:

- `vn-financial-data-collector` → dữ liệu BCTC/giá;
- `vn-fundamental-analysis` → ratios, DuPont, CAGR;
- `vn-valuation-engine` → định giá và assumptions;
- `vn-technical-analysis` → indicators/patterns khi có dữ liệu thật;
- `vn-news-digest` → sự kiện và sentiment, optional.

Không bịa dữ liệu. Không mô phỏng giá/technical nếu không fetch được. Mọi `DERIVED` phải có formula/input; mọi `SCENARIO` phải được phân biệt với actual.

# Output modes

- `dashboard`: dashboard cũ, tương thích ngược.
- `financial-html`: dashboard + narrative layer; mặc định cho báo cáo BCTC/chuyên sâu mới.
- `compact`: ít section, narrative tối giản, không bắt buộc sticky-scroll.
- `profile`: hồ sơ giá-khối lượng trung tính, phi tư vấn.

# Workflow

## Bước 0 — Design system

Template dùng `_viz-shared/`:

- `tokens.css`: theme Fintech/Bloomberg/Corporate;
- `components.css`: component dashboard;
- `viz.js`: chart registry, candlestick, navigation;
- `inject.py`: inline shared CSS/JS vào template.

Không hard-code một design system thứ hai cho narrative layer. Component mới phải dùng CSS variables hiện có.

## Bước 1 — Khóa dữ liệu và narrative package

Tạo bộ dữ liệu nguồn duy nhất:

```text
project/
├── financial_data.json
├── evidence_ledger.csv hoặc claims.json
├── chart_manifest.csv
├── uncertainty_register.csv
├── chapter_schema.json
├── claim_graph.json
├── counterpoints.json
├── narrative_manifest.json
└── index.html
```

Có thể khởi tạo bằng:

```bash
python scripts/init_financial_narrative.py --ticker [TICKER] --out ./project
```

### Chapter schema

Mỗi chương/section trọng yếu phải có:

- `chapter_id`, `title`, `guiding_question`;
- `provisional_thesis`;
- `claim_ids`;
- `centerpiece_visual_id` nếu có;
- `counterpoint_id` nếu có;
- `mini_conclusion`, `risk_of_interpretation`, `takeaway`.

Mạch mặc định:

> Câu hỏi → kết luận sơ bộ → KPI/evidence → cơ chế/so sánh → phản biện → kết luận chương → chỉ tiêu cần theo dõi.

### Claim taxonomy

Giữ hai chiều phân loại:

- `evidence_class`: `FACT`, `DERIVED`, `INFERENCE`, `SCENARIO`, `RECOMMENDATION`;
- `epistemic_status`: `VERIFIED`, `QUALIFIED`, `DISPUTED`, `AUTHOR_VIEW`, `INSUFFICIENT_EVIDENCE`.

### Claim graph

Relation hợp lệ:

```text
SUPPORTS
CONTRADICTS
QUALIFIES
EXPLAINS
DERIVED_FROM
SYNTHESIZES
DEPENDS_ON
INVALIDATES_IF
REFERENCES
SUPERSEDES
```

Graph phải là evidence graph, không phải sơ đồ trang trí. Mỗi edge có `from_claim_id`, `relation`, `to_claim_id`, và `note` ngắn khi cần.

### Counterpoint object

Counterpoint phải có:

- câu hỏi tranh luận;
- `main_view` + supporting claim IDs;
- `opposing_view` + supporting claim IDs;
- `synthesis`;
- `decision_metrics`: dữ liệu nào sẽ phân định hai quan điểm.

Không dùng “rủi ro chung chung” thay cho counterpoint.

### Narrative manifest

Mỗi centerpiece ghi:

- `visual_id`, `chapter_id`, `type`, `layout`;
- `data_mode`: `verified-data`, `derived-data`, `scenario-data`, `illustrative-mechanism`;
- `claim_ids`, `source_ids`;
- `mobile_fallback`, `print_fallback`, `accessibility_note`;
- `steps` hoặc `milestones`.

`illustrative-mechanism` phải có disclosure rằng đây là sơ đồ cơ chế, không phải dữ liệu quan sát.

## Bước 2 — Chọn cấu trúc báo cáo

Financial HTML đầy đủ nên gồm:

1. Hero + KPI
2. Executive Summary
3. Scope/Data Quality
4. Kết quả kinh doanh
5. Chất lượng lợi nhuận/dòng tiền
6. Bảng cân đối/chất lượng tài sản
7. Định giá + scenario/sensitivity
8. Counterpoints & risks
9. Catalyst/monitoring dashboard
10. Sources/Methodology

Với ngân hàng, thay bằng NIM/CASA, tín dụng, NPL/nợ nhóm 2, dự phòng, CAR, ROE và P/B. Với chứng khoán, ưu tiên thanh khoản, môi giới, margin, tự doanh, vốn và ROE.

Mỗi chương có một guiding question. Không để section chỉ là tập hợp chart không có câu hỏi phân tích.

## Bước 3 — Copy template và gắn narrative components

Copy:

```text
assets/dashboard_template.html
```

Sau đó tích hợp snippet:

```text
assets/narrative_components.html
```

Snippet cung cấp:

- View mode switcher;
- chapter header;
- claim/evidence cards;
- counterpoint panel;
- claim graph renderer;
- sticky centerpiece/stepper;
- progressive disclosure bằng `<details>`;
- mobile/print/reduced-motion fallback.

Không tạo hai file Reader và Research riêng. Hai mode dùng cùng DOM và dataset:

```html
<html data-view="reader">
```

## Bước 4 — Data binding

Dùng `str.replace` hoặc data object rõ ràng; không dùng f-string trực tiếp với template nhiều brace.

Mọi số xuất hiện trong KPI, text, chart và research disclosure phải lấy từ cùng dataset đã khóa.

### Reader mode

- ưu tiên KPI, chart, insight và takeaway;
- ẩn claim ID, công thức chi tiết, graph edges và uncertainty sâu;
- nguồn hiển thị rút gọn.

### Research mode

- hiện claim ID, evidence class, epistemic status;
- nguồn, kỳ, đơn vị, formula/input;
- uncertainty/caveat;
- claim graph và counterpoint evidence.

### Progressive disclosure

Ba cấp:

1. **Primary:** KPI → chart → insight → takeaway;
2. **Details:** cách tính, nguồn, kỳ, giới hạn;
3. **Research:** claim graph, formula, input claims, uncertainty, contradictory evidence.

Dùng `<details>` để nội dung vẫn accessible, printable và hoạt động khi JavaScript lỗi.

## Bước 5 — Narrative centerpiece

Mỗi báo cáo đầy đủ dùng 1–3 centerpiece, chỉ khi có giá trị kể chuyện:

- `earnings-bridge`;
- `cash-conversion-cascade`;
- `balance-sheet-pressure-map`;
- `credit-quality-cascade`;
- `funding-to-nim`;
- `capital-constraint-path`;
- `policy-timeline`;
- `cause-effect-network`;
- `scenario-path`.

Không dùng sticky-scroll thay cho chart thông thường. Nếu không có chuỗi step hợp lý, dùng card/timeline tĩnh.

## Bước 6 — QA

### Kiểm tra dữ liệu/schema

```bash
python scripts/qa_financial_narrative.py ./project
```

Bắt lỗi:

- ID trùng hoặc tham chiếu không tồn tại;
- `DERIVED` thiếu formula/input;
- `VERIFIED` thiếu source;
- edge relation không hợp lệ;
- counterpoint thiếu một phía/evidence;
- centerpiece thiếu claim/source/fallback;
- `illustrative-mechanism` thiếu disclosure.

### Kiểm tra HTML/interaction

```bash
NODE_PATH=/tmp/qa-runner/node_modules node scripts/qa_dashboard.js \
  --url=file:///path/to/index.html \
  --output=/tmp/qa-[TICKER] \
  --narrative
```

`--narrative` kiểm tra thêm:

- Reader/Research toggle hoạt động;
- progressive disclosure tồn tại;
- chapter question và takeaway;
- counterpoint + claim graph;
- centerpiece step interaction;
- mobile 390 px không scroll ngang;
- print/reduced-motion fallback;
- không có `NaN`, `Infinity`, placeholder hoặc JS error.

Dashboard cũ không dùng narrative vẫn chạy QA không có flag để bảo toàn tương thích.

# Quy tắc thiết kế

- Dashboard vẫn ưu tiên tốc độ đọc KPI và so sánh số chính xác.
- Narrative layer không được làm chart/table khó tra cứu.
- Component density 2–4/chương; centerpiece tối đa 1/chương.
- Mobile: sticky chuyển thành stacked step cards.
- Print: hiện toàn bộ research details và tất cả step; không dùng position sticky.
- Có `prefers-reduced-motion`.
- Không phụ thuộc JavaScript để đọc được nội dung cốt lõi.
- Không để research mode gây tràn ngang.

# Hard fail

Không publish Financial HTML narrative nếu:

- text/KPI/chart dùng dữ liệu khác nhau;
- claim trọng yếu không có provenance;
- `DERIVED` thiếu formula/input;
- `SCENARIO` bị trình bày như actual/forecast chính thức;
- counterpoint chỉ có một phía;
- conclusion không có supporting claim;
- centerpiece không có mobile/print fallback;
- graph có orphan/unknown claim;
- reader/research toggle làm mất nội dung hoặc sai số liệu;
- có placeholder, JS error, blank chart, overlap hoặc scroll ngang;
- lộ prompt/hướng dẫn nội bộ.

# Tài nguyên

- `assets/dashboard_template.html`
- `assets/narrative_components.html`
- `references/data_binding.md`
- `references/style_variants.md`
- `references/chart_recipes.md`
- `references/cover_image.md`
- `references/narrative_layer.md`
- `schemas/financial_narrative.schema.json`
- `scripts/init_financial_narrative.py`
- `scripts/qa_financial_narrative.py`
- `scripts/qa_dashboard.js`
