#!/usr/bin/env python3
"""Golden E2E test — chạy verifier trên 1 work dir chuẩn, assert mọi REQ critical/high
PASS (ngoại trừ REQ-050 advisory). Dùng để regression khi sửa skill:
`python3 scripts/tests/test_golden_e2e.py [WORK_DIR]` (default: ctd-v4flash).

V4 Flash: đóng gói "phiên chạy thật CTD 69/70 + 13/13 chart + 0 meta nội bộ"
thành 1 lệnh — phát hiện sớm việc sửa skill làm hỏng báo cáo chuẩn.
"""
import json, os, subprocess, sys, glob

DEFAULT_WORK = "/Users/bobo/ZCodeProject/ctd-v4flash"
VERIFIER = os.path.join(os.path.dirname(__file__), "..", "independent_verifier.py")
ADVISORY = {"REQ-050"}  # comparison baseline — không chặn deploy

def main():
    work = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WORK
    report = os.path.join(work, "CTD_Complete_Report.html")
    if not os.path.exists(report):
        print(f"❌ Không tìm thấy report: {report}")
        sys.exit(2)
    r = subprocess.run([sys.executable, VERIFIER, "CTD", report],
                       capture_output=True, text=True, timeout=180)
    fails = {}
    for f in glob.glob(os.path.join(work, ".task-state", "evidence", "REQ-*.json")):
        d = json.load(open(f))
        if d["status"] == "fail":
            fails[d["requirement_id"]] = d["text"][:80]
    hard_fails = {k: v for k, v in fails.items() if k not in ADVISORY}
    # REQ mới quan trọng bắt buộc phải PASS
    must_pass = {"REQ-069", "REQ-070", "REQ-071", "REQ-072", "REQ-073"}
    missed = [k for k in must_pass if k in fails]
    total = len(glob.glob(os.path.join(work, ".task-state", "evidence", "REQ-*.json")))
    advisory_fails = sorted(set(fails.keys()) & ADVISORY)
    print(f"Evidence: {total} REQ | hard fails: {len(hard_fails)} | advisory: {advisory_fails}")
    if hard_fails:
        print("❌ HARD FAILS:")
        for k, v in sorted(hard_fails.items()):
            print(f"   {k}: {v}")
    if missed:
        print(f"❌ REQ mới phải PASS nhưng FAIL: {missed}")
    ok = not hard_fails and not missed
    print("✅ GOLDEN TEST PASS — báo cáo chuẩn đạt, skill không làm hỏng gì" if ok
          else "❌ GOLDEN TEST FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
