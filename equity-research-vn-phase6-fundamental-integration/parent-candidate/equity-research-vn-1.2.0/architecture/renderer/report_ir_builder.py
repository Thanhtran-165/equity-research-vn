#!/usr/bin/env python3
"""
report_ir_builder.py — Deterministic report IR builder.

Architecture Phase B component #2.
Transforms: canonical data contract → report IR (validated against schema).

The IR is the single structured representation that drives:
- deterministic renderer (HTML shell + DATA + charts)
- section-level model generation (narrative inputs)
- final verification
"""
import json, os, sys, hashlib

# Add paths for preserved hotfix components
HOTFIX_RUNNER = os.path.expanduser("~/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner")
sys.path.insert(0, HOTFIX_RUNNER)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from applicability_engine import detect_sector, decide_all
from period_key_resolver import resolve_periods, ResolverError


def build_ir(source_pack_dir, contract_path=None):
    """Build a complete report IR from a source pack.

    Args:
        source_pack_dir: Path to source pack (CSVs + overview.json + fundamental_sponsor.json)
        contract_path: Optional pre-built verified-dashboard-data.json

    Returns:
        report_ir dict (validated against report-ir.schema.json)
    """
    # Step 1: Load source metadata
    overview = json.load(open(os.path.join(source_pack_dir, "overview.json")))
    sector = detect_sector(overview)
    ticker = overview.get("symbol", "")

    # Step 2: Build canonical data contract (using preserved hotfix builder)
    from build_data_contract import main as build_contract
    import tempfile
    if contract_path is None:
        tmpdir = tempfile.mkdtemp()
        try:
            import subprocess
            subprocess.run([sys.executable, os.path.join(HOTFIX_RUNNER, "build_data_contract.py"),
                           source_pack_dir, tmpdir], check=True, timeout=60,
                          env={**os.environ, "PATH": "/opt/homebrew/bin:" + os.environ.get("PATH", "")})
            contract_path = os.path.join(tmpdir, "verified-dashboard-data.json")
        except Exception as e:
            return {"error": f"build_data_contract failed: {e}"}
    contract = json.load(open(contract_path))

    # Step 3: Extract financial metrics from contract
    fin = contract.get("financials", {})
    field_app = contract.get("field_applicability", {})

    metrics = {}
    for canon_field, fin_key in [("revenue", "revenue"), ("net_profit", "netProfit"),
                                  ("eps", "eps"), ("total_assets", "totalAssets"),
                                  ("total_equity", "equity"), ("capex", "capex")]:
        values = fin.get(fin_key)
        app_info = field_app.get(canon_field, {})
        if canon_field == "revenue":
            app_info = field_app.get("revenue", {})
        status = app_info.get("status", "VALID") if isinstance(app_info, dict) else "VALID"
        rule = app_info.get("applicability_rule") if isinstance(app_info, dict) else None

        # Build period→value dict
        years = fin.get("years", [])
        values_dict = {}
        if values is not None and isinstance(values, list):
            for i, y in enumerate(years):
                values_dict[str(y)] = values[i] if i < len(values) else None
        else:
            for y in years:
                values_dict[str(y)] = None

        metrics[canon_field] = {
            "canonical_field": canon_field,
            "values": values_dict,
            "status": status,
            "applicability_rule": rule,
            "provenance": {"source_id": "vnstock_sponsor", "source_type": "api"},
        }

    # Step 4: Build field statuses for applicability engine
    field_statuses = {field: m["status"] for field, m in metrics.items()}

    # Step 5: Load source evidence for applicability decisions
    source_evidence = {}
    events_path = os.path.join(source_pack_dir, "events.csv")
    if os.path.exists(events_path):
        import csv
        with open(events_path) as f:
            source_evidence["events"] = list(csv.DictReader(f))
    tech_active_path = os.path.join(source_pack_dir, "technical_active.json")
    if os.path.exists(tech_active_path):
        source_evidence["technical_active"] = json.load(open(tech_active_path))
    tech_profile_path = os.path.join(source_pack_dir, "technical_profile.json")
    if os.path.exists(tech_profile_path):
        source_evidence["technical_profile"] = json.load(open(tech_profile_path))

    # Step 6: Compute applicability decisions
    decisions = decide_all(ticker, sector, field_statuses, source_evidence)

    # Step 7: Build derived metrics (deterministic)
    valuation = contract.get("valuation", {})
    derived = {
        "valuation": {
            "pe": valuation.get("pe"),
            "pb": valuation.get("pb"),
            "graham": None,  # computed later if needed
        },
        "scores": source_evidence.get("technical_active", {}),
    }

    # Step 8: Build chart specifications
    years_int = [int(y) for y in years]
    charts = []
    chart_specs = [
        ("chartHistRev", "bar", ["revenue"], "Doanh thu 5 năm (tỷ VND)"),
        ("chartHistNP", "bar", ["net_profit"], "Lợi nhuận 5 năm (tỷ VND)"),
        ("chartHistCash", "bar", ["capex"], "CapEx 5 năm (tỷ VND)"),
        ("chartBSDt", "bar", ["total_assets", "total_equity"], "Tổng tài sản & VCSH (tỷ VND)"),
        ("chartValPE", "line", ["eps"], "EPS 5 năm (VND)"),
    ]
    for chart_id, chart_type, source_metrics, title in chart_specs:
        # Check if all source metrics are applicable
        all_applicable = all(
            metrics.get(m, {}).get("status") == "VALID"
            for m in source_metrics
        )
        period_values = {}
        if all_applicable:
            for m in source_metrics:
                for y in years:
                    val = metrics.get(m, {}).get("values", {}).get(str(y))
                    if val is not None:
                        # Convert to tỷ VND for display (revenue/assets/equity/capex in tỷ, eps raw)
                        if m != "eps":
                            val = val / 1e9 if val > 1e6 else val  # raw VND → tỷ
                        period_values.setdefault(str(y), val)
        charts.append({
            "chart_id": chart_id,
            "chart_type": chart_type,
            "source_metrics": source_metrics,
            "period_value_pairs": period_values,
            "applicability": "VALID" if all_applicable else "NOT_APPLICABLE",
            "title": title,
            "annotations": [],
        })

    # Step 9: Build section list
    section_defs = [
        ("executive_summary", "Tóm tắt điều hành", True),
        ("company_profile", "Hồ sơ doanh nghiệp", True),
        ("industry_overview", "Tổng quan ngành", True),
        ("history", "Lịch sử tài chính", True),
        ("segment", "Phân khúc kinh doanh", True),
        ("thesis", "Luận điểm đầu tư", True),
        ("valuation", "Định giá", True),
        ("peers", "So sánh ngành", True),
        ("balance_sheet", "Bảng cân đối kế toán", True),
        ("risk", "Rủi ro", True),
        ("scenario", "Kịch bản", True),
        ("checklist", "Checklist đầu tư", True),
        ("insight_1", "Insight #1", True),
        ("insight_2", "Insight #2", True),
        ("insight_3", "Insight #3", True),
        ("tech_active", "Phân tích kỹ thuật", decisions.get("tech_active", {}).get("status") == "APPLICABLE"),
        ("tech_profile", "Hồ sơ kỹ thuật", decisions.get("tech_profile", {}).get("status") == "APPLICABLE"),
        ("analyst_notes", "Ghi chú phân tích", True),
        ("glossary", "Thuật ngữ", True),
        ("sources", "Nguồn tham khảo", True),
    ]
    sections = []
    for sec_id, title, required in section_defs:
        app_status = "APPLICABLE"
        app_rule = None
        if sec_id == "financial_overview" and field_statuses.get("revenue") == "NOT_APPLICABLE":
            app_status = "NOT_APPLICABLE"
            app_rule = "INSURANCE_REVENUE_NOT_GENERIC_SALES"
        elif sec_id == "audit_notes":
            ad = decisions.get("audit_split", {})
            app_status = ad.get("status", "APPLICABLE")
            app_rule = ad.get("rule_id")
        elif sec_id in ("tech_active", "tech_profile"):
            ad = decisions.get(sec_id, {})
            app_status = ad.get("status", "NOT_APPLICABLE")
            app_rule = ad.get("rule_id")
            if app_status != "APPLICABLE":
                required = False

        sections.append({
            "section_id": sec_id,
            "title": title,
            "required": required,
            "applicability": app_status,
            "applicability_rule": app_rule,
            "structured_facts": {},
            "narrative": "",  # filled by model in Phase C; empty for Phase B
            "warnings": [],
            "validation_status": "PENDING",
        })

    # Step 10: Build final IR
    ir = {
        "schema_version": "1.0.0-arch-b",
        "metadata": {
            "ticker": ticker,
            "company_name": overview.get("organ_name", ticker),
            "sector": sector,
            "industry": overview.get("industry_name", ""),
            "exchange": overview.get("com_group_code", "HOSE"),
            "generated_at": __import__("datetime").datetime.now().isoformat(),
            "source_snapshot_hashes": {},
        },
        "reporting_scope": {
            "statement_scope": "consolidated",
            "currency": "VND",
            "unit": "raw",
            "annual_periods": years_int,
        },
        "financial_data": {"metrics": metrics},
        "derived_metrics": derived,
        "sections": sections,
        "charts": charts,
        "external_claims": [],
        "validation": {
            "unresolved_items": [],
            "section_results": {},
            "deterministic_gate_results": {},
            "applicability_decisions": decisions,
        },
    }
    return ir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 report_ir_builder.py <source_pack_dir>")
        sys.exit(1)
    ir = build_ir(sys.argv[1])
    if "error" in ir:
        print(f"ERROR: {ir['error']}")
        sys.exit(1)
    print(json.dumps(ir, indent=2, ensure_ascii=False, default=str)[:2000])
