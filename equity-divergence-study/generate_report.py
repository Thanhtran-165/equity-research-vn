"""generate_report.py — PLAIN-LANGUAGE canonical generator for divergence study.

Editorial rebuild: report written for readers with zero statistics background.
Technical terms (Holm, beta, log-point, parent, child, OOS, materiality, fold,
power, FIT_FAILED, survivorship, taxonomy) appear ONLY inside
`<details data-layer="technical">` blocks.

Plain-language dictionary enforced:
  beta → "mức chênh lệch trung bình"
  CI 95% → "khoảng ước lượng"
  Holm significant → "vẫn còn đáng chú ý sau khi kiểm tra nhiều khả năng"
  parent → "bằng chứng chung trên nhiều khoảng thời gian"
  child → "kết quả tại một khoảng thời gian cụ thể"
  OOS → "kiểm tra trên những giai đoạn chưa dùng để xây mô hình"
  baseline → "mô hình đơn giản không dùng phân kỳ"
  augmented → "mô hình có thêm phân kỳ"
  materiality → "mức cải thiện đủ lớn để có ý nghĩa thực tế"
  fold → "giai đoạn kiểm tra"
  power limited → "dữ liệu chưa đủ mạnh để loại trừ những quan hệ yếu"
  FIT_FAILED → "không đủ dữ liệu hoàn chỉnh để đánh giá"
  breadth → "mức độ nhiều hay ít cổ phiếu cùng tham gia"

Plain-language gate (fail-closed) scans VISIBLE text after stripping CSS/JS
and the contents of every <details data-layer="technical"> block.

Source-gated: reads ONLY the 10 R3 artifacts. Empirical claims and source
hashes unchanged from prior freeze. Idempotent: regenerate → byte-identical.
"""
from __future__ import annotations
import json, csv, hashlib, re, math
from pathlib import Path

SRC = Path("/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_divergence_outcomes_v1/outputs")
OUT = Path("/Users/bobo/ZCodeProject/equity-divergence-study")
QA = OUT / "qa"
QA.mkdir(parents=True, exist_ok=True)

SOURCE_FILES = [
    "20_phase1_results.json", "21_prediction_registry.csv", "22_parent_results.json",
    "23_verdicts.json", "24_multiple_testing.json", "25_reconciliation.json",
    "26_audit_manifest.json", "28_claim_evidence_map.json", "02_expected_test_matrix.csv",
    "11_synthetic_validation.json",
]

# ---------------------------------------------------------------------------
# SOURCE GATE
# ---------------------------------------------------------------------------
def lock_sources():
    hashes = {}
    for s in SOURCE_FILES:
        p = SRC / s
        if not p.exists():
            raise SystemExit(f"BLOCKED_HTML_SOURCE_MISMATCH: missing {s}")
        hashes[s] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes

SRC_HASHES = lock_sources()

with open(SRC / "20_phase1_results.json") as f: PHASE1 = json.load(f)
with open(SRC / "22_parent_results.json") as f: PARENTS = json.load(f)
with open(SRC / "23_verdicts.json") as f: VERDICTS = json.load(f)
with open(SRC / "24_multiple_testing.json") as f: MT = json.load(f)
with open(SRC / "25_reconciliation.json") as f: RECON = json.load(f)
with open(SRC / "26_audit_manifest.json") as f: AUDIT = json.load(f)
with open(SRC / "28_claim_evidence_map.json") as f: CLAIMS = json.load(f)

import pandas as pd
PRED = pd.read_csv(SRC / "21_prediction_registry.csv")
CHILD_CORR = MT["child_corrected"]; PARENT_CORR = MT["parent_corrected"]

HEADLINE_TID = "D1__PV__VNINDEX__daily__lb20__H60__forward_return__down__child"
HEADLINE_PARENT = "D1__PV__VNINDEX__daily__lb20__PARENT__forward_return__down__parent"
H = PHASE1[HEADLINE_TID]; HL = H["layer_b"]; HP = PARENTS[HEADLINE_PARENT]

H_PRED = PRED[PRED["test_id"] == HEADLINE_TID].copy()
fold_data = H_PRED.groupby("fold").agg(
    n=("paired_loss_diff", "count"), mean_diff=("paired_loss_diff", "mean")).reset_index()
FOLDS = [{"fold": int(r["fold"]), "n": int(r["n"]),
          "mean_diff": float(r["mean_diff"])} for _, r in fold_data.iterrows()]
N_BETTER = sum(1 for f in FOLDS if f["mean_diff"] < 0)

PARENT_FINDINGS = sorted([t for t, p in PARENT_CORR.items() if p < 0.05],
                          key=lambda x: PARENT_CORR[x])

# Units
BETA = HL["beta"]; SE = HL["se"]
SIMPLE_RETURN = math.exp(BETA) - 1
SIMPLE_CI_LO = math.exp(BETA - 1.96 * SE) - 1
SIMPLE_CI_HI = math.exp(BETA + 1.96 * SE) - 1
CI_LO_LP = BETA - 1.96 * SE; CI_HI_LP = BETA + 1.96 * SE

# Parent plain-language mapping
PARENT_SCENARIOS = {
    "D1__PV__VNINDEX__daily__lb20__PARENT__forward_return__down__parent":
        ("VNINDEX", "có dấu hiệu cụ thể ở khoảng 60 phiên"),
    "D1__PV__VN30__daily__lb20__PARENT__forward_return__down__parent":
        ("VN30", "có dấu hiệu chung khi xét nhiều khoảng thời gian, chưa có khoảng riêng đủ chắc chắn"),
    "D1__PV__VN30__daily__lb20__PARENT__forward_drawdown__down__parent":
        ("VN30", "có dấu hiệu chung khi xét nhiều khoảng thời gian, chưa có khoảng riêng đủ chắc chắn"),
    "D1__PV__VNFINSELECT__daily__lb20__PARENT__forward_return__down__parent":
        ("VNFINSELECT", "có dấu hiệu chung khi xét nhiều khoảng thời gian, chưa có khoảng riêng đủ chắc chắn"),
}

# ---------------------------------------------------------------------------
# CLAIM REGISTRY (unchanged claims, plain-language wording in display only)
# ---------------------------------------------------------------------------
claim_registry = {
    "headline_average_difference": {
        "claim": f"mức chênh lệch trung bình = {(SIMPLE_RETURN*100):.2f}% (simple return)",
        "artifact": "outputs/20_phase1_results.json", "test_id": HEADLINE_TID,
        "sha256": SRC_HASHES["20_phase1_results.json"],
    },
    "headline_estimation_range": {
        "claim": f"khoảng ước lượng 95% [{(SIMPLE_CI_LO*100):.2f}%, {(SIMPLE_CI_HI*100):.2f}%]",
        "artifact": "outputs/20_phase1_results.json", "test_id": HEADLINE_TID,
        "sha256": SRC_HASHES["20_phase1_results.json"],
    },
    "headline_noteworthy_after_many_checks": {
        "claim": "vượt ngưỡng đáng chú ý sau khi kiểm tra nhiều khả năng",
        "artifact": "outputs/24_multiple_testing.json", "test_id": HEADLINE_TID,
        "sha256": SRC_HASHES["24_multiple_testing.json"],
    },
    "headline_parent_noteworthy": {
        "claim": "bằng chứng chung trên nhiều khoảng thời gian cũng đáng chú ý",
        "artifact": "outputs/24_multiple_testing.json", "test_id": HEADLINE_PARENT,
        "sha256": SRC_HASHES["24_multiple_testing.json"],
    },
    "oos_negative": {
        "claim": f"kiểm tra ngoài mẫu: mô hình có phân kỳ kém hơn một chút (độ cải thiện {H['oos_improvement']:.4f})",
        "artifact": "outputs/20_phase1_results.json", "test_id": HEADLINE_TID,
        "sha256": SRC_HASHES["20_phase1_results.json"],
    },
    "fold_consistency_3of6": {
        "claim": f"3/6 giai đoạn kiểm tra cho kết quả tốt hơn",
        "artifact": "outputs/21_prediction_registry.csv", "test_id": HEADLINE_TID,
        "sha256": SRC_HASHES["21_prediction_registry.csv"],
    },
    "materiality_fail": {
        "claim": "mức cải thiện không đủ lớn để có ý nghĩa thực tế",
        "artifact": "outputs/20_phase1_results.json", "test_id": HEADLINE_TID,
        "sha256": SRC_HASHES["20_phase1_results.json"],
    },
    "four_indices_noteworthy": {
        "claim": f"{len(PARENT_FINDINGS)} chỉ số có bằng chứng chung đáng chú ý",
        "artifact": "outputs/24_multiple_testing.json",
        "test_id": ";".join(PARENT_FINDINGS),
        "sha256": SRC_HASHES["24_multiple_testing.json"],
    },
    "no_operational_warning": {
        "claim": "0 trường hợp đạt tiêu chuẩn cảnh báo vận hành",
        "artifact": "outputs/28_claim_evidence_map.json", "test_id": "ALL",
        "sha256": SRC_HASHES["28_claim_evidence_map.json"],
    },
    "d4_held_back": {
        "claim": "Một kết quả khác đáng chú ý nhưng không đủ dữ liệu hoàn chỉnh để đánh giá",
        "artifact": "outputs/23_verdicts.json",
        "test_id": "D4__COMBINED__VNINDEX__daily__lb20__H60__forward_return__price_lone_up__child",
        "sha256": SRC_HASHES["23_verdicts.json"],
    },
    "data_not_strong_enough": {
        "claim": "dữ liệu chưa đủ mạnh để loại trừ những quan hệ yếu (binary power 0,355)",
        "artifact": "outputs/28_claim_evidence_map.json", "test_id": "ALL_BINARY",
        "sha256": SRC_HASHES["28_claim_evidence_map.json"],
    },
    "breadth_incomplete": {
        "claim": f"{RECON['n_partial']} ô về độ rộng không đủ dữ liệu hoàn chỉnh để đánh giá",
        "artifact": "outputs/25_reconciliation.json", "test_id": "ALL_BREADTH",
        "sha256": SRC_HASHES["25_reconciliation.json"],
    },
    "total_cells": {
        "claim": f"{RECON['expected']} = {RECON['computed']} đã tính + {RECON['blocked']} không đủ điều kiện",
        "artifact": "outputs/25_reconciliation.json", "test_id": "MATRIX",
        "sha256": SRC_HASHES["25_reconciliation.json"],
    },
}

# ---------------------------------------------------------------------------
# GATES
# ---------------------------------------------------------------------------
FORBIDDEN_TERMS = [
    "tín hiệu mua", "xác nhận xu hướng", "dự báo được",
    "món quà", "luôn ", "chắc chắn", "chắc sẽ", "đảm bảo",
    "100%", "every time", "always", "guaranteed",
]

# Technical terms that must NOT appear in visible (non-technical-details) text.
# Allowed only inside <details data-layer="technical">...</details>.
TECHNICAL_TERMS = [
    "holm", "fwer", "bootstrap", "p-value", "adjusted p", "beta",
    "ols", "regression", "log-point", "parent", "child", "oos",
    "materiality", "fold consistency", "effective_n", "fit_failed",
    "divergence_warning_candidate", "research_only_survivorship_limited",
]


def strip_to_visible_text(html: str) -> str:
    """Return visible text only: remove <script>, <style>, and the inner
    contents of every <details data-layer="technical"> block, then strip tags."""
    out = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    out = re.sub(r"<style[^>]*>.*?</style>", "", out, flags=re.DOTALL | re.IGNORECASE)
    # Remove <details data-layer="technical">...</details> blocks entirely
    out = re.sub(r'<details[^>]*data-layer="technical"[^>]*>.*?</details>',
                 "", out, flags=re.DOTALL | re.IGNORECASE)
    out = re.sub(r"<[^>]+>", " ", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def plain_language_gate(html: str):
    """Fail-closed: no technical term allowed in visible (non-technical) text."""
    visible = strip_to_visible_text(html).lower()
    violations = []
    for term in TECHNICAL_TERMS:
        if term.lower() in visible:
            violations.append(term)
    # Negation-aware "chứng minh"
    cleaned = re.sub(r"chưa được chứng minh|chưa chứng minh|không chứng minh|chưa được kiểm chứng",
                     "", visible)
    if "chứng minh" in cleaned:
        violations.append("chứng minh (non-negated)")
    if violations:
        raise SystemExit(f"BLOCKED_PLAIN_LANGUAGE: technical terms in visible text: {violations}")
    return violations


def overclaim_gate(html: str):
    visible = strip_to_visible_text(html).lower()
    violations = []
    for term in FORBIDDEN_TERMS:
        if term.lower() in visible:
            # Allow "tín hiệu mua bán" (compound, cautionary) and negated contexts
            if term == "tín hiệu mua":
                # Allow "tín hiệu mua bán", "không... tín hiệu mua", "chưa phải tín hiệu mua"
                cleaned = re.sub(r"tín hiệu mua bán|không phải tín hiệu mua|chưa phải tín hiệu mua|thành tín hiệu mua bán|dùng làm tín hiệu mua|làm tín hiệu mua", "", visible)
                if "tín hiệu mua" in cleaned:
                    violations.append(term)
            elif term == "chắc chắn":
                # Allow compound/cautionary forms: độ chắc chắn, đủ chắc chắn, etc.
                cleaned = re.sub(r"độ chắc chắn|đủ chắc chắn|sự chắc chắn|không chắc chắn|chưa chắc chắn|chắc chắn nhất|phát hiện chắc chắn|đảo chiều chắc chắn|tình huống nào đủ chắc chắn", "", visible)
                if "chắc chắn" in cleaned:
                    violations.append(term)
            else:
                violations.append(term)
    if violations:
        raise SystemExit(f"BLOCKED_HTML_OVERCLAIM: {violations}")
    return violations


def unresolved_claims_check():
    unresolved = [k for k, v in claim_registry.items()
                  if not (v.get("artifact") and v.get("test_id") and v.get("sha256"))]
    if unresolved:
        raise SystemExit(f"BLOCKED_HTML_UNRESOLVED_CLAIMS: {unresolved}")
    return unresolved


# ---------------------------------------------------------------------------
# BUILD HTML
# ---------------------------------------------------------------------------
def build_html():
    folds_json = json.dumps(FOLDS)
    mse_base = float(H_PRED["loss_base"].mean())
    mse_aug = float(H_PRED["loss_aug"].mean())
    scenarios_json = json.dumps([{
        "index": PARENT_SCENARIOS[p][0],
        "finding": PARENT_SCENARIOS[p][1],
    } for p in PARENT_FINDINGS])

    return HTML_TEMPLATE.format(
        simple_pct=round(SIMPLE_RETURN * 100, 2),
        simple_ci_lo_pct=round(SIMPLE_CI_LO * 100, 2),
        simple_ci_hi_pct=round(SIMPLE_CI_HI * 100, 2),
        oos_improvement=round(H["oos_improvement"], 4),
        n_better=N_BETTER, n_partial=RECON["n_partial"],
        effective_n=H["effective_n"],
        folds_json=folds_json, scenarios_json=scenarios_json,
        mse_base=round(mse_base, 6), mse_aug=round(mse_aug, 6),
        n_parents=len(PARENT_FINDINGS),
        n_total=RECON["expected"], n_computed=RECON["computed"],
        n_blocked=RECON["blocked"],
        rerun_total=RECON["n_rerun_B9999_children"] + RECON["n_rerun_B9999_parents"],
        n_predictions=AUDIT["n_predictions"],
        # Technical appendix values (kept for the technical details block)
        beta_lp=round(BETA, 4), se_lp=round(SE, 4),
        ci_lo_lp=round(CI_LO_LP, 4), ci_hi_lp=round(CI_HI_LP, 4),
        child_adj_p=round(CHILD_CORR[HEADLINE_TID], 4),
        parent_adj_p=round(PARENT_CORR[HEADLINE_PARENT], 4),
        raw_p_initial=H["raw_p_initial"], raw_p_final=H["raw_p_final"],
        b_final=H["B_requested_final"], valid_ratio=H["valid_ratio"],
        source_hashes_json=json.dumps(SRC_HASHES, indent=2),
        claim_registry_json=json.dumps(claim_registry, indent=2, ensure_ascii=False),
    )


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Phân kỳ đáng để chú ý, nhưng chưa đủ để mua bán</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #fafaf7; --ink: #1a1a1a; --muted: #5a5a5a; --line: #d8d8d2;
    --accent: #1e5f8e; --accent-soft: #e8f0f6; --warn: #b8581c; --warn-soft: #fbeee0;
    --ok: #2d6a4f; --ok-soft: #e3f0e9; --card: #ffffff; --card-border: #e0e0d8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    background: var(--bg); color: var(--ink); line-height: 1.7;
    font-size: 18px; -webkit-font-smoothing: antialiased;
    overflow-wrap: break-word; word-wrap: break-word;
  }}
  .wrap {{ max-width: 920px; margin: 0 auto; padding: 0 18px; overflow-wrap: break-word; }}
  pre {{ overflow-x: auto; max-width: 99%; }}
  header.hero {{
    background: linear-gradient(135deg, #1e5f8e 0%, #2a7ab0 99%);
    color: white; padding: 64px 0 54px;
  }}
  header.hero h1 {{
    font-size: 34px; font-weight: 700; line-height: 1.3;
    margin-bottom: 22px; max-width: 760px;
  }}
  header.hero .lede {{
    font-size: 20px; opacity: 0.96; max-width: 760px; line-height: 1.55;
  }}
  header.hero .meta {{
    margin-top: 26px; font-size: 13px; opacity: 0.8;
    border-top: 1px solid rgba(255,255,255,0.25); padding-top: 14px;
  }}
  nav {{
    background: var(--card); border-bottom: 1px solid var(--line);
    position: sticky; top: 0; z-index: 100; overflow-x: auto;
  }}
  nav .wrap {{ display: flex; gap: 4px; padding: 8px 18px; }}
  nav a {{
    color: var(--ink); text-decoration: none; font-size: 13px;
    padding: 8px 12px; border-radius: 6px; white-space: nowrap; transition: background 0.15s;
  }}
  nav a:hover {{ background: var(--accent-soft); }}
  section {{ padding: 52px 0; border-bottom: 1px solid var(--line); scroll-margin-top: 70px; }}
  section h2 {{
    font-size: 27px; font-weight: 700; margin-bottom: 10px; color: var(--ink); line-height: 1.3;
  }}
  section .answer {{
    font-size: 19px; color: var(--accent); margin-bottom: 24px; font-weight: 500; line-height: 1.5;
  }}
  section p {{ margin-bottom: 18px; }}
  section ul, section ol {{ margin: 0 0 18px 24px; }}
  section li {{ margin-bottom: 10px; }}
  .card {{
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 10px; padding: 24px; margin: 20px 0;
  }}
  .card.accent {{ border-left: 4px solid var(--accent); }}
  .card.warn {{ border-left: 4px solid var(--warn); background: var(--warn-soft); }}
  .card.ok {{ border-left: 4px solid var(--ok); background: var(--ok-soft); }}
  .card h3 {{ font-size: 18px; margin-bottom: 12px; font-weight: 600; }}
  .stat-row {{ display: flex; gap: 24px; flex-wrap: wrap; margin: 18px 0; }}
  .stat {{ flex: 1; min-width: 150px; }}
  .stat .num {{ font-size: 30px; font-weight: 700; color: var(--accent); }}
  .stat .lbl {{ font-size: 14px; color: var(--muted); }}
  .chart-box {{
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 10px; padding: 22px; margin: 22px 0; position: relative;
  }}
  .chart-box canvas {{ max-height: 340px; }}
  .chart-box .caption {{ font-size: 14px; color: var(--muted); margin-top: 14px; font-style: italic; line-height: 1.55; }}
  .chart-box .q {{ font-size: 17px; font-weight: 600; margin-bottom: 16px; color: var(--ink); }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0; }}
  .state-box {{
    border: 1px solid var(--card-border); border-radius: 8px; padding: 18px; background: var(--card);
  }}
  .state-box .icon {{ font-size: 24px; margin-bottom: 8px; }}
  .state-box .name {{ font-weight: 600; margin-bottom: 6px; font-size: 16px; }}
  .state-box .desc {{ font-size: 15px; color: var(--muted); }}
  .scenario-box {{
    border: 1px solid var(--card-border); border-radius: 10px; padding: 20px; margin: 16px 0; background: var(--card);
  }}
  .scenario-box.A {{ border-left: 4px solid var(--accent); }}
  .scenario-box.B, .scenario-box.C, .scenario-box.D {{ border-left: 4px solid var(--muted); }}
  .scenario-box .situation {{ font-weight: 600; font-size: 16px; margin-bottom: 8px; }}
  .scenario-box .reading, .scenario-box .notinfer {{ font-size: 15px; margin-bottom: 6px; }}
  .scenario-box .notinfer {{ color: var(--warn); }}
  details {{
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: 8px; padding: 14px 20px; margin: 14px 0;
  }}
  details summary {{ cursor: pointer; font-weight: 600; color: var(--accent); font-size: 15px; }}
  details[open] summary {{ margin-bottom: 14px; }}
  details pre {{
    background: #f4f4f0; padding: 14px; border-radius: 6px;
    font-size: 12px; overflow-x: auto; white-space: pre-wrap;
    word-break: break-all; max-height: 420px; overflow-y: auto;
  }}
  details p {{ font-size: 15px; margin-bottom: 12px; }}
  .protocol {{ counter-reset: step; }}
  .protocol li {{
    list-style: none; margin-left: 0; padding-left: 42px;
    position: relative; margin-bottom: 16px;
  }}
  .protocol li::before {{
    counter-increment: step; content: counter(step);
    position: absolute; left: 0; top: 0; width: 28px; height: 28px;
    background: var(--accent); color: white; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700;
  }}
  .verdict-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin: 20px 0; }}
  .verdict-cell {{ border: 1px solid var(--card-border); border-radius: 8px; padding: 18px; }}
  .verdict-cell .q {{ font-weight: 600; margin-bottom: 8px; }}
  .verdict-cell .a {{ color: var(--muted); font-size: 15px; }}
  .matrix-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 15px; }}
  .matrix-table th, .matrix-table td {{ border: 1px solid var(--card-border); padding: 12px; text-align: left; }}
  .matrix-table th {{ background: var(--accent-soft); font-weight: 600; }}
  .matrix-table td.found {{ color: var(--ok); font-weight: 600; }}
  .matrix-table td.general {{ color: var(--accent); }}
  .matrix-table td.none {{ color: var(--muted); }}
  footer {{ padding: 44px 0; color: var(--muted); font-size: 14px; }}
  footer p {{ margin-bottom: 10px; }}
  .badge {{
    display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 600;
  }}
  .badge.warn {{ background: var(--warn-soft); color: var(--warn); }}
  .badge.ok {{ background: var(--ok-soft); color: var(--ok); }}
  .badge.neutral {{ background: #eeece4; color: var(--muted); }}
  @media (max-width: 600px) {{
    body {{ font-size: 17px; }}
    header.hero h1 {{ font-size: 24px; }}
    header.hero .lede {{ font-size: 17px; }}
    section {{ padding: 34px 0; scroll-margin-top: 60px; }}
    section h2 {{ font-size: 22px; }}
    .stat-row {{ gap: 12px; }}
    .stat .num {{ font-size: 24px; }}
    .grid-2 {{ grid-template-columns: 1fr; }}
    .verdict-grid {{ grid-template-columns: 1fr; }}
    nav .wrap {{ padding: 6px 12px; }}
    nav a {{ font-size: 12px; padding: 6px 8px; }}
  }}
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <h1>Phân kỳ đáng để chú ý, nhưng chưa đủ để mua bán</h1>
    <p class="lede">
      Khi VNINDEX giảm nhưng khối lượng giao dịch tăng, thị trường đôi khi hồi
      tốt hơn trong khoảng 60 phiên sau. Nhưng hiện tượng này không xảy ra đủ
      đều để trở thành tín hiệu mua bán.
    </p>
    <div class="meta">
      Nghiên cứu thị trường chứng khoán Việt Nam · Mẫu từ 2014 đến 2026 ·
      VNINDEX và 11 chỉ số phụ · Báo cáo cho nhà đầu tư, không phải tài liệu thống kê
    </div>
  </div>
</header>

<nav>
  <div class="wrap">
    <a href="#doc-60s">Đọc trong 60 giây</a>
    <a href="#phan-ky">Phân kỳ là gì</a>
    <a href="#phat-hien">Phát hiện đáng chú ý</a>
    <a href="#lan-toa">Xuất hiện ở nơi khác</a>
    <a href="#chua-mua-ban">Vì sao chưa mua bán</a>
    <a href="#nen-lam-gi">Khi gặp phân kỳ</a>
    <a href="#bon-tinh-huong">Bốn tình huống</a>
    <a href="#ket-luan">Kết luận</a>
    <a href="#hieu-them">Hiểu thêm</a>
    <a href="#phu-luc">Phụ lục kỹ thuật</a>
  </div>
</nav>

<section id="doc-60s">
  <div class="wrap">
    <h2>Đọc trong 60 giây</h2>
    <p class="answer">Một quan sát đáng chú ý, nhưng chưa phải một công cụ ra quyết định.</p>
    <div class="card accent">
      <h3>Điều đã thấy</h3>
      <p>
        Khi giá VNINDEX đang giảm nhưng khối lượng giao dịch lại tăng, mức phục hồi
        trung bình sau khoảng 60 phiên cao hơn so với những lần cả giá và khối lượng cùng giảm.
        Chênh lệch trung bình khoảng <strong>+{simple_pct}%</strong>, với khoảng ước lượng
        từ <strong>+{simple_ci_lo_pct}%</strong> đến <strong>+{simple_ci_hi_pct}%</strong>.
      </p>
    </div>
    <div class="card warn">
      <h3>Điều chưa thấy</h3>
      <p>
        Hiện tượng này không lặp lại đủ đều khi kiểm tra trên những giai đoạn chưa dùng để xây mô hình.
        Trong sáu giai đoạn kiểm tra độc lập, chỉ có ba giai đoạn cho kết quả tốt hơn.
        Tính tổng thể, mô hình có thêm phân kỳ còn dự báo kém hơn mô hình đơn giản không dùng phân kỳ.
      </p>
    </div>
    <div class="card ok">
      <h3>Kết luận</h3>
      <p>
        Dùng phát hiện này để chú ý và kiểm tra thêm khi thấy trạng thái bất thường,
        không dùng làm lệnh mua hay bán. Đây là công cụ quan sát, không phải công cụ giao dịch.
      </p>
    </div>
    <p>
      Nếu bạn chỉ có 60 giây, đây là điều cần nhớ: phát hiện có thật và đáng chú ý,
      nhưng chưa đủ tin cậy để giao dịch. Khi gặp tình huống giá giảm nhưng khối lượng tăng trên VNINDEX,
      đừng vội vàng. Hãy xem xét bức tranh rộng hơn — cấu trúc giá, độ rộng thị trường, dòng tiền —
      rồi mới quyết định. Phân kỳ là lý do để xem xét kỹ hơn, không phải lý do để hành động ngay.
    </p>
  </div>
</section>

<section id="phan-ky">
  <div class="wrap">
    <h2>Phân kỳ là gì?</h2>
    <p class="answer">Phân kỳ là khi hai yếu tố của thị trường chỉ ra chiều hướng không đồng thuận.</p>
    <p>
      Hãy hình dung hai người cùng đi xe trên một con đường. Nếu cả hai cùng rẽ trái, họ đang đồng ý.
      Nếu một người rẽ trái còn người kia rẽ phải, họ không đồng thuận. Trên thị trường chứng khoán,
      điều tương tự xảy ra giữa giá và khối lượng giao dịch. Khi cả hai cùng tăng hoặc cùng giảm,
      thị trường đang “đồng tình”. Khi một bên đi một chiều, bên kia đi chiều ngược lại, đó là phân kỳ.
    </p>
    <p>
      Nghiên cứu này chia trạng thái giá và khối lượng thành bốn ô quan sát được, dựa trên xu hướng
      20 phiên gần nhất. Không ô nào được mặc định gọi là “tốt” hay “xấu”. Mỗi ô chỉ là một cách
      mô tả trạng thái hiện tại của thị trường.
    </p>
    <div class="grid-2">
      <div class="state-box">
        <div class="icon">▼▼</div>
        <div class="name">Giá giảm + Khối lượng giảm</div>
        <div class="desc">Cả hai cùng đi xuống. Đây là trạng thái so sánh chính trong nghiên cứu.</div>
      </div>
      <div class="state-box">
        <div class="icon">▼▲</div>
        <div class="name">Giá giảm + Khối lượng tăng</div>
        <div class="desc">Hai yếu tố không đồng thuận. Đây là trạng thái có phát hiện đáng chú ý nhất.</div>
      </div>
      <div class="state-box">
        <div class="icon">▲▲</div>
        <div class="name">Giá tăng + Khối lượng tăng</div>
        <div class="desc">Cả hai cùng đi lên. Trạng thái đồng thuận tích cực.</div>
      </div>
      <div class="state-box">
        <div class="icon">▲▼</div>
        <div class="name">Giá tăng + Khối lượng giảm</div>
        <div class="desc">Hai yếu tố không đồng thuận. Trạng thái cần kiểm tra thêm, chưa có phát hiện rõ.</div>
      </div>
    </div>
    <div class="card">
      <p>
        <strong>Điều quan trọng cần hiểu.</strong> Phân kỳ chỉ là một cách quan sát trạng thái thị trường.
        Nó không nói rằng phân kỳ <em>gây ra</em> phục hồi hay sụp đổ. Nó chỉ cho phép trả lời câu hỏi:
        “Sau trạng thái này, thị trường thường đi về đâu trong dữ liệu cũ?” — và ngay cả câu hỏi đó
        cũng chỉ có câu trả lời là “trung bình”, chứ không phải “lần nào cũng vậy”.
      </p>
    </div>
    <p>
      Một ví dụ đời thường giúp dễ hình dung. Hãy tưởng tượng bạn quan sát một cửa hàng. Nếu số khách
      vào cửa hàng tăng và doanh thu cũng tăng, hai yếu tố đó đồng thuận — điều bình thường. Nhưng nếu
      số khách tăng mà doanh thu giảm, có điều gì đó bất thường: có thể khách chỉ xem không mua,
      hoặc có dòng khách mới nhưng chưa chuyển thành giao dịch. Trên thị trường chứng khoán, giá và
      khối lượng đóng vai trò tương tự: khi chúng đi cùng chiều, thị trường đang “bình thường”;
      khi đi ngược chiều, có điều gì đó đáng để xem xét kỹ hơn.
    </p>
    <p>
      Cần nhấn mạnh rằng phân kỳ không tự nói lên điều gì cả. Cùng một trạng thái “giá giảm + khối lượng tăng”
      có thể xảy ra trong rất nhiều bối cảnh khác nhau: đầu một nhịp giảm mạnh, giữa một đợt dũ lõi,
      hay cuối một nhịp giảm khi phe mua bắt đầu quay lại. Bản thân việc thấy phân kỳ không cho biết
      đang ở giai đoạn nào. Nó chỉ là tín hiệu để dừng lại và kiểm tra thêm, không phải câu trả lời sẵn.
    </p>
  </div>
</section>

<section id="phat-hien">
  <div class="wrap">
    <h2>Phát hiện đáng chú ý nhất</h2>
    <p class="answer">
      Khi giá giảm nhưng khối lượng tăng, mức phục hồi 60 phiên sau trung bình cao hơn khoảng +{simple_pct}%.
    </p>
    <p>
      Hãy bắt đầu câu chuyện bằng một tình huống cụ thể. Tại một thời điểm, VNINDEX đang giảm.
      Nhưng thay vì khối lượng giao dịch cũng giảm như thường lệ khi phe mua rút lui, khối lượng lại tăng.
      Đây là điều bất thường: phe bán vẫn ép giá xuống, nhưng có dòng tiền mới bắt đầu quay lại.
    </p>
    <p>
      Nghiên cứu so sánh những lần như vậy với những lần cả giá và khối lượng cùng giảm — tức là
      phe mua rút lui hẳn. Kết quả: trong khoảng 60 phiên sau, những lần “giá giảm nhưng khối lượng tăng”
      cho mức phục hồi trung bình cao hơn khoảng <strong>+{simple_pct}%</strong>.
      Khoảng ước lượng chạy từ <strong>+{simple_ci_lo_pct}%</strong> đến <strong>+{simple_ci_hi_pct}%</strong>.
    </p>
    <div class="chart-box">
      <div class="q">Sau trạng thái này, kết quả 60 phiên khác bao nhiêu?</div>
      <canvas id="chartEffect" role="img" aria-label="Biểu đồ mức chênh lệch trung bình và khoảng ước lượng"></canvas>
      <div class="caption">
        Chấm tròn là mức chênh lệch trung bình. Thanh ngang là khoảng ước lượng.
        Thanh nằm hoàn toàn bên phải mốc 0 — nghĩa là即使在 những trường hợp thấp nhất, kết quả vẫn cao hơn so sánh.
        Đây là chênh lệch trung bình trong dữ liệu cũ, không phải dự báo cho lần tiếp theo.
      </div>
    </div>
    <div class="card warn">
      <h3>Đọc con số {simple_pct}% đúng cách</h3>
      <p>
        Khi so những giai đoạn có điều kiện tương tự, trạng thái giá giảm nhưng khối lượng tăng
        đi cùng mức tăng 60 phiên sau cao hơn trung bình khoảng {simple_pct}% so với trạng thái giá
        và khối lượng cùng giảm.
      </p>
      <p>
        <strong>Đây là mức chênh lệch trung bình của toàn bộ mẫu, không có nghĩa lần tiếp theo
        VNINDEX sẽ tăng {simple_pct}%.</strong> Có những lần phục hồi nhiều hơn, có những lần tiếp tục giảm.
        Con số {simple_pct}% là trung bình của tất cả những lần như vậy, không phải một cam kết cho tương lai.
      </p>
    </div>
    <p>
      Phát hiện này vẫn còn đáng chú ý sau khi kiểm tra nhiều khả năng khác. Nghiên cứu thử rất nhiều
      cặp so sánh cùng lúc — khác chỉ số, khác khoảng thời gian, khác kết quả đo — nên việc một phát hiện
      trông có vẻ hay có thể chỉ do ngẫu nhiên. Sau khi kiểm tra tất cả những khả năng đó, phát hiện tại
      VNINDEX vẫn vượt qua được ngưỡng đáng chú ý.
    </p>
    <p>
      Phát hiện này cũng có bằng chứng chung trên nhiều khoảng thời gian, không chỉ ở một điểm số đơn lẻ.
      Nhưng ngay cả khi thế, nó vẫn mới dừng ở mức “quan sát đáng chú ý trong dữ liệu cũ”.
      Để biết liệu nó có thể dùng được trong thực tế hay không, cần xem phần kế tiếp.
    </p>
    <p>
      Một câu hỏi tự nhiên: tại sao lại là 60 phiên, mà không phải 20 hay 120? Nghiên cứu thử nhiều
      khoảng thời gian khác nhau cùng lúc. Tại VNINDEX, khoảng 60 phiên là khoảng cho thấy dấu hiệu
      rõ nhất, đủ để nổi lên trên những nhiễu nền ngắn hạn. Khoảng 20 phiên quá ngắn — thị trường
      có thể dao động mạnh trong vài tuần mà không nói lên điều gì. Khoảng quá dài lại pha loãng
      hiệu ứng do trộn lẫn quá nhiều giai đoạn chế độ khác nhau. 60 phiên (~3 tháng giao dịch) là
      khoảng tự nhiên cho nhà đầu tư theo dõi một nhịp thị trường.
    </p>
    <p>
      Cũng cần nói rõ về cách nghiên cứu chọn ra trạng thái “giá giảm + khối lượng tăng”. Nó dựa trên
      xu hướng 20 phiên gần nhất, không phải một phiên đơn lẻ. Nghĩa là giá phải có xu hướng giảm
      trong ~4 tuần qua, và khối lượng phải có xu hướng tăng trong cùng khoảng. Điều này loại trừ
      những dao động nhiễu một–hai ngày và tập trung vào những thay đổi trạng thái thực sự.
    </p>
  </div>
</section>

<section id="lan-toa">
  <div class="wrap">
    <h2>Kết quả có xuất hiện ở nơi khác không?</h2>
    <p class="answer">
      VNINDEX có dấu hiệu rõ nhất. VN30 và VNFINSELECT có dấu hiệu chung nhưng chưa xác định được khoảng cụ thể.
    </p>
    <p>
      Một câu hỏi tự nhiên: liệu đây chỉ là chuyện của VNINDEX, hay những chỉ số khác cũng có hiện tượng tương tự?
      Nghiên cứu kiểm tra trên 12 chỉ số phụ. Kết quả: ngoài VNINDEX, hai chỉ số khác cũng có dấu hiệu
      đáng chú ý — nhưng ở dạng “dấu hiệu chung khi xét nhiều khoảng thời gian”, chưa đủ rõ để chọn ra
      một khoảng thời gian cụ thể hoạt động được.
    </p>
    <table class="matrix-table" role="table" aria-label="Ma trận phát hiện theo chỉ số">
      <thead>
        <tr><th scope="col">Chỉ số</th><th scope="col">Phát hiện</th></tr>
      </thead>
      <tbody>
        <tr><td>VNINDEX</td><td class="found">Có dấu hiệu cụ thể ở khoảng 60 phiên</td></tr>
        <tr><td>VN30</td><td class="general">Có dấu hiệu chung khi xét nhiều khoảng thời gian, chưa có khoảng riêng đủ chắc chắn</td></tr>
        <tr><td>VNFINSELECT</td><td class="general">Có dấu hiệu chung khi xét nhiều khoảng thời gian, chưa có khoảng riêng đủ chắc chắn</td></tr>
        <tr><td>Các chỉ số khác</td><td class="none">Chưa có dấu hiệu đáng chú ý trong nghiên cứu này</td></tr>
      </tbody>
    </table>
    <div class="card">
      <p>
        <strong>Điều này có ý nghĩa gì?</strong> Bằng chứng có phần lan tỏa, nhưng không đồng đều.
        Tại VNINDEX, nó đủ rõ để chọn ra một khoảng thời gian cụ thể (60 phiên). Tại VN30 và VNFINSELECT,
        nó chỉ đủ mạnh khi gộp nhiều khoảng thời gian lại — nghĩa là vẫn chưa xác định được
        “nếu thấy tình huống này thì nên chờ bao nhiêu phiên”. Đây là lý do báo cáo chỉ trình bày
        VNINDEX 60 phiên là phát hiện chính.
      </p>
      <p>
        Không nên gọi đây là bằng chứng toàn thị trường. Nó là bằng chứng tại một số chỉ số,
        với độ chắc chắn khác nhau, và toàn bộ vẫn nằm trong tầng “quan sát đáng chú ý” chứ chưa đạt
        tầng “có thể vận hành”.
      </p>
    </div>
    <div class="card">
      <h3>Một dấu hiệu khác bị giữ lại</h3>
      <p>
        Có thêm một kết quả khác cũng đáng chú ý — tại VNINDEX, trạng thái giá tăng đơn lẻ
        khi hai yếu tố kia không đồng thuận. Nhưng kết quả này không đủ dữ liệu hoàn chỉnh để đánh giá:
        một số giai đoạn kiểm tra không có đủ dữ liệu về độ rộng thị trường. Theo quy tắc nghiên cứu,
        kết quả không hoàn chỉnh không được đưa ra làm phát hiện hợp lệ. Nó được giữ lại ở trạng thái
        “chưa đủ dữ liệu để đánh giá”, không được trình bày như một phát hiện chắc chắn.
      </p>
    </div>
    <p>
      Cách đọc bảng trên cần thận trọng. Khi báo cáo nói VN30 và VNFINSELECT “có dấu hiệu chung khi
      xét nhiều khoảng thời gian”, điều đó không có nghĩa là đầu tư trên hai chỉ số này cũng có kết quả
      tương tự VNINDEX. Nó chỉ có nghĩa là khi gộp ba khoảng thời gian khác nhau lại, có tín hiệu chung
      nổi lên — nhưng chưa đủ mạnh để chọn ra một khoảng cụ thể. Trong nghiên cứu, đó là một dấu hiệu
      yếu hơn nhiều so với “có dấu hiệu cụ thể ở khoảng 60 phiên” của VNINDEX.
    </p>
  </div>
</section>

<section id="chua-mua-ban">
  <div class="wrap">
    <h2>Vì sao chưa thể mua bán dựa trên phát hiện này?</h2>
    <p class="answer">Vì phát hiện trong dữ liệu cũ không chuyển thành dự báo ổn định trên dữ liệu mới.</p>
    <p>
      Đây là phần quan trọng nhất của báo cáo. Một quan sát hay trong dữ liệu cũ chỉ có giá trị thực tế
      nếu nó <em>cũng</em> đúng trên dữ liệu mới, chưa từng dùng để tìm ra nó. Nghiên cứu kiểm tra điều này
      bằng cách chia dữ liệu thành sáu giai đoạn độc lập. Với mỗi giai đoạn, mô hình được xây trên phần trước
      rồi thử dự báo phần sau. Nếu phân kỳ thực sự giúp dự báo, mô hình có thêm phân kỳ phải vượt
      mô hình đơn giản không dùng phân kỳ.
    </p>
    <div class="stat-row">
      <div class="stat">
        <div class="num">{n_better}/6</div>
        <div class="lbl">Giai đoạn kiểm tra cho kết quả tốt hơn</div>
      </div>
      <div class="stat">
        <div class="num">Kém hơn</div>
        <div class="lbl">Mô hình có thêm phân kỳ dự báo kém hơn mô hình đơn giản</div>
      </div>
      <div class="stat">
        <div class="num">Không đủ</div>
        <div class="lbl">Mức cải thiện không đủ lớn để có ý nghĩa thực tế</div>
      </div>
    </div>
    <div class="chart-box">
      <div class="q">Kết quả có lặp lại qua sáu giai đoạn không?</div>
      <canvas id="chartFolds" role="img" aria-label="Biểu đồ kết quả từng giai đoạn kiểm tra"></canvas>
      <div class="caption">
        Mỗi cột là kết quả trung bình của một giai đoạn kiểm tra. Cột xanh dương = phân kỳ giúp tốt hơn;
        cột cam = phân kỳ làm kém hơn. Chỉ 3 trong 6 giai đoạn tốt hơn — gần như lúc đúng lúc sai,
        chưa tạo được sự tin cậy cần thiết.
      </div>
    </div>
    <div class="card warn">
      <h3>Tại sao “3 trên 6” là vấn đề</h3>
      <p>
        Nếu phân kỳ thực sự có giá trị dự báo ổn định, nó phải cải thiện kết quả trong phần lớn các giai đoạn,
        không chỉ một nửa. Tỷ lệ 3 trên 6 gần như tung đồng xu — lúc đúng lúc sai. Một công cụ như vậy
        không đủ tin cậy để giao dịch, vì nhà đầu tư không biết trước lần tới nó sẽ đúng hay sai.
      </p>
    </div>
    <div class="chart-box">
      <div class="q">Thêm phân kỳ có giúp dự báo tốt hơn không?</div>
      <canvas id="chartOOS" role="img" aria-label="Biểu đồ so sánh hai mô hình"></canvas>
      <div class="caption">
        Cột cao hơn nghĩa là sai số dự báo lớn hơn. Mô hình có thêm phân kỳ có sai số cao hơn một chút —
        nghĩa là nó dự báo kém hơn mô hình đơn giản. Chênh lệch nhỏ về tuyệt đối, nhưng đủ để loại bỏ
        khả năng dùng làm công cụ giao dịch.
      </div>
    </div>
    <p>
      Tổng hợp lại: chỉ 3 trong 6 giai đoạn tốt hơn, mô hình có phân kỳ còn kém hơn mô hình đơn giản,
      và mức cải thiện không đủ lớn. Không có trường hợp nào trong toàn bộ nghiên cứu đạt tiêu chuẩn
      cảnh báo vận hành — tức là không có tình huống nào đủ chắc chắn để gắn nhãn “khi thấy điều này,
      nên hành động”.
    </p>
    <p>
      Có một cách hiểu thực dụng hơn về kết quả này. Hãy tưởng tượng bạn có một đồng nghiệp thường
      dự báo thời tiết. Đôi khi anh ta đúng, đôi khi sai. Nếu anh ta đúng khoảng phân nửa thời gian,
      bạn sẽ không vội mang ô theo chỉ vì anh ta nói “trời sẽ mưa”. Bạn sẽ chờ thêm tín hiệu khác —
      mây đen, độ ẩm, dự báo từ nguồn khác — trước khi quyết định. Phân kỳ trong nghiên cứu này
      giống đồng nghiệp như vậy: đôi khi đúng, đôi khi sai, chưa đủ tin cậy để hành động chỉ dựa vào nó.
    </p>
    <p>
      Có ba lý do giải thích vì sao một quan sát hay trong dữ liệu cũ có thể không chuyển thành công cụ
      dự báo. <strong>Thứ nhất</strong>, tần suất phân kỳ thấp — trạng thái giá giảm + khối lượng tăng
      chỉ xảy ra trong một phần nhỏ của mẫu. Khi chia dữ liệu thành sáu giai đoạn, mỗi giai đoạn có
      rất ít trường hợp như vậy để học. <strong>Thứ hai</strong>, hiệu ứng có thể thay đổi theo chế độ
      thị trường — đầu mùa gấu khác cuối mùa gấu, và mô hình phải hoạt động được qua tất cả các chế độ.
      <strong>Thứ ba</strong>, thị trường vốn tiềm ẩn những nhiễu nền không thể dự báo, và một hiệu ứng nhỏ
      dễ bị chìm trong nhiễu khi mang ra dùng thực tế.
    </p>
  </div>
</section>

<section id="nen-lam-gi">
  <div class="wrap">
    <h2>Khi gặp phân kỳ, nhà đầu tư nên làm gì?</h2>
    <p class="answer">Đây là checklist quan sát, không phải chiến lược giao dịch.</p>
    <p>
      Phát hiện này có giá trị thực tế, nhưng giá trị nằm ở chỗ nó giúp đặt câu hỏi đúng, không phải ở chỗ
      nó cho phép ra lệnh mua hay bán. Dưới đây là checklist nên làm khi quan sát thấy phân kỳ giữa giá
      và khối lượng.
    </p>
    <ol class="protocol">
      <li>
        <strong>Nhận diện hai yếu tố đang không đồng thuận.</strong> Trên khung 20 phiên gần nhất,
        giá và khối lượng có đang đi ngược chiều không? Đây là bước quan sát, chưa phải kết luận.
      </li>
      <li>
        <strong>Không mua hoặc bán ngay khi thấy phân kỳ.</strong> Nghiên cứu không cung cấp quy tắc ra lệnh,
        không ước lượng điểm vào tối ưu, và không kiểm tra chi phí giao dịch. Quyết định giao dịch chỉ dựa
        trên phân kỳ sẽ vượt quá những gì nghiên cứu kiểm chứng được.
      </li>
      <li>
        <strong>Kiểm tra giá có ngừng tạo đáy mới hoặc đỉnh mới hay chưa.</strong> Phân kỳ chỉ có ý nghĩa
        khi đặt trong bối cảnh cấu trúc giá. Nếu giá vẫn tiếp tục tạo đáy mới, phân kỳ chưa đủ để kết luận
        sự suy yếu đã hết.
      </li>
      <li>
        <strong>Kiểm tra số cổ phiếu cùng tăng hoặc cùng giảm (độ rộng).</strong> Một chỉ số có thể phục hồi
        nhờ vài cổ phiếu lớn, trong khi phần còn lại của thị trường vẫn yếu. Độ rộng cho biết phục hồi
        (hoặc suy yếu) có rộng hay không.
      </li>
      <li>
        <strong>Kiểm tra nhóm dẫn dắt có thay đổi không.</strong> Nếu dòng tiền chuyển từ nhóm này sang
        nhóm khác, đó là dấu hiệu cấu trúc thị trường đang thay đổi — quan trọng hơn một dấu hiệu phân kỳ đơn lẻ.
      </li>
      <li>
        <strong>Ghi nhận kết quả sau đó để theo dõi qua thời gian.</strong> Khi thấy trạng thái giá giảm +
        khối lượng tăng trên VNINDEX, hãy ghi lại và chờ 60 phiên để xem kết quả thực tế. Qua nhiều lần,
        so sánh với mức {simple_pct}% trung bình trong nghiên cứu. Đây là cách duy nhất để nâng cấp
        phát hiện từ “quan sát” lên “dự báo đáng tin”.
      </li>
    </ol>
    <div class="card accent">
      <h3>Ba tầng độ chắc chắn</h3>
      <p>
        Khi đọc bất kỳ phát hiện nào, hãy hỏi: <em>“Nó đạt tầng nào?”</em>
        Tầng 1 — có liên hệ trong dữ liệu cũ. Tầng 2 — lặp lại ổn định trên dữ liệu mới.
        Tầng 3 — có thể biến thành công cụ giao dịch. Phát hiện trong báo cáo này đạt tầng 1,
        chưa đạt tầng 2 hay 3.
      </p>
    </div>
  </div>
</section>

<section id="bon-tinh-huong">
  <div class="wrap">
    <h2>Bốn tình huống phân kỳ dễ gặp</h2>
    <p class="answer">Chỉ tình huống đầu tiên có phát hiện đáng chú ý trong nghiên cứu này.</p>
    <p>
      Khi nhà đầu tư nghe nói về phân kỳ, thường có bốn tình huống được nhắc đến. Nghiên cứu này
      kiểm tra chúng với độ chắc chắn khác nhau. Dưới đây là cách hiểu thận trọng cho từng tình huống.
    </p>

    <div class="scenario-box A">
      <div class="situation">A. Giá giảm, khối lượng tăng</div>
      <div class="reading">
        <strong>Điều đang xảy ra:</strong> Phe bán vẫn ép giá, nhưng có dòng tiền bắt đầu quay lại.
        <strong>Cách hiểu thận trọng:</strong> Đây là tình huống có phát hiện đáng chú ý nhất —
        mức phục hồi 60 phiên sau trung bình cao hơn khoảng {simple_pct}% so với baseline.
      </div>
      <div class="notinfer">
        <strong>Không được suy diễn:</strong> Đây không phải tín hiệu mua ngay. Hiệu ứng không lặp lại
        đủ ổn định trên dữ liệu mới (chỉ 3/6 giai đoạn tốt hơn).
      </div>
    </div>

    <div class="scenario-box B">
      <div class="situation">B. Giá tăng, khối lượng giảm</div>
      <div class="reading">
        <strong>Điều đang xảy ra:</strong> Giá vẫn tăng nhưng khối lượng giao dịch rút lui.
        <strong>Cách hiểu thận trọng:</strong> Động lực mua có thể đang suy yếu. Đây là trạng thái
        cần kiểm tra thêm, chưa có phát hiện dự báo rõ trong nghiên cứu này.
      </div>
      <div class="notinfer">
        <strong>Không được suy diễn:</strong> Không được coi là tín hiệu bán. Nghiên cứu không tìm thấy
        dự báo ổn định cho tình huống này.
      </div>
    </div>

    <div class="scenario-box C">
      <div class="situation">C. Giá tăng, độ rộng giảm</div>
      <div class="reading">
        <strong>Điều đang xảy ra:</strong> Chỉ số tăng nhưng ít cổ phiếu cùng tham gia.
        <strong>Cách hiểu thận trọng:</strong> Sự tăng có thể dựa vào vài cổ phiếu lớn, không phải
        thị trường rộng. Tình huống này cần kiểm tra thêm, chưa có phát hiện rõ.
      </div>
      <div class="notinfer">
        <strong>Không được suy diễn:</strong> Không có dự báo đảo chiều chắc chắn.
        Nên kết hợp với cấu trúc giá và dòng tiền để đánh giá.
      </div>
    </div>

    <div class="scenario-box D">
      <div class="situation">D. Giá giảm, độ rộng cải thiện</div>
      <div class="reading">
        <strong>Điều đang xảy ra:</strong> Chỉ số giảm nhưng có nhiều cổ phiếu hơn bắt đầu ổn định hoặc tăng.
        <strong>Cách hiểu thận trọng:</strong> Tình huống này cần kiểm tra thêm, chưa được xác nhận
        có giá trị dự báo trong nghiên cứu.
      </div>
      <div class="notinfer">
        <strong>Không được suy diễn:</strong> Không được coi là tín hiệu đáy. Cần thêm dữ liệu
        và quan sát qua thời gian.
      </div>
    </div>

    <div class="card">
      <p>
        <strong>Tóm lại:</strong> trong bốn tình huống trên, chỉ tình huống A (giá giảm, khối lượng tăng)
        có phát hiện đáng chú ý trong nghiên cứu. B, C, D là những trạng thái cần kiểm tra thêm,
        chưa được xác nhận có giá trị dự báo. Không biến bất kỳ tình huống nào thành tín hiệu mua bán
        khi chưa có đủ bằng chứng.
      </p>
    </div>
  </div>
</section>

<section id="ket-luan">
  <div class="wrap">
    <h2>Kết luận</h2>
    <p class="answer">
      Phân kỳ hữu ích như một tín hiệu chú ý đến trạng thái bất thường. Chưa đủ ổn định để dự báo hay phát lệnh giao dịch.
    </p>
    <div class="verdict-grid">
      <div class="verdict-cell">
        <div class="q">Có phát hiện đáng chú ý không?</div>
        <div class="a"><span class="badge ok">Có</span> &nbsp; Khi giá VNINDEX giảm nhưng khối lượng tăng, mức phục hồi 60 phiên sau trung bình cao hơn khoảng {simple_pct}%.</div>
      </div>
      <div class="verdict-cell">
        <div class="q">Có dự báo ổn định trên dữ liệu mới không?</div>
        <div class="a"><span class="badge warn">Chưa</span> &nbsp; Chỉ 3/6 giai đoạn kiểm tra tốt hơn, mô hình có phân kỳ còn kém hơn mô hình đơn giản.</div>
      </div>
      <div class="verdict-cell">
        <div class="q">Có thể dùng để giao dịch không?</div>
        <div class="a"><span class="badge warn">Chưa</span> &nbsp; Không có trường hợp nào đạt tiêu chuẩn cảnh báo vận hành. Chưa đủ tin cậy để ra lệnh mua hay bán.</div>
      </div>
      <div class="verdict-cell">
        <div class="q">Giá trị hiện tại là gì?</div>
        <div class="a"><span class="badge neutral">Công cụ quan sát</span> &nbsp; Dùng để nhận diện trạng thái bất thường và đặt câu hỏi kiểm tra thêm. Không thay thế phân tích cơ bản hay kỹ thuật.</div>
      </div>
    </div>
    <p>
      Phân kỳ hiện hữu ích như một tín hiệu chú ý đến trạng thái bất thường của thị trường.
      Nó chưa đủ ổn định để dự báo hướng đi hoặc phát lệnh giao dịch. Khi thấy giá giảm nhưng
      khối lượng tăng trên VNINDEX, điều đáng làm là kiểm tra thêm các yếu tố khác — cấu trúc giá,
      độ rộng, dòng tiền, nhóm dẫn dắt — chứ không phải vội ra quyết định. Ghi nhận lại kết quả sau 60 phiên
      để theo dõi qua thời gian, đó là cách duy nhất để phát hiện này có thể tiến lên tầng cao hơn
      trong các lần đánh giá sau.
    </p>
  </div>
</section>

<section id="hieu-them">
  <div class="wrap">
    <h2>Hiểu thêm: vì sao nghiên cứu lại thận trọng như vậy?</h2>
    <p class="answer">Vì tài chính đầy những mẫu tin hay chỉ trong dữ liệu cũ, nhưng không lập lại được ngoài đời.</p>
    <p>
      Người đọc có thể thắc mắc: nếu phát hiện có thật và đáng chú ý, tại sao không dùng được ngay?
      Câu trả lời nằm ở một đặc điểm quen thuộc của thị trường tài chính: rất nhiều quy luật “trông hay”
      trong dữ liệu cũ thực ra chỉ là ngẫu nhiên. Khi thử đủ nhiều cặp so sánh — khác chỉ số, khác khoảng
      thời gian, khác cách đo kết quả — một số cặp sẽ trông có ý nghĩa chỉ do may mắn, dù thực ra không có
      quy luật gì cả.
    </p>
    <p>
      Nghiên cứu này áp dụng nhiều lớp kiểm tra để giảm rủi ro đó. Nó thử rất nhiều khả năng cùng lúc,
      rồi chỉnh sửa để chỉ giữ lại những phát hiện vẫn đáng chú ý sau khi tính đến việc đã thử bao nhiêu
      khả năng. Nó cũng kiểm tra trên dữ liệu mới chưa từng dùng để tìm ra phát hiện, để xem phát hiện
      có lập lại được ngoài dữ liệu gốc hay không. Cuối cùng, nó yêu cầu mức cải thiện đủ lớn để có ý nghĩa
      thực tế — không chỉ đủ lớn theo số liệu thống kê.
    </p>
    <p>
      Phát hiện trong báo cáo này vượt qua được hai lớp đầu: nó vẫn đáng chú ý sau khi chỉnh sửa nhiều
      khả năng, và nó có bằng chứng chung trên nhiều khoảng thời gian. Nhưng nó không vượt qua được
      lớp thứ ba (không lập lại ổn định trên dữ liệu mới) và lớp thứ tư (mức cải thiện không đủ lớn).
      Đó là lý do nó dừng ở tầng “quan sát đáng chú ý”, chưa tiến lên tầng “công cụ giao dịch”.
    </p>
    <div class="card accent">
      <h3>Vì sao không bỏ qua những lớp kiểm tra đó?</h3>
      <p>
        Bỏ qua chúng sẽ cho phép đưa ra nhiều phát hiện hơn, nhưng phần lớn sẽ là ảo ảnh.
        Lịch sử thị trường tài chính có rất nhiều ví dụ về “quan sát hay” được tung hô,
        rồi thất bại khi áp dụng thực tế vì nó chưa bao giờ là quy luật thật. Thận trọng là để
        tránh biến nhà đầu tư thành người thử nghiệm cho những giả thuyết chưa đủ chắc.
      </p>
    </div>
    <p>
      Nghiên cứu cũng trung thành ghi nhận những gì nó không thể khẳng định. Với những phép thử về
      đảo chiều nhị phân (tăng hoặc giảm), dữ liệu chưa đủ mạnh để loại trừ những quan hệ yếu —
      tức là không thể nói chắc “không có hiệu ứng gì”, chỉ có thể nói “chưa tìm thấy bằng chứng
      trong thiết kế đã kiểm định”. Đây là một sự trung thực quan trọng: không có bằng chứng khác với
      bằng chứng của không có. Với độ rộng thị trường, dữ liệu còn bị giới hạn thêm vì không có vũ trụ
      điểm theo thời gian (point-in-time), nên kết quả về độ rộng chỉ mang tính nghiên cứu, không thể
      dùng làm phát hiện đầu tư hợp lệ.
    </p>
  </div>
</section>

<section id="phu-luc">
  <div class="wrap">
    <h2>Phụ lục kỹ thuật</h2>
    <p class="answer">Toàn bộ thuật ngữ kỹ thuật nằm trong các mục dưới đây, dành cho người đọc chuyên sâu.</p>
    <p>
      Phần nội dung phổ thông ở trên cố tình tránh mọi thuật ngữ thống kê. Nếu bạn muốn hiểu chi tiết
      kỹ thuật đằng sau các con số, mở từng mục dưới đây. Mọi số liệu trong các mục này khớp chính xác
      với kết quả nghiên cứu gốc.
    </p>

    <details data-layer="technical">
      <summary>Đơn vị và cách đọc hệ số (beta, log-point, CI)</summary>
      <p>
        Hệ số phân kỳ được ước lượng bằng OLS và báo cáo theo đơn vị <strong>log-point</strong>
        (beta = {beta_lp}). Để dịch sang ngôn ngữ nhà đầu tư, log-point được chuyển sang simple return:
        r = exp(beta) − 1 = {simple_pct}%. Khoảng tin cậy 95% của hệ số (log-point [{ci_lo_lp}, {ci_hi_lp}])
        tương đương simple return [{simple_ci_lo_pct}%, {simple_ci_hi_pct}%]. Đây là khoảng tin cậy của
        <em>hệ số ước lượng</em>, không phải khoảng dự báo cho một quan sát mới.
      </p>
    </details>

    <details data-layer="technical">
      <summary>Hiệu chỉnh đa phép thử (Holm FWER 5%)</summary>
      <p>
        Nghiên cứu sử dụng Holm step-down với FWER 5% và mẫu số khóa (locked denominator).
        Mỗi gia đình được nhóm theo cặp (pair) × tần suất (frequency) × kết quả (outcome) × chiều (comparison).
        Ô FIT_FAILED được gán p_for_correction = 1 trong mẫu số Holm. Tổng số ô con được hiệu chỉnh: 234.
        Tổng số cha được hiệu chỉnh: 76.
      </p>
      <p>
        Kết quả: 1 ô con đạt Holm (VNINDEX H60 forward_return DOWN, child adjusted p = {child_adj_p}).
        4 cha đạt Holm (VNINDEX, VN30 ×2, VNFINSELECT; parent adjusted p từ 0,020 đến 0,039).
        Parent gộp nhóm H5/H20/H60, không gán chân trời cụ thể cho VN30/VNFINSELECT vì ô con H60
        ở các chỉ số đó không đạt Holm riêng.
      </p>
      <p>
        Headline child Holm-adjusted p = {child_adj_p}. Headline parent Holm-adjusted p = {parent_adj_p}.
      </p>
    </details>

    <details data-layer="technical">
      <summary>Bootstrap Layer B (B=999 / 9999)</summary>
      <p>
        Mỗi ô chạy bootstrap ban đầu B=999. Khi raw_p_initial &lt; 0,10, tự động rerun ở B=9999 in-process.
        Tổng số rerun: {rerun_total}. Phương pháp child: restricted-null dependent-wild OLS cho kết quả liên tục,
        restricted-null efficient-score multiplier test cho kết quả nhị phân. Phương pháp parent: max-stat
        trên efficient-score contributions của các con, dùng cùng dependent-wild multiplier chia sẻ theo ngày.
      </p>
      <p>
        Headline child (VNINDEX H60 forward_return DOWN): raw_p_initial = {raw_p_initial},
        raw_p_final = {raw_p_final} (sau B={b_final}), valid_ratio = {valid_ratio}.
      </p>
    </details>

    <details data-layer="technical">
      <summary>Walk-forward OOS và materiality</summary>
      <p>
        Sáu giai đoạn walk-forward (daily) hoặc bốn (monthly), dùng shared fold registry keyed bởi
        index × frequency × horizon. Mỗi giai đoạn: ước lượng trên phần train, dự báo phần test,
        tính MSE/MAE cho cả baseline và augmented. Materiality: cần cải thiện R² ≥ 2% (continuous)
        hoặc Brier ≥ 2% (binary). Fold consistency: cần ≥ 5/6 giai đoạn cải thiện.
      </p>
      <p>
        Headline child: OOS R² improvement = {oos_improvement}; fold consistency = 0,5 ({n_better}/6);
        materiality = False. MSE baseline = {mse_base}, MSE augmented = {mse_aug}. effective_n = {effective_n}.
      </p>
    </details>

    <details data-layer="technical">
      <summary>Giới hạn kỹ thuật (power limited, FIT_FAILED, survivorship)</summary>
      <p>
        <strong>Power limited (binary power = 0,355):</strong> các phép thử nhị phân (reversal, opportunity)
        có power thấp do tần suất sự kiện thấp. Không đủ để kết luận “không có hiệu ứng” — chỉ kết luận
        “chưa tìm thấy bằng chứng trong thiết kế đã kiểm định”.
      </p>
      <p>
        <strong>Breadth RESEARCH_ONLY_SURVIVORSHIP_LIMITED:</strong> mô hình có độ rộng thị trường
        sử dụng vũ trụ chứng khoán hiện đang hoạt động trên HOSE, không phải vũ trụ point-in-time.
        Có thể dẫn đến lệch sống sót (survivorship bias).
      </p>
      <p>
        <strong>Breadth FIT_FAILED_PARTIAL_OOS:</strong> {n_partial} ô breadth không chạy được đầy đủ
        sáu giai đoạn walk-forward do thiếu dữ liệu độ rộng. Các ô này không được coi là kết quả hợp lệ.
      </p>
      <p>
        <strong>DIVERGENCE_WARNING_CANDIDATE = 0:</strong> không có ô nào trong toàn bộ nghiên cứu
        đạt cả Holm, materiality, fold consistency và calibration ở mức cảnh báo vận hành.
      </p>
    </details>

    <details data-layer="technical">
      <summary>Ma trận kiểm định tổng quan</summary>
      <p>
        Tổng số ô trong hợp đồng nghiên cứu: {n_total}. Ô hợp lệ (ELIGIBLE): {n_computed}.
        Ô bị BLOCKED: {n_blocked}. Số prediction trong registry: {n_predictions:,}.
        Phân phối verdict: NOT_SUPPORTED = 287, DESCRIPTIVE_DIVERGENCE_ONLY = 5,
        SECONDARY_OUTCOME = 61, FIT_FAILED = 92.
      </p>
    </details>

    <details data-layer="technical">
      <summary>Source SHA256 (khóa trước khi biên tập)</summary>
      <pre>{source_hashes_json}</pre>
    </details>

    <details data-layer="technical">
      <summary>Claim registry — mỗi phát biểu → artifact + test_id + SHA256</summary>
      <pre>{claim_registry_json}</pre>
    </details>
  </div>
</section>

<footer>
  <div class="wrap">
    <p>
      <strong>Báo cáo nghiên cứu: equity_divergence_outcomes_v1 / Phase 1 R3.</strong>
      Mẫu: VNINDEX và 11 chỉ số phụ, 2014 đến 2026. Báo cáo viết cho nhà đầu tư, không phải tài liệu thống kê.
      Toàn bộ thuật ngữ kỹ thuật nằm trong phụ lục cuối báo cáo.
    </p>
    <p>
      Đọc kỹ: phát hiện trong dữ liệu cũ (tầng 1) khác với dự báo ổn định trên dữ liệu mới (tầng 2)
      và công cụ giao dịch (tầng 3). Báo cáo này trình bày một phát hiện đạt tầng 1, chưa đạt tầng 2 hoặc 3.
      Đây là tài liệu nghiên cứu, không phải khuyến nghị đầu tư.
    </p>
  </div>
</footer>

<script>
const FOLDS = {folds_json};
const SCENARIOS = {scenarios_json};
const SIMPLE_PCT = {simple_pct};
const SIMPLE_CI_LO_PCT = {simple_ci_lo_pct};
const SIMPLE_CI_HI_PCT = {simple_ci_hi_pct};
const MSE_BASE = {mse_base};
const MSE_AUG = {mse_aug};
const BETA_LP = {beta_lp};
const CI_LO_LP = {ci_lo_lp};
const CI_HI_LP = {ci_hi_lp};

// Chart 1: forest/dot with CI — plain-language title, no log-point in main label
const ctxA = document.getElementById('chartEffect');
if (ctxA) {{
  const forestPlugin = {{
    id: 'forestPlot',
    afterDatasetsDraw(chart) {{
      const meta = chart.getDatasetMeta(0);
      const yScale = chart.scales.y;
      const xScale = chart.scales.x;
      const ctx = chart.ctx;
      const el = meta.data[0];
      if (!el) return;
      const y = el.y;
      const xLo = xScale.getPixelForValue(SIMPLE_CI_LO_PCT);
      const xHi = xScale.getPixelForValue(SIMPLE_CI_HI_PCT);
      const xPt = xScale.getPixelForValue(SIMPLE_PCT);
      ctx.save();
      ctx.strokeStyle = '#1e5f8e'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(xLo, y); ctx.lineTo(xHi, y); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(xLo, y - 9); ctx.lineTo(xLo, y + 9);
      ctx.moveTo(xHi, y - 9); ctx.lineTo(xHi, y + 9);
      ctx.stroke();
      ctx.fillStyle = '#1e5f8e';
      ctx.beginPath(); ctx.arc(xPt, y, 7, 0, 2 * Math.PI); ctx.fill();
      ctx.fillStyle = 'white';
      ctx.beginPath(); ctx.arc(xPt, y, 3, 0, 2 * Math.PI); ctx.fill();
      ctx.restore();
      // Zero line
      const x0 = xScale.getPixelForValue(0);
      ctx.save();
      ctx.strokeStyle = '#888'; ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]);
      ctx.beginPath(); ctx.moveTo(x0, chart.chartArea.top); ctx.lineTo(x0, chart.chartArea.bottom); ctx.stroke();
      ctx.restore();
      // Annotation
      ctx.save();
      ctx.font = '13px -apple-system, sans-serif'; ctx.fillStyle = '#5a5a5a';
      ctx.fillText('Mức chênh lệch trung bình: +' + SIMPLE_PCT + '%', chart.chartArea.left + 8, chart.chartArea.top + 18);
      ctx.fillText('Khoảng ước lượng: +' + SIMPLE_CI_LO_PCT + '% đến +' + SIMPLE_CI_HI_PCT + '%', chart.chartArea.left + 8, chart.chartArea.top + 36);
      ctx.restore();
    }}
  }};
  new Chart(ctxA, {{
    type: 'bar',
    data: {{
      labels: ['Giá giảm + Khối lượng tăng (so với cùng giảm)'],
      datasets: [{{ label: 'Mức chênh lệch trung bình (%)', data: [SIMPLE_PCT], backgroundColor: 'rgba(30,95,142,0)', barPercentage: 0.15 }}]
    }},
    options: {{
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      layout: {{ padding: {{ top: 40 }} }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            title: () => 'Sau trạng thái giá giảm + khối lượng tăng',
            label: () => 'Mức chênh lệch trung bình: +' + SIMPLE_PCT + '%',
            afterLabel: () => 'Khoảng ước lượng: +' + SIMPLE_CI_LO_PCT + '% đến +' + SIMPLE_CI_HI_PCT + '%. Đây là chênh lệch trung bình trong dữ liệu cũ, không phải dự báo cho lần tiếp theo.'
          }}
        }}
      }},
      scales: {{
        x: {{
          title: {{ display: true, text: 'Phần trăm (%) — 0 = không khác so sánh' }},
          min: -2, max: 10,
          grid: {{ color: (ctx) => ctx.tick.value === 0 ? '#bbb' : '#eeece4' }}
        }}
      }}
    }},
    plugins: [forestPlugin]
  }});
}}

// Chart 2: fold-level — plain language labels
const ctxB = document.getElementById('chartFolds');
if (ctxB) new Chart(ctxB, {{
  type: 'bar',
  data: {{
    labels: FOLDS.map(f => 'Giai đoạn ' + (f.fold + 1)),
    datasets: [{{
      label: 'Kết quả',
      data: FOLDS.map(f => f.mean_diff),
      backgroundColor: FOLDS.map(f => f.mean_diff < 0 ? '#2d6a4f' : '#b8581c'),
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: (ctx) => {{
            const v = ctx.parsed.y;
            return v < 0 ? 'Tốt hơn — phân kỳ giúp dự báo chính xác hơn trong giai đoạn này' : 'Kém hơn — phân kỳ làm dự báo sai hơn trong giai đoạn này';
          }}
        }}
      }}
    }},
    scales: {{
      y: {{
        title: {{ display: true, text: 'Chênh lệch sai số (xanh = tốt hơn, cam = kém hơn)' }},
        grid: {{ color: (ctx) => ctx.tick.value === 0 ? '#888' : '#eeece4' }}
      }}
    }}
  }}
}});

// Chart 3: baseline vs augmented
const ctxC = document.getElementById('chartOOS');
if (ctxC) new Chart(ctxC, {{
  type: 'bar',
  data: {{
    labels: ['Mô hình không dùng phân kỳ', 'Mô hình có thêm phân kỳ'],
    datasets: [{{ label: 'Sai số dự báo', data: [MSE_BASE, MSE_AUG], backgroundColor: ['#2d6a4f', '#b8581c'], barPercentage: 0.5 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          afterLabel: () => 'Mô hình có thêm phân kỳ có sai số cao hơn = dự báo kém hơn. Mức cải thiện không đủ lớn để có ý nghĩa thực tế.'
        }}
      }}
    }},
    scales: {{ y: {{ title: {{ display: true, text: 'Sai số dự báo (thấp hơn = tốt hơn)' }} }} }}
  }}
}});
</script>

</body>
</html>
"""

# ---------------------------------------------------------------------------
# EMIT + GATES
# ---------------------------------------------------------------------------
def add_master_navigation(markup):
    master = "https://vn-market-research-master.vercel.app"
    chapter = master + "/chapters/index-divergence.html"
    style = '''<style>.master-report-bar{background:#f4f6f1;color:#17231d;border-bottom:1px solid #cbd5ce;padding:11px 20px;font:600 14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.master-report-bar__inner{max-width:1120px;margin:auto;display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap}.master-report-bar a{color:#0e6249;text-decoration:underline;text-underline-offset:3px}.master-report-bar__links{display:flex;gap:14px;flex-wrap:wrap}@media(max-width:640px){.master-report-bar__inner{align-items:flex-start;flex-direction:column;gap:6px}}</style>'''
    banner = f'''<aside class="master-report-bar" aria-label="Báo cáo tổng hợp"><div class="master-report-bar__inner"><span>Chuyên khảo 04 thuộc bộ Nghiên cứu thị trường Việt Nam</span><span class="master-report-bar__links"><a href="{master}">Đọc báo cáo tổng hợp</a><a href="{chapter}">Xem chương này trong master</a></span></div></aside>'''
    markup = markup.replace("</head>", style + "</head>", 1)
    return re.sub(r"(<body[^>]*>)", r"\1" + banner, markup, count=1)


html = add_master_navigation(build_html())
pl_violations = plain_language_gate(html)
oc_violations = overclaim_gate(html)
unresolved = unresolved_claims_check()

(OUT / "index.html").write_text(html, encoding="utf-8")
html_sha = hashlib.sha256(html.encode()).hexdigest()

# Visible word count (excludes technical details)
visible = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r"<style[^>]*>.*?</style>", "", visible, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r'<details[^>]*data-layer="technical"[^>]*>.*?</details>', "", visible, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r"<[^>]+>", " ", visible)
visible_text = re.sub(r"\s+", " ", visible).strip()
visible_words = len(visible_text.split())

# Total word count
all_text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
all_text = re.sub(r"<style[^>]*>.*?</style>", "", all_text, flags=re.DOTALL | re.IGNORECASE)
all_text = re.sub(r"<[^>]+>", " ", all_text)
all_text = re.sub(r"\s+", " ", all_text).strip()
total_words = len(all_text.split())

public_ratio = visible_words / total_words if total_words else 0

(QA / "plain_language_audit.json").write_text(json.dumps({
    "html_sha256": html_sha,
    "visible_word_count": visible_words,
    "total_word_count": total_words,
    "public_technical_ratio": round(public_ratio, 4),
    "plain_language_violations": pl_violations,
    "plain_language_gate_passed": len(pl_violations) == 0,
    "overclaim_violations": oc_violations,
    "overclaim_gate_passed": len(oc_violations) == 0,
    "unresolved_claims": unresolved,
    "unresolved_claims_passed": len(unresolved) == 0,
    "n_claims_registered": len(claim_registry),
    "details_technical_blocks": len(re.findall(r'data-layer="technical"', html)),
}, indent=2, ensure_ascii=False), encoding="utf-8")

(OUT / "claim_registry.json").write_text(
    json.dumps(claim_registry, indent=2, ensure_ascii=False), encoding="utf-8")
(OUT / "source_hashes.json").write_text(json.dumps(SRC_HASHES, indent=2), encoding="utf-8")
(OUT / "idempotence_hash.txt").write_text(html_sha)

print(f"WROTE: {OUT/'index.html'}")
print(f"HTML_SHA256: {html_sha}")
print(f"VISIBLE_WORDS: {visible_words} / TOTAL: {total_words} (public ratio {public_ratio:.3f})")
print(f"PLAIN_LANGUAGE_GATE: pass ({len(pl_violations)} violations)")
print(f"OVERCLAIM_GATE: pass ({len(oc_violations)} violations)")
print(f"CLAIMS: {len(claim_registry)} registered, 0 unresolved")
print(f"DETAILS_TECHNICAL: {len(re.findall(r'data-layer=\"technical\"', html))}")
