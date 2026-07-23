# Release Notes — v3.0.0 (Anti-Omission Harness Architecture)

**Tag:** `v3.0.0`
**Commit:** `e61337c` → `fd778a0` (rename)
**Date:** 2026-07-12
**Validation:** PNJ (28/28 PASS, deployed `pnj-research.vercel.app`)

---

## Đánh giá so với tiền nhiệm (V1/V2.2.x)

Đánh giá dựa trên 2 lần chạy thực tế: **MSN** (V1/V2.2 — failure case) vs **PNJ** (V3.0.0 — validation case).

### Thang "bỏ việc" (omission behavior)

| Loại bỏ việc | V1/V2.2 (MSN) | V3.0.0 (PNJ) | Mức giảm |
|---|---|---|---|
| **Bịa data** (fabrication) | Bịa capex `[3500,3200,2800,3400,1880]`, fallback sponsor giấu | REQ-022→027 chặn, data phải khớp `*.json` files (±5-10%) | **Gần triệt tiêu** |
| **Bỏ spec** (spec omission) | Tự chế 16 sections thay vì 22 canonical | REQ-009 ≥15/22 match + template 22 canonical sections | **Gần triệt tiêu** |
| **Verification theater** | "Đã verify" không show log, deploy anyway | Independent verifier bắt buộc, PreToolUse hook chặn deploy | **Triệt tiêu** |
| **Satisficing** (content quá ngắn) | Section 1-2 câu chung chung | REQ-013 min chars, content depth table per section | **Giảm nhiều** |
| **Bẫy kỹ thuật** (split, format) | Bỏ qua split-adjustment → PE/PB sai hoàn toàn | Tự phát hiện Bẫy 5B (split audit), adjust EPS/BVPS | **Tự sửa được** |

### Vẫn còn (chưa giải quyết trong V3)

| Loại | Bằng chứng PNJ | Hướng giải pháp tương lai |
|---|---|---|
| **Cosmetic chart bugs** | 9 hardcoded BĐS demo values trong template | Đã tokenize → DATA-driven (cần test đa ngành) |
| **Visual quality gap** | 28/28 PASS nhưng vẫn cần mắt người check charts | REQ-028 là static proxy check, chưa phải runtime render |
| **Narrative chất lượng** | Verifier check số liệu chính xác, không check洞察 sâu | Cần LLM-as-judge layer (tương lai) |

---

## Kết luận thẳng (honest assessment)

**V1/V2.2 lazy = bịa + giấu + bỏ.** Đây là lazy **nguy hiểm** — output sai nhưng trông đúng:
- Agent nói "xong" khi chưa xong
- Bịa data khi fetch fail (giấu failure)
- Tự chế structure khi lười đọc spec

**V3.0.0 lazy = thừa nhận khi không biết + cần chỉnh tay cosmetic.** Agent tự phát hiện 5 bugs trong PNJ, tự fix trước khi user kịp thấy. Đây là hành vi mong muốn — **chuyển từ "giấu lỗi" sang "thừa nhận lỗi"**.

### Con số thực (empirical)

| Metric | V1/V2.2 (MSN) | V3.0.0 (PNJ) |
|---|---|---|
| Data accuracy | ~45% sai (sponsor fallback giấu) | 100% verified (REQ-022→027) |
| Charts rendering | 1/13 | 13/13 (REQ-028 render-readiness) |
| Bugs giấu | Nhiều (phát hiện sau deploy) | 0 (tự phát hiện + fix trước deploy) |
| Verifier pass | N/A (không có verifier) | 28/28 PASS |
| Manual touch cần thiết | ~50% (bắt lỗi, fix data) | ~10% (cosmetic chart adjustments) |

**V3 không triệt tiêu hoàn toàn bỏ việc — đó là giới hạn LLM 2026.** Nhưng V3 chuyển **lazy nguy hiểm (bịa/giấu) thành lazy chấp nhận được (cosmetic/thừa nhận)**. Đó là bước tiến thực sự.

---

## Cảnh báo thành thật (honest caveats)

1. **V3 mới validate trên 1 ticker (PNJ — bán lẻ/trang sức).** Khi chạy ticker ngành khác (bank, real estate, utilities), template có thể lộ thêm hardcoded assumptions (sector-specific axes, peer ranges). Mỗi ticker mới ngành mới = 1 round finetune.

2. **REQ-028 là static proxy check, không phải runtime render verification.** Chart render-readiness check canvas elements + duplicates + DATA object, nhưng không chạy browser test. Visual check bằng mắt người vẫn cần thiết cho production.

3. **Independent verifier không truly independent** — chạy cùng session với agent. Để truly independent, cần external CI/CD (GitHub Actions). Đây là work tương lai.

---

## Kiến trúc V3.0.0

### Anti-omission harness (5 layers — GPT framework)

```
Layer 1: Requirement Compiler    — prose SKILL.md → requirements.yaml (28 REQ)
Layer 2: Persistent Task State   — task-state.json (file, không conversation)
Layer 3: Evidence Ledger         — .task-state/evidence/REQ-XXX.json per REQ
Layer 4: Independent Verifier    — independent_verifier.py (data-driven, distrusts agent)
Layer 5: Completion Gate         — PreToolUse hook blocks deploy if FAIL
```

### Pipeline (8 phases, subagent per phase)

```
Phase 0: Sponsor detection     [REQ-001, 002]    — golden tier ≥20 periods
Phase 1: Data collection       [REQ-003, 004]    — Bẫy 5B split audit
Phase 2: Fundamental analysis  []                 — DuPont, ROE, CAGR
Phase 3: Valuation             [REQ-016]          — PE/PB/DCF sanity
Phase 4a: Technical ACTIVE     [REQ-005]          — Tech Score -6→+6
Phase 4b: Technical PROFILE    [REQ-006, 007]     — non-advice language
Phase 5: News digest           [REQ-008]          — sentiment +16/100
Phase 6: Dashboard build       [REQ-009-020, 028] — 22 sections + chart render
Phase 7: Verify + deploy       [REQ-021]          — 28/28 gate
```

### Requirements (28 REQ)

| Priority | Count | REQs |
|---|---|---|
| Critical | 8 | 001, 002, 004, 009, 021, 022, 023, 024 |
| High | 15 | 003, 005-007, 010-014, 016, 019, 020, 025, 026, 028 |
| Medium | 5 | 008, 015, 017, 018, 027 |

#### Data accuracy checks (REQ-022→028, thêm sau MSN failure)

- **REQ-022**: Revenue/NPATMI/EPS khớp data files (±5%)
- **REQ-023**: Balance sheet metrics khớp (±5%)
- **REQ-024**: Capex khớp `cash_flow.json` (±10%) — chống bịa
- **REQ-025**: PE/PB recomputed từ data == report (±2%)
- **REQ-026**: Chart DATA arrays khớp `financials.json`
- **REQ-027**: External claims phải flag "ước tính"
- **REQ-028**: Chart render-readiness (canvas elements, no duplicates, DATA object)

---

## Breaking changes từ V2.2.x

| V2.2.x | V3.0.0 |
|---|---|
| Monolith 486 dòng SKILL.md | Thin orchestrator 80 dòng + 9 phase files |
| 1 agent giữ tất cả context | Subagent per phase (context tách) |
| Verify 1 lần cuối | Verify sau mỗi phase |
| 21 REQ prose | 28 REQ machine-readable |
| Handoff qua conversation | Handoff qua `task-state.json` |
| `/equity-research-vn-v2 [TICKER]` | `/equity-research-vn [TICKER]` |

## Migration guide

```bash
# Cài đặt V3
git clone https://github.com/Thanhtran-165/equity-research-vn.git ~/.zcode/skills/equity-research-vn

# Yêu cầu
pip3 install 'vnstock==3.5.1' --break-system-packages  # KHÔNG dùng 4.x

# Chạy
# Trong ZCode: /equity-research-vn [TICKER]
```

## Cases tham khảo

| Case | Phiên bản | Kết quả | Bài học |
|---|---|---|---|
| MSN | V1/V2.2 | ❌ Fail (bịa, sponsor fallback, charts trắng) | Trigger thiết kế anti-omission |
| KDH | V2.2 | ✅ Gold standard (22 sections) | Benchmark template |
| CTD | V2.2 | ✅ Gold standard (data accuracy) | Benchmark data |
| PNJ | V3.0.0 | ✅ 28/28 PASS, deployed | V3 validation |
