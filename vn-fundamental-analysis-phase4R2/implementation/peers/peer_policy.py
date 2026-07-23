"""Peer comparison policies — Phase 4R (MUT-FUND-027 / 028 / 029 / 030)."""
from __future__ import annotations
from enum import Enum


class CentralTendencyPolicy(str, Enum):
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    TRIMMED_MEAN = "TRIMMED_MEAN"


MINIMUM_PEER_COVERAGE = 3
