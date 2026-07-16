#!/usr/bin/env python3
"""Validate dry run v2 against owner's 3-case classification + dry-run gate."""
import sys, os, json, subprocess
ws = sys.argv[1]
checks = []
def chk(name, ok, detail=""): checks.append({"check":name,"pass":ok,"detail":detail})

rr_path = f"{ws}/run-result.json"
if not os.path.exists(rr_path):
    print(json.dumps({"valid":False,"error":"no run-result.json"})); sys.exit(1)
rr = json.load(open(rr_path))

# dry-run gate (owner spec)
chk("genuine_agent_response", rr.get("execution_type")=="genuine_agent", rr.get("execution_type"))
chk("scored_false", rr.get("scored")==False)
chk("verifier_verdict_recorded", rr.get("final_verdict") in ("PASS","FAIL"), f"verdict={rr.get('final_verdict')}")
chk("run_result_schema_valid", "execution_type" in rr and "phase_events" in rr)
# phase6-specific (new)
ph6 = next((e.get("phase6_preflight",{}) for e in rr.get("phase_events",[]) if e.get("phase")=="phase6_dashboard"), {})
chk("phase6_attempts_recorded", bool(ph6.get("attempts")), f"attempts={len(ph6.get('attempts',[]))}")
chk("preflight_executed", "class" in ph6, f"final_class={ph6.get('class')}")
chk("artifact_classification_recorded", "class" in ph6, ph6.get("class"))
chk("inline_template_injected", ph6.get("attempts") and len(ph6.get("attempts",[]))>=1, "attempt-1 ran")
# secret leak
leak = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "check_secret_leak.py"), ws], capture_output=True, text=True)
ld = json.loads(leak.stdout)
chk("no_secret_leak", not ld["secret_leak_detected"], str(ld.get("leaks")))

allok = all(c["pass"] for c in checks)
# 3-case classification (owner directive)
attempts = ph6.get("attempts",[])
recovered = ph6.get("recovered")
final_cls = ph6.get("class")
first_cls = attempts[0].get("artifact_type") if attempts else None
if first_cls == "HTML":
    case_label = "CASE 1: HTML on first attempt (patch solved narration directly)"
elif recovered:
    case_label = "CASE 2: first attempt failed, retry produced HTML (autonomous recovery)"
elif final_cls in ("NARRATION","MALFORMED_HTML","OUTPUT_TRUNCATED","EMPTY"):
    case_label = f"CASE 3: all 3 attempts failed (instrumentation PASS, agent behavior FAIL; final={final_cls})"
else:
    case_label = "UNCLASSIFIED"

print(json.dumps({
  "instrumentation_valid": allok,
  "dry_run_gate_checks": checks,
  "phase6_classification": {
    "case": case_label,
    "first_attempt_class": first_cls,
    "final_class": final_cls,
    "recovered": recovered,
    "total_attempts": len(attempts),
    "attempt_classes": [a.get("artifact_type") for a in attempts],
  },
  "verifier_verdict": rr.get("final_verdict"),
  "recall_pct": rr.get("validator_results",{}).get("recall_pct"),
}, indent=2))
sys.exit(0 if allok else 1)
