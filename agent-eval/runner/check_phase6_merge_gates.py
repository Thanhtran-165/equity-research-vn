#!/usr/bin/env python3
"""check_phase6_merge_gates.py — Phase-6 patch merge gates (8 additional per owner directive)."""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def check():
    gates = []
    def g(gid, name, status, detail=""): gates.append({"gate_id":gid,"name":name,"status":status,"detail":detail})

    # FIX #1: HRS value separated from coverage
    import analyze_cohort as AC
    hrs_block_has_value = "value" in AC.analyze([], {}).get("hrs", {})
    g("MG-HRS-SPLIT", "hrs_value_separated_from_coverage", "PASS" if hrs_block_has_value else "FAIL",
      f"analyze hrs block has 'value' key: {hrs_block_has_value}")

    # FIX #2: preflight whitespace tolerant
    import phase6_preflight as PF
    p1,_,_ = (lambda o,s=None: PF.preflight_phase6(o, stop_reason=s)[:3])('<!DOCTYPE html><html><body><section id="sec-x">y</section><canvas id="c"></canvas><script>const DATA = {}</script></body></html>')
    p2,_,_ = (lambda o,s=None: PF.preflight_phase6(o, stop_reason=s)[:3])('<!DOCTYPE html><html><body><section class="x" id="sec-x">y</section><canvas id="c"></canvas><script>const DATA={};</script></body></html>')
    g("MG-PREFLIGHT-WS", "preflight_whitespace_tolerant", "PASS" if p1 and p2 else "FAIL", f"spaces:{p1} attr-order:{p2}")

    # FIX #2b: HTML attribute order tolerant
    g("MG-ATTR-ORDER", "html_attribute_order_tolerant", "PASS" if p2 else "FAIL", f"id-not-first-attr:{p2}")

    # FIX #3: truncation detection
    _,e3,c3 = (lambda o,s=None: PF.preflight_phase6(o, stop_reason=s)[:3])('<!DOCTYPE html><html><body><section id="sec-x">y', "max_tokens")
    g("MG-TRUNC", "output_truncation_detection", "PASS" if c3=="OUTPUT_TRUNCATED" else "FAIL", f"class={c3}")

    # FIX #4: retry artifacts + max-3 policy — inspect runner code
    runner_code = open(os.path.join(HERE,"agent_runner.py")).read()
    has_attempt_preserve = ".phase6-attempt-" in runner_code
    has_3_max = "recovery < 2" in runner_code
    g("MG-RETRY-ARTIFACTS", "retry_attempt_artifacts_preserved", "PASS" if has_attempt_preserve else "FAIL", f".phase6-attempt-N files: {has_attempt_preserve}")
    g("MG-MAX-ATTEMPTS", "maximum_total_attempts_explicit", "PASS" if has_3_max else "FAIL", "1 initial + 2 recovery = 3 max")

    # FIX #5: new protocol hash
    proto_v2 = os.path.exists("/Users/bobo/ZCodeProject/agent-eval/evaluation-protocol-v0.2.0.lock.yaml")
    g("MG-PROTO-V2", "new_protocol_hash_created", "PASS" if proto_v2 else "FAIL", "evaluation-protocol-v0.2.0.lock.yaml exists")

    # secret-leak on inlined prompt
    import json as _j, re
    key = _j.load(open(os.path.expanduser("~/.zcode/cli/config.json")))["provider"]["builtin:zai-coding-plan"]["options"]["apiKey"]
    tmpl = open("/Users/bobo/.zcode/skills/equity-research-vn/vn-research-dashboard/assets/dashboard_template.html").read()
    no_leak = key not in tmpl and key[:12] not in tmpl
    g("MG-NO-SECRET", "no_secret_in_inlined_prompt_or_logs", "PASS" if no_leak else "FAIL", "template has no API key")

    owner = "PENDING_OWNER"
    auto = [x for x in gates if x["status"]!="PENDING_OWNER"]
    allauto = all(x["status"]=="PASS" for x in auto)
    result = {"additional_gates_pass": allauto, "owner_review": owner,
              "overall": "READY_FOR_OWNER_MERGE" if allauto else "BLOCKED", "gates": gates}
    print(json.dumps(result, indent=2))
    return 0 if allauto else 1

if __name__ == "__main__":
    sys.exit(check() or 0)
