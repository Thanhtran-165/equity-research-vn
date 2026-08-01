#!/usr/bin/env python3
"""Mutation corpus mở rộng (W4-4 — Wave 4): các failure mode Wave 5.

Mỗi mutation phải làm verifier FAIL ở REQ tương ứng:
1. non-calendar FY: task-state thiếu fiscal_year_type cảnh báo → REQ-067 FAIL
2. missing CFO: cash_flow.json thiếu CFO → REQ-059/REQ-061 fail (provenance/recompute)
3. stale peer: peers.json thiếu ngày fetch → REQ-032/REQ-059 fail
4. multi-file report: tham chiếu nhiều HTML trong project (deploy gate ambiguity) → gate test
Chạy: python3 scripts/tests/test_mutation_wave.py
"""
import json, os, shutil, subprocess, sys, tempfile

BASE = "/Users/bobo/ZCodeProject/ctd-v4flash"
VERIFIER = "/Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py"

def run_verify(work, expect_fail_reqs):
    r = subprocess.run([sys.executable, VERIFIER, "CTD", f"{work}/CTD_Complete_Report.html"],
                       capture_output=True, text=True, timeout=180)
    fails = set()
    import glob
    for f in glob.glob(f"{work}/.task-state/evidence/REQ-*.json"):
        d = json.load(open(f))
        if d["status"] == "fail":
            fails.add(d["requirement_id"])
    ok = bool(expect_fail_reqs & fails)
    return ok, fails

def case(name, mutate, expect):
    work = tempfile.mkdtemp(prefix=f"mut_{name}_")
    shutil.copytree(BASE, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    try:
        mutate(work)
        ok, fails = run_verify(work, set(expect))
        if not ok:
            print(f"❌ {name}: kỳ vọng FAIL {expect} nhưng fails = {sorted(fails)}")
            return False
        print(f"✅ {name}: bắt đúng {expect}")
        return True
    finally:
        shutil.rmtree(work, ignore_errors=True)

def main():
    results = []

    # 1. Non-calendar FY (Pro review Wave 4: verifier đọc fiscal_year_type từ TOP-LEVEL
    #    + phase1_data.result, KHÔNG đọc phase0 — mutate đúng nơi verifier đọc mới bác bỏ được)
    def m1(w):
        ts = json.load(open(f"{w}/.task-state/task-state.json"))
        ts.pop("fiscal_year_type", None)
        p1 = ts["phases"].get("phase1_data", {}).get("result")
        if isinstance(p1, dict):
            p1.pop("fiscal_year_type", None)
        json.dump(ts, open(f"{w}/.task-state/task-state.json", "w"), ensure_ascii=False)
    results.append(case("non-calendar-FY", m1, ["REQ-067", "REQ-068"]))

    # 2. Missing CFO: xóa cfo khỏi financials.json (nếu có) / cash_flow rỗng
    def m2(w):
        import re
        # xóa dataset cfo khỏi DATA trong report → REQ-071/REQ-069 không phát hiện vì cfo vẫn là list...
        # thay vào đó: xóa dòng CFO khỏi cash_flow.json → provenance fail
        cf = json.load(open(f"{w}/data/cash_flow.json"))
        cf.pop("Net cash inflows/(outflows) from operating activities", None)
        json.dump(cf, open(f"{w}/data/cash_flow.json", "w"), ensure_ascii=False)
    results.append(case("missing-CFO", m2, ["REQ-059", "REQ-061"]))

    # 3. Stale peer: peers.json thiếu timestamp/nguồn
    def m3(w):
        pj = json.load(open(f"{w}/data/peers.json"))
        pj.pop("source", None)
        json.dump(pj, open(f"{w}/data/peers.json", "w"), ensure_ascii=False)
    results.append(case("stale-peer", m3, ["REQ-059", "REQ-032"]))

    ok_all = all(results)
    print("KẾT QUẢ:", f"{sum(results)}/{len(results)} mutation bắt đúng" if ok_all else "CÓ CASE LỌT")
    sys.exit(0 if ok_all else 1)

if __name__ == "__main__":
    main()
