#!/usr/bin/env python3
"""Negative tests: corrupt fixture → mỗi REQ V5 phải FAIL."""
import json, os, shutil, subprocess, sys

BASE = "/tmp/ervn_e2e/CTD"
VERIFIER = "/Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py"

def run_case(name, mutate):
    work = f"/tmp/neg_{name}"
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(BASE, work)
    mutate(work)
    r = subprocess.run([sys.executable, VERIFIER, "CTD", f"{work}/CTD_Complete_Report.html"],
                       capture_output=True, text=True, timeout=120)
    out = r.stdout
    # đọc evidence
    import glob
    fails = set()
    for f in glob.glob(f"{work}/.task-state/evidence/REQ-*.json"):
        d = json.load(open(f))
        if d["status"] == "fail":
            fails.add(d["requirement_id"])
    target = name.split(":")[0]
    ok = target in fails
    print(f"{'✅' if ok else '❌'} {name}: REQ {target} {'FAIL (bắt đúng)' if ok else 'KHÔNG FAIL (lọt!)'}")
    if not ok:
        print("   fails:", sorted(fails))
    return ok

results = []

def p(path, rel):
    return os.path.join(path, rel)

# 1. REQ-059: bịa financials.json revenue 2025
def m1(w):
    fin = json.load(open(p(w, "data/financials.json")))
    fin["revenue_ty"]["2025"] = 50000.0  # thật là 30699
    json.dump(fin, open(p(w, "data/financials.json"), "w"))
results.append(run_case("REQ-059:revenue-gia", m1))

# 2. REQ-060: report ghi P/E 15x (không khớp EPS×giá)
def m2(w):
    h = open(p(w, "CTD_Complete_Report.html")).read()
    h = h.replace("P/E <b>9.3x</b>", "P/E <b>15x</b>").replace("P/E <b>9.3x</b>,", "P/E <b>15x</b>,")
    open(p(w, "CTD_Complete_Report.html"), "w").write(h)
results.append(run_case("REQ-060:pe-gia", m2))

# 3. REQ-061: claim ROE 24% (thật 8.3%)
def m3(w):
    h = open(p(w, "CTD_Complete_Report.html")).read()
    h = h.replace("ROE <b>8.3%</b>", "ROE <b>24%</b>")
    open(p(w, "CTD_Complete_Report.html"), "w").write(h)
results.append(run_case("REQ-061:roe-gia", m3))

# 4. REQ-063: mention EV/EBITDA 5x (task-state không có giá trị, không N/A)
def m4(w):
    h = open(p(w, "CTD_Complete_Report.html")).read()
    h = h.replace("(theo DCF và PE-implied)", "(theo DCF, PE-implied và EV/EBITDA 5x)")
    open(p(w, "CTD_Complete_Report.html"), "w").write(h)
results.append(run_case("REQ-063:ev-ebitda-gia", m4))

# 5. REQ-064: narrative "doanh thu giảm" (data tăng)
def m5(w):
    h = open(p(w, "CTD_Complete_Report.html")).read()
    h = h.replace("Doanh thu đạt <b>30.699 tỷ đồng</b> trong năm 2025, tăng 34%",
                  "Doanh thu giảm xuống còn <b>30.699 tỷ đồng</b> trong năm 2025")
    open(p(w, "CTD_Complete_Report.html"), "w").write(h)
results.append(run_case("REQ-064:trend-nguoc", m5))

# 6. REQ-065: exec tone tiêu cực (upside +14%)
def m6(w):
    h = open(p(w, "CTD_Complete_Report.html")).read()
    h = h.replace("Triển vọng tích cực và khả quan nhờ hồi phục ngành xây dựng, kỳ vọng tăng trưởng doanh thu tiếp tục nhờ đầu tư công.",
                  "Triển vọng tiêu cực, kém khả quan với nhiều rủi ro suy giảm và cảnh báo thận trọng.")
    open(p(w, "CTD_Complete_Report.html"), "w").write(h)
results.append(run_case("REQ-065:verdict-nguoc", m6))

# 7. REQ-066: xóa api_source khỏi task-state
def m7(w):
    ts = json.load(open(p(w, ".task-state/task-state.json")))
    del ts["phases"]["phase0_sponsor"]["result"]["api_source"]
    json.dump(ts, open(p(w, ".task-state/task-state.json"), "w"))
results.append(run_case("REQ-066:thieu-api-source", m7))

# 8. REQ-067: xóa fiscal_year_type
def m8(w):
    ts = json.load(open(p(w, ".task-state/task-state.json")))
    ts.pop("fiscal_year_type", None)
    ts["phases"]["phase1_data"]["result"].pop("fiscal_year_type", None)
    json.dump(ts, open(p(w, ".task-state/task-state.json"), "w"))
results.append(run_case("REQ-067:thieu-fiscal-year", m8))

print()
print(f"KẾT QUẢ: {sum(results)}/{len(results)} negative test bắt đúng hành vi bịa")
sys.exit(0 if all(results) else 1)
