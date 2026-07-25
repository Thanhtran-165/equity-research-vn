"""Integration version + mapping policy — Phase 6 fundamental integration.

Defines the adapter identity, mapping policy, allowed/forbidden targets.
Mirrors valuation-engine integration_version.py precedent.
"""
ADAPTER_ID = "vn-fundamental-analysis_to_equity-research-vn"
ADAPTER_VERSION = "1.0.0"
CHILD_CANDIDATE_COMMIT = "4ecc6b940"
CHILD_STANDALONE_MATURITY = "FUNCTIONAL"
PARENT_VERSION = "equity-research-vn-1.1.0"
PARENT_CANDIDATE_VERSION = "1.2.0-candidate"
PARENT_REPORT_IR_VERSION = "1.0.0-arch-b"
MAPPING_MODE = "LOSSLESS"

MAPPING_POLICY = {
    "silent_rename": "PROHIBITED",
    "lossy_mapping": "FAIL",
    "unknown_critical_field": "FAIL",
    "parent_default_recalculation": "PROHIBITED",
    "cross_ticker_contamination": "FAIL",
    "stale_verifier_result": "FAIL",
    "missing_to_zero": "FAIL",
}

# Zones fundamental adapter CAN write to in parent IR
ALLOWED_TARGETS = [
    "fundamental_metrics",
    "derived_metrics",
    "applicability_decisions",
    "quality_summary",
    "audit_notes.fundamental",
    "citations.fundamental_provenance",
]

# Zones fundamental adapter CANNOT touch
FORBIDDEN_TARGETS = [
    "canonical_financial_DATA",
    "raw_financial_source_arrays",
    "financial_period_labels",
    "ticker_identity",
    "valuation_methods",
    "valuation_results",
    "news_event_clusters",
    "chart_datasets",
    "parent_source_snapshots",
    "parent_verifier_configuration",
]

# Collector → Fundamental field mapping
COLLECTOR_TO_FUNDAMENTAL_MAP = {
    "revenue": {
        "collector_field": "revenue",
        "fundamental_metric_id": "revenue",
        "collector_unit": "VND_raw",
        "fundamental_unit": "BILLION_VND",
        "normalization_factor": 1.0e-9,
        "period_kind": "ANNUAL",
        "reporting_scope": "CONSOLIDATED",
        "attribution_scope": "TOTAL_GROUP",
    },
    "net_profit": {
        "collector_field": "net_profit",
        "fundamental_metric_id": "net_income",
        "collector_unit": "VND_raw",
        "fundamental_unit": "BILLION_VND",
        "normalization_factor": 1.0e-9,
        "period_kind": "ANNUAL",
        "reporting_scope": "CONSOLIDATED",
        "attribution_scope": "ATTRIBUTABLE_TO_PARENT",
        "note": "Must use attributable-to-parent, not total-group NPAT",
    },
    "total_assets": {
        "collector_field": "total_assets",
        "fundamental_metric_id": "total_assets",
        "collector_unit": "VND_raw",
        "fundamental_unit": "BILLION_VND",
        "normalization_factor": 1.0e-9,
        "period_kind": "POINT_IN_TIME",
        "reporting_scope": "CONSOLIDATED",
        "attribution_scope": "TOTAL_GROUP",
        "denominator_basis": "AVERAGE_TOTAL_ASSETS",
    },
    "total_equity": {
        "collector_field": "total_equity",
        "fundamental_metric_id": "equity",
        "collector_unit": "VND_raw",
        "fundamental_unit": "BILLION_VND",
        "normalization_factor": 1.0e-9,
        "period_kind": "POINT_IN_TIME",
        "reporting_scope": "CONSOLIDATED",
        "attribution_scope": "ATTRIBUTABLE_TO_PARENT",
        "denominator_basis": "AVERAGE_COMMON_EQUITY",
    },
    "eps_basic": {
        "collector_field": "eps_basic",
        "fundamental_metric_id": "_eps_for_share_derivation",
        "collector_unit": "VND_per_share",
        "fundamental_unit": "VND_per_share",
        "normalization_factor": 1.0,
        "note": "EPS used ONLY for weighted-share back-calc (DERIVED_INPUT). NOT used as independent oracle.",
    },
    "shares_outstanding": {
        "collector_field": "shares_outstanding",
        "fundamental_metric_id": "shares_outstanding",
        "collector_unit": "shares_count",
        "fundamental_unit": "BILLION_SHARES",
        "normalization_factor": 1.0e-9,
        "period_kind": "POINT_IN_TIME",
        "share_basis": "PERIOD_END_BASIC",
        "note": "Period-end from collector. Weighted-average derived from EPS×NPAT, marked DERIVED_INPUT.",
    },
}

# Status mapping: fundamental → valuation handoff
STATUS_HANDOFF_MAP = {
    "VALID": "FORWARD",
    "VALID_NEGATIVE": "FORWARD",
    "INPUT_INCOMPLETE": "BLOCK",
    "NOT_APPLICABLE": "BLOCK",
    "MANUAL_REVIEW_REQUIRED": "BLOCK",
    "ERROR": "BLOCK",
}

# Valuation applicability rules
VALUATION_APPLICABILITY = {
    "negative_EPS": {
        "condition": "EPS_value <= 0",
        "PE_method": "NOT_APPLICABLE",
        "EPS_exported": True,
        "EPS_status": "VALID_NEGATIVE",
    },
    "negative_equity": {
        "condition": "BVPS_value < 0",
        "PB_method": "NOT_APPLICABLE",
        "ROE_method": "NOT_APPLICABLE",
        "BVPS_exported": True,
        "BVPS_status": "VALID_NEGATIVE",
    },
    "near_zero_equity": {
        "condition": "equity/assets < 0.05",
        "equity_methods": "MANUAL_REVIEW_REQUIRED",
        "required_warning": "EXTREME_EQUITY_RATIO_WARNING",
    },
}
