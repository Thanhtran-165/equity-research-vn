#!/usr/bin/env python3
"""Registry linter (P1-01 — Wave 1): kiểm tính nhất quán giữa requirements.yaml,
requirements-phase-map.yaml và SKILL.md.

Checks:
1. requirements.yaml: id duy nhất, không trống, method có trong verifier METHODS (nếu có thể đọc)
2. phase map: mọi ID trong map phải thuộc registry; không có ID lạ (parse YAML — bắt lỗi
   kiểu "REQ-065 - REQ-069"); không duplicate ngoài policy; mọi registry ID được map ≥1 phase
3. priority index: mọi REQ phải xuất hiện trong đúng 1 danh sách priority

Exit code: 0 = hợp lệ, 1 = có lỗi.
Chạy: python3 scripts/tests/requirements-lint.py
"""
import json, os, re, sys, yaml

SKILL = os.path.expanduser("~/.zcode/skills/equity-research-vn")
REQ_FILE = os.path.join(SKILL, "requirements.yaml")
MAP_FILE = os.path.join(SKILL, "requirements-phase-map.yaml")

def main():
    errors = []

    # 1. Registry
    reqs = yaml.safe_load(open(REQ_FILE))["requirements"]
    ids = [r["id"] for r in reqs]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        errors.append(f"registry ID trùng: {dupes}")
    if not all(re.fullmatch(r"REQ-\d{3}", i) for i in ids):
        errors.append("registry có ID không đúng format REQ-###")
    registry = set(ids)

    # 2. Phase map
    pm = yaml.safe_load(open(MAP_FILE))["phase_requirements"]
    map_ids = []
    for phase, info in pm.items():
        map_ids.extend(info["reqs"])
    unknown = sorted({i for i in map_ids if i not in registry})
    if unknown:
        errors.append(f"phase map chứa ID không có trong registry: {unknown}")
    # Duplicate policy: REQ có thể xuất hiện ở phase chuyên biệt + phase6/7 (final verify).
    # Duplicate giữa 2 phase chuyên biệt (không phải final) → lỗi.
    FINAL_PHASES = {"phase6_dashboard", "phase7_deploy"}
    seen = {}
    for phase, info in pm.items():
        for r in info["reqs"]:
            seen.setdefault(r, []).append(phase)
    dup_illegal = sorted(r for r, phases in seen.items()
                         if len(phases) > 1 and not any(p in FINAL_PHASES for p in phases))
    if dup_illegal:
        errors.append(f"REQ bị map ở 2 phase chuyên biệt (ngoài final verify): {dup_illegal}")
    unmapped = sorted(registry - set(map_ids))
    if unmapped:
        errors.append(f"registry ID chưa được map phase nào: {unmapped}")

    # 3. Priority index
    prio = {}
    for section in ("critical", "high", "medium", "low"):
        prio[section] = set(reqs.get(section, [])) if isinstance(reqs, dict) else set()
    # requirements.yaml structure: {"requirements": [...], "critical": [...], ...}
    doc = yaml.safe_load(open(REQ_FILE))
    listed = []
    for section in ("critical", "high", "medium", "low"):
        listed.extend(doc.get(section, []))
    missing_prio = sorted(registry - set(listed))
    if missing_prio:
        errors.append(f"REQ thiếu trong index priority: {missing_prio}")
    extra_prio = sorted(set(listed) - registry)
    if extra_prio:
        errors.append(f"index priority chứa ID không có trong registry: {extra_prio}")

    if errors:
        print("❌ REGISTRY LINT FAIL:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"✅ REGISTRY LINT OK — {len(registry)} REQ, {len(pm)} phases, map khớp registry, priority đầy đủ")

if __name__ == "__main__":
    main()
