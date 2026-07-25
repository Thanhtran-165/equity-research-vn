"""Research context envelope — Phase 6 hash-bound context.

Every child invocation uses the same immutable context, hash-bound to ensure
no ticker/period/scope/currency drift between collector → fundamental → valuation.
"""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ResearchContext:
    """Immutable research context, hash-bound across all child invocations."""
    research_context_id: str = ""
    ticker: str = ""
    exchange: str = ""
    as_of_date: str = ""
    fiscal_period: int = 0
    currency: str = "VND"
    reporting_scope: str = "CONSOLIDATED"
    attribution_scope: str = "ATTRIBUTABLE_TO_PARENT"
    source_snapshot_hash: str = ""
    collector_evidence_hash: str = ""
    context_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "ticker": self.ticker, "exchange": self.exchange,
            "as_of_date": self.as_of_date, "fiscal_period": self.fiscal_period,
            "currency": self.currency, "reporting_scope": self.reporting_scope,
            "attribution_scope": self.attribution_scope,
            "source_snapshot_hash": self.source_snapshot_hash,
            "collector_evidence_hash": self.collector_evidence_hash,
        }
        self.context_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
        return self.context_hash

    def to_dict(self) -> Dict[str, Any]:
        if not self.context_hash:
            self.compute_hash()
        return {
            "research_context_id": self.research_context_id,
            "ticker": self.ticker, "exchange": self.exchange,
            "as_of_date": self.as_of_date, "fiscal_period": self.fiscal_period,
            "currency": self.currency, "reporting_scope": self.reporting_scope,
            "attribution_scope": self.attribution_scope,
            "source_snapshot_hash": self.source_snapshot_hash,
            "collector_evidence_hash": self.collector_evidence_hash,
            "context_hash": self.context_hash,
        }


def verify_context_match(ctx1: ResearchContext, ctx2: ResearchContext) -> tuple[bool, Optional[str]]:
    """Verify two contexts match on all invariant fields."""
    fields = ["ticker", "fiscal_period", "currency", "reporting_scope", "attribution_scope",
              "source_snapshot_hash", "collector_evidence_hash"]
    for f in fields:
        v1, v2 = getattr(ctx1, f), getattr(ctx2, f)
        if v1 != v2:
            return False, f"CONTEXT_MISMATCH: {f} differs ({v1} vs {v2})"
    return True, None
