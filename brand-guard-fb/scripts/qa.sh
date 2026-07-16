#!/usr/bin/env bash
# brand-guard-fb — QA script: compile + test + no-network smoke
# Usage: bash scripts/qa.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON="${PROJECT_ROOT}/.venv/bin/python"

echo "=========================================="
echo "  brand-guard-fb QA"
echo "=========================================="

# 1. Compile check
echo ""
echo "[1/4] compileall..."
"$PYTHON" -m compileall -q src tests
echo "  ✓ compileall PASS"

# 2. Pytest
echo ""
echo "[2/4] pytest..."
"$PYTHON" -m pytest -q src tests
echo "  ✓ pytest PASS"

# 3. No-network smoke (uses real cache if present)
echo ""
echo "[3/4] --no-network smoke..."
CACHE_VALID=$("$PYTHON" -m src.cli --inspect-cache --brand chim_cut | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin).get("valid", 0))')
SMOKE_JSON=$("$PYTHON" -m src.cli --brand chim_cut --no-network --report-json 2>/dev/null)
PAGES_SCANNED=$(printf '%s' "$SMOKE_JSON" | "$PYTHON" -c 'import json,sys; print(sum(len(r.get("pages", [])) for r in json.load(sys.stdin)))')
if [ "$PAGES_SCANNED" -gt 0 ] 2>/dev/null; then
    echo "  ✓ no-network smoke PASS ($PAGES_SCANNED pages from cache)"
elif [ "$CACHE_VALID" -gt 0 ] 2>/dev/null; then
    echo "  ✗ no-network smoke FAIL (cache has $CACHE_VALID valid entries but scan returned 0 pages)"
    exit 1
else
    echo "  ⚠ no-network smoke: 0 pages (cache may be empty — run live scan first)"
fi

# 4. Config validation
echo ""
echo "[4/4] config validation..."
if "$PYTHON" -c "from src.config_loader import load_config; from pathlib import Path; load_config(Path('config/brands.yaml'))" 2>/dev/null; then
    echo "  ✓ config validation PASS"
else
    echo "  ✗ config validation FAIL"
    exit 1
fi

echo ""
echo "=========================================="
echo "  QA COMPLETE — ALL CHECKS PASSED"
echo "=========================================="
