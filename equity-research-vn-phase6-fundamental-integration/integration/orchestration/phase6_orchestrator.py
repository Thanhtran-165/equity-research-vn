"""Phase 6 orchestrator — coordinator for collector → fundamental → valuation.

Shadow mode: fundamental output saved as evidence but not rendered in parent.
Fail-closed: invalid metrics blocked, no fabricated fallback.
"""
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vn-fundamental-analysis-phase5R3b" / "workspace" / "implementation"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import run_fundamental
from verifier.independent_verifier import verify
from context.research_context import ResearchContext, verify_context_match
from adapter.collector_to_fundamental import adapt_collector_to_fundamental
from adapter.fundamental_to_valuation import create_valuation_handoff


def run_integrated_fundamental(collector_output: Dict[str, Any],
                                context: ResearchContext) -> Dict[str, Any]:
    """Run fundamental analysis in integrated mode.

    Pipeline: collector packet → context gate → adapter → fundamental engine → verifier → handoff

    Returns dict with all stages + evidence.
    """
    # 1. Context gate: verify collector ticker matches context
    collector_ticker = collector_output.get("ticker", "")
    if collector_ticker != context.ticker:
        return _fail("CONTEXT_GATE", f"ticker mismatch: collector={collector_ticker} context={context.ticker}")

    # 2. Adapt collector → fundamental request
    try:
        request, adapter_evidence = adapt_collector_to_fundamental(collector_output, context)
    except Exception as e:
        return _fail("ADAPTER_FAILURE", str(e))

    # 3. Run fundamental engine
    try:
        pipeline_result = run_fundamental(request)
    except Exception as e:
        return _fail("ENGINE_FAILURE", str(e))

    output = pipeline_result.output

    # 4. Run verifier
    try:
        vr = verify(request, output)
    except Exception as e:
        return _fail("VERIFIER_FAILURE", str(e))

    # 5. Verifier gate: only proceed if PASS
    if vr.overall_verdict != "PASS":
        return {
            "status": "VERIFIER_GATE_BLOCKED",
            "verifier_verdict": vr.overall_verdict,
            "verifier_mismatches": vr.mismatches[:5],
            "fundamental_output": output.to_dict(),
            "adapter_evidence": adapter_evidence,
            "handoff": None,
        }

    # 6. Create valuation handoff
    handoff = create_valuation_handoff(output.to_dict(), context.context_hash)

    # 7. Build lineage chain
    output_hash = hashlib.sha256(
        json.dumps(output.to_dict(), sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()

    lineage = {
        "collector_packet_hash": adapter_evidence["collector_output_hash"],
        "context_hash": context.context_hash,
        "fundamental_input_hash": adapter_evidence["collector_output_hash"],
        "fundamental_output_hash": output_hash,
        "fundamental_verifier_hash": hashlib.sha256(
            json.dumps(vr.to_dict(), sort_keys=True, default=str).encode()
        ).hexdigest(),
        "valuation_handoff_hash": handoff["handoff_hash"],
    }

    return {
        "status": "PASS",
        "verifier_verdict": vr.overall_verdict,
        "fundamental_output": output.to_dict(),
        "adapter_evidence": adapter_evidence,
        "handoff": handoff,
        "lineage": lineage,
        "final_status": pipeline_result.final_status,
        "errors": pipeline_result.errors,
    }


def _fail(code: str, message: str) -> Dict[str, Any]:
    return {
        "status": code,
        "message": message,
        "fundamental_output": None,
        "handoff": None,
        "lineage": None,
    }
