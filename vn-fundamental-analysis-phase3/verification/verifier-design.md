# Independent Verifier Design — vn-fundamental-analysis
# Phase 3 P3C.
skill: vn-fundamental-analysis
phase: 3

independence: "Verifier recomputes from raw inputs. Does NOT call formula engine."

checks:
  total: 18

  1_entity_consistency:
    req: VFA-REQ-001
    method: "compare entity fields across input/output"

  2_schema_validity:
    req: VFA-REQ-002
    method: "validate output against fundamental-output.schema.json"

  3_unit_recomputation:
    req: VFA-REQ-004
    method: "re-derive scale from raw values; check normalized consistency"

  4_share_adjustment_recomputation:
    req: VFA-REQ-008
    method: "recompute weighted average; verify split back-calc"

  5_EPS_recomputation:
    req: VFA-REQ-010
    method: "recompute EPS from NPAT_attributable / weighted_avg_shares"

  6_BVPS_recomputation:
    req: VFA-REQ-012
    method: "recompute BVPS from common_equity / period_end_shares"

  7_ROE_recomputation:
    req: VFA-REQ-013
    method: "recompute ROE from NI / avg_equity"

  8_ROA_recomputation:
    req: VFA-REQ-014
    method: "recompute ROA from NI / avg_total_assets"

  9_margin_recomputation:
    req: VFA-REQ-015
    method: "recompute NPM from NI / revenue"

  10_dupont_NPM:
    req: VFA-REQ-016
    method: "recompute dupont_NPM"

  11_dupont_AT:
    req: VFA-REQ-017
    method: "recompute asset turnover"

  12_dupont_EM:
    req: VFA-REQ-018
    method: "recompute equity multiplier"

  13_dupont_consistency:
    req: VFA-REQ-024
    method: "|NPM × AT × EM - ROE/100| < 0.005"

  14_CAGR_recomputation:
    req: VFA-REQ-020
    method: "recompute CAGR; verify applicability conditions"

  15_missing_data_behavior:
    req: VFA-REQ-022
    method: "verify no zero substitution; check INPUT_INCOMPLETE status"

  16_negative_value_behavior:
    req: VFA-REQ-023
    method: "verify VALID_NEGATIVE and MANUAL_REVIEW_REQUIRED applied correctly"

  17_provenance_resolution:
    req: VFA-REQ-027
    method: "resolve each material metric to source_id; check binding"

  18_downstream_export_eligibility:
    req: VFA-REQ-029
    method: "verify only VALID/VALID_NEGATIVE metrics in downstream_export"

repair_behavior: PROHIBITED
  description: "Verifier detects → reports → FAILs. Never repairs output."
