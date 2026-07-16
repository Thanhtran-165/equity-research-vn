# LESSONS LEARNED — vn-rates-weekly W26/2026

> Tổng hợp các lỗi gặp phải trong quá trình xây dựng skill, rút kinh nghiệm để cập nhật SKILL.md + QA pipeline.

---

## NHÓM 1: HTML STRUCTURE ERRORS (nghiêm trọng nhất)

### Lỗi 1.1: Thiếu `</section>` — layout vỡ toàn bộ
- **Triệu chứng**: Click tab nào cũng trống, `getBoundingClientRect` = 0×0 cho mọi section
- **Nguyên nhân**: Khi di chuyển block content (slope/convexity), vô tình xóa `</section>` đóng TPCP
- **Phát hiện**: Đo `getBoundingClientRect` cho từng section → tất cả 0×0 → kiểm tra `<section>` count vs `</section>` count → diff = 1
- **Fix**: Thêm `</section>` thiếu
- **Tần suất**: 2 lần (Section 4 render + slope/convexity move)
- **Cách phòng**: 
  - **QA RULE MỚI**: sau mỗi edit HTML, kiểm tra `<div>` open/close balance + `<section>` open/close balance
  - Script: `python3 -c "import re; html=open('report.html').read(); print(f'div diff={html.count(\"<div\")-html.count(\"</div>\")}, section diff={html.count(\"<section\")-html.count(\"</section>\")}')"`

### Lỗi 1.2: Content bị leak sang section sai
- **Triệu chứng**: Slope/convexity chart hiện trong tab "Trái phiếu DN" thay vì "Trái phiếu CP"
- **Nguyên nhân**: Insert content **giữa** `</section>` (đóng section A) và `<section>` (mở section B) — nằm "lơ lửng", browser parse vào section gần nhất
- **Fix**: Insert content **bên trong** section, trước `</section>` của section đó
- **Tần suất**: 3 lần (cross-week inject, slope move, USD chart inject)
- **Cách phòng**:
  - **QA RULE MỚI**: sau mỗi insert, verify `getBoundingClientRect` của section đích > 0
  - Verify chart/element nằm đúng section bằng: `document.querySelector('#tpcp').contains(document.getElementById('chartSlope'))`

### Lỗi 1.3: Chart data inject ghi đè file
- **Triệu chứng**: Thay đổi không lưu — re-render ghi đè toàn bộ inject trước đó
- **Nguyên nhân**: `render_polished.py` re-render từ template gốc, xóa hết modifications
- **Fix**: Tất cả chart inject phải nằm TRONG render script, không modify HTML sau render
- **Tần suất**: 2 lần
- **Cách phòng**:
  - **ARCHITECTURE RULE**: render script phải tạo hoàn chỉnh output, không post-process

---

## NHÓM 2: PARSER BUGS

### Lỗi 2.1: Tenor substring match ("5 năm" match "15 năm")
- **Triệu chứng**: HNX yield curve trả duplicate 5Y, thiếu 15Y
- **Nguyên nhân**: `if "5 năm" in cells[0]` match cả "15 năm"
- **Fix**: Exact match `if cells[0].strip() == vn_tenor`
- **Cách phòng**: Port Bond Lab `_match_tenor` pattern (exact match, không substring)

### Lỗi 2.2: VN-format decimal (dot vs comma)
- **Triệu chứng**: Parser không tìm thấy số "6.97%" vì regex tìm `[\d,]+`
- **Nguyên nhân**: VBMA pdftotext dùng dot decimal (6.97), SBV dùng comma decimal (6,97)
- **Fix**: Regex `[\d.,]+` + handle cả 2 format
- **Cách phòng**: Port Bond Lab `_parse_vietnamese_float` (xử lý cả dot/comma)

### Lỗi 2.3: HNX HTML entity encoding
- **Triệu chứng**: Parser không tìm thấy "năm" vì HNX encode `&#224;` (à)
- **Nguyên nhân**: HNX trả HTML entities, cần decode trước parse
- **Fix**: `html.unescape()` trước khi match
- **Cách phòng**: Luôn decode HTML entities khi parse response từ website VN

### Lỗi 2.4: SBV W25 thiếu LNH 9M
- **Triệu chứng**: Chart LNH 9M đứt quãng W25
- **Nguyên nhân**: SBV chỉ publish 6 kỳ hạn W25 (thiếu 9M) — missing data thật
- **Fix**: `spanGaps: true` trong Chart.js
- **Cách phòng**: Handle null/missing gracefully, không giả định đủ data

---

## NHÓM 3: DATA ACCURACY

### Lỗi 3.1: Coverage text chỉ 5% (ban đầu)
- **Nguyên nhân**: Chỉ trích số, không tận dụng prose phân tích từ 3 PDF
- **Fix**: Hybrid approach — cluster agent per tuần + cross-week synthesis
- **Lesson**: Text coverage cần đo bằng insight units (52%), không chỉ chars (5%)

### Lỗi 3.2: Speculation ("chốt lời", "bài học kỷ luật")
- **Nguyên nhân**: LLM tự suy diễn động cơ/context không có trong source
- **Fix**: Danh sách cấm speculation trong data_cards.md
- **Lesson**: Chỉ trần thuật + kết nối, không tự đánh giá

### Lỗi 3.3: Số liệu thiếu (13/43 trọng yếu bỏ sót)
- **Nguyên nhân**: Extract không đủ sâu
- **Fix**: Audit coverage trước publish, bổ sung 8 ưu tiên cao

---

## NHÓM 4: DESIGN/UX

### Lỗi 4.1: Fork template macro → "Frankenstein"
- **Nguyên nhân**: Copy macro template nguyên xi (gồm demo content GSO) rồi chỉ sửa bề mặt
- **Fix**: Viết template mới từ đầu, không fork
- **Lesson**: Fork = giữ skeleton, xóa body; không giữ body

### Lỗi 4.2: Operational language leak ("W23/W24", "cluster agent")
- **Nguyên nhân**: Narrative dùng label hạ tầng thay vì ngôn ngữ tự nhiên
- **Fix**: Rewrite "đầu tháng/giữa tháng/cuối tháng" + 0 grep cho operational terms

### Lỗi 4.3: Canvas không render trong display:none tab
- **Nguyên nhân**: Chart.js không render khi container 0px width
- **Fix**: Lazy render khi tab được click
- **Lesson**: Luôn lazy-render charts cho tab-switching UI

---

## NHÓM 5: SSL / CONNECTIVITY

### Lỗi 5.1: SSL cert HNX không verify được
- **Nguyên nhân**: HNX cert chain thiếu intermediate, certifi không có
- **Fix**: Unverified SSL context cho HNX, verified cho FRED
- **Lesson**: Bond Lab dùng truststore (system certs) — port pattern này

---

## UPDATE SKILL — RULES MỚI

### QA Gate mới: HTML Structure Check
```bash
# Sau mỗi edit HTML, verify:
python3 -c "
import re
html = open('report.html').read()
div_diff = html.count('<div') - html.count('</div>')
sec_diff = html.count('<section') - html.count('</section>')
print(f'div diff={div_diff}, section diff={sec_diff}')
if div_diff != 0 or sec_diff != 0:
    print('❌ HTML STRUCTURE BROKEN')
    exit(1)
else:
    print('✅ HTML structure OK')
"
```

### QA Gate mới: Section Visibility Check (Playwright)
```javascript
// Verify mỗi section có content visible khi active
const sections = document.querySelectorAll('.group-section');
for (let s of sections) {
  s.classList.add('active');
  const rect = s.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) {
    console.error(`Section ${s.id} has 0 dimensions!`);
  }
  s.classList.remove('active');
}
```

### QA Gate mới: Content Position Check
```javascript
// Verify chart nằm đúng section
const checks = [
  ['chartLNH', 'lnh'],
  ['chartYields', 'tpcp'],
  ['chartYieldCurve', 'tpcp'],
  ['chartSlope', 'tpcp'],
  ['chartConvex', 'tpcp'],
  ['chartFX', 'fx'],
  ['chartUS10Y', 'global'],
  ['chartDXY', 'global'],
];
for (const [canvas, section] of checks) {
  const el = document.getElementById(canvas);
  const sec = document.getElementById(section);
  if (el && sec && !sec.contains(el)) {
    console.error(`${canvas} is NOT in section ${section}!`);
  }
}
```

### Render Architecture Rule
- **KHÔNG post-process HTML** sau render script
- Tất cả charts/data/hints phải được inject **trong render script**, không modify file output sau đó
- Nếu cần thay đổi → sửa render script + re-render, không sed/inject trực tiếp
