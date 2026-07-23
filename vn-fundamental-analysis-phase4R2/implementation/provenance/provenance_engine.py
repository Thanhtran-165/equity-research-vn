"""Provenance engine — Phase 4R (MUT-FUND-031).

Builds a ProvenanceRecord for every material metric, resolving
metric_result -> formula_inputs -> normalized_inputs -> collector_metric_id ->
source_id -> raw_evidence. Each record is hash-bound so a downstream swap
is detectable.
"""
from __future__ import annotations
import hashlib, json
from typing import Dict, List, Optional
from models import MetricInput, ProvenanceRecord


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def build_provenance(metric_id: str, input_metrics: Dict[str, MetricInput], year: int,
                     formula_input_ids: Optional[List[str]] = None) -> ProvenanceRecord:
    """Build a provenance record from the input metrics that fed this metric at `year`."""
    normalized_input_ids: List[str] = []
    collector_metric_ids: List[str] = []
    source_ids: List[str] = []
    source_dates: List[str] = []
    source_types: List[str] = []
    raw_evidence_parts: List[Dict] = []

    for role, m in input_metrics.items():
        if m is None:
            continue
        normalized_input_ids.append(m.metric_id)
        # collector_metric_id is the per-slot source_metric_id binding if present, else metric_id
        sm = m.get_binding(year, "source_metric_ids") if year in m.periods else None
        collector_metric_ids.append(sm or m.metric_id)
        source_ids.append(m.get_binding(year, "source_dates") or m.source_id or f"src:{m.metric_id}")
        # source_date / source_type bindings
        sd = m.get_binding(year, "source_dates") or ""
        st = m.get_binding(year, "source_types") or ""
        source_dates.append(sd)
        source_types.append(st)
        v = m.get_value(year)
        raw_evidence_parts.append({"role": role, "metric_id": m.metric_id, "year": year, "value": v, "source_id": m.source_id})

    raw_evidence_hash = _hash(raw_evidence_parts)
    record = ProvenanceRecord(
        source_id=source_ids[0] if source_ids else "",
        source_date=source_dates[0] if source_dates else "",
        source_type=source_types[0] if source_types else "",
        collector_metric_id=collector_metric_ids[0] if collector_metric_ids else "",
        normalized_input_ids=normalized_input_ids,
        formula_input_ids=formula_input_ids or list(input_metrics.keys()),
        raw_evidence_hash=raw_evidence_hash,
    )
    # provenance_hash binds the full record so a swap is detectable.
    record.provenance_hash = _hash(record.to_dict())
    return record


def provenance_is_complete(record: Optional[ProvenanceRecord]) -> bool:
    if record is None:
        return False
    return bool(record.source_id and record.collector_metric_id and record.raw_evidence_hash and record.provenance_hash)


def provenance_hash_matches(record: Optional[ProvenanceRecord], expected_hash: str) -> bool:
    if record is None:
        return False
    return record.provenance_hash == expected_hash
