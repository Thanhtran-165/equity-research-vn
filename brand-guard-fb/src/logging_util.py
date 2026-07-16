"""Structured logging helper for brand-guard-fb.

Replaces scattered print() calls with consistent stderr logging.
Supports --verbose flag for debug-level output.
"""
from __future__ import annotations

import sys
from datetime import datetime

_verbose: bool = False


def set_verbose(enabled: bool) -> None:
    global _verbose
    _verbose = enabled


def _log(level: str, msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level} {msg}", file=sys.stderr)


def info(msg: str) -> None:
    """Normal operational message."""
    _log("INFO", msg)


def warn(msg: str) -> None:
    """Warning — something unexpected but non-fatal."""
    _log("WARN", msg)


def error(msg: str) -> None:
    """Error — something failed."""
    _log("ERROR", msg)


def debug(msg: str) -> None:
    """Debug — only shown with --verbose."""
    if _verbose:
        _log("DEBUG", msg)


def summary(stats: dict) -> None:
    """Print scan summary stats."""
    print("", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("  SCAN SUMMARY", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    for key, val in stats.items():
        print(f"  {key:30} {val}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
