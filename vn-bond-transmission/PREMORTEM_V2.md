# 🔍 Premortem Vòng 2: vn-bond-transmission (sau fix P0 + đổi thesis)

**Phase**: mid-build (post-fix)
**Input**: OUTLINE revised (12 chương regime-dependent) + Ch1-3 updated + CPI fixed + rolling corr data
**Thesis mới**: "Mối quan hệ trái phiếu↔4 biến đảo dấu theo regime chính sách"

**Context budget**: Đã đọc hết. Premortem vòng 1 fix 2 P0 → map đổi → blind spot mới.

---

## 🔴 Lens A — Assumption stress-test (thesis MỚI)

### A.1 Chỉ 2/5 regime có corr statistically significant — 3 regime corr CI bao qua 0
- **Claim**: Ch1 + thesis — "5 regime có corr khác nhau"
- **Stress test**: Fisher z-transform 95% CI cho mỗi regime:
  - R1 (2014-16): corr +0.04, CI **−0.37 đến +0.44** → KHÔNG significant
  - R2 (2017-19): corr −0.66, CI −0.82 đến −0.40 → ✅ significant
  - R3 (COVID): corr +0.16, CI **−0.18 đến +0.46** → KHÔNG significant
  - R4 (thắt): corr −0.08, CI **−0.68 đến +0.58** (n=10 quá ít) → KHÔNG significant
  - R5 (nới): corr +0.86, CI +0.73 đến +0.93 → ✅ significant
- **Why weak**: Thesis nói "5 regime khác nhau" nhưng thực ra chỉ **2/5** (R2 âm, R5 dương) đủ data để claim. 3 regime còn lại CI bao qua 0 — không thể nói corr khác 0.
- **If false, what breaks**: Ch1 KPI "-0.96 đến +0.87" + claim "5 regime" thuyết phục nhưng misleading — đọc kỹ sẽ thấy 3 regime "không có quan hệ rõ" chứ không "corr khác". Reviewer sẽ flag: "bài over-claim 5 regime khi chỉ 2 significant".
- **Fix hint**: Đổi frame từ "5 regime khác nhau" → "2 regime có mối quan hệ thật (R2 âm, R5 dương), 3 regime noise". Giữ 5 chương chronological nhưng phân biệt rõ regime nào "có signal" vs "noise".

### A.2 Regime R4 (thắt 2022) chỉ 10 tháng — quá ít cho corr
- **Claim**: Ch7 — R4 corr = −0.08
- **Why weak**: n=10. Corr với n=10 có CI cực rộng (−0.68 đến +0.58). Không thể claim gì từ 10 điểm.
- **Fix hint**: Ch7 nên nói "data quá ít (10 tháng) để kết luận" thay vì claim corr −0.08.

---

## 🟡 Lens B — Silent-failure surface

### B.1 Regime boundary có thể cherry-picked
- **Stress test**: Dịch boundary R4/R5 ±3 tháng → corr R5 không đổi (+0.86), nhưng R4 nhảy từ −0.08 → −0.27.
- **Why weak**: R4 corr nhạy với việc chọn điểm cắt. Nếu chọn boundary khác → R4 "nhìn" khác.
- **Good news**: R5 (+0.86) robust với boundary — không cherry-picked. Chỉ R4 yếu.
- **Fix hint**: Ch7 dùng rolling corr thay vì point estimate, tránh boundary dependency.

### B.2 Rolling corr 61% thời gian âm, 39% dương — không "đảo liên tục" như nghe
- **Claim**: Ch1 thesis nghe "đảo dấu liên tục"
- **Thực tế**: Chỉ 4 sign-flips trong 113 điểm (rolling 24M). 61% thời gian âm.
- **Fix hint**: Ch1 nên nói "corr dao động qua 0 nhiều lần" thay vì "đảo dấu" — chính xác hơn.

---

## 🟢 Lens C — Right-problem check

Thesis regime-dependent **đúng hướng hơn** "biến trung tâm" — khiêm tốn, cụ thể. Nhưng có 1 vấn đề premise:

**"5 regime" có thực sự là cách tốt nhất để cắt data không?** Boundary dựa vào SBV decisions (cut/hike) — nhưng SBV decisions phản ứngFed/DXY/lạm phát. Có thể "regime" thật là **DXY regime** (USD mạnh/yếu) hoặc **Fed regime** (hike/cut), không phải SBV regime. Nếu đổi sang DXY regime → corr có thể stable hơn.

→ Đây là câu hỏi mở cho nghiên cứu tiếp, không phải bug. Thesis hiện tại (SBV regime) đủ hợp lý để publish.

---

## 📊 Scorecard vòng 2

- **P0 bugs**: 0 (vòng 1 đã fix hết)
- **P1 bugs**: 2 (A.1 over-claim regime, A.2 R4 n=10)
- **P2 bugs**: 2 (B.1 boundary, B.2 "đảo dấu" wording)
- **Stop signal**: **DỪNG được** — 0 P0, ≤2 P1. Bug còn lại là polish wording + 1 caveat về n=10.
- **Recommend**: Không cần premortem vòng 3. Fix A.1 (frame 2 significant vs 3 noise) + A.2 (R4 caveat n=10) rồi viết tiếp.

## Cross-skill patterns
N/A (project độc lập).

---

## Honest closing

Thesis regime-dependent **vững hơn** "biến trung tâm" — nhưng over-claim nhẹ ở "5 regime" khi thực ra chỉ 2 significant. Fix duy nhất cần trước khi viết 9 chương còn lại: **Ch1 phân biệt rõ "2 regime có signal (R2 âm, R5 dương)" vs "3 regime noise"** — tránh reviewer bác "Simpson's paradox của chính Simpson's paradox".

Sau fix đó + R4 caveat, bài sẵn sàng viết tiếp. Premortem vòng 3 không cần thiết (stop signal triggered).
