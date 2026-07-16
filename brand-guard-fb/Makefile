.PHONY: install test compile qa smoke lint clean

PYTHON := .venv/bin/python
PIP := .venv/bin/pip

install:
	$(PIP) install -r requirements-dev.txt
	.venv/bin/playwright install chromium

compile:
	$(PYTHON) -m compileall -q src tests

test:
	$(PYTHON) -m pytest -q src tests

smoke:
	$(PYTHON) -m src.cli --brand chim_cut --no-network

qa: compile test smoke
	@echo "=== QA COMPLETE ==="

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .cache/complaints/*.md 2>/dev/null || true
