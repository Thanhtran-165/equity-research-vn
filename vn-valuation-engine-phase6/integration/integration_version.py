"""Integration version — adapter identity contract (Directive Phase 6 §8.2)."""
ADAPTER_ID = "vn-valuation-engine_to_equity-research-vn"
ADAPTER_VERSION = "1.2.0"
CHILD_SCHEMA_VERSION = "1.0.0-phase2"
PARENT_VERSION = "equity-research-vn-1.1.0"
PARENT_REPORT_IR_VERSION = "1.0.0-arch-b"
MAPPING_MODE = "LOSSLESS"

# Lossless mapping policy (Directive Phase 6 §8.5-8.6)
MAPPING_POLICY = {
    "silent_rename": "PROHIBITED",
    "lossy_mapping": "FAIL",
    "unknown_critical_field": "FAIL",
    "duplicate_method_id": "FAIL",
    "orphan_reference": "FAIL",
    "parent_default_recalculation": "PROHIBITED",
}

# Allowed parent report IR targets (Directive Phase 6 §8.3, report-ir-mapping.yaml)
ALLOWED_TARGETS = [
    "valuation_inputs",
    "valuation_methods",
    "valuation_results",
    "valuation_assumptions",
    "risks",
    "executive_summary_inputs",
    "audit_notes",
    "citations",
]

# Forbidden parent report IR targets (Directive Phase 6 §8.4)
FORBIDDEN_TARGETS = [
    "canonical_financial_DATA",
    "raw_financial_source_arrays",
    "financial_period_labels",
    "ticker_identity",
    "news_event_clusters",
    "unrelated_chart_datasets",
    "parent_source_snapshots",
    "parent_verifier_configuration",
]


def get_adapter_metadata():
    return {
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "child_schema_version": CHILD_SCHEMA_VERSION,
        "parent_version": PARENT_VERSION,
        "parent_report_IR_version": PARENT_REPORT_IR_VERSION,
        "mapping_mode": MAPPING_MODE,
        "mapping_policy": MAPPING_POLICY,
    }
