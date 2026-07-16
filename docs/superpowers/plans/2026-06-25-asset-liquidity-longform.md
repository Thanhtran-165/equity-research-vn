# Thanh khoản Tài sản — Longform Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây báo cáo longform HTML 6 phần + 3 phụ lục về thanh khoản đa tài sản cho nhà đầu tư cá nhân, dùng template `longform` skill, style Amber, mood nâu đất-navy, numerated citations.

**Architecture:** Single-page `index.html` trong `thanh-khoan-tai-san/`, copy từ `assets/article_template.html`, thay tokens, viết 6 `<section>` + phụ lục, nhúng 6 chart Chart.js + 1 flow diagram CSS, numerated refs. Toàn bộ số từ paper kinh điển (không chạy số thực). Cuối: fact-check số liệu + lý thuyết + QA kỹ thuật + verify nội dung.

**Tech Stack:** HTML/CSS (template có sẵn dark theme), Chart.js 4.4.1 (CDN), vanilla JS (minimap + presentation + chart init).

**Spec nguồn:** `docs/superpowers/specs/2026-06-25-asset-liquidity-design.md`

**Quyết định đã chốt:** Amber family; mood `linear-gradient(135deg,#422006 0%,#1e3a8a 50%,#312e81 100%)`; numerated citations; viết hết rồi mới trình bày; số từ paper quốc tế cho cả ví dụ + data.

---

## File Structure

- Create: `thanh-khoan-tai-san/index.html` — báo cáo chính (scaffold từ template + nội dung).
- Spec: `docs/superpowers/specs/2026-06-25-asset-liquidity-design.md` (đã có, tham chiếu).

Một file HTML duy nhất (theo convention longform — self-contained, có thể deploy Vercel sau).

## Chart inventory (chốt trước khi viết)

| # | Vị trí | Loại | Nội dung | Data nguồn |
|---|---|---|---|---|
| C1 | Section 3 | Chart.js **scatter** | 6 tài sản theo 2 trục (log time-to-exit × cost-to-exit %) | ước lượng từ spec Phần 3 |
| C2 | Section 3 | Chart.js **bar** (log y) | Amihud ILLIQ so sánh 6 tài sản | từ Amihud 2002 + Hasbrouck 2009 ranges |
| C3 | Section 4 | Chart.js **line** | Spread ↔ expected return (Amihud-Mendelson quan hệ đơn điệu) | conceptual line, ~2–6 bps/bps |
| C4 | Section 4 | Chart.js **bar** | L-Sharpe so sánh 6 tài sản | tính từ spec Phần 4 |
| C5 | Section 5 | CSS **`.fd` flow diagram** | Liquidity spiral kép (Brunnermeier-Pedersen 2009) | — |
| C6 | Section 5 | Chart.js **line** | Tương quan → 1 khi stress (concept, 3 sự kiện) | conceptual |
| C7 | Section 6 | Chart.js **radar** | 6 tài sản × 4 thước (spread nhỏ/lỏng, depth, liquidity beta, exit cost thấp) | từ profile Phần 3 |

→ 6 Chart.js + 1 CSS flow = 7 visual.

## Table inventory (`.tbl` component)

T1 (S1): mini-table "dự đoán của bạn" — BTC vs trái phiếu.
T2 (S2): 4 thước đo × công thức × paper.
T3 (S3): profile 9 dòng (6 loại tài sản, vàng 2 dòng, cổ phiếu 2 dòng, crypto 2 dòng).
T4 (S4): premium thực chứng (4 tài sản × premium × realized × xứng?).
T5 (S4): công thức L-Sharpe components.
T6 (S6): Liquidity Tier (L0–L3 × đặc điểm × tỷ trọng).
T7 (S6): checklist 7 dòng.
T8 (phụ lục A): bảng công thức đầy đủ (Roll, CS, Amihud, Kyle, P-S, LCAPM).
T9 (phụ lục C): thư mục paper (15 dòng, annotation 1 câu).

---

### Task 1: Scaffold — copy template, fill hero/meta, setup chart defaults

**Files:**
- Create: `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Tạo thư mục + copy template**

```bash
mkdir -p /Users/bobo/ZCodeProject/thanh-khoan-tai-san
cp "/Users/bobo/.zcode/skills/longform/assets/article_template.html" /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
```

- [ ] **Step 2: Replace hero/meta tokens** (string replace, không f-string)

Tokens → giá trị:
- `{{HERO_TITLE}}` → `Thanh khoản Tài sản`
- `{{BADGE}}` → `Khung đa tài sản · Nhà đầu tư cá nhân`
- `{{HERO_SUB}}` → `Vì sao thanh khoản quyết định giá, biến động và rủi ro — và cách dùng nó làm thước đo risk/reward khi phân bổ vốn giữa 6 loại tài sản.`
- `{{UPDATE_DATE}}` → `2026-06-25`
- `{{META_SCOPE}}` → `6 loại tài sản · 4 thước đo kinh điển · framework áp dụng`
- `{{META_CHAPTERS}}` → `6 phần + 3 phụ lục`
- `{{FOOTER_TITLE}}` → `Thanh khoản Tài sản — Longform`

- [ ] **Step 3: Thiết lập family AMBER (giữ mặc định template) + mood nâu đất-navy**

Sửa `.hero{background:...}` → `linear-gradient(135deg,#422006 0%,#1e3a8a 50%,#312e81 100%)` (mood tài.fin VN). Family Amber đã là default template — không cần đổi `.num` badge / `.kpi`.

- [ ] **Step 4: Setup Chart.defaults ở đầu `<script>` đầu tiên**

```js
Chart.defaults.color = '#cbd5e1';
Chart.defaults.borderColor = 'rgba(148,163,184,.2)';
Chart.defaults.font.family = "'Inter',system-ui,sans-serif";
```

- [ ] **Step 5: Verify không còn placeholder hero**

```bash
grep -oE "{{[A-Z_0-9]+}}" /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html | sort -u
```
Expected: chỉ còn `{{SECTION_*}}` và `{{SRC_*}}` (sẽ fill ở task sau).

- [ ] **Step 6: Commit**

```bash
cd /Users/bobo/ZCodeProject && git init -q 2>/dev/null; git add thanh-khoan-tai-san/index.html && git commit -m "scaffold: longform asset-liquidity report from template" 
```
(Nếu chưa phải git repo, bỏ qua commit hoặc init.)

---

### Task 2: Section 1 — Trực giác: "Ra tiền trong bao lâu, mất bao nhiêu %?"

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Thay `{{SECTION_1_TITLE}}` / `{{SECTION_1_SHORT}}`** trong minimap + section title → `Trực giác: ra tiền trong bao lâu?` / `Trực giác`.

- [ ] **Step 2: Viết nội dung Section 1** (~1.200 chữ)

Cấu trúc component:
1. `<p>` mở: hook "Bạn cầm 1 tỷ, 500 cổ phiếu + 500 căn hộ, mai cần tiền gấp — ra bao nhiêu, trong bao lâu, mất bao nhiêu %?"
2. `<div class="callout info">` — định nghĩa 2 trục: **thời gian thoát** (t) và **chi phí thoát** (c). `Mọi thước đo phức tạp sau này đều quy về 2 trục này.`
3. `.kpi-grid` 3 ô: Trading liquidity / Funding liquidity / Market liquidity (theo Brunnermeier & Pedersen 2009)<sup class="ref">1</sup>.
4. `<div class="callout warn">` — 2 bẫy trực giác: (a) "blue-chip luôn lỏng" sai (Black Monday 1987<sup class="ref">2</sup>, Flash Crash 2010<sup class="ref">3</sup>); (b) "BĐS chậm vì giá trị lớn" — nửa đúng, thật ra vì BĐS là *search market* (Case & Shiller 2003<sup class="ref">4</sup>).
5. `T1` mini-table `.tbl`: "Bạn đoán xem" — hàng 1 "BTC lỏng hơn trái phiếu chính phủ?", hàng 2 đáp án ngược trực giác (để lại câu trả lời cho Section 3).

- [ ] **Step 3: Verify section có đủ component**

```bash
python3 -c "
import re
html=open('/Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html').read()
m=re.search(r'<section id=\"s1\"[^>]*>(.*?)</section>', html, re.S)
b=m.group(1) if m else ''
print('callout:', b.count('callout'))
print('kpi:', b.count('class=\"kpi\"'))
print('tbl:', b.count('class=\"tbl\"'))
"
```
Expected: callout ≥2, kpi ≥3, tbl ≥1.

- [ ] **Step 4: Commit**

---

### Task 3: Section 2 — 4 thước đo kinh điển + công thức

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Thêm minimap entry "Phần 2 — 4 thước đo"** + `<section id="s2">`.

- [ ] **Step 2: Viết Section 2** (~1.800 chữ)

Cấu trúc:
1. `<p>` hook: cổ phiếu A spread 0.05%/vol 100 tỷ vs B spread 0.8%/vol 5 tỷ — cái nào lỏng hơn, "hơn bao nhiêu"?
2. `T2` `.tbl`: 4 thước đo × (câu hỏi trả lời, công thức, paper). Hàng:
   - Roll 1984<sup class="ref">5</sup>: `s = 2√(−cov(r_t, r_{t−1}))`
   - Corwin-Schultz 2012<sup class="ref">6</sup>: từ high-low
   - Amihud 2002<sup class="ref">7</sup>: `ILLIQ = (1/D)·Σ|r_d| / DVOL_d`
   - Kyle 1985<sup class="ref">8</sup>: `Δp = λ·flow + ε`
   - Pastor-Stambaugh 2003<sup class="ref">9</sup>: hồi quy reversal
3. `<div class="callout info">` — điểm cốt lõi: 3 thước đầu đo **mức riêng**; P-S đo **rủi ro hệ thống**. Sự khác biệt này trở lại Section 5.
4. Mỗi thước đo 1 đoạn giải thích ngắn (1–2 câu + trực giác đời thường).
5. `<div class="callout tip">` mini-challenge: "Bạn có thể tự tính Amihud ILLIQ cho cổ phiếu bạn đang nắm — chỉ cần giá đóng + khối lượng hàng ngày" (không chạy số thực, chỉ nêu cách).

- [ ] **Step 3: Verify công thức hiển thị đúng** (check có 5 `<sup class="ref">` với id 5–9).

- [ ] **Step 4: Commit**

---

### Task 4: Section 3 — Profile 6 tài sản + charts C1, C2

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Thêm minimap "Phần 3 — Profile 6 tài sản"** + `<section id="s3">`.

- [ ] **Step 2: Viết intro + `T3` profile table** (~2.000 chữ cho cả section)

`T3` 9 dòng (spread, time-to-exit, chi phí, liquidity beta, nguồn — số từ spec, mỗi số có `<sup class="ref">`):
- Tiền mặt/CD, T-bill, T-bond (Fleming 2003<sup class="ref">10</sup>), large-cap (Hasbrouck 2009<sup class="ref">11</sup>), small-cap (Amihud 2002<sup class="ref">7</sup>), GLD, vàng vật lý, BĐS (Case & Shiller 2003<sup class="ref">4</sup>), BTC (Makarov-Schoar 2020<sup class="ref">12</sup>), altcoin.

- [ ] **Step 3: Chart C1 — scatter 2 trục**

`<canvas id="c1">` + Chart.js scatter. Data 9 chấm (x = log(time-to-exit ngày), y = cost-to-exit %):
- Tiền mặt: (0.01, 0), T-bill: (0.01, 0.02), large-cap: (0.01, 0.15), GLD: (0.01, 0.1), small-cap: (0.1, 2), BTC: (0.01, 0.1), vàng vật lý: (1, 3.5), T-bond: (0.01, 0.1), BĐS: (120, 7), altcoin: (0.5, 2.5).
- Log x-axis, y %. Tooltip hiện tên tài sản.

- [ ] **Step 4: Chart C2 — bar log Amihud ILLIQ**

`<canvas id="c2">` + bar. y log-scale. Data (ILLIQ ×10⁻⁶, order lớn = ít lỏng): T-bill 0.01, large-cap 0.1, GLD 0.2, BTC 0.5, small-cap 5, vàng vật lý 50, BĐS 2000, altcoin 10. Label ghi rõ "ước lượng, log-scale, đơn vị tương đối".

- [ ] **Step 5: 3 "thẻ" bất ngờ** — mỗi cái 1 `<div class="callout warn">`:
1. Trái phiếu chính phủ Mỹ lỏng hơn cổ phiếu (spread < 0.01%).
2. Vàng vật lý gần như "không lỏng" so với GLD.
3. Crypto lỏng 24/7 nhưng liquidity beta cao nhất.

- [ ] **Step 6: Verify 2 chart**

```bash
grep -c '<canvas' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
grep -c 'new Chart' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
```
Expected: bằng nhau (≥2 sau task này).

- [ ] **Step 7: Commit**

---

### Task 5: Section 4 — Premium + R/R + charts C3, C4

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Thêm minimap + `<section id="s4">`.**

- [ ] **Step 2: Viết 4 sub-block** (~2.500 chữ)

A. Lý thuyết premium — Amihud & Mendelson 1986<sup class="ref">13</sup> (quan hệ đơn điệu spread→return), Acharya & Pedersen 2005 LCAPM<sup class="ref">14</sup> (4 beta thanh khoản). Công thức LCAPM trong callout.

B. `T4` `.tbl` thực chứng: small-cap (Amihud 2002<sup class="ref">7</sup>, Hou et al. 2020<sup class="ref">15</sup>), BĐS (Flavin & Yamashita 2002<sup class="ref">16</sup>), trái phiếu off-the-run (Krishnamurthy 2002<sup class="ref">17</sup>), crypto. Cột "Có xứng?".

C. Cốt lõi — Liquidity-adjusted Sharpe. `T5` bảng components: `L-Sharpe = (E[R] − Rf − c_liquidation) / σ`, `c_liquidation = spread + slippage + time cost`. Fire-sale BĐS: bán gấp 30 ngày vs 150 ngày mất thêm ~10–15% (Campbell, Giglio & Pathak 2011<sup class="ref">18</sup>). So-what: L-Sharpe cao nhất = tài sản đủ lỏng mà vẫn có premium.

D. Quy tắc ngón tay cái (2 callout tip): `prem < chi phí thoát × 5` → không đủ bù; `horizon > 5 × time-to-exit` mới nắm tài sản ít lỏng. **Cảnh báo: heuristic, không phải luật.**

- [ ] **Step 3: Chart C3 — line spread↔return** (Amihud-Mendelson quan hệ đơn điệu). `<canvas id="c3">` + line, slope ~2–6 bps return mỗi 1 bps spread, vùng shade premium.

- [ ] **Step 4: Chart C4 — bar L-Sharpe so sánh 6 tài sản**. `<canvas id="c4">` + bar. Tính từ spec Phần 4 (large-cap cao, trái phiếu off-the-run cao, GLD trung bình, small-cap thấp, BĐS thấp, BTC thấp/không xác định). Label "ước lượng khái niệm".

- [ ] **Step 5: Verify 4 chart tổng cộng**

```bash
grep -c '<canvas' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
grep -c 'new Chart' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
```
Expected: bằng nhau, ≥4.

- [ ] **Step 6: Commit**

---

### Task 6: Section 5 — Liquidity factor + spiral C5 + correlation C6

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Thêm minimap + `<section id="s5">`.**

- [ ] **Step 2: Viết Section 5** (~2.200 chữ)

A. Liquidity spirals — Brunnermeier & Pedersen 2009<sup class="ref">1</sup> (đã ref ở S1, tái dùng). Vòng xoáy kép: market liquidity ↓ → funding liquidity ↓ (margin calls) → market liquidity ↓ thêm. "Thứ tự thoát: tài sản lỏng trước".

B. C5 — CSS `.fd` flow diagram vòng xoáy kép (xem `references/components.md` recipe `.fd`): 2 vòng market↔funding, mũi tên vòng.

C. Liquidity factor là nhân tố rủi ro — Pastor & Stambaugh 2003<sup class="ref">9</sup> (premium ~1.5–3%/năm cho liquidity beta thấp), Sadka 2006<sup class="ref">19</sup> (chỉ liquidity vĩnh viễn mới có premium).

D. Tail risk cho cá nhân — Herfindahl sổ lệnh; "dash for cash" 3/2020 ETF tiền thị trường rớt; quy tắc "giả định tương quan → 0.9". Tiền mặt vật lý + T-bill trực tiếp mới thực sự an toàn.

E. C6 — Chart.js line "tương quan → 1 khi stress": 3 sự kiện (2008, 3/2020, 5/2022). Line tương quan trung bình ngày thường ~0.3, stress → 0.9. Số: 3/2020 Treasury spread nới gấp 10× trong 2 tuần; BTC 5/2022 spread 0.02%→2–5%.

- [ ] **Step 3: Verify flow diagram `.fd`** có đủ node + mũi tên.

- [ ] **Step 4: Commit**

---

### Task 7: Section 6 — Framework áp dụng + Tier C7 + checklist

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Thêm minimap + `<section id="s6">`.**

- [ ] **Step 2: Viết Section 6** (~2.000 chữ)

A. `T6` Liquidity Tier `.tbl`: L0 (ra tiền <1 ngày, loss <0.5%, 5–15%), L1 (<5 ngày, <1%, 25–40%), L2 (5–30 ngày, 1–5%, 20–35%), L3 (>30 ngày, >5%, <15%).

B. 3 câu hỏi tự kiểm (callout info): 7 ngày mất bao nhiêu %? liquidity beta cao? horizon > 5×exit?

C. 4 bẫy nhà ĐT VN (callout warn): cổ phiếu thin; BĐS = giá tăng ≠ thanh khoản; crypto 24/7 ≠ bán giá công bằng; trái phiếu ngân hàng gates khi stress (SCB 2022).

D. `T7` checklist 7 dòng `.tbl` (checkbox UI).

E. C7 — Chart.js radar: 6 tài sản × 4 trục (lỏng spread, depth, liquidity beta thấp, exit cost thấp). Radar cho thấy không tài sản nào thắng cả 4 — tradeoff.

- [ ] **Step 3: Verify 6 chart + 1 flow tổng**

```bash
grep -c '<canvas' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html  # expect 6
grep -c 'new Chart' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html  # expect 6
grep -c 'class=\"fd\"' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html  # expect ≥1
```

- [ ] **Step 4: Commit**

---

### Task 8: Phụ lục A (công thức) + B (glossary) + C (refs table)

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Phụ lục A — `<section id="app-a">`** "Bảng công thức đầy đủ".

`T8` `.tbl`: Roll, Corwin-Schultz, Amihud, Kyle λ, Pastor-Stambaugh, LCAPM — mỗi dòng công thức đầy đủ + 1 câu ý nghĩa + paper.

- [ ] **Step 2: Phụ lục B — `<section id="app-b">`** "Glossary ~30 thuật ngữ".

Dùng component glossary (xem `references/components.md`). 30 thuật ngữ: liquidity, spread, depth, slippage, lambda, liquidity beta, fire-sale, gating, dash-for-cash, search market, auction market, market maker, order book, off-the-run, on-the-run, funding liquidity, market liquidity, trading liquidity, ILLIQ, LCAPM, premium, L-Sharpe, Herfindahl, reversal, order flow, margin call, liquidation cascade, thin stock, time-to-exit, cost-to-exit.

- [ ] **Step 3: Phụ lục C — `<section id="app-c">`** "Thư mục paper".

`T9` `.tbl`: 15 paper, mỗi dòng: tác giả + năm + tiêu đề + 1 câu annotation. (Roll 1984, Corwin-Schultz 2012, Amihud 2002, Amihud-Mendelson 1986, Kyle 1985, Pastor-Stambaugh 2003, Acharya-Pedersen 2005, Brunnermeier-Pedersen 2009, Hasbrouck 2009, Sadka 2006, Fleming 2003, Case-Shiller 2003, Flavin-Yamashita 2002, Krishnamurthy 2002, Makarov-Schoar 2020, Hou et al. 2020, Campbell-Giglio-Pathak 2011.)

- [ ] **Step 4: Commit**

---

### Task 9: Citations — numerated `ol.refs` + đồng bộ `<sup class="ref">`

**Files:** Modify `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Xây `ol.refs` cuối bài** — mode numerated (xem `references/citations.md`). 

19 entry (id 1–19 theo thứ tự xuất hiện):
1. Brunnermeier & Pedersen 2009 — Market Liquidity and Funding Liquidity
2. (Black Monday 1987 — nguồn)
3. (Flash Crash 2010 — nguồn)
4. Case & Shiller 2003 — Is There a Real Estate Bubble?
5. Roll 1984 — A Simple Implicit Measure
6. Corwin & Schultz 2012 — A Simple Way to Estimate Bid-Ask Spreads
7. Amihud 2002 — Illiquidity and Stock Returns
8. Kyle 1985 — Informed Trading
9. Pastor & Stambaugh 2003 — Liquidity Risk and Expected Stock Returns
10. Fleming 2003 — Measuring Treasury Market Liquidity
11. Hasbrouck 2009 — Trading Costs and Returns for US Equities
12. Makarov & Schoar 2020 — Trading and Arbitrage in Cryptocurrency Markets
13. Amihud & Mendelson 1986 — Asset Pricing and the Bid-Ask Spread
14. Acharya & Pedersen 2005 — Asset Pricing with Liquidity Risk (LCAPM)
15. Hou, Xue, Zhang 2020 — Replicating Anomalies
16. Flavin & Yamashita 2002 — Owner-Occupied Housing and the Composition of the Household Portfolio
17. Krishnamurthy 2002 — The Bond/Old-Bond Spread
18. Campbell, Giglio, Pathak 2011 — Forced Sales and House Prices
19. Sadka 2006 — Momentum and Post-Earnings-Announcement Drift Anomalies (liquidity)

- [ ] **Step 2: Thay `{{SRC_*}}` tokens** (3 source template mẫu) bằng 3 paper đầu, hoặc xóa block SRC nếu dùng ol.refs đầy đủ.

- [ ] **Step 3: Verify số `<sup class="ref">` = số entry trong ol.refs**

```bash
python3 -c "
import re
html=open('/Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html').read()
sup=set(re.findall(r'class=\"ref\">(\d+)', html))
refs=set(re.findall(r'<li value=\"?(\d+)\"?', html)) or set(range(1,len(re.findall(r'<li', html[html.find('ol class=\"refs\"'):]))+1))
print('sup ids:', sorted(int(x) for x in sup))
print('missing in refs:', sorted(int(x) for x in sup if int(x) not in range(1,20)))
"
```
Expected: missing = [] (mọi sup đều có entry).

- [ ] **Step 4: Commit**

---

### Task 10: Fact-check số liệu (Bước 5 longform)

**Files:** Read-only verify trên `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Trích xuất toàn bộ claim định lượng** (text + chart data) bằng Agent Explore — ghi số dòng + claim + loại.

- [ ] **Step 2: Phát hiện mâu thuẫn nội bộ** — grep các từ khóa số liệu (spread, %, ngày, ×10⁻⁶). Kiểm cùng 1 chỉ số nhiều chỗ có khớp không.

- [ ] **Step 3: Đối chiếu nguồn ngoài cho claim 🔑 quan trọng** — premium Amihud-Mendelson ~2–6 bps/bps; P-S premium 1.5–3%/năm; fire-sale BĐS 10–15%; Treasury spread 3/2020 nới 10×; BTC spread LUNA 0.02→2–5%. Khi không verify được → dùng range, ghi thời điểm.

- [ ] **Step 4: Sửa text + chart data** (cùng bộ số), thêm caveat "ước lượng từ paper, thị trường Mỹ" ở nơi cần.

- [ ] **Step 5: Commit**

---

### Task 11: Fact-check lý thuyết học thuật (Bước 5b longform)

**Files:** Read-only verify

- [ ] **Step 1: Trích xuất mọi claim lý thuyết** — tên + tác giả + năm. (Roll 1984, Amihud 2002, Kyle 1985, P-S 2003, Acharya-Pedersen 2005 LCAPM, Brunnermeier-Pedersen 2009, Sadka 2006, Case-Shiller 2003, Amihud-Mendelson 1986, Campbell-Giglio-Pathak 2011.)

- [ ] **Step 2: Verify tên lý thuyết + tác giả + năm** đối chiếu Wikipedia/journal gốc. Cảnh báo: Amihud 2002 = *Journal of Financial Markets*; P-S 2003 = *Journal of Political Economy*; Kyle 1985 = *Econometrica*; Roll 1984 = *Journal of Finance*.

- [ ] **Step 3: Sửa sai + đảm bảo mỗi lý thuyết có entry trong ol.refs.**

- [ ] **Step 4: Commit**

---

### Task 12: QA kỹ thuật (Bước 6 longform)

**Files:** `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: JS syntax check** — extract `<script>` ra file tạm, `node --check`.

- [ ] **Step 2: No raw placeholder**

```bash
grep -oE "{{[A-Z_0-9]+}}" /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html | sort -u
```
Expected: EMPTY.

- [ ] **Step 3: Canvas count = new Chart count**

```bash
grep -c '<canvas' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
grep -c 'new Chart' /Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html
```
Expected: bằng nhau (= 6).

- [ ] **Step 4: Playwright QA**

```bash
npm install playwright --prefix /tmp/qa-runner 2>/dev/null && npx playwright install chromium 2>/dev/null
node "/Users/bobo/.zcode/skills/longform/scripts/qa_article.js" \
  --url=file:///Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html \
  --output=/tmp/qa-shots-liquidity
```
Expected: `✅ PASS` hoặc `⚠️ PASS WITH WARNINGS`. Nếu lỗi (exit 2) → sửa trước.

- [ ] **Step 5: Commit**

---

### Task 13: Verify nội dung + báo cáo trung thực (Bước 7 longform)

**Files:** `thanh-khoan-tai-san/index.html`

- [ ] **Step 1: Đếm section, chart, table bằng script** (không suy đoán)

```bash
python3 -c "
import re
html=open('/Users/bobo/ZCodeProject/thanh-khoan-tai-san/index.html').read()
print('sections:', len(re.findall(r'<section ', html)))
print('canvas:', html.count('<canvas'))
print('new Chart:', html.count('new Chart'))
print('flow .fd:', html.count('class=\"fd\"'))
print('tbl:', html.count('class=\"tbl\"'))
print('callout:', html.count('class=\"callout'))
print('sup ref:', len(re.findall(r'class=\"ref\">\d+', html)))
"
```

- [ ] **Step 2: Kiểm tra đồng bộ minimap ↔ section** (mỗi section có entry minimap).

- [ ] **Step 3: Kiểm tra disclaimer** (đầu + cuối: framework giáo dục, số Mỹ, không lời khuyên đầu tư).

- [ ] **Step 4: Báo cáo trung thực** — dán output script thực tế, báo "6/6 chart, 9/9 table, N section", nếu thiếu nói thẳng.

- [ ] **Step 5: Trình bày bản đầy đủ cho user** (mở `index.html` qua Vercel preview hoặc file://) + tóm tắt gì đã làm.

---

## Self-Review (chạy sau khi viết xong plan)

**Spec coverage:** Mỗi mục spec (6 phần + 3 phụ lục) → có task. ✅ Phần 1→T2, 2→T3, 3→T4, 4→T5, 5→T6, 6→T7, phụ lục→T8. Chart inventory 7 cái → T4(2), T5(2), T6(2: 1 chart + 1 flow), T7(1). Fact-check → T10/T11. QA → T12/T13.

**Placeholder scan:** Không có "TBD/TODO/similar to". Mọi step có nội dung cụ thể. ✅

**Type consistency:** Section id dùng `s1`–`s6` + `app-a/b/c`. Chart id `c1`–`c7` (c5 là flow, không canvas — verify ở T7 step 3). Ref id 1–19. ✅

**Lưu ý đã thích nghi cho content:** đây là task viết nội dung, không TDD code; thay "test fail→pass" bằng "verify bằng grep/script". Nguyên tắc longform skill (fact-check số liệu + lý thuyết + QA + báo cáo trung thực) được tôn trọng ở T10–T13.
