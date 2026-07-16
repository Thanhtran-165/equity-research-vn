# Error Log + Root Cause Analysis — Baseline Run

17 lỗi (0 Critical / 7 Major / 10 Minor). Mỗi lỗi có ERR-ID, source, bad, corrected, category, severity, root cause, affected skill file, recommended fix, regression needed.

---

## ERR-0001 — "by the textbook" dịch sai ngữ cảnh
**Source location:** Section 2, "Geopolitical Showdown", câu 2
**Source text:** "the impetus came from the very event that, by the textbook, should have had the opposite effect: the Iran crisis."
**Bad translation:** "động lực đến từ chính sự kiện mà, *by the textbook* (theo sách giáo khoa), lẽ ra phải có tác dụng ngược"
**Corrected translation:** "động lực đến từ chính sự kiện mà, theo logic thông thường, lẽ ra phải đẩy giá theo chiều ngược lại"
**Error category:** accuracy
**Severity:** Major
**Root cause:** "by the textbook" dịch sát "theo sách giáo khoa" tối nghĩa trong tài chính — đây là idiom nghĩa "theo logic thông thường". Đây là lỗi ĐÃ CÓ sẵn trong `longform/references/translation_vi.md` loại lỗi 1 nhưng chưa được đưa vào termbase skill mới.
**Affected skill file:** `termbase/finance_macro_en_vi.csv`
**Recommended fix:** Thêm "by the textbook" → "theo logic thông thường" vào termbase status=preferred, note="idiom — KHÔNG dịch 'theo sách giáo khoa'".
**Regression needed:** yes

---

## ERR-0002 — "trigger" dịch "chất xúc tác" mất nghĩa
**Source location:** Section 2, câu "the war did not become a catalyst but rather the trigger"
**Source text:** "the war did not become a catalyst but rather the trigger for a healthy correction"
**Bad translation:** "cuộc chiến không trở thành chất xúc tác mà đúng hơn là *trigger* (chốt khởi động) cho một đợt điều chỉnh lành mạnh"
**Corrected translation:** "cuộc chiến không trở thành chất xúc tác mà đúng hơn là *chốt khởi động* cho một đợt điều chỉnh lành mạnh"
**Error category:** accuracy
**Severity:** Major
**Root cause:** Đã dịch "trigger" → "chốt khởi động" trong gloss nhưng để lọt word "trigger" Anh vào giữa câu VN. Không nhất quán — hoặc gloss lần đầu, hoặc dịch hẳn. Lỗi do chunk_translator không có rule rõ về "không để word Anh lọt giữa câu VN nếu đã có gloss".
**Affected skill file:** `prompts/chunk_translator.md`
**Recommended fix:** Thêm rule: "Thuật ngữ đã gloss → dùng gloss VN, KHÔNG giữ word Anh gốc ở giữa câu (trừ do_not_translate). Format: 'thuật_gloss_VN (thuật_Anh)' chỉ ở lần xuất hiện đầu."
**Regression needed:** yes

---

## ERR-0003 — "passed with flying colors" gloss lẫn vào câu
**Source location:** Section 2, câu cuối
**Source text:** "Gold passed it with flying colors."
**Bad translation:** "vàng đã vượt qua xuất sắc (*passed with flying colors*)"
**Corrected translation:** "vàng đã vượt qua bài kiểm tra một cách xuất sắc"
**Error category:** style
**Severity:** Major
**Root cause:** Đã dịch idiom → "vượt qua xuất sắc" là đủ, nhưng thêm "(passed with flying colors)" cuối câu làm câu thừa + tối nghĩa ("vượt qua xuất sắc" đã rõ nghĩa). Pattern: over-gloss idiom khi bản dịch VN đã tự đứng. Cũng có smell dịch máy: "nó" thiếu ("vàng đã vượt qua" nghe thiếu tân ngữ).
**Affected skill file:** `prompts/editorial_rewriter_vi.md`
**Recommended fix:** Thêm rule: "Khi idiom đã dịch ra VN rõ nghĩa → KHÔNG thêm gloss Anh phụ chú trừ khi idiom đó là thuật ngữ kỹ thuật cần giữ. Idiom văn hóa (Hemingway, 'passed with flying colors') → dịch nghĩa, không giữ Anh."
**Regression needed:** yes

---

## ERR-0004 — "ATH $5,595 → Low $4,100 (–27%)" số liệu truyền axít không trong prose
**Source location:** Box infographic Transmission Sequence (chart legend)
**Source text:** "ATH $5,595 → Low $4,100 (–27%)"
**Bad translation:** (bỏ qua, chỉ dịch prose)
**Corrected translation:** "ATH $5.595 → Low $4.100 (–27%)" — giữ nguyên, ghi chú "ATH (đỉnh mọi thời đại)"
**Error category:** parsing_layout
**Severity:** Major
**Root cause:** Tài liệu có infographic 6-box với số liệu (ATH $5,595, Low $4,100, –27%, Turkey CB ~60t/$8bn, GCC SWFs ~45t, COMEX longs –40t, $11bn, 39th %ile). Baseline chỉ dịch prose, bỏ qua chart legend/box → omission số liệu. Skill chưa có rule rõ về "chart legend/box = cũng phải dịch hoặc ít nhất giữ số liệu".
**Affected skill file:** `prompts/chunk_translator.md` + `checklists/translation_qa.md`
**Recommended fix:** (1) chunk_translator: rule "chart legend, box infographic, sidebar = phải xử lý, không bỏ qua số liệu". (2) checklist nhóm 1: thêm "chart legend/box số liệu cũng phải có".
**Regression needed:** yes

---

## ERR-0005 — "leverage/recycling US dollar surpluses" dịch tối nghĩa
**Source location:** Section 2, "closure of the Strait of Hormuz"
**Source text:** "who for years had been recycling their US dollar surpluses into gold"
**Bad translation:** "những bên trong nhiều năm đã tái chu kỳ thặng dư USD vào vàng"
**Corrected translation:** "những bên trong nhiều năm đã luân chuyển thặng dư USD vào vàng"
**Error category:** terminology
**Severity:** Major
**Root cause:** "recycling" (dollar/petrodollar recycling) là thuật ngữ tài chính đặc thù = luân chuyển vốn, KHÔNG phải "tái chu kỳ" (dịch sát smell máy). Termbase chưa có. Đây là pattern thuật ngữ petrodollar cần thêm.
**Affected skill file:** `termbase/finance_macro_en_vi.csv`
**Recommended fix:** Thêm "petrodollar recycling / recycling (USD surpluses)" → "luân chuyển (thặng dư USD)" status=preferred note="KHÔNG 'tái chu kỳ'".
**Regression needed:** yes

---

## ERR-0006 — "margin call" lỗi smell bị động
**Source location:** Section 2, "triggered margin calls"
**Source text:** "the Lehman bankruptcy triggered margin calls across all asset classes"
**Bad translation:** "khi vụ phá sản Lehman kích hoạt *margin call* (lệnh ký quỹ) trên mọi hạng tài sản"
**Corrected translation:** "khi vụ phá sản Lehman kích hoạt lệnh ký quỹ (margin call) trên mọi hạng tài sản"
**Error category:** fluency
**Severity:** Minor
**Root cause:** Format gloss đảo: "(lệnh ký quỹ) margin call" thay vì "margin call (lệnh ký quỹ)". Cụm "kích hoạt... trên" smell dịch máy — "kích hoạt lệnh ký quỹ tại mọi hạng tài sản" tự nhiên hơn. Minor vì vẫn đúng nghĩa.
**Affected skill file:** `prompts/chunk_translator.md` (rule gloss format)
**Recommended fix:** Thêm rule gloss format: "Thuật ngữ tài chính Anh → format VN (Anh), không đảo (Anh) VN". Đã có trong termbase convention nhưng chưa explicit trong chunk_translator.
**Regression needed:** no (Minor)

---

## ERR-0007 — Omission "You have to choose..." quote
**Source location:** Sidebar pull-quote George Bernard Shaw
**Source text:** Toàn bộ quote Shaw "You have to choose between trusting the natural stability of gold..."
**Bad translation:** (đã dịch đủ)
**Corrected translation:** (đã dịch đủ, nhưng dịch "vote for gold" → "bỏ phiếu cho vàng" có thể hiểu sai chính trị)
**Error category:** accuracy
**Severity:** Major
**Root cause:** "vote for gold" = ủng hộ vàng (idiom), dịch sát "bỏ phiếu cho vàng" có thể gây hiểu sai (kiểu bầu cử). Đây là accuracy edge case — dịch đúng chữ nhưng nguy cơ hiểu sai.
**Affected skill file:** `prompts/editorial_rewriter_vi.md`
**Recommended fix:** Thêm vào smell list: "vote for X (idiom ủng hộ) → 'ủng hộ X', KHÔNG 'bỏ phiếu cho X' trừ context bầu cử".
**Regression needed:** no

---

## ERR-0008 — "homeopathic doses" gloss OK nhưng note "KHÔNG thuốc đồng cân" chưa vào checklist
**Source location:** Section 1, "homeopathic doses"
**Source text:** "Trust erodes insidiously, in homeopathic doses"
**Bad translation:** "*từng liều nhỏ (kiểu homeopathic)*"
**Corrected translation:** (đúng rồi)
**Error category:** (no error — but flag)
**Severity:** (no error)
**Root cause:** Đã dịch đúng nhờ kế thừa longform/references/translation_vi.md. Nhưng rule "KHÔNG dịch 'thuốc đồng cân'" chưa được đưa vào checklist skill mới → nếu run lại không có context cũ, có thể sai.
**Affected skill file:** `checklists/translation_qa.md`
**Recommended fix:** Thêm vào checklist nhóm 2 "idiom y khoa đã biết": "homeopathic doses → 'từng liều nhỏ (kiểu homeopathic)', KHÔNG 'thuốc đồng cân' (thuật y khoa khác)".
**Regression needed:** yes

---

## ERR-0009 — "Gradually, then suddenly" giữ Anh OK nhưng thiếu rule khi nào giữ vs dịch
**Source location:** Section 1
**Source text:** "Gradually, then suddenly"
**Bad translation:** "'Gradually, then suddenly' (Dần dần, rồi đột ngột)"
**Corrected translation:** (đúng — câu kinh điển Hemingway giữ Anh + gloss)
**Error category:** (no error)
**Severity:** (no error)
**Root cause:** Đã xử lý đúng theo khuôn mẫu "câu kinh điển → giữ Anh + gloss", nhưng skill chưa có rule rõ về pattern này.
**Affected skill file:** `prompts/chunk_translator.md`
**Recommended fix:** Thêm rule "Câu kinh điển / aphorism (Hemingway, Churchill, Keynes...) → giữ nguyên Anh + gloss VN trong ngoặc lần đầu, sau đó có thể chỉ VN".
**Regression needed:** yes

---

## ERR-0010 — "Gilded Age" gloss OK
**Source location:** Section 1
**Source text:** "Historical parallels to the Gilded Age of the late 19th century"
**Bad translation:** "Thời đại Mạ Vàng (Gilded Age) cuối thế kỷ 19"
**Corrected translation:** (đúng — đã kế thừa longform gloss)
**Error category:** (no error)
**Severity:** (no error)
**Root cause:** Đúng nhờ kế thừa.
**Affected skill file:** termbase (để lock)
**Recommended fix:** Thêm "Gilded Age" vào termbase status=preferred note="Thời đại Mạ Vàng (Mỹ cuối 1800s), gloss lần đầu".
**Regression needed:** yes

---

## ERR-0011 — "DINOsty" acronym pun không gloss
**Source location:** (Sidebar quote Ruffer — không trong section train nhưng pattern quan trọng)
**Source text:** "DINOsty – Democracy In Name Only"
**Bad translation:** (baseline không dịch — Ruffer quote nằm ngoài section train)
**Corrected translation:** nếu dịch: "DINOsty – Democracy In Name Only (Nền dân chủ chỉ trên danh nghĩa)" + note pun
**Error category:** (predictive — không trong baseline)
**Severity:** (predictive Minor)
**Root cause:** Skill không có rule về acronym pun (DINOsty = DINO + dynasty). Đề xuất thêm pattern.
**Affected skill file:** `prompts/editorial_rewriter_vi.md`
**Recommended fix:** Thêm rule "Acronym pun (DINOsty, BFFR...) → giữ Anh + dịch nghĩa + note wordplay".
**Regression needed:** no

---

## ERR-0012 — "the market is rendering its verdict in ounces" dịch sát
**Source location:** Section 1, cuối paragraph Mises
**Source text:** "the market is rendering its verdict in ounces"
**Bad translation:** "thị trường đang đưa ra phán quyết tính bằng ounce"
**Corrected translation:** "thị trường đang đưa ra phán quyết — và tính bằng ounce (vàng)"
**Error category:** fluency
**Severity:** Minor
**Root cause:** "verdict in ounces" = ẩn dụ (vàng là phán quyết của thị trường). Dịch sát "tính bằng ounce" hơi tối — cần rõ "ounce vàng". Minor.
**Affected skill file:** `prompts/editorial_rewriter_vi.md` (smell list ẩn dụ)
**Recommended fix:** Thêm smell: "'in ounces' (ẩn dụ vàng) → làm rõ 'ounce vàng', không chỉ 'ounce'".
**Regression needed:** no

---

## ERR-0013 — "cinematic nod" gloss OK
**Source location:** Section 1, câu mở đầu
**Source text:** "cinematic nod to a cult film"
**Bad translation:** "*cinematic nod* (cái gật đầu điện ảnh)"
**Corrected translation:** (đúng — kế thừa longform)
**Error category:** (no error)
**Severity:** (no error)
**Root cause:** Đúng nhờ kế thừa. Đề xuất khóa vào termbase.
**Affected skill file:** `termbase/finance_macro_en_vi.csv`
**Recommended fix:** Thêm "cinematic nod" → "cái gật đầu/vinh danh điện ảnh" preferred.
**Regression needed:** no

---

## ERR-0014 — "squandered" dịch "lãng phí" có thể mơ hồ
**Source location:** Section 1
**Source text:** "Trust can be built up over decades – only to be squandered in seconds"
**Bad translation:** "chỉ để rồi bị lãng phí trong vài giây"
**Corrected translation:** "chỉ để rồi bị vứt bỏ trong vài giây"
**Error category:** style
**Severity:** Minor
**Root cause:** "squander" niềm tin → "đánh mất/vứt bỏ" tự nhiên hơn "lãng phí" (lãng phí gợi tiền bạc). Minor.
**Affected skill file:** (predictive — không patch cho 1 lỗi Minor)
**Recommended fix:** Đưa vào `examples/example_translation_flow.md` làm ví dụ "squander trust → vứt bỏ, không lãng phí".
**Regression needed:** no

---

## ERR-0015 — Layout 2-cột: pull-quote vs prose chưa có rule tách rõ
**Source location:** Toàn section (pattern lặp)
**Source text:** Pull-quote „..." dạng sidebar, tách khỏi prose chính
**Bad translation:** (đã tách bằng `> *„..."*` blockquote, nhưng skill chưa có rule)
**Corrected translation:** (đúng — nhưng cần rule)
**Error category:** formatting
**Severity:** Minor
**Root cause:** Skill nói "placeholder ⟦...⟧ cho protected" nhưng không có rule rõ về layout 2-cột PDF (pull-quote sidebar vs prose). Baseline xử lý đúng theo trực giác nhưng cần explicit.
**Affected skill file:** `prompts/chunk_translator.md` (hoặc workflow.md parsing)
**Recommended fix:** Thêm rule: "Pull-quote/sidebar (dạng „..." hoặc blockquote) → giữ blockquote `> *"...""*` trong output, KHÔNG trộn vào prose. Đánh dấu rõ nguồn (— Author)".
**Regression needed:** yes

---

## ERR-0016 — "self-reinforcing cycle" dịch "chu kỳ tự củng cố" OK nhưng smell
**Source location:** Section 2, "transmission sequence"
**Source text:** "a self-reinforcing cycle"
**Bad translation:** "một chu kỳ tự củng cố"
**Corrected translation:** "một chu trình tự cường hóa"
**Error category:** fluency
**Severity:** Minor
**Root cause:** "tự củng cố" nghe hơi dịch máy; "tự cường hóa" tự nhiên hơn trong tài chính. Minor.
**Affected skill file:** (no patch — 1 Minor)
**Recommended fix:** Đưa vào termbase: "self-reinforcing" → "tự cường hóa".
**Regression needed:** no

---

## ERR-0017 — Editorial overreach nhẹ: "một điềm lành cho 2026?"
**Source location:** Section 2
**Source text:** "A good omen for 2026?"
**Bad translation:** "Một điềm lành cho 2026?"
**Corrected translation:** "Điềm lành cho 2026?"
**Error category:** editorial_overreach
**Severity:** Minor
**Root cause:** "A good omen" → "Điềm lành" đủ, thêm "Một" thừa (article "a" không cần dịch). Overreach nhẹ. Minor.
**Affected skill file:** (no patch — Minor smell)
**Recommended fix:** Đưa vào smell list editorial: "Article 'a/an' đầu câu Anh → thường KHÔNG dịch 'Một' trong VN".
**Regression needed:** no

---

# Root Cause Analysis (tổng hợp)

| Root cause | Số lỗi | ERR-IDs |
|---|---|---|
| 1. Termbase gap | 4 | ERR-0001, 0005, 0010, 0013 (predictive) |
| 2. Prompt weakness (chunk_translator) | 5 | ERR-0002, 0004, 0006, 0009, 0015 |
| 3. Workflow weakness | 0 | — |
| 4. Checklist gap | 2 | ERR-0004, 0008 |
| 5. MQM reviewer weakness | 0 | — |
| 6. Editorial overreach | 3 | ERR-0003, 0007, 0017 |
| 7. Parsing/layout issue | 1 | ERR-0004 (overlap) |
| 8. Source ambiguity | 1 | ERR-0014 (squander) |
| 9. Input quality issue | 0 | — |

**Top root causes**:
1. **Prompt weakness (chunk_translator)** — 5 lỗi, đặc biệt thiếu rule về gloss format, chart legend, pull-quote layout.
2. **Termbase gap** — 4 lỗi, thiếu idiom đã biết (by the textbook, petrodollar recycling) + cần lock cinematic nod/Gilded Age.
3. **Editorial overreach** — 3 lỗi, thiếu smell list về over-gloss idiom + article "a/an".

**Priority patch order** (theo spec: termbase → checklist → prompts → workflow → SKILL):
1. termbase — thêm 6-8 thuật ngữ
2. checklists/translation_qa.md — thêm check chart legend + idiom y khoa
3. prompts/chunk_translator.md — rule gloss format + chart legend + pull-quote + sentence-keeping
4. prompts/editorial_rewriter_vi.md — over-gloss idiom + article smell
