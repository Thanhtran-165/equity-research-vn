"""Shared helpers for the VTA Phase 3 independent verifier.

This module is supporting infrastructure for the six verification-domain
modules and the entrypoint. It contains only:

  * Plain data carriers (CheckOutcome).
  * Frozen-fixture / contract / registry loaders (YAML / JSON).
  * Independent primitive arithmetic used by the formula-conformance domain.

INDEPENDENCE CONTRACT (vta-phase-3-implementation-scope.yaml Section 7):
  - This file MUST NOT import any production decision logic
    (normalization_engine, indicator_engine, profile_engine, output_assembler,
    integration_adapter, language_verifier, runner).
  - Only the standard library, numpy, and pyyaml are permitted dependencies.
  - Mathematical primitives below are reimplemented from the frozen formula
    contract registry; they are NOT calls into production code.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

try:
    import numpy as np
except ImportError as exc:
    raise ImportError(
        "The VTA independent verifier requires numpy for independent formula "
        "recomputation. Install numpy to continue."
    ) from exc


# Status sentinels (machine contract strings).
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_ERROR = "ERROR"
STATUS_SKIPPED = "SKIPPED"

# Verdict sentinels. A verdict describes whether the verifier agreed with the
# frozen expectation for the case, not whether the production output was clean.
VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_ERROR = "ERROR"

# Sentinel for "no failure code" (non-failing checks). This is the documented
# non-code sentinel from the failure-code registry reconciliation, not a code.
CODE_NONE = "NONE"


class CheckOutcome:
    """The independently observed result of evaluating one VC obligation.

    Fields:
      observed_status: PASS if the production output satisfied the obligation
        (no violation observed); FAIL if the verifier observed the controlled
        failure; ERROR if the verifier could not evaluate (malformed packet).
      observed_primary_code: the PRIMARY failure code the verifier would emit
        for this VC given the observed output, or CODE_NONE when clean.
      observed_diagnostic_codes: ordered list of DIAGNOSTIC codes co-emitted.
      evidence: structured, JSON-serialisable details supporting the outcome.
    """

    __slots__ = (
        "observed_status",
        "observed_primary_code",
        "observed_diagnostic_codes",
        "evidence",
    )

    def __init__(
        self,
        observed_status: str,
        observed_primary_code: str = CODE_NONE,
        observed_diagnostic_codes: Optional[Sequence[str]] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.observed_status = observed_status
        self.observed_primary_code = observed_primary_code
        self.observed_diagnostic_codes = list(observed_diagnostic_codes or [])
        self.evidence = dict(evidence or {})

    @classmethod
    def pass_clean(cls, **evidence: Any) -> "CheckOutcome":
        return cls(STATUS_PASS, CODE_NONE, [], evidence)

    @classmethod
    def fail(
        cls,
        primary_code: str,
        diagnostic_codes: Optional[Sequence[str]] = None,
        **evidence: Any,
    ) -> "CheckOutcome":
        return cls(STATUS_FAIL, primary_code, diagnostic_codes or [], evidence)

    @classmethod
    def error(cls, reason: str, **evidence: Any) -> "CheckOutcome":
        return cls(STATUS_ERROR, CODE_NONE, [], {"reason": reason, **evidence})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observed_status": self.observed_status,
            "observed_primary_code": self.observed_primary_code,
            "observed_diagnostic_codes": list(self.observed_diagnostic_codes),
            "evidence": self.evidence,
        }


# ===========================================================================
# Frozen-artifact loaders
# ===========================================================================


def load_yaml(path: str) -> Any:
    """Load a frozen YAML contract/registry deterministically."""
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: str) -> Any:
    """Load a frozen JSON fixture / output packet deterministically."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_artifact(path: str) -> Any:
    """Load a frozen YAML or JSON artifact by extension."""
    _, ext = os.path.splitext(path)
    if ext.lower() in (".yaml", ".yml"):
        return load_yaml(path)
    if ext.lower() == ".json":
        return load_json(path)
    raise ValueError(f"Unsupported artifact extension: {ext} ({path})")


# Registry/document canonical-key map. The frozen review manifests all wrap
# their payload under a single top-level key (e.g. vta_failure_code_registry,
# vc_to_verifier_mapping, vta_formula_contract_registry). These helpers unwrap
# that wrapper when present so domain code can address the payload directly.
_REGISTRY_WRAPPER_KEYS = ("vta_failure_code_registry", "failure_code_registry")
_MAPPING_WRAPPER_KEYS = ("vc_to_verifier_mapping", "verifier_obligation_matrix")
_FORMULA_WRAPPER_KEYS = ("vta_formula_contract_registry", "formula_contract_registry")


def _unwrap(doc: Any, candidate_keys: Sequence[str]) -> Any:
    if not isinstance(doc, dict):
        return doc
    for key in candidate_keys:
        inner = doc.get(key)
        if isinstance(inner, dict):
            return inner
    return doc


def unwrap_failure_code_registry(doc: Any) -> Dict[str, Any]:
    return _unwrap(doc, _REGISTRY_WRAPPER_KEYS) or {}


def unwrap_vc_mapping(doc: Any) -> Dict[str, Any]:
    return _unwrap(doc, _MAPPING_WRAPPER_KEYS) or {}


def unwrap_formula_contracts(doc: Any) -> Dict[str, Any]:
    return _unwrap(doc, _FORMULA_WRAPPER_KEYS) or {}


# ===========================================================================
# Registry-derived failure-code lookup (frozen registry is the authority)
# ===========================================================================


def build_vc_primary_code_map(registry: Dict[str, Any]) -> Dict[str, str]:
    """Build {VC_id -> PRIMARY failure_code} from the frozen failure-code
    registry. PRIMARY codes win over DIAGNOSTIC codes when a VC is owned by
    both. This map encodes the authoritative Review-R3 ownership and is the
    source of truth for the observed_primary_code each VC check emits.

    Accepts either the raw wrapped document (vta_failure_code_registry: {...})
    or the unwrapped payload; the wrapper is detected and stripped.
    """
    if isinstance(registry, dict) and not registry.get("codes"):
        registry = unwrap_failure_code_registry(registry)
    codes: List[Dict[str, Any]] = registry.get("codes", []) if isinstance(registry, dict) else []
    mapping: Dict[str, str] = {}
    diagnostic_owner: Dict[str, str] = {}
    for entry in codes:
        code = entry.get("failure_code")
        if not code:
            continue
        classification = entry.get("classification", "PRIMARY")
        owners = entry.get("owning_VC_ids", []) or []
        for vc in owners:
            if classification == "PRIMARY":
                mapping[vc] = code
            else:
                diagnostic_owner.setdefault(vc, code)
    for vc, code in diagnostic_owner.items():
        mapping.setdefault(vc, code)
    return mapping


def build_vc_diagnostic_codes_map(registry: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build {VC_id -> [DIAGNOSTIC failure_codes]} from the frozen registry.
    Accepts the wrapped or unwrapped registry document."""
    if isinstance(registry, dict) and not registry.get("codes"):
        registry = unwrap_failure_code_registry(registry)
    codes: List[Dict[str, Any]] = registry.get("codes", []) if isinstance(registry, dict) else []
    mapping: Dict[str, List[str]] = {}
    for entry in codes:
        if entry.get("classification", "PRIMARY") != "DIAGNOSTIC":
            continue
        code = entry.get("failure_code")
        for vc in entry.get("owning_VC_ids", []) or []:
            mapping.setdefault(vc, []).append(code)
    return mapping


# ===========================================================================
# Independent primitive arithmetic (reimplemented from frozen contracts).
# ===========================================================================


def _as_float_array(values: Iterable[Any]) -> "np.ndarray":
    arr = np.asarray(list(values), dtype=float)
    return arr


def kahan_sum(values: Sequence[float]) -> float:
    """Kahan compensated summation for long windows (>=60) per floating-point
    policy in the formula contract registry."""
    total = 0.0
    compensation = 0.0
    for value in values:
        y = float(value) - compensation
        t = total + y
        compensation = (t - total) - y
        total = t
    return total


def simple_moving_average(values: Sequence[float], window: int) -> "np.ndarray":
    """SMA with Kahan summation semantics for window >= 60, naive otherwise.

    Returns an array of len(values); positions before window-1 are NaN.
    """
    n = len(values)
    out = np.full(n, np.nan, dtype=float)
    if window <= 0 or n < window:
        return out
    arr = _as_float_array(values)
    use_kahan = window >= 60
    if use_kahan:
        for i in range(window - 1, n):
            out[i] = kahan_sum(arr[i - window + 1 : i + 1]) / float(window)
    else:
        csum = np.cumsum(arr, dtype=float)
        csum[window:] = csum[window:] - csum[:-window]
        out[window - 1 :] = csum[window - 1 :] / float(window)
    return out


def population_std(values: Sequence[float], window: int) -> "np.ndarray":
    """Population standard deviation (divide by N), frozen convention for
    F-BOLLINGER, F-HV, F-BETA shared kernel. Returns array with NaN warmup."""
    n = len(values)
    out = np.full(n, np.nan, dtype=float)
    if window <= 0 or n < window:
        return out
    arr = _as_float_array(values)
    for i in range(window - 1, n):
        chunk = arr[i - window + 1 : i + 1]
        mean = kahan_sum(chunk) / float(window)
        variance = kahan_sum((x - mean) ** 2 for x in chunk) / float(window)
        out[i] = math.sqrt(variance) if variance > 0.0 else 0.0
    return out


def sample_std(values: Sequence[float], window: int) -> "np.ndarray":
    """Sample standard deviation (divide by N-1). Retained so the verifier can
    detect simple-smoothing / wrong-convention injection (VC-WRONG-SMOOTH-1,
    VC-BOLL-1) by comparing production output against BOTH conventions."""
    n = len(values)
    out = np.full(n, np.nan, dtype=float)
    if window <= 0 or n < window or window < 2:
        return out
    arr = _as_float_array(values)
    for i in range(window - 1, n):
        chunk = arr[i - window + 1 : i + 1]
        mean = kahan_sum(chunk) / float(window)
        variance = kahan_sum((x - mean) ** 2 for x in chunk) / float(window - 1)
        out[i] = math.sqrt(variance) if variance > 0.0 else 0.0
    return out


def wilder_rsi(closes: Sequence[float], period: int = 14) -> "np.ndarray":
    """Independent Wilder-smoothed RSI reimplementation.

    Contract source: vta-formula-contract-registry.yaml F-RSI
      - Seed avgGain/avgLoss as arithmetic mean of first `period` gains/losses
        (Wilder SMA seed), NOT data[0].
      - Recurse with (period-1) multiplier:
            avgGain_t = (avgGain_{t-1}*(period-1) + gain_t) / period
      - RS = avgGain / avgLoss; RSI = 100 - 100/(1+RS)
      - avgLoss == 0 -> RSI = 100; avgGain==0 and avgLoss==0 -> RSI = 50.
      - First valid RSI emitted at bar index `period` (0-based).
    """
    arr = _as_float_array(closes)
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=float)
    if n < period + 1:
        return out
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = kahan_sum(gains[:period]) / float(period)
    avg_loss = kahan_sum(losses[:period]) / float(period)
    out[period] = _rsi_from_avg(avg_gain, avg_loss)
    for i in range(period, n - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / float(period)
        avg_loss = (avg_loss * (period - 1) + losses[i]) / float(period)
        out[i + 1] = _rsi_from_avg(avg_gain, avg_loss)
    return out


def _rsi_from_avg(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0.0:
        if avg_gain == 0.0:
            return 50.0
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def simple_rsi(closes: Sequence[float], period: int = 14) -> "np.ndarray":
    """Simple-smoothed (SMA every window) RSI. Used ONLY as the injected
    mutation reference to detect VC-WRONG-SMOOTH-1 (simple-smoothing injection
    must be distinguishable from Wilder). Not used as an oracle for production."""
    arr = _as_float_array(closes)
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=float)
    if n < period + 1:
        return out
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    for i in range(period, n):
        window_gains = gains[i - period : i]
        window_losses = losses[i - period : i]
        avg_gain = kahan_sum(window_gains) / float(period)
        avg_loss = kahan_sum(window_losses) / float(period)
        out[i] = _rsi_from_avg(avg_gain, avg_loss)
    return out


def ema(values: Sequence[float], period: int, seed: Optional[float] = None) -> "np.ndarray":
    """Exponential moving average with explicit seed. For F-MACD the frozen
    contract mandates seed = values[0] (DATA_0), NOT an SMA seed."""
    arr = _as_float_array(values)
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=float)
    if n == 0:
        return out
    k = 2.0 / (period + 1.0)
    out[0] = float(seed) if seed is not None else float(arr[0])
    for i in range(1, n):
        out[i] = arr[i] * k + out[i - 1] * (1.0 - k)
    return out


def ols_slope(values: Sequence[float]) -> float:
    """Ordinary-least-squares slope of `values` vs index (0,1,2,...).

    Used for VC-CHANNEL-1: normalized_slope_pct_per_bar must equal
    100 * OLS_slope / median(close_window) per the frozen F-CHANNEL-SLOPE
    contract referenced from oracle O-009.
    """
    arr = _as_float_array(values)
    n = arr.shape[0]
    if n < 2:
        return 0.0
    xs = np.arange(n, dtype=float)
    x_mean = kahan_sum(xs.tolist()) / float(n)
    y_mean = kahan_sum(arr.tolist()) / float(n)
    num = kahan_sum((xs[i] - x_mean) * (arr[i] - y_mean) for i in range(n))
    den = kahan_sum((xs[i] - x_mean) ** 2 for i in range(n))
    if den == 0.0:
        return 0.0
    return num / den


def obv_series(closes: Sequence[float], volumes: Sequence[float]) -> "np.ndarray":
    """On-Balance Volume series (independent primitive)."""
    c = _as_float_array(closes)
    v = _as_float_array(volumes)
    n = c.shape[0]
    out = np.zeros(n, dtype=float)
    for i in range(1, n):
        if c[i] > c[i - 1]:
            out[i] = out[i - 1] + v[i]
        elif c[i] < c[i - 1]:
            out[i] = out[i - 1] - v[i]
        else:
            out[i] = out[i - 1]
    return out


def vpt_series(closes: Sequence[float], volumes: Sequence[float]) -> "np.ndarray":
    """Volume Price Trend series (independent primitive).

    VPT_t = VPT_{t-1} + volume_t * (close_t - close_{t-1}) / close_{t-1}
    """
    c = _as_float_array(closes)
    v = _as_float_array(volumes)
    n = c.shape[0]
    out = np.zeros(n, dtype=float)
    for i in range(1, n):
        prev = c[i - 1]
        if prev == 0.0:
            out[i] = out[i - 1]
        else:
            out[i] = out[i - 1] + v[i] * ((c[i] - prev) / prev)
    return out


def pct_change(series: Sequence[float]) -> "np.ndarray":
    """Simple percentage returns (fraction). NaN at position 0."""
    arr = _as_float_array(series)
    out = np.full(arr.shape[0], np.nan, dtype=float)
    if arr.shape[0] < 2:
        return out
    prev = arr[:-1]
    safe = np.where(prev == 0.0, np.nan, prev)
    out[1:] = (arr[1:] - prev) / safe
    return out


def population_covariance(x: Sequence[float], y: Sequence[float]) -> float:
    """Population covariance (divide by N), frozen convention for F-BETA."""
    ax = _as_float_array(x)
    ay = _as_float_array(y)
    n = min(ax.shape[0], ay.shape[0])
    if n == 0:
        return 0.0
    mx = kahan_sum(ax[:n].tolist()) / float(n)
    my = kahan_sum(ay[:n].tolist()) / float(n)
    return kahan_sum((ax[i] - mx) * (ay[i] - my) for i in range(n)) / float(n)


def is_close(a: float, b: float, tol: float = 1.0e-9) -> bool:
    """Finite relative/absolute closeness test."""
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= tol + tol * abs(b)


def finite_or_none(value: Any) -> Optional[float]:
    """Coerce a value to a finite float, else None."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f
