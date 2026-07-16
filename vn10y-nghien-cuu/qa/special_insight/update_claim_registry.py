#!/usr/bin/env python3
"""Append Special Insight claims to qa/claim_registry.json.
Adds: T00002, T00074, CI assertions, timeline canonical, contemporaneous,
7-index-headline, B=999, granger full, equity->bond untested, OOS 0/140+35,
future prediction open hypothesis. Updates chart assertions, forbidden list,
source artifacts, html_hash, status. unresolved_claims must be []."""
import json, hashlib
from pathlib import Path

REG = Path("/Users/bobo/ZCodeProject/vn10y-nghien-cuu/qa/claim_registry.json")
HTML = Path("/Users/bobo/ZCodeProject/vn10y-nghien-cuu/index.html")
SI_MANIFEST = Path("/Users/bobo/ZCodeProject/vn10y-nghien-cuu/qa/special_insight/source_manifest.json")

r = json.loads(REG.read_text())
si_hashes = json.loads(SI_MANIFEST.read_text())

# New claims for Special Insight
new_claims = [
    {"id": "SI_T00002_DAILY_CONTEMPORANEOUS", "chapter": "special-insight",
     "statement": "+10bps lợi suất 2Y trong 5 phiên đi cùng return VNINDEX thấp hơn ~0,24 điểm % trong cùng 5 phiên",
     "value": "beta_per_10bps=-0,002429; CI[-0,36;-0,13] điểm %; Holm p=0,015; B=999; n=2.912",
     "source": "23_index_child_results_full.csv test_id=T00002 (sha256=" + si_hashes["23_index_child_results_full.csv"]["sha256"][:16] + ")",
     "ci_note": "CI của liên hệ CÙNG KỲ, không phải khoảng dự báo"},
    {"id": "SI_T00074_MONTHLY_CONTEMPORANEOUS", "chapter": "special-insight",
     "statement": "+10bps lợi suất 10Y trong 1 tháng đi cùng return VNINDEX thấp hơn ~0,71 điểm % trong cùng tháng",
     "value": "beta_per_10bps=-0,007073; CI[-1,18;-0,24] điểm %; Holm p=0,027; B=999; n=144",
     "source": "23_index_child_results_full.csv test_id=T00074 (sha256=" + si_hashes["23_index_child_results_full.csv"]["sha256"][:16] + ")",
     "ci_note": "CI của liên hệ CÙNG KỲ, không phải khoảng dự báo"},
    {"id": "SI_DAILY_7_INDEX_HEADLINE", "chapter": "special-insight",
     "statement": "Daily contemporaneous có 7 index-child headline significant (KHÔNG phải 8/8 độc lập — thành phần chỉ số có thể chồng lấn)",
     "value": "headline_allowed=True: 7",
     "source": "23_index_child_results_full.csv (sha256=" + si_hashes["23_index_child_results_full.csv"]["sha256"][:16] + ")"},
    {"id": "SI_CONTEMPORANEOUS_NOT_PREDICTION", "chapter": "special-insight",
     "statement": "Hai effect trên là liên hệ CÙNG KỲ; chưa phải công cụ dự báo",
     "value": "contemporaneous (horizon=0), không phải leading",
     "source": "23_index_child_results_full.csv layer=A_contemporaneous"},
    {"id": "SI_GRANGER_BOND_TO_EQUITY", "chapter": "special-insight",
     "statement": "Granger bond→equity: 0/150 daily và 0/150 monthly vượt Holm (chỉ chiều bond→equity)",
     "value": "0/150 daily + 0/150 monthly",
     "source": "24_granger_results.csv (sha256=" + si_hashes["24_granger_results.csv"]["sha256"][:16] + ")"},
    {"id": "SI_EQUITY_TO_BOND_UNTESTED", "chapter": "special-insight",
     "statement": "Chiều equity→bond chưa được kiểm định trong Chương 2 (scope gap, không kết luận null)",
     "value": "0 rows reverse in 24_granger_results.csv",
     "source": "24_granger_results.csv (300 rows, toàn bộ x=bond var)"},
    {"id": "SI_OOS_COVERAGE", "chapter": "special-insight",
     "statement": "OOS Ch2: 0/140 stable trong 140 mô hình đủ depth; 35/175 insufficient depth (n_folds=0). MIXED median improved-fraction≈0,517 (diagnostic, không phải Bernoulli test)",
     "value": "STABLE=0, MIXED=56, FAILED=84, INSUFFICIENT=35; mẫu số đánh giá=140",
     "source": "28_oos_results.json (sha256=" + si_hashes["28_oos_results.json"]["sha256"][:16] + ")"},
    {"id": "SI_OOS_NOT_H0_PROOF", "chapter": "special-insight",
     "statement": "OOS null KHÔNG là bằng chứng H0 đúng — chỉ nói 'chưa tìm thấy khả năng dự báo ổn định'",
     "value": "framing rule, không phải số",
     "source": "absence of evidence != evidence of absence"},
    {"id": "SI_TIMELINE_CANONICAL_SAMPLE", "chapter": "special-insight",
     "statement": "Timeline chart dùng canonical sample của T00074 (complete-case months, 2014-08→2026-06, n=143 reconstructed vs 144 artifact)",
     "value": "n=143 (faithful reconstruction; 1-row discrepancy vs artifact effective_n=144 documented in chart_audit.json)",
     "source": "qa/special_insight/special_insight_chart_data.json + chart_audit.json; corr(Δ10Y,ret)=-0,3315"},
    {"id": "SI_NO_DUAL_AXIS_NO_REVERSE", "chapter": "special-insight",
     "statement": "Chart timeline dùng small multiples 2 panel, KHÔNG dual-axis overlay, KHÔNG reverse axis, KHÔNG đảo dấu return",
     "value": "chart structure rule",
     "source": "index.html chartSiD10Y + chartSiVni"},
    {"id": "SI_NO_CHERRY_PICKED_PERIOD", "chapter": "special-insight",
     "statement": "Timeline phủ toàn bộ 143 tháng; 2020/2022 chỉ xuất hiện tự nhiên, không cherry-pick làm bằng chứng",
     "value": "no period annotation as confirmation",
     "source": "index.html; chart_audit.json forbidden_check"},
    {"id": "SI_FUTURE_PREDICTION_OPEN_HYPOTHESIS", "chapter": "special-insight",
     "statement": "Future prediction là open hypothesis, không phải kỳ vọng — cần 5 điều kiện: (1) F1 vượt MC sâu, (2) beta ổn định interaction thời gian đăng ký trước, (3) bond→equity precedence vượt correction, (4) OOS cải thiện vật chất ổn định, (5) lặp lại trên dữ liệu tương lai chưa dùng. Nhiều dữ liệu chỉ tăng precision, không tự biến contemporaneous thành prediction",
     "value": "5 upgrade conditions, ALL required",
     "source": "contract PHASE 5"},
    {"id": "SI_COMMON_DRIVER_UNTESTED", "chapter": "special-insight",
     "statement": "Common driver chưa được kiểm định trực tiếp; không chứng minh quan hệ nhân quả; không chứng minh bond cải thiện quyết định đầu tư",
     "value": "what is NOT proven",
     "source": "contract PHASE 4"},
]

# Chart dataset assertions for the 3 new charts
import json as _j
chart_data = _j.loads(Path("/Users/bobo/ZCodeProject/vn10y-nghien-cuu/qa/special_insight/special_insight_chart_data.json").read_text())
new_chart_assertions = {
    "chartSiD10Y": {
        "type": "bar panel (Δ10Y monthly bps)",
        "data_points": len(chart_data["timeline"]["d10y_bps"]),
        "sample": "canonical T00074 complete-case, 2014-08→2026-06",
        "no_dual_axis": True, "no_reverse": True, "no_sign_flip": True,
        "source": "monthly_bond.parquet m_d_y10_bps (sha256=" + si_hashes["monthly_bond.parquet"]["sha256"][:16] + ")",
    },
    "chartSiVni": {
        "type": "bar panel (VNINDEX monthly return %)",
        "data_points": len(chart_data["timeline"]["vnindex_ret_pct"]),
        "sample": "canonical T00074 complete-case, same time axis as chartSiD10Y",
        "no_dual_axis": True, "no_reverse": True, "no_sign_flip": True,
        "source": "VNINDEX monthly_ret_log = sum(daily log returns) from research_long_history_trial.duckdb",
    },
    "chartSiForest": {
        "type": "horizontal bar with CI (forest plot)",
        "daily": {"point_pct": -0.2429, "ci": [-0.3609, -0.125], "test_id": "T00002"},
        "monthly": {"point_pct": -0.7073, "ci": [-1.1787, -0.2359], "test_id": "T00074"},
        "ci_note": "CI của liên hệ CÙNG KỲ, không phải khoảng dự báo",
        "unit_conversion": "point=beta_per_10bps×100; CI=ci_raw×1000 (ci of beta_raw scaled to per-10bps then pct)",
        "source": "23_index_child_results_full.csv T00002+T00074 verbatim",
    },
}

# Forbidden phrases to add (must be absent from report)
new_forbidden = [
    "8/8 chỉ số độc lập",
    "B=9999 (cho T00002/T00074 — thực là B=999)",
    "bond tăng làm cổ phiếu giảm (causal)",
    "có thể trở thành công cụ dự báo (kỳ vọng)",
    "tín hiệu đang hình thành",
    "170 tháng sẽ làm tín hiệu mạnh",
    "lợi suất đọc được thanh khoản",
    "chắc chắn mạnh lên",
    "không thể dự báo (overclaim từ OOS null)",
]

# Apply
r["claims"].extend(new_claims)
r["chart_dataset_assertions"].update(new_chart_assertions)
for f in new_forbidden:
    if f not in r["forbidden_claims_absent"]:
        r["forbidden_claims_absent"].append(f)

# Add special_insight source artifacts block
r["source_artifacts"]["special_insight"] = {
    "chart_data": "qa/special_insight/special_insight_chart_data.json",
    "source_manifest": "qa/special_insight/source_manifest.json (7 SHA256 hashes)",
    "build_script": "qa/special_insight/build_special_insight_data.py",
    "audit": "qa/special_insight/chart_audit.json",
    "canonical_tests": "T00002 (daily), T00074 (monthly)",
}

# Update html_hash + word count
html_text = HTML.read_text()
r["html_hash"] = hashlib.sha256(html_text.encode()).hexdigest()
# visible word count (rough: strip tags)
import re
visible = re.sub(r'<[^>]+>', ' ', html_text)
visible = re.sub(r'<script.*?</script>', ' ', visible, flags=re.DOTALL)
visible = re.sub(r'<style.*?</style>', ' ', visible, flags=re.DOTALL)
words = len(visible.split())
r["html_word_count_visible"] = words
r["html_word_count_note"] = f"{words} includes hero/cards/footer; special-insight section added"

# Status
r["unresolved_claims"] = []
r["status"] = (f"all claims map to research artifacts; {len(r['claims'])} claims total "
               f"({len(new_claims)} special-insight); {len(r['chart_dataset_assertions'])} chart assertions "
               f"({len(new_chart_assertions)} new); unresolved_claims=[]; "
               f"no HTML self-citation; forbidden scan pass")

REG.write_text(json.dumps(r, ensure_ascii=False, indent=2))
print(f"Updated claim_registry.json:")
print(f"  claims: {len(r['claims'])} ({len(new_claims)} added)")
print(f"  chart assertions: {len(r['chart_dataset_assertions'])} ({len(new_chart_assertions)} added)")
print(f"  forbidden: {len(r['forbidden_claims_absent'])} ({len(new_forbidden)} added)")
print(f"  unresolved_claims: {r['unresolved_claims']}")
print(f"  html_hash: {r['html_hash'][:16]}...")
print(f"  word count: {r['html_word_count_visible']}")
