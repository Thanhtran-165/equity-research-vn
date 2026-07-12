#!/usr/bin/env python3
"""
run_phase.py — Phase runner cho equity-research-vn-v2

Thin orchestrator: chạy từng phase tuần tự, verify sau mỗi phase.

Mỗi phase:
  1. Đọc phases/phaseN-xxx.md (prompt)
  2. Agent (subagent hoặc same-agent) execute theo prompt
  3. Verifier check REQ cho phase đó
  4. FAIL → BLOCK, không qua phase tiếp

Usage:
  python3 run_phase.py [TICKER] [WORK_DIR] [PHASE]
  python3 run_phase.py MSN /path/to/work phase0_sponsor
  python3 run_phase.py MSN /path/to/work --all

Output: cập nhật task-state.json + evidence/
"""
import json, sys, os, subprocess, yaml

TICKER = sys.argv[1] if len(sys.argv) > 1 else "UNKNOWN"
WORK_DIR = sys.argv[2] if len(sys.argv) > 2 else "."
PHASE_ARG = sys.argv[3] if len(sys.argv) > 3 else "--all"

SKILL_DIR = os.path.expanduser("~/.zcode/skills/equity-research-vn-v2")
STATE_DIR = os.path.join(WORK_DIR, ".task-state")
STATE_FILE = os.path.join(STATE_DIR, "task-state.json")
PHASE_MAP_FILE = os.path.join(SKILL_DIR, "requirements-phase-map.yaml")

PHASES = [
    ("phase0_sponsor", "phases/phase0-sponsor.md"),
    ("phase1_data", "phases/phase1-data.md"),
    ("phase2_fundamental", "phases/phase2-fundamental.md"),
    ("phase3_valuation", "phases/phase3-valuation.md"),
    ("phase4a_tech_active", "phases/phase4a-tech-active.md"),
    ("phase4b_tech_profile", "phases/phase4b-tech-profile.md"),
    ("phase5_news", "phases/phase5-news.md"),
    ("phase6_dashboard", "phases/phase6-dashboard.md"),
    ("phase7_deploy", "phases/phase7-deploy.md"),
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return None

def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def read_phase_prompt(prompt_path):
    full_path = os.path.join(SKILL_DIR, prompt_path)
    if not os.path.exists(full_path):
        return f"Phase prompt not found: {full_path}"
    with open(full_path) as f:
        return f.read()

def verify_phase(phase_id):
    """Run verifier for specific phase REQs."""
    if not os.path.exists(PHASE_MAP_FILE):
        print("⚠️ No phase map, skipping per-phase verify")
        return True

    with open(PHASE_MAP_FILE) as f:
        phase_map = yaml.safe_load(f) or {}

    phase_reqs = phase_map.get("phase_requirements", {}).get(phase_id, {}).get("reqs", [])
    if not phase_reqs:
        print(f"  ℹ️  Phase {phase_id} has no REQs to verify")
        return True

    # Run full verifier, then filter results for this phase
    state = load_state()
    artifact = state.get("artifact_path") if state else None

    # For pre-deploy phases (0-5), artifact may not exist yet
    # Run command-based REQs only
    req_file = os.path.join(SKILL_DIR, "requirements.yaml")
    with open(req_file) as f:
        req_data = yaml.safe_load(f)

    all_pass = True
    for req in req_data.get("requirements", []):
        if req["id"] not in phase_reqs:
            continue
        method = req["verification"]["method"]
        if method == "command":
            cmd = req["verification"]["command"].replace("$TICKER", TICKER).replace("$REPORT", artifact or "")
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                passed = result.returncode == req["verification"].get("expect_exit", 0)
                if not passed:
                    print(f"  ❌ {req['id']} FAIL: {req['text'][:60]}")
                    all_pass = False
                else:
                    print(f"  ✅ {req['id']} PASS: {req['text'][:60]}")
            except Exception as e:
                print(f"  ❌ {req['id']} ERROR: {e}")
                all_pass = False
        else:
            print(f"  ⏭️  {req['id']} SKIP (artifact check, will verify at Phase 6/7)")

    return all_pass


def run_single_phase(phase_id, prompt_path):
    """Run one phase: print prompt for agent + verify after."""
    print(f"\n{'='*60}")
    print(f"  PHASE: {phase_id}")
    print(f"{'='*60}\n")

    prompt = read_phase_prompt(prompt_path)
    prompt = prompt.replace("[TICKER]", TICKER).replace("[WORK_DIR]", WORK_DIR)

    print("📋 PHASE PROMPT (agent executes this):")
    print("─" * 60)
    print(prompt)
    print("─" * 60)

    # Check if phase already completed
    state = load_state()
    if state:
        phase_status = state.get("phases", {}).get(phase_id, {}).get("status", "pending")
        if phase_status == "completed":
            print(f"\n✅ Phase {phase_id} already completed")

    # Verify phase REQs
    print(f"\n🔍 VERIFYING Phase {phase_id}...")
    passed = verify_phase(phase_id)

    if passed:
        print(f"\n✅ Phase {phase_id} VERIFIED — ready for next phase")
        return True
    else:
        print(f"\n❌ Phase {phase_id} FAILED — fix before proceeding")
        return False


def main():
    state = load_state()
    if not state:
        print("❌ Task state not found. Run: python3 scripts/init_task_state.py [TICKER] [WORK_DIR]")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Equity Research v2 — {TICKER}")
    print(f"  Work dir: {WORK_DIR}")
    print(f"  Current phase: {state.get('phase', 'init')}")
    print(f"{'='*60}")

    if PHASE_ARG == "--all":
        # Run all phases in sequence
        for phase_id, prompt_path in PHASES:
            passed = run_single_phase(phase_id, prompt_path)
            if not passed:
                print(f"\n🛑 PIPELINE BLOCKED at {phase_id}")
                print(f"   Fix issues, then re-run: python3 run_phase.py {TICKER} {WORK_DIR} {phase_id}")
                sys.exit(1)
        print(f"\n🎉 ALL PHASES COMPLETE — report ready for deploy")
    else:
        # Run single phase
        phase_found = False
        for phase_id, prompt_path in PHASES:
            if phase_id == PHASE_ARG or phase_id.startswith(PHASE_ARG):
                phase_found = True
                passed = run_single_phase(phase_id, prompt_path)
                if not passed:
                    sys.exit(1)
                break
        if not phase_found:
            print(f"❌ Unknown phase: {PHASE_ARG}")
            print(f"   Available: {[p[0] for p in PHASES]}")
            sys.exit(1)


if __name__ == "__main__":
    main()
