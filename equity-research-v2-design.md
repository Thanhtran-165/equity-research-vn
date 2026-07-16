# Equity Research VN v2 — Architecture Design

> **Principle**: "Thin orchestrator + subagent per phase"
> Mỗi phase chạy trong context tách biệt. Giao tiếp qua file (task-state.json).
> Agent không "giữ trong đầu" — đọc file trạng thái.

---

## So sánh v1 → v2

| | v1 (hiện tại) | v2 (mới) |
|---|---|---|
| Orchestrator | 486 dòng prose monolith | ~80 dòng thin coordinator |
| Agent context | 1 session giữ tất cả | Mỗi phase = subagent riêng |
| Giao tiếp | Conversation (mất khi compact) | task-state.json + evidence/ |
| Verification | End-pipeline (enforce_spec.sh) | Per-phase checkpoint |
| Rủi ro bỏ sót | Cao (quên details xa) | Thấp (mỗi phase chỉ biết spec của nó) |

---

## Cấu trúc thư mục v2

```
~/.zcode/skills/equity-research-vn-v2/
  SKILL.md                      Thin orchestrator (~80 dòng)
  requirements.yaml             Requirement matrix (21 REQ — migrate từ v1)
  requirements-phase-map.yaml   REQ → phase mapping
  
  phases/                       ← MỚI: 1 file prompt per phase
    phase0-sponsor.md           Prompt cho subagent Phase 0
    phase1-data.md              Prompt cho subagent Phase 1
    phase2-fundamental.md       Prompt cho subagent Phase 2
    phase3-valuation.md         Prompt cho subagent Phase 3
    phase4a-tech-active.md      Prompt cho subagent Phase 4a
    phase4b-tech-profile.md     Prompt cho subagent Phase 4b
    phase5-news.md              Prompt cho subagent Phase 5
    phase6-dashboard.md         Prompt cho subagent Phase 6
    phase7-deploy.md            Prompt cho subagent Phase 7
  
  scripts/
    init_task_state.py          (migrate từ v1)
    run_phase.py                ← MỚI: runner — spawn subagent per phase
    independent_verifier.py     (migrate từ v1)
    measure_kpi.py              (migrate từ v1)
    enforce_spec.sh             (migrate, update paths v2)
  
  _viz-shared/                  (symlink hoặc copy từ v1)
  vn-research-dashboard/        (sub-skill, migrate template mới)
  vn-technical-analysis/        (sub-skill, copy từ v1)
  vn-financial-data-collector/  (sub-skill, copy từ v1)
  ...                           (các sub-skill khác, copy từ v1)
```

---

## Thin Orchestrator SKILL.md (~80 dòng)

Chỉ chứa:
1. **Trigger** (khi nào invoke)
2. **Pipeline overview** (8 phases, thứ tự)
3. **Cách chạy** (init task-state → run_phase per phase → verify)
4. **Phase prompt path** (`phases/phaseN-xxx.md`)

KHÔNG chứa:
- Lessons learned (chuyển sang `phases/phaseN-xxx.md` liên quan)
- Quality Gate detail (chuyển sang verifier)
- Sub-skill spec (chuyển sang sub-skill SKILL.md)

---

## Phase Prompt File (ví dụ: phase0-sponsor.md)

```markdown
# Phase 0: Sponsor Package Detection

Bạn là subagent Phase 0. Context của bạn HOÀN TOÀN tách biệt.

## Input
Đọc: [WORK_DIR]/.task-state/task-state.json (field: ticker)

## Nhiệm vụ
1. Check ~/.vnstock/auth_state.json → tier
2. Test `from vnstock_data import Finance`
3. Nếu fail → fix bằng `pip3 install 'vnstock==3.5.1'`
4. Verify sponsor data ≥20 kỳ

## Output — ghi vào task-state.json
Cập nhật:
  phases.phase0_sponsor.status = "completed"
  phases.phase0_sponsor.result = {tier, periods, sponsor_ok}

## Requirements (REQ cho phase này)
- REQ-001: Sponsor import OK
- REQ-002: Sponsor data ≥20 kỳ

## KHÔNG được
- Fallback community tier
- Skip nếu fail — phải fix

## Không cần biết
- Phase 6 dashboard spec (không phải việc của bạn)
- Section map canonical (không phải việc của bạn)
- Template tokens (không phải việc của bạn)
```

---

## run_phase.py — Subagent Runner

```python
"""
Spawn subagent per phase. Mỗi subagent:
1. Đọc phases/phaseN-xxx.md (prompt riêng)
2. Đọc task-state.json (input từ phase trước)
3. Execute
4. Ghi output vào task-state.json + evidence/
5. Verifier check REQ cho phase đó

Parent orchestrator chỉ gọi run_phase.py lần lượt.
"""
```

---

## Verifier per-phase (không chỉ end-pipeline)

```
Phase 0 done → verifier check REQ-001, REQ-002
  ↓ FAIL → BLOCK, không cho qua Phase 1
Phase 1 done → verifier check REQ-003, REQ-004
  ↓ FAIL → BLOCK
...
Phase 6 done → verifier check REQ-009 đến REQ-020
  ↓ FAIL → BLOCK
Phase 7 → hook chặn deploy nếu bất kỳ phase nào fail
```

**Khác v1**: v1 verify 1 lần cuối. v2 verify **sau mỗi phase** → bắt lỗi sớm, không propagate.

---

## Giao tiếp giữa phases (task-state.json)

```json
{
  "ticker": "MSN",
  "current_phase": "phase3_valuation",
  "phases": {
    "phase0_sponsor": {
      "status": "completed",
      "result": {"tier": "golden", "periods": 41, "sponsor_ok": true}
    },
    "phase1_data": {
      "status": "completed",
      "result": {
        "revenue": [88628767000000, 76189225000000, ...],
        "net_profit": [8562882000000, 3566996000000, ...],
        "data_source": "sponsor"
      }
    },
    "phase2_fundamental": {
      "status": "completed",
      "result": {"roe": 9.11, "dupont": {...}}
    },
    "phase3_valuation": {
      "status": "in_progress"
    }
  }
}
```

**Phase 3 subagent chỉ cần đọc**:
- task-state.json (lấy data từ Phase 1)
- phases/phase3-valuation.md (spec của nó)
- requirements.yaml REQ-016 (DCF sanity)

**KHÔNG cần đọc**: Phase 0 sponsor spec, Phase 6 dashboard spec, 486 dòng orchestrator.

---

## Rollout plan (GPT 4 cấp)

1. **Shadow**: v2 chạy song song v1. So sánh output. Không block.
2. **Advisory**: v2 chạy, warn nếu lệch. V1 vẫn deploy được.
3. **Enforced**: v2 block deploy nếu fail. V1 retire.
4. **Production**: V1 deleted. V2 default.
