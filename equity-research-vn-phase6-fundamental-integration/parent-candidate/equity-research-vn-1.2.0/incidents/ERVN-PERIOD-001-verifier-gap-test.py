#!/usr/bin/env python3
"""
ERVN-PERIOD-001 — Verifier gap proof.

Hypothesis: independent_verifier.py v0.14.9 cannot detect the period-inversion
defect because REQ-022/025/026 use the contract's OWN values as ground truth.

Test: synthesize a fixture where:
  - raw CSV has periods=[2021,2022,2023,2024,2025], values=[10,20,30,40,50]
  - bad_output contract has SAME periods but INVERTED values [50,40,30,20,10]
  - Run current verifier against bad_output
  - Expected: verifier still PASSES (because it trusts contract's labels)

This proves the verifier needs augmentation: it MUST cross-check (period,value)
pairs against the raw CSV.
"""
import os, sys, json, tempfile, subprocess

PYTHON = sys.executable
VERIFIER = "/Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py"
WORK = tempfile.mkdtemp(prefix="ervn_verifier_gap_")

# Build a minimal "bad_output" work directory
os.makedirs(os.path.join(WORK, "data"), exist_ok=True)

# Mock HTML report with section that matches the contract (inverted values)
# The verifier extracts PE/PB from the HTML and compares to contract's PE/PB.
# We embed the INVERTED eps → computed PE will match the inverted HTML PE.
html = """<!DOCTYPE html>
<html><body>
<section id="sec-hero">
  <h1>TEST Tall</h1>
</section>
<section id="sec-exec">
  <p>P/E (TTM) 18.4x based on inverted mapping.</p>
  <p>P/B 3.2x.</p>
</section>
<section id="sec-valuation">
  <p>Valuation: P/E 18.4x, P/B 3.2x — note these are computed from inverted-period data.</p>
</section>
<script>
const DATA = {
  "financials": {
    "revenue": [50, 40, 30, 20, 10],
    "netProfit": [25, 20, 15, 10, 5],
    "eps": [5500, 4400, 3300, 2200, 1100],
    "years": ["2021", "2022", "2023", "2024", "2025"]
  },
  "valuation": {"pe": 18.4, "pb": 3.2, "price": 101200}
};
</script>
</body></html>"""
html_path = os.path.join(WORK, "report.html")
open(html_path, "w").write(html)

# data/financials.json (inverted, matches HTML)
fin = {
  "revenue_ty": {"2021": 50, "2022": 40, "2023": 30, "2024": 20, "2025": 10},
  "npatmi_ty":  {"2021": 25, "2022": 20, "2023": 15, "2024": 10, "2025": 5},
  "eps_vnd":    {"2021": 5500, "2022": 4400, "2023": 3300, "2024": 2200, "2025": 1100},
  "overview": {"current_price": 101200, "issue_share": 1000000, "ticker": "TEST"}
}
json.dump(fin, open(os.path.join(WORK, "data/financials.json"), "w"), indent=2)

# verified-dashboard-data.json (inverted, matches HTML/fin)
contract = {
  "company": "Test Tall",
  "ticker": "TEST",
  "price": 101200,
  "shares": 1000000,
  "periods": [2021, 2022, 2023, 2024, 2025],
  "financials": {
    "revenue": [50, 40, 30, 20, 10],
    "netProfit": [25, 20, 15, 10, 5],
    "eps": [5500, 4400, 3300, 2200, 1100],
    "years": ["2021", "2022", "2023", "2024", "2025"]
  },
  "valuation": {"pe": 18.4, "pb": 3.2, "price": 101200},
  "technical": None,
  "company_profile": None,
  "references": {},
  "_provenance": {"built_at": "2026-07-18", "source": "synthetic fixture"}
}
json.dump(contract, open(os.path.join(WORK, "verified-dashboard-data.json"), "w"), indent=2)

# Mock raw CSV (true periods: ascending values, NOT inverted)
# Place in source-pack-style location for any future cross-check
csv_path = os.path.join(WORK, "income_statement_sponsor.csv")
open(csv_path, "w").write(
    "report_period,ticker,Sales,EPS basic (VND)\n"
    "year,TEST,10,1100\n"     # 2021
    "year,TEST,20,2200\n"     # 2022
    "year,TEST,30,3300\n"     # 2023
    "year,TEST,40,4400\n"     # 2024
    "year,TEST,50,5500\n"     # 2025
)

print(f"=== Verifier gap test ===")
print(f"work dir: {WORK}")
print(f"raw CSV ascending truth: revenue[2021]=10, revenue[2025]=50")
print(f"contract (BAD): revenue[2021]=50, revenue[2025]=10  ← INVERTED")
print(f"contract (BAD): eps[2025]=1100 (actually 2021's value)  ← INVERTED")
print(f"contract computes: pe = 101200/1100 = 18.4 ← INVERTED")
print(f"HTML matches inverted contract: PE=18.4, PB=3.2")
print()

# Run the verifier
result = subprocess.run([PYTHON, VERIFIER, "TEST", html_path],
                        capture_output=True, text=True, timeout=30, cwd=WORK)
print(f"--- verifier stdout (last 30 lines) ---")
out_lines = result.stdout.split("\n")
for line in out_lines[-30:]:
    print(f"  {line}")
print(f"--- verifier exit code: {result.returncode} ---")
print()
print(f"=== Conclusion ===")
if result.returncode == 0:
    print(f"VERIFIER GAP CONFIRMED: v0.14.9 returns exit 0 on a contract with fully")
    print(f"inverted period labels. The defect is undetectable by the current verifier")
    print(f"because REQ-022/025/026 use contract.valuation.pe (line 758-761) as ground")
    print(f"truth — it never compares against raw CSV (period, value) pairs.")
else:
    print(f"Surprising: verifier FAILED on the bad fixture — needs investigation.")
    print(f"(This would contradict our forensic findings.)")
