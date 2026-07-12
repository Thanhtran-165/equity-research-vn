# Equity Research VN v3.0 — Anti-Omission Harness Architecture

Pipeline 8 phases phân tích cổ phiếu Việt Nam — từ sponsor data đến dashboard deploy được.

## Kiến trúc v3.0 (breaking change từ v2.2.x)

| v2.2.x (cũ) | v3.0 (này) |
|---|---|
| Monolith 486 dòng SKILL.md | Thin orchestrator 80 dòng + 9 phase files |
| 1 agent giữ tất cả context | Subagent per phase (context tách) |
| Verify 1 lần cuối | Verify sau mỗi phase |
| 21 REQ prose | 28 REQ machine-readable (requirements.yaml) |
| Handoff qua conversation | Handoff qua task-state.json |
| Bỏ sót ở handoff = hên xui | Independent verifier chặn sớm |

## Anti-omission harness (5 layers)

Dựa trên GPT framework cho AI agent anti-omission:

1. **Requirement Compiler** — prose SKILL.md → `requirements.yaml` (28 REQ, machine-readable)
2. **Persistent Task State** — trạng thái trong FILE (`task-state.json`), không trong conversation
3. **Evidence Ledger** — mỗi REQ có evidence file trong `.task-state/evidence/`
4. **Independent Verifier** — `independent_verifier.py` chạy data-driven checks, không tin agent claims
5. **Deterministic Completion Gate** — PreToolUse hook chặn `vercel deploy` nếu verifier FAIL

## Pipeline (8 phases)

```
Phase 0: Sponsor detection     → phases/phase0-sponsor.md     [REQ-001, 002]
Phase 1: Data collection       → phases/phase1-data.md        [REQ-003, 004]
Phase 2: Fundamental analysis  → phases/phase2-fundamental.md []
Phase 3: Valuation             → phases/phase3-valuation.md   [REQ-016]
Phase 4a: Technical ACTIVE     → phases/phase4a-tech-active.md [REQ-005]
Phase 4b: Technical PROFILE    → phases/phase4b-tech-profile.md [REQ-006, 007]
Phase 5: News digest           → phases/phase5-news.md        [REQ-008]
Phase 6: Dashboard build       → phases/phase6-dashboard.md   [REQ-009-020, 028]
Phase 7: Verify + deploy       → phases/phase7-deploy.md      [REQ-021]
```

## Requirements (28 REQ)

| Priority | REQs | Count |
|----------|------|-------|
| Critical | 001, 002, 004, 009, 021, 022, 023, 024 | 8 |
| High | 003, 005-007, 010-014, 016, 019, 020, 025, 026, 028 | 15 |
| Medium | 008, 015, 017, 018, 027 | 5 |

### Data accuracy checks (REQ-022→028, thêm sau MSN failure)

- **REQ-022**: Revenue/NPATMI/EPS khớp data files (±5%)
- **REQ-023**: Balance sheet metrics khớp (±5%)
- **REQ-024**: Capex khớp cash_flow.json (±10%) — chống bịa
- **REQ-025**: PE/PB recomputed từ data == report (±2%)
- **REQ-026**: Chart DATA arrays khớp financials.json
- **REQ-027**: External claims phải flag "ước tính"
- **REQ-028**: Chart render-readiness (canvas elements, no duplicates, DATA object)

## Cách chạy

```bash
# 1. Init task state
python3 scripts/init_task_state.py [TICKER] [WORK_DIR]

# 2. Chạy từng phase (agent đọc phases/phaseN-xxx.md)
#    Mỗi phase: execute → ghi task-state.json → verifier check REQ

# 3. Final verify
python3 scripts/independent_verifier.py [TICKER] [OUTPUT].html
# PASS 28/28 → deploy OK
# FAIL → block, fix trước
```

## Benchmark cases

- **KDH**: Gold standard report (22 canonical sections)
- **CTD**: Gold standard (data accuracy reference)
- **PNJ**: v3.0 validation (28/28 PASS, deployed pnj-research.vercel.app)
- **MSN**: v2.2 failure case (sponsor fallback, bịa capex, charts trắng)

## Lessons learned ( tích lũy từ 6 failure cases)

Xem `equity-research-vn/lessons/` cho taxonomy 10 failure modes (FM-01→FM-10).

## License

MIT — xem [LICENSE](LICENSE)

## Disclaimer

Xem [DISCLAIMER.md](DISCLAIMER.md) — báo cáo phân tích, không phải lời khuyên đầu tư.
