#!/usr/bin/env python3
"""Validate the final dry run meets all §IV instrumentation criteria."""
import sys, os, json, subprocess
ws = sys.argv[1]
rr_path = f"{ws}/run-result.json"
checks = []
def check(name, ok, detail=""): checks.append({"check":name,"pass":ok,"detail":detail})
if not os.path.exists(rr_path):
    print(json.dumps({"valid":False,"checks":[{"check":"run-result exists","pass":False}]})); sys.exit(1)
rr = json.load(open(rr_path))
check("execution_type==genuine_agent", rr.get("execution_type")=="genuine_agent", rr.get("execution_type"))
check("scored==false (dry run)", rr.get("scored")==False)
vr = rr.get("validator_results",{})
check("verifier_invoked", vr.get("exit_code") is not None)
check("verifier_verdict_recorded", vr.get("verdict") in ("PASS","FAIL"), f"verdict={vr.get('verdict')}")
check("all_phases_completed", rr.get("phases_completed",0)>=8, f"phases={rr.get('phases_completed')}")
check("artifact_written", len(rr.get("artifacts",[]))>0, str(rr.get("artifacts")))
# secret leak
leak = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__),"check_secret_leak.py"), ws],
                      capture_output=True, text=True)
leak_data = json.loads(leak.stdout)
check("secret_leak_detected==false", not leak_data["secret_leak_detected"], str(leak_data.get("leaks")))
allok = all(c["pass"] for c in checks)
print(json.dumps({"valid":allok, "checks":checks}, indent=2))
sys.exit(0 if allok else 1)
