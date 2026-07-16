#!/usr/bin/env python3
"""generate_report.py — Canonical HTML report generator for equity_multivariate_index_forecast_v1.

R2 REWRITE: post-2014 null finding is the headline. Full-sample H5 demoted to
'historical pooled finding driven by pre-2014'. Brier explained correctly
(squared probability error, NOT percentage points). Calibration examples use
actual bins. H5 checkpoint hash locked in source manifest.

Reads FROZEN R9 artifacts (outputs/20-23) + H5 checkpoint from research workdir.
Idempotent: two runs produce identical SHA256.
"""
import json, hashlib, os, re, sys
from pathlib import Path

RESEARCH = Path(os.path.expanduser(
    "~/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_multivariate_index_forecast_v1/outputs"))
OUT = Path(__file__).parent
QA = OUT / "qa"

LOCKED_HASHES = {
    "20_phase1_prediction_registries.json": "f2b72ef1b2f3c70d3207689b5f36ea47f3f7b2e9321ef42da0fb0b1c737f4504",
    "21_phase1_inference.json": "356ab5f9c88f03fd9f06684d40693f8879033d2c64b9fd937c7c9713096e89c9",
    "22_phase1_verdicts.json": "93220fc1e38b2f656bf99c0c04fd708aa7105cac330517fe70a3d6fbc7c229c8",
    "23_phase1_reconciliation.json": "8032749fd10844defd0b38cc0bb03691855267167d774f0881e71cab07c6afae",
}

H5_CHECKPOINT_HASH = "82c47e0022c10098f16595d8c8fa7a10dac7c93a9985521a930ed13ad1a2d0ea"
H5_CHECKPOINT_FILE = "P1_price_volume__VNINDEX__daily__short__H5__direction__confirmatory__P1_vs_P0.json"

FORBIDDEN_IN_PLAIN = [
    "volume dự báo được", "tín hiệu giao dịch", "có thể dùng mua/bán",
    "tín hiệu vẫn hiệu quả", "breadth dự báo được thị trường",
    "sai ít hơn khoảng",
]


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_sources():
    hashes = {}
    ok = True
    for f, expected in LOCKED_HASHES.items():
        actual = sha256_file(RESEARCH / f)
        hashes[f] = actual
        if actual != expected:
            ok = False
    # Also verify H5 checkpoint
    ckpt_path = RESEARCH / "phase1_checkpoint" / H5_CHECKPOINT_FILE
    if ckpt_path.exists():
        ckpt_hash = sha256_file(ckpt_path)
        hashes["h5_checkpoint"] = ckpt_hash
        if ckpt_hash != H5_CHECKPOINT_HASH:
            ok = False
    return ok, hashes


def load_artifacts():
    inf = json.load(open(RESEARCH / "21_phase1_inference.json"))
    ver = json.load(open(RESEARCH / "22_phase1_verdicts.json"))
    return inf, ver


def extract_chart_data(inf, ver):
    import numpy as np
    h5_tid = "P1_price_volume__VNINDEX__daily__short__H5__direction__confirmatory__P1_vs_P0"
    h5_inf = inf["cell_inference"][h5_tid]
    ckpt_path = RESEARCH / "phase1_checkpoint" / H5_CHECKPOINT_FILE
    cr = json.load(open(ckpt_path))
    rows = cr["registry_rows"]

    # Fold chart
    folds = {}
    for r in rows:
        folds.setdefault(r["outer_fold"], []).append((r["loss_aug"], r["loss_ref"]))
    fold_improvements = []
    for fid in sorted(folds):
        los = folds[fid]
        ma, mr = np.mean([l[0] for l in los]), np.mean([l[1] for l in los])
        fold_improvements.append(round(mr - ma, 4))

    # Regime breakdown + post-2014
    per_regime = {}
    for r in rows:
        per_regime.setdefault(r["regime"], []).append(r["paired_loss_diff"])
    total_gain = sum(max(0, -np.sum(v)) for v in per_regime.values())
    regime_labels_map = {"R0": "Trước 2014", "R1": "2014–2018", "R2": "2019–2021", "R3": "2022–2026"}
    regime_data = []
    for reg in sorted(per_regime):
        d_vals = per_regime[reg]
        gain = max(0, -np.sum(d_vals))
        share = gain / total_gain if total_gain > 0 else 0
        regime_data.append({
            "label": regime_labels_map.get(reg, reg),
            "mean_d": round(float(np.mean(d_vals)), 6),
            "improvement": round(float(-np.mean(d_vals)), 6),
            "contribution_share": round(float(share), 4),
            "n": len(d_vals),
        })
    # Post-2014 aggregate
    post_d = [r["paired_loss_diff"] for r in rows if r["regime"] in ("R1", "R2", "R3")]
    post_2014_improvement = round(float(-np.mean(post_d)), 6)

    # Calibration bins
    probs = np.array([r["probability_aug"] for r in rows if r["probability_aug"] is not None])
    y_true = np.array([r["y_true"] for r in rows if r["probability_aug"] is not None])
    bins = np.linspace(0, 1, 11)
    cal_bins = {"centers": [], "actual": [], "predicted": [], "counts": []}
    for i in range(10):
        mask = (probs >= bins[i]) & (probs < bins[i + 1])
        if i == 9:
            mask = (probs >= bins[i]) & (probs <= bins[i + 1])
        if mask.sum() > 0:
            cal_bins["centers"].append(round((bins[i] + bins[i + 1]) / 2, 2))
            cal_bins["actual"].append(round(float(y_true[mask].mean()), 3))
            cal_bins["predicted"].append(round(float(probs[mask].mean()), 3))
            cal_bins["counts"].append(int(mask.sum()))

    # Horizon summary
    horizon_rows = []
    for tid in sorted(ver.keys()):
        if "VNINDEX" not in tid or "P1_vs_P0" not in tid or "direction" not in tid:
            continue
        ci = inf["cell_inference"].get(tid, {})
        suffix = tid.split("__VNINDEX__")[1]
        parts = suffix.split("__")
        horizon_rows.append({
            "freq": parts[0], "hlabel": parts[1], "H": parts[2],
            "model": parts[4] if len(parts) > 4 else "?",
            "verdict": ver[tid],
            "raw_p": ci.get("raw_p_final"),
        })

    return {
        "h5": {
            "tid": h5_tid, "adjusted_p": h5_inf["adjusted_p"],
            "mean_d": h5_inf["mean_d"],
            "brier_improvement": round(-h5_inf["mean_d"], 4),
            "fold_consistency": round(h5_inf["fold_consistency"], 4),
            "n_folds_aug_lower": h5_inf["n_folds_aug_lower"],
            "cal_slope": round(h5_inf["calibration"]["calibration_slope"], 4),
            "cal_intercept": round(h5_inf["calibration"]["calibration_intercept"], 4),
            "cal_gate": h5_inf["calibration"]["calibration_gate"],
            "regime_gate": h5_inf["regime"]["regime_gate"],
            "regime_max_share": round(h5_inf["regime"]["max_contribution_share"], 4),
            "verdict": ver[h5_tid],
        },
        "post_2014_improvement": post_2014_improvement,
        "fold_improvements": fold_improvements,
        "regime_data": regime_data,
        "cal_bins": cal_bins,
        "horizon_rows": horizon_rows,
        "verdict_counts": json.load(open(RESEARCH / "23_phase1_reconciliation.json"))["verdict_counts"],
    }


H5_TID = "P1_price_volume__VNINDEX__daily__short__H5__direction__confirmatory__P1_vs_P0"
VNREAL_H20_TID = "P1_price_volume__VNREAL__daily__medium__H20__direction__confirmatory__P1_vs_P0"
H1_TID = "P1_price_volume__VNINDEX__daily__sensitivity__H1__direction__sensitivity__P1_vs_P0"
FIT_FAILED_IDS = [
    "P0_price_only__VNINDEX__monthly__long__H6__direction__confirmatory__P0_vs_B0",
    "P0_price_only__VNIT__daily__long__H60__direction__confirmatory__P0_vs_B0",
    "P1_price_volume__VNINDEX__monthly__long__H6__direction__confirmatory__P1_vs_P0",
    "P1_price_volume__VNIT__daily__long__H60__direction__confirmatory__P1_vs_P0",
]


def claim_source(artifact, test_id_or_key, sha256):
    """A concrete, hash-pinned R9 source; never a report HTML source."""
    return {"artifact": artifact, "test_id_or_key": test_id_or_key, "sha256": sha256}


def claim_entry(claim_id, claim, exact_value, scope_or_limitation, sources):
    """Every claim has one primary direct mapping and all contributing sources."""
    primary = sources[0]
    return {"id": claim_id, "claim": claim, "artifact": primary["artifact"],
            "test_id_or_key": primary["test_id_or_key"], "sha256": primary["sha256"],
            "exact_value": exact_value, "scope_or_limitation": scope_or_limitation,
            "sources": sources}


def build_claims():
    a21 = "outputs/21_phase1_inference.json"; h21 = LOCKED_HASHES["21_phase1_inference.json"]
    a22 = "outputs/22_phase1_verdicts.json"; h22 = LOCKED_HASHES["22_phase1_verdicts.json"]
    a23 = "outputs/23_phase1_reconciliation.json"; h23 = LOCKED_HASHES["23_phase1_reconciliation.json"]
    ack = f"outputs/phase1_checkpoint/{H5_CHECKPOINT_FILE}"
    hck = H5_CHECKPOINT_HASH
    h5inf = f"cell_inference.{H5_TID}"
    return [
        claim_entry("post_2014_evaluation_descriptive", "Trong các forecast origins từ 2014–2026, Brier improvement mô tả = −0,000435. Đây không phải confirmatory rerun.", "-0.00043518004295662075", "Hậu kỳ trên evaluation origins từ 2014; không phải pipeline train+evaluation được rerun hoàn toàn từ 2014.", [claim_source(ack, "registry_rows[regime in R1,R2,R3].paired_loss_diff", hck)]),
        claim_entry("h5_full_sample", "Toàn mẫu H5 Brier improvement = 0,0352, adjusted p = 0,0006", "brier_improvement=0.035205365670256394; adjusted_p=0.0006000000000000001", "Brier improvement = −mean_d trong pooled H5 confirmatory result; không đủ điều kiện operational khi fold/calibration/regime gates fail.", [claim_source(a21, h5inf + ".mean_d", h21), claim_source(a21, h5inf + ".adjusted_p", h21)]),
        claim_entry("pre_2014_dominance", "98,5% tổng improvement tập trung trước 2014", "R0.contribution_share=0.9853742104376875", "Phân rã pooled OOS H5; không chứng minh hiệu quả ở thị trường hiện đại.", [claim_source(a21, h5inf + ".regime.per_regime.R0.contribution_share", h21)]),
        claim_entry("h5_folds", "Chỉ 2/6 folds cải thiện", "n_folds_aug_lower=2; fold_consistency=0.3333333333333333", "Pooled result không thay thế kiểm tra ổn định theo 6 outer folds.", [claim_source(a21, h5inf + ".n_folds_aug_lower", h21)]),
        claim_entry("h5_calibration", "Calibration slope = −0,10, gate FAIL", "calibration_slope=-0.10160640922145492; calibration_gate=FAIL", "Pooled OOS logistic calibration; slope âm là kết quả calibration, không phải diễn giải causal.", [claim_source(a21, h5inf + ".calibration", h21)]),
        claim_entry("calibration_bin_83", "Nhóm dự báo TB 83,2% → thực tế 44,3%", "predicted=0.832; actual=0.443", "Bin mô tả được generator tính quyết định từ registry_rows H5; không phải artifact nghiên cứu độc lập.", [claim_source(ack, "registry_rows -> deterministic probability bin [0.8,0.9)", hck)]),
        claim_entry("calibration_bin_74", "Nhóm dự báo TB 73,5% → thực tế 51,3%", "predicted=0.735; actual=0.513", "Bin mô tả được generator tính quyết định từ registry_rows H5; không phải artifact nghiên cứu độc lập.", [claim_source(ack, "registry_rows -> deterministic probability bin [0.7,0.8)", hck)]),
        claim_entry("vnreal_h20", "VNREAL H20 adjusted p = 0,0396, secondary UNSTABLE", "adjusted_p=0.0396; verdict=PREDICTIVE_INCREMENTAL_UNSTABLE", "Validation/secondary index, non-operational; calibration and regime gates fail.", [claim_source(a21, f"cell_inference.{VNREAL_H20_TID}", h21), claim_source(a22, VNREAL_H20_TID, h22)]),
        claim_entry("zero_breadth", "0 breadth cells sống sót Holm", "0/24 breadth-family members have adjusted_p<0.05", "Research-only breadth families; 12 direction + 12 return members, not a claim of market predictability.", [claim_source(a21, "family_adjusted.F_BREADTH_DIRECTION_RESEARCH", h21), claim_source(a21, "family_adjusted.F_BREADTH_RETURN_RESEARCH", h21)]),
        claim_entry("zero_return", "0 return cells sống sót Holm", "0/42 P1 return-family members have adjusted_p<0.05", "P1 return families: primary denominator 6 plus validation denominator 36; no return survivor claim.", [claim_source(a21, "family_adjusted.F_PRIMARY_RETURN_P1_VNINDEX", h21), claim_source(a21, "family_adjusted.F_VALIDATION_RETURN_P1", h21)]),
        claim_entry("h1_null", "H1 sensitivity raw p = 0,635, không cải thiện", "raw_p_final=0.635", "Sensitivity-only H1; not confirmatory and not eligible for a headline conclusion.", [claim_source(a21, f"cell_inference.{H1_TID}", h21)]),
        claim_entry("reconciliation", "442 = 220 computed + 222 blocked", "expected_total=442; computed=220; blocked=222", "Matrix accounting only; does not assert an empirical signal.", [claim_source(a23, "expected_total", h23), claim_source(a23, "computed", h23), claim_source(a23, "blocked", h23), claim_source(a23, "expected_equals_computed_plus_blocked", h23)]),
        claim_entry("fit_failed", "4 FIT_FAILED (single-class inner fold)", "FIT_FAILED=4; ids=" + ",".join(FIT_FAILED_IDS), "Persisted fit status; FIT_FAILED cells retain p_for_correction=1 where applicable and do not shrink locked families.", [claim_source(a22, tid, h22) for tid in FIT_FAILED_IDS]),
    ]


def validate_claims(claims):
    required = ("artifact", "test_id_or_key", "sha256", "exact_value", "scope_or_limitation")
    errors = []
    if len(claims) != 13:
        errors.append(f"claim_count={len(claims)}")
    for claim in claims:
        for key in required:
            if not claim.get(key):
                errors.append(f"{claim.get('id')}:missing:{key}")
        sources = claim.get("sources") or []
        if not sources:
            errors.append(f"{claim.get('id')}:missing:sources")
        for source in sources:
            artifact = source.get("artifact", "")
            digest = source.get("sha256", "")
            if "index.html" in artifact or not artifact.startswith("outputs/"):
                errors.append(f"{claim.get('id')}:invalid_artifact:{artifact}")
                continue
            path = RESEARCH.parent / artifact
            if not path.exists() or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest) or sha256_file(path) != digest:
                errors.append(f"{claim.get('id')}:source_hash_mismatch:{artifact}")
    return errors


def build_claim_registry(html_hash, claims):
    errors = validate_claims(claims)
    if errors:
        raise RuntimeError("CLAIM_GOVERNANCE_GATE_FAIL: " + "; ".join(errors))
    return {"authority": {"chain": "R9", "research_root": str(RESEARCH.parent),
                          "h5_checkpoint_role": "derived supplemental artifact"},
            "claims": claims, "unresolved_claims": [], "html_sha256": html_hash}


def build_editorial_audit(html_content):
    return {
        "forbidden_scan": [w for w in FORBIDDEN_IN_PLAIN if w in html_content.lower()],
        "forbidden_gate_pass": not any(w in html_content.lower() for w in FORBIDDEN_IN_PLAIN),
    }


def build_html(data):
    h5 = data["h5"]
    fi = json.dumps(data["fold_improvements"])
    rd = json.dumps(data["regime_data"])
    cb = json.dumps(data["cal_bins"])
    hr = json.dumps(data["horizon_rows"])
    post_imp = data["post_2014_improvement"]

    # Build chart configs as JSON strings to avoid f-string brace issues
    fold_cfg = json.dumps({
        "type": "bar",
        "data": {"labels": ["Fold 1","Fold 2","Fold 3","Fold 4","Fold 5","Fold 6"],
                 "datasets": [{"data": data["fold_improvements"],
                               "backgroundColor": ["#2d8659" if v > 0 else "#c0392b" for v in data["fold_improvements"]],
                               "borderWidth": 0}]},
        "options": {"plugins": {"title": {"display": True, "text": "Cải thiện Brier theo giai đoạn kiểm tra (toàn mẫu H5)"}},
                    "scales": {"y": {"title": {"display": True, "text": "Brier improvement"}}}}})
    cal_cfg = json.dumps({
        "type": "scatter",
        "data": {"datasets": [
            {"data": [{"x": p, "y": a} for p, a in zip(data["cal_bins"]["predicted"], data["cal_bins"]["actual"])],
             "backgroundColor": "#0066cc", "pointRadius": 6},
            {"data": [{"x": 0, "y": 0}, {"x": 1, "y": 1}], "borderColor": "#999", "showLine": True, "pointRadius": 0}]},
        "options": {"plugins": {"title": {"display": True, "text": "Hiệu chuẩn xác suất (H5 toàn mẫu)"}},
                    "scales": {"x": {"title": {"display": True, "text": "Xác suất dự báo"}},
                               "y": {"title": {"display": True, "text": "Tần suất thực tế"}}}}})
    regime_cfg = json.dumps({
        "type": "bar",
        "data": {"labels": [r["label"] for r in data["regime_data"]],
                 "datasets": [{"data": [r["contribution_share"] * 100 for r in data["regime_data"]],
                               "backgroundColor": ["#0066cc", "#e0e0e0", "#e0e0e0", "#e0e0e0"], "borderWidth": 0}]},
        "options": {"plugins": {"title": {"display": True, "text": "Đóng góp cải thiện theo giai đoạn (%)"}},
                    "scales": {"y": {"title": {"display": True, "text": "Đóng góp (%)"}, "max": 100}}}})

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dự Báo VNINDEX: Khối Lượng Có Bổ Sung Gì Từ 2014?</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#fafafa;--card:#fff;--ink:#1a1a1a;--muted:#666;--accent:#0066cc;--good:#2d8659;--bad:#c0392b;--border:#e0e0e0}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6;overflow-x:hidden}}
.container{{max-width:900px;margin:0 auto;padding:20px;overflow-x:hidden}}
.hero{{background:var(--card);border-radius:16px;padding:40px 30px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.hero h1{{font-size:1.7rem;margin-bottom:16px;line-height:1.3}}
.hero p{{font-size:1.05rem;color:var(--muted);margin-bottom:20px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:20px}}
.card{{padding:20px;border-radius:12px;text-align:center;font-size:1rem;font-weight:500}}
.card.bad{{background:#fce4ec;color:var(--bad)}}
.card.warn{{background:#fff3e0;color:#e65100}}
.card.neutral{{background:#f5f5f5;color:#666}}
section{{background:var(--card);border-radius:12px;padding:30px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
section h2{{font-size:1.35rem;margin-bottom:16px;color:var(--accent)}}
section p{{margin-bottom:12px}}
.metric{{display:inline-block;background:var(--bg);padding:4px 12px;border-radius:6px;font-weight:600;margin:2px}}
details{{background:var(--bg);border-radius:8px;padding:16px;margin-top:12px}}
details summary{{cursor:pointer;font-weight:600;color:var(--accent)}}
details[open] summary{{margin-bottom:12px}}
.chart-box{{position:relative;width:100%;margin:16px 0}}
.chart-caption{{font-size:.9rem;color:var(--muted);text-align:center;margin-top:8px}}
table{{width:100%;max-width:100%;border-collapse:collapse;margin:12px 0;font-size:.9rem;table-layout:fixed;word-break:break-word}}
.table-wrap{{overflow-x:auto;overflow-y:hidden;margin:12px 0;max-width:100%}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid var(--border)}}
th{{background:var(--bg);font-weight:600}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.8rem;font-weight:600}}
.badge.unstable{{background:#fff3e0;color:#e65100}}
.badge.none{{background:#f5f5f5;color:#999}}
.badge.failed{{background:#fce4ec;color:#c0392b}}
.badge.sensitivity{{background:#e3f2fd;color:#1565c0}}
footer{{text-align:center;padding:30px;color:var(--muted);font-size:.85rem}}
nav{{position:sticky;top:0;background:var(--bg);z-index:100;padding:10px 0;border-bottom:1px solid var(--border);margin-bottom:20px}}
nav a{{color:var(--accent);text-decoration:none;margin-right:16px;font-size:.9rem}}
nav a:hover{{text-decoration:underline}}
@media(max-width:600px){{.hero h1{{font-size:1.3rem}}.container{{padding:10px}}section{{padding:20px}}}}
@media(max-width:360px){{.container{{padding:5px}}section{{padding:12px;font-size:.9rem}}table{{font-size:.8rem}}th,td{{padding:4px 6px}}}}
</style>
</head>
<body>
<nav class="container"><a href="#hero">Tóm tắt</a><a href="#post2014">Từ 2014</a><a href="#h5">Toàn mẫu</a><a href="#why">Tại sao</a><a href="#conclusion">Kết luận</a></nav>
<div class="container">

<div class="hero" id="hero">
<h1>Trong phần dự báo ngoài mẫu có ngày đánh giá từ 2014 trở đi, nghiên cứu chưa tìm thấy giá trị dự báo bổ sung từ khối lượng giao dịch cho VNINDEX. Kết quả dương trên toàn mẫu gần như hoàn toàn do giai đoạn trước 2014 — khi thị trường còn rất sơ khai.</h1>
<p>Nghiên cứu so sánh mô hình chỉ dùng giá (price-only) với mô hình thêm khối lượng giao dịch (price + volume) để dự báo hướng VNINDEX. Volume = khối lượng cổ phiếu giao dịch, không phải độ biến động (volatility).</p>
<p><em>Đây là phân tích hậu kỳ trên các dự báo đã sinh từ pipeline toàn mẫu. Một số mô hình vẫn được huấn luyện bằng dữ liệu trước 2014. Nghiên cứu chưa chạy lại pipeline với cả training và evaluation bắt đầu từ 2014.</em></p>
<div class="cards">
<div class="card bad">Trong evaluation từ 2014: Brier improvement mô tả = −0,0004 — gần bằng 0</div>
<div class="card warn">Toàn mẫu: cải thiện 0,035 nhưng 98,5% đến từ trước 2014</div>
<div class="card neutral">Kết quả hiện không cho thấy khả năng ứng dụng trong giai đoạn đánh giá 2014–2026</div>
</div>
</div>

<section id="read90">
<h2>Đọc trong 90 giây</h2>
<p><strong>Mô hình chỉ dùng giá (price-only)</strong> dự báo xu hướng VNINDEX dựa vào lịch sử giá: lợi nhuận gần, động lượng, độ biến động, khoảng cách đường trung bình. Đây là nền tảng so sánh.</p>
<p><strong>Mô hình thêm khối lượng (price + volume)</strong> bổ sung thông tin về lượng giao dịch: thay đổi khối lượng, tỷ lệ khối lượng trung bình, khối lượng bất thường. Được so sánh với price-only trên cùng dữ liệu, cùng giai đoạn.</p>
<p><strong>Kết quả chính:</strong> trên toàn bộ dữ liệu (2007–2026), mô hình thêm volume giảm sai số Brier trung bình 0,035. Nhưng khi tách theo giai đoạn, 98,5% cải thiện đến từ trước 2014. <strong>Trong phần dự báo ngoài mẫu có ngày đánh giá từ 2014 trở đi, volume không bổ sung gì — thậm chí hơi kém hơn.</strong></p>
<p><strong>Vì sao?</strong> Thị trường trước 2014 rất sơ khai: thanh khoản mỏng, ít cổ phiếu niêm yết, cấu trúc khác biệt. Cải thiện trong giai đoạn này không thể suy ra cho thị trường hiện tại.</p>
</section>

<section id="post2014">
<h2>Trong evaluation từ 2014 trở đi</h2>
<p>Đây là phân tích hậu kỳ trên các dự báo đã sinh từ pipeline toàn mẫu. Một số mô hình vẫn được huấn luyện bằng dữ liệu trước 2014. Nghiên cứu chưa chạy lại pipeline với cả training và evaluation bắt đầu từ 2014.</p>
<p>Trong các forecast origins có ngày đánh giá từ 2014 trở đi (gồm 2014–2018, 2019–2021, 2022–2026), Brier improvement mô tả = <span class="metric">−0,0004</span>. Đây không phải confirmatory rerun — đây là phân tích mô tả hậu kỳ.</p>
<div class="table-wrap"><table>
<thead><tr><th>Giai đoạn</th><th>Số phiên</th><th>Brier improvement</th><th>Nhận xét</th></tr></thead>
<tbody>
<tr><td>Trước 2014</td><td>1.527</td><td style="color:var(--good)">+0,1068</td><td>Cải thiện lớn — nhưng thị trường sơ khai</td></tr>
<tr><td>2014–2018</td><td>1.205</td><td style="color:var(--bad)">−0,0015</td><td>Volume hơi kém hơn</td></tr>
<tr><td>2019–2021</td><td>752</td><td style="color:var(--good)">+0,0032</td><td>Cải thiện rất nhỏ</td></tr>
<tr><td>2022–2026</td><td>1.109</td><td style="color:var(--bad)">−0,0018</td><td>Volume hơi kém hơn</td></tr>
</tbody>
</table></div>
<div class="chart-box"><canvas id="regimeChart"></canvas></div>
<p class="chart-caption">Giai đoạn trước 2014 chiếm 98,5% tổng cải thiện. Các giai đoạn gần đây không lặp lại kết quả.</p>
</section>

<section id="h5">
<h2>Toàn mẫu: phát hiện lịch sử ở 5 phiên</h2>
<p>Khi gộp toàn bộ dữ liệu 2007–2026, có một tín hiệu thống kê: mô hình thêm volume giảm sai số Brier trung bình <span class="metric">0,035</span> so với price-only. Ngưỡng vật chất tối thiểu là 0,02. Holm-adjusted p = <span class="metric">0,0006</span>.</p>
<p><strong>Brier là gì?</strong> Brier score đo sai số của dự báo xác suất bằng trung bình bình phương chênh lệch giữa xác suất dự báo và kết quả thực. Giá trị thấp hơn là tốt hơn. Cải thiện 0,035 Brier nghĩa là trung bình bình phương sai số giảm 0,035 đơn vị — đây là đơn vị bình phương, không tuyến tính theo xác suất.</p>
<p><strong>Nhưng đây là phát hiện lịch sử.</strong> Cải thiện này gần như hoàn toàn đến từ giai đoạn trước 2014. Verdict: <span class="badge unstable">PREDICTIVE_INCREMENTAL_UNSTABLE</span></p>
<div class="chart-box"><canvas id="foldChart"></canvas></div>
<p class="chart-caption">Chỉ 2/6 giai đoạn kiểm tra cho kết quả tốt hơn. Cải thiện chủ yếu từ giai đoạn đầu.</p>
</section>

<section id="why">
<h2>Tại sao không thể sử dụng</h2>
<p>Ba vấn đề ngăn kết quả toàn mẫu trở thành chỉ báo dùng được:</p>
<p><strong>1. Gần như toàn bộ lợi ích là lịch sử.</strong> 98,5% cải thiện đến từ trước 2014. Từ 2014, volume không bổ sung gì. Thị trường trước 2014 quá sơ khai để suy ra cho hiện tại.</p>
<p><strong>2. Chỉ 2/6 giai đoạn kiểm tra cải thiện.</strong> Nghiên cứu chia dữ liệu thành 6 giai đoạn kiểm tra liên tiếp. Chỉ 2 giai đoạn tốt hơn; 4 giai đoạn còn lại bằng hoặc xấu hơn.</p>
<p><strong>3. Xác suất dự báo bị hiệu chuẩn sai.</strong> Calibration slope = −0,10 (lý tưởng là 1,0). Slope âm nghĩa là mô hình có khả năng sắp hạng xác suất rất yếu hoặc đảo chiều — khi mô hình dự báo cao thì thực tế lại thấp. Ví dụ: nhóm dự báo trung bình 83,2%, tần suất thực tế chỉ 44,3%; nhóm dự báo 73,5%, thực tế 51,3%.</p>
<div class="chart-box"><canvas id="calChart"></canvas></div>
<p class="chart-caption">Xác suất dự báo (trục ngang) không khớp tần suất thực tế (trục đứng). Đường chéo là hiệu chuẩn hoàn hảo.</p>
</section>

<section id="horizons">
<h2>Các khung thời gian khác</h2>
<div class="table-wrap"><table>
<thead><tr><th>Khung thời gian</th><th>Loại</th><th>Kết quả</th></tr></thead>
<tbody>
<tr><td>1 phiên (H1)</td><td>Nhạy cảm</td><td><span class="badge sensitivity">Không cải thiện</span> raw p = 0,635</td></tr>
<tr><td>5 phiên (H5)</td><td>Xác nhận chính</td><td><span class="badge unstable">Không ổn định</span> toàn mẫu có tín hiệu; trong evaluation subset từ 2014 không cải thiện</td></tr>
<tr><td>20 phiên (H20)</td><td>Xác nhận chính</td><td><span class="badge none">Không có bằng chứng</span> trong thiết kế toàn mẫu</td></tr>
<tr><td>60 phiên (H60)</td><td>Xác nhận chính</td><td><span class="badge none">Không có bằng chứng</span> trong thiết kế toàn mẫu</td></tr>
<tr><td>1 tháng</td><td>Xác nhận chính</td><td><span class="badge none">Không có bằng chứng</span> trong thiết kế toàn mẫu</td></tr>
<tr><td>3 tháng</td><td>Xác nhận chính</td><td><span class="badge none">Không có bằng chứng</span> trong thiết kế toàn mẫu</td></tr>
<tr><td>6 tháng</td><td>Xác nhận chính</td><td><span class="badge failed">Không đủ dữ liệu</span></td></tr>
</tbody>
</table></div>
</section>

<section id="vnreal">
<h2>Kết quả riêng VNREAL ở 20 phiên</h2>
<p>VNREAL (chứng khoán bất động sản) ở 20 phiên: adjusted p = 0,0396, secondary validation. Verdict = PREDICTIVE_INCREMENTAL_UNSTABLE. Chỉ áp dụng cho VNREAL, không đại diện toàn thị trường. Không operational.</p>
</section>

<section id="breadth-return">
<h2>Độ rộng thị trường và dự báo lợi suất</h2>
<p><strong>Độ rộng (breadth):</strong> 0 cell sống sót Holm. Breadth không bổ sung dự báo ổn định ngoài price. Breadth vẫn survivorship-limited (không PIT).</p>
<p><strong>Lợi suất (return):</strong> 0 cell return sống sót Holm.</p>
</section>

<section id="conclusion">
<h2>Kết luận</h2>
<p><strong>Trong phần dự báo ngoài mẫu có ngày đánh giá từ 2014 trở đi, nghiên cứu chưa tìm thấy giá trị dự báo bổ sung từ khối lượng giao dịch cho hướng VNINDEX ở khung thời gian H5.</strong> Ở các horizon còn lại (H1, H20, H60, monthly), không có bằng chứng cải thiện trong thiết kế toàn mẫu đã khóa.</p>
<p>Trên toàn mẫu (2007–2026), có một tín hiệu thống kê ở 5 phiên — nhưng gần như hoàn toàn đến từ giai đoạn trước 2014 khi thị trường còn sơ khai. Trong evaluation subset từ 2014, Brier improvement mô tả = −0,0004 (gần bằng 0, hơi âm).</p>
<p><em>Lưu ý: đây là phân tích hậu kỳ trên các dự báo đã sinh từ pipeline toàn mẫu. Một số mô hình vẫn được huấn luyện bằng dữ liệu trước 2014. Nghiên cứu chưa chạy lại pipeline với cả training và evaluation bắt đầu từ 2014.</em></p>
<p>Kết quả hiện không cho thấy khả năng ứng dụng trong giai đoạn đánh giá 2014–2026. Đây là phát hiện nghiên cứu, không phải chỉ báo đầu tư.</p>
</section>

<details>
<summary>Phụ lục kỹ thuật</summary>
<div class="table-wrap"><table>
<tr><td>Tổng phép thử</td><td>442 = 220 computed + 222 blocked</td></tr>
<tr><td>Verdict counts</td><td>BASELINE_DIAGNOSTIC=82, SENSITIVITY_ONLY=28, NO_INCREMENTAL_VALUE=104, PREDICTIVE_INCREMENTAL_UNSTABLE=2, FIT_FAILED=4</td></tr>
<tr><td>Holm denominators</td><td>Primary direction=6, primary return=6, validation direction=36, validation return=36, breadth direction=12, breadth return=12</td></tr>
<tr><td>FIT_FAILED</td><td>4 cells: single-class inner fold</td></tr>
<tr><td>Bootstrap</td><td>B=999, dependent-wild (Shao 2010), plus-one p</td></tr>
<tr><td>Folds</td><td>6 outer contiguous, expanding train, purge+embargo=horizon</td></tr>
<tr><td>Calibration</td><td>Pooled OOS logistic. Operational: slope ∈[0.75,1.25], |intercept|≤0.10</td></tr>
<tr><td>Regime</td><td>4 regimes (PRE_2014, 2014–2018, 2019–2021, 2022–2026). Operational: ≥3/4 pass, max share &lt;0.80</td></tr>
<tr><td>Brier</td><td>mean((p−y)²) — sai số bình phương, không tuyến tính theo xác suất</td></tr>
</table></div>
</details>

<footer>
<p>Báo cáo sinh từ artifacts R9 đã nghiệm thu. Nghiên cứu: equity_multivariate_index_forecast_v1 (v1.7).</p>
<p>Volume = khối lượng giao dịch, không phải volatility. Báo cáo không phải khuyến nghị đầu tư.</p>
</footer>
</div>

<script>
new Chart(document.getElementById('foldChart'), {fold_cfg});
new Chart(document.getElementById('calChart'), {cal_cfg});
new Chart(document.getElementById('regimeChart'), {regime_cfg});
</script>
</body>
</html>"""
    return html


def add_master_navigation(markup):
    master = "https://vn-market-research-master.vercel.app"
    chapter = master + "/chapters/forecast.html"
    style = '''<style>.master-report-bar{background:#f4f6f1;color:#17231d;border-bottom:1px solid #cbd5ce;padding:11px 20px;font:600 14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.master-report-bar__inner{max-width:1120px;margin:auto;display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap}.master-report-bar a{color:#0e6249;text-decoration:underline;text-underline-offset:3px}.master-report-bar__links{display:flex;gap:14px;flex-wrap:wrap}@media(max-width:640px){.master-report-bar__inner{align-items:flex-start;flex-direction:column;gap:6px}}</style>'''
    banner = f'''<aside class="master-report-bar" aria-label="Báo cáo tổng hợp"><div class="master-report-bar__inner"><span>Chuyên khảo 03 thuộc bộ Nghiên cứu thị trường Việt Nam</span><span class="master-report-bar__links"><a href="{master}">Đọc báo cáo tổng hợp</a><a href="{chapter}">Xem chương này trong master</a></span></div></aside>'''
    markup = markup.replace("</head>", style + "</head>", 1)
    return re.sub(r"(<body[^>]*>)", r"\1" + banner, markup, count=1)


def main():
    QA.mkdir(exist_ok=True)
    ok, hashes = verify_sources()
    if not ok:
        print("BLOCKED_SOURCE_MISMATCH")
        sys.exit(1)
    claims = build_claims()
    claim_errors = validate_claims(claims)
    if claim_errors:
        print("BLOCKED_CLAIM_GOVERNANCE: " + "; ".join(claim_errors))
        sys.exit(1)
    inf, ver = load_artifacts()
    data = extract_chart_data(inf, ver)
    html = add_master_navigation(build_html(data))
    html_path = OUT / "index.html"
    html_path.write_text(html, encoding="utf-8")
    html_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()

    source_manifest = {"locked_hashes": LOCKED_HASHES, "actual_hashes": hashes,
                       "h5_checkpoint_hash": H5_CHECKPOINT_HASH}
    (QA / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2))
    (QA / "claim_registry.json").write_text(json.dumps(build_claim_registry(html_hash, claims), indent=2))
    editorial = build_editorial_audit(html)
    (QA / "editorial_audit.json").write_text(json.dumps(editorial, indent=2))

    print(f"HTML SHA256: {html_hash}")
    print(f"forbidden_gate_pass: {editorial['forbidden_gate_pass']}")
    print(f"claims: {len(claims)}, unresolved: 0")


if __name__ == "__main__":
    main()
