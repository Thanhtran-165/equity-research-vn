#!/usr/bin/env python3
"""Test matrix cho predeploy-gate.sh (P0-05 — Wave 1).

Chạy hook với input PreToolUse JSON giả lập, kiểm EXIT CODE thực theo từng mode:
- shadow  : mọi tình huống allow (exit 0)
- advisory: mọi tình huống allow (exit 0) + warning
- enforced: verifier FAIL / thiếu artifact / ticker không xác định / verifier mất → BLOCK (exit 2)
Chạy: python3 scripts/tests/test_predeploy_gate.py
"""
import json, os, shutil, subprocess, sys, tempfile

HOOK = os.path.expanduser("~/.zcode/hooks/predeploy-gate.sh")
SKILL = os.path.expanduser("~/.zcode/skills/equity-research-vn")
VERIFIER = os.path.join(SKILL, "scripts", "independent_verifier.py")

def run_hook(mode, project_dir, command="npx vercel deploy --prod"):
    env = dict(os.environ)
    env["EQUITY_GATE_MODE"] = mode
    env["ZCODE_PROJECT_DIR"] = project_dir
    payload = json.dumps({"tool_input": {"command": command}})
    r = subprocess.run(["bash", HOOK], input=payload, capture_output=True,
                       text=True, env=env, timeout=120)
    return r.returncode, r.stderr

def make_failing_report(work):
    """Tạo report FAIL verifier: copy report CTD rồi chèn meta nội bộ (REQ-070 fail)."""
    import re
    src = "/Users/bobo/ZCodeProject/ctd-v4flash/CTD_Complete_Report.html"
    h = open(src).read()
    m = re.search(r'(<section id="sec-biz".*?<p>)', h, re.DOTALL)
    h = h[:m.end()] + 'lỗi cố ý theo financials.json phase 3 ' + h[m.end():]
    with open(os.path.join(work, "CTD_Complete_Report.html"), "w") as f:
        f.write(h)

def run():
    work = tempfile.mkdtemp(prefix="gate_test_")
    fails = []
    try:
        # Case A: project đầy đủ context (report + data + .task-state) → verifier PASS
        shutil.copytree("/Users/bobo/ZCodeProject/ctd-v4flash", work, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
        for mode in ("shadow", "advisory", "enforced"):
            code, _ = run_hook(mode, work)
            if code != 0:
                fails.append(f"[PASS report] {mode}: exit {code} (kỳ vọng 0)")

        # Case B: project có report FAIL (chèn meta → REQ-070 fail) — copy full context
        work_b = tempfile.mkdtemp(prefix="gate_fail_")
        shutil.copytree("/Users/bobo/ZCodeProject/ctd-v4flash", work_b, dirs_exist_ok=True)
        make_failing_report(work_b)
        for mode in ("shadow", "advisory"):
            code, err = run_hook(mode, work_b)
            if code != 0:
                fails.append(f"[FAIL report] {mode}: exit {code} (kỳ vọng 0 — allow+log)")
        code, err = run_hook("enforced", work_b)
        if code != 2:
            fails.append(f"[FAIL report] enforced: exit {code} (kỳ vọng 2 — BLOCK)")
        if "DEPLOY BLOCKED" not in err:
            fails.append("enforced: thiếu thông báo DEPLOY BLOCKED")

        # Case C: project KHÔNG có HTML (thiếu artifact)
        work_c = tempfile.mkdtemp(prefix="gate_empty_")
        for mode in ("shadow", "advisory"):
            code, _ = run_hook(mode, work_c)
            if code != 0:
                fails.append(f"[no artifact] {mode}: exit {code} (kỳ vọng 0)")
        code, err = run_hook("enforced", work_c)
        if code != 2:
            fails.append(f"[no artifact] enforced: exit {code} (kỳ vọng 2 — fail closed)")

        # Case D: command không phải vercel → hook không kích hoạt (exit 0 mọi mode)
        work_d = tempfile.mkdtemp(prefix="gate_novercel_")
        code, _ = run_hook("enforced", work_d, command="npm run build")
        if code != 0:
            fails.append(f"[non-vercel] enforced: exit {code} (kỳ vọng 0 — ngoài phạm vi)")

        # Case E: verifier mất → enforced block
        work_e = tempfile.mkdtemp(prefix="gate_nover_")
        shutil.copy("/Users/bobo/ZCodeProject/ctd-v4flash/CTD_Complete_Report.html",
                    os.path.join(work_e, "CTD_Complete_Report.html"))
        backup = VERIFIER + ".bak_wave1"
        os.rename(VERIFIER, backup)
        try:
            for mode in ("shadow", "advisory"):
                code, _ = run_hook(mode, work_e)
                if code != 0:
                    fails.append(f"[no verifier] {mode}: exit {code} (kỳ vọng 0)")
            code, err = run_hook("enforced", work_e)
            if code != 2:
                fails.append(f"[no verifier] enforced: exit {code} (kỳ vọng 2)")
        finally:
            os.rename(backup, VERIFIER)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if fails:
        print("❌ DEPLOY GATE TEST FAIL:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("✅ DEPLOY GATE OK — matrix 3 mode × 5 tình huống:")
    print("   - PASS report: allow mọi mode ✓")
    print("   - FAIL report: shadow/advisory allow+log, enforced BLOCK (exit 2) ✓")
    print("   - Thiếu artifact: enforced fail-closed ✓")
    print("   - Non-vercel command: ngoài phạm vi ✓")
    print("   - Verifier mất: enforced block ✓")

if __name__ == "__main__":
    run()
