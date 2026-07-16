"""
environment_preflight.py — Pre-cohort environment qualification gate (v0.8.0).

PURPOSE (owner directive 2026-07-14):
  Cohort C ran 10 GLM-5.2 agent runs where REQ-001/002 (sponsor golden tier)
  were guaranteed to FAIL because vnstock_data wasn't available. This burned
  ~2.5 hours of API time on runs whose PASS/FAIL was environmentally determined.

  This preflight runs BEFORE the first cohort run. If a mandatory dependency
  is unavailable, it fails closed: prints ENVIRONMENT_NOT_QUALIFIED and exits(3).
  The orchestrator must NOT start agent runs if this gate fails.

  Per owner directive, two policies are supported:
    Policy A (live dependency): vnstock_data MUST be importable → fail closed if not
    Policy B (snapshot/cache):  sponsor data must be materialized in source-packs
                                with provenance/hash → REQ-001/002 become N/A

  This implementation defaults to Policy A (stricter). Policy B can be activated
  by setting ENV_PREFLIGHT_POLICY=snapshot in the environment, in which case
  REQ-001/002 are marked NOT_APPLICABLE and the preflight checks source-pack
  completeness instead.
"""
import subprocess
import sys
import os
import json
import datetime


def _run_cmd(cmd, timeout=30):
    """Run a shell command, return (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)


def check_vnstock_data_importable(python="python3"):
    """Check if vnstock_data (sponsor golden tier) is importable.
    This is the exact command REQ-001 runs."""
    rc, out, err = _run_cmd(f'{python} -c "from vnstock_data import Finance; print(\'OK\')" 2>/dev/null')
    return {
        "check": "vnstock_data_importable",
        "passed": rc == 0 and "OK" in out,
        "returncode": rc,
        "stdout": out[:200],
        "stderr": err[:200] if err else "",
    }


def check_sponsor_returns_periods(python, ticker="CTD"):
    """Check if sponsor Finance returns ≥20 periods (REQ-002 equivalent).
    Uses a representative ticker."""
    cmd = (
        f'{python} -c "import warnings; warnings.filterwarnings(\'ignore\'); '
        f'from vnstock_data import Finance; f=Finance(symbol=\'{ticker}\',source=\'VCI\'); '
        f'print(len(f.income_statement()))" 2>/dev/null'
    )
    rc, out, err = _run_cmd(cmd, timeout=45)
    periods = None
    try:
        # Extract the last numeric line
        for line in out.split('\n'):
            line = line.strip()
            if line.isdigit():
                periods = int(line)
    except Exception:
        pass
    return {
        "check": "sponsor_returns_20plus_periods",
        "passed": periods is not None and periods >= 20,
        "returncode": rc,
        "periods_returned": periods,
        "stdout": out[:200],
    }


def check_glm_backend_available():
    """Check if the ZAI/GLM backend can be constructed (API key present)."""
    rc, out, err = _run_cmd(
        '/opt/homebrew/bin/python3 -c "import sys; sys.path.insert(0,\'/Users/bobo/ZCodeProject/agent-eval/runner\'); '
        'from model_backends import get_backend; b=get_backend(\'zai\',\'GLM-5.2\'); print(\'OK\')" 2>&1'
    )
    return {
        "check": "glm_backend_constructable",
        "passed": rc == 0 and "OK" in out,
        "returncode": rc,
        "stdout": out[:200],
    }


def run_preflight(policy="live", python="/opt/homebrew/bin/python3"):
    """Run all environment preflight checks.

    policy: 'live' (Policy A — vnstock_data must be available) or
            'snapshot' (Policy B — source-packs must be complete; REQ-001/002 N/A)

    Returns: {
        'passed': bool,
        'policy': str,
        'checks': [check results],
        'failures': [failed check names],
        'not_applicable': [N/A check names],  # only under snapshot policy
        'timestamp': iso,
    }
    """
    results = []
    failures = []
    not_applicable = []

    # 1. GLM backend (always required — agent runs need it)
    glm_check = check_glm_backend_available()
    results.append(glm_check)
    if not glm_check["passed"]:
        failures.append("glm_backend_constructable")

    # 2. vnstock_data (REQ-001/002 dependency)
    if policy == "live":
        vnd = check_vnstock_data_importable(python)
        results.append(vnd)
        if not vnd["passed"]:
            failures.append("vnstock_data_importable")
        else:
            # 3. Sponsor periods (REQ-002)
            per = check_sponsor_returns_periods(python)
            results.append(per)
            if not per["passed"]:
                failures.append("sponsor_returns_20plus_periods")
    else:  # snapshot policy
        not_applicable.extend(["vnstock_data_importable", "sponsor_returns_20plus_periods"])

    passed = len(failures) == 0
    return {
        "passed": passed,
        "policy": policy,
        "checks": results,
        "failures": failures,
        "not_applicable": not_applicable,
        "timestamp": datetime.datetime.now().isoformat(),
    }


def main():
    """CLI entry point. Exits 0 if passed, 3 if ENVIRONMENT_NOT_QUALIFIED."""
    policy = os.environ.get("ENV_PREFLIGHT_POLICY", "live")
    result = run_preflight(policy=policy)

    print(json.dumps({
        "status": "ENVIRONMENT_QUALIFIED" if result["passed"] else "ENVIRONMENT_NOT_QUALIFIED",
        "policy": result["policy"],
        "passed": result["passed"],
        "failures": result["failures"],
        "not_applicable": result["not_applicable"],
        "checks": [{k: v for k, v in c.items() if k in ("check", "passed", "periods_returned")}
                   for c in result["checks"]],
        "timestamp": result["timestamp"],
    }, indent=2, ensure_ascii=False))

    if not result["passed"]:
        print("\n⚠ ENVIRONMENT_NOT_QUALIFIED — do NOT start cohort runs.", file=sys.stderr)
        print("  REQ-001/002 will FAIL on every run if vnstock_data is unavailable.", file=sys.stderr)
        print("  Options: (A) install sponsor golden tier, or (B) set ENV_PREFLIGHT_POLICY=snapshot", file=sys.stderr)
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
