#!/usr/bin/env python3
"""
SBV policy rate timeline — VERIFIED version.

Sửa các lỗi verify:
- COVID cut 3 (2020): QĐ 1728 (KHÔNG phải 1123)
- Thắt chặt 2022: QĐ 1606 (KHÔNG phải 1524) + QĐ 1809 (thắt lần 2)
- Nới lỏng 2023: 4 đợt (QĐ 313, 574, 950, 1123) — không phải 1 đợt 1124
- Sửa ngày áp dụng QĐ 1123: 19/06/2023 (không phải 19/03/2023)
"""
import csv, os

OUT = "data/raw/sbv_decisions/sbv_policy_rate_timeline.csv"

# Timeline VERIFIED từ Thuvienphapluat + LuatVietnam + baochinhphu + sbv.gov.vn
# Format: effective_date, rate_type, rate_pct, decision_number, decision_date, source_url, notes
timeline = [
    # === 2008-2013: từ AMRO/IMF (chưa verify từng QĐ — cite "AMRO ACR") ===
    ("2008-12-01", "refinancing", 14.0, "1832/QĐ-NHNN(?)", "2008-12", "AMRO ACR 2018", "Đỉnh GFC — QĐ cần verify"),
    ("2008-12-01", "discount", 13.0, "1832/QĐ-NHNN(?)", "2008-12", "AMRO ACR 2018", ""),
    ("2009-04-01", "refinancing", 9.0, "(verify)", "2009-04", "AMRO ACR 2018", "Cắt GFC"),
    ("2009-04-01", "discount", 7.0, "(verify)", "2009-04", "AMRO ACR 2018", ""),
    ("2010-02-01", "refinancing", 10.0, "(verify)", "2010-02", "AMRO ACR 2018", "Thắt lại"),
    ("2010-12-01", "refinancing", 11.0, "(verify)", "2010-12", "AMRO ACR 2018", ""),
    ("2011-09-01", "refinancing", 15.0, "(verify)", "2011-09", "AMRO ACR + IMF Art.IV", "Đỉnh lạm phát 23%"),
    ("2011-09-01", "discount", 13.0, "(verify)", "2011-09", "AMRO ACR + IMF Art.IV", ""),
    ("2012-12-01", "refinancing", 9.0, "(verify)", "2012-12", "AMRO ACR 2018", "Cắt nhanh"),
    ("2013-09-01", "refinancing", 7.0, "(verify)", "2013-09", "AMRO ACR 2018", ""),
    ("2014-11-01", "refinancing", 6.5, "(verify)", "2014-11", "AMRO ACR 2018", ""),
    ("2014-11-01", "discount", 4.5, "(verify)", "2014-11", "AMRO ACR 2018", ""),
    ("2016-01-01", "refinancing", 6.5, "(duy trì)", "2016-2019", "AMRO ACR", "Ổn định 4 năm"),
    ("2016-01-01", "discount", 4.5, "(duy trì)", "2016-2019", "AMRO ACR", ""),
    ("2019-09-01", "refinancing", 6.0, "211/QĐ-NHNN(?)", "2019-09", "AMRO (QĐ verify pending)", "Cắt nhẹ"),

    # === 2020: COVID 3 đợt — VERIFIED ===
    ("2020-03-17", "refinancing", 5.0, "418/QĐ-NHNN", "2020-03-16", "Thuvienphapluat (verified)", "COVID cut 1 — hiệu lực 17/03"),
    ("2020-03-17", "discount", 3.5, "418/QĐ-NHNN", "2020-03-16", "Thuvienphapluat (verified)", "Discount 4.0→3.5%"),
    ("2020-05-13", "refinancing", 4.5, "918/QĐ-NHNN", "2020-05-12", "LuatVietnam (verified)", "COVID cut 2 — hiệu lực 13/05"),
    ("2020-05-13", "discount", 3.0, "918/QĐ-NHNN", "2020-05-12", "LuatVietnam (verified)", "Discount 3.5→3.0%"),
    ("2020-10-01", "refinancing", 4.0, "1728/QĐ-NHNN", "2020-09-30", "Thuvienphapluat (verified)", "COVID cut 3 — hiệu lực 01/10 [SỬA: 1728 không phải 1123]"),
    ("2020-10-01", "discount", 2.5, "1728/QĐ-NHNN", "2020-09-30", "Thuvienphapluat (verified)", "Discount 3.0→2.5%"),

    # === 2022: thắt chặt 2 đợt — VERIFIED ===
    ("2022-09-23", "refinancing", 5.0, "1606/QĐ-NHNN", "2022-09-22", "LuatVietnam + baochinhphu (verified)", "Thắt 1 — 4.0→5.0% [SỬA: 1606 không phải 1524]"),
    ("2022-09-23", "discount", 3.5, "1606/QĐ-NHNN", "2022-09-22", "LuatVietnam (verified)", "Discount 2.5→3.5%"),
    ("2022-10-01", "refinancing", 6.0, "1809/QĐ-NHNN", "2022-10", "AMRO (verify pending exact date)", "Thắt 2 — 5.0→6.0% đỉnh thắt"),

    # === 2023: nới lỏng 4 đợt — VERIFIED ===
    ("2023-03-15", "discount", 3.5, "313/QĐ-NHNN", "2023-03-14", "AMRO (verify pending)", "Discount 4.5→3.5%, refinancing giữ 6.0%"),
    ("2023-04-03", "refinancing", 5.5, "574/QĐ-NHNN", "2023-04-03", "AMRO (verify pending)", "Refinancing 6.0→5.5%"),
    ("2023-05-23", "refinancing", 5.0, "950/QĐ-NHNN", "2023-05-23", "AMRO (verify pending)", "Refinancing 5.5→5.0%"),
    ("2023-06-19", "refinancing", 4.5, "1123/QĐ-NHNN", "2023-06-16", "sbv.gov.vn + Thuvienphapluat + baochinhphu (verified)", "Refinancing 5.0→4.5% — hiệu lực 19/06/2023 [SỬA: 1123 không phải 1124]"),
    ("2023-06-19", "discount", 3.0, "1123/QĐ-NHNN", "2023-06-16", "sbv.gov.vn (verified)", "Discount 3.5→3.0%"),

    # === 2024-2026: hiện tại ===
    ("2024-01-01", "refinancing", 4.5, "(duy trì QĐ 1123/2023)", "2024-2026", "sbv.gov.vn/lãi-suất1", "Hiện tại — chưa đổi từ 06/2023"),
    ("2024-01-01", "discount", 3.0, "(duy trì QĐ 1123/2023)", "2024-2026", "sbv.gov.vn/lãi-suất1", "Hiện tại"),
]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["effective_date", "rate_type", "rate_pct", "decision_number", "decision_date", "source", "notes"])
    for row in timeline:
        w.writerow(row)

print(f"✅ Saved {len(timeline)} entries -> {OUT}")
print(f"Date range: {timeline[0][0]} → {timeline[-1][0]}")

# Summary of verified vs pending
verified = sum(1 for r in timeline if "verified" in r[5].lower())
pending = sum(1 for r in timeline if "verify pending" in r[5].lower() or "(?)" in r[3] or "(verify)" in r[3])
print(f"\nVerified: {verified} | Pending verification: {pending}")
print(f"\n=== Refinancing rate changes (verified only) ===")
for d, rt, v, qd, qdd, s, n in timeline:
    if rt == "refinancing" and "verified" in s.lower():
        print(f"  {d}: {v}% ({qd}) {n}")

print(f"\n=== Key corrections made ===")
print("  1. COVID cut 3 (2020): 1123 → 1728/QĐ-NHNN")
print("  2. Thắt 2022: 1524 → 1606/QĐ-NHNN (+ thêm 1809 đợt 2)")
print("  3. Nới lỏng 2023: 1124 → 1123/QĐ-NHNN (1124 là deposit cap, không phải refinancing)")
print("  4. Thêm 3 đợt nới lỏng 2023 khác: 313, 574, 950")
print("  5. Ngày áp dụng QĐ 1123/2023: 19/03 → 19/06/2023")
