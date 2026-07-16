#!/usr/bin/env python3
"""
data_contract_enforcer.py — Deterministic DATA block enforcement (Branch A, v0.11.0).

PURPOSE (owner directive 2026-07-15):
  The agent sometimes renames DATA keys (netProfit→netIncome) or alters values.
  This module deterministically serializes the const DATA JS block from the
  verified-dashboard-data.json contract and INJECTS it into the final HTML,
  overwriting whatever the agent wrote. The LLM never has the final say on
  machine-readable data.

  Two modes:
    1. inject: replace the agent's DATA block with the canonical one (post-process)
    2. validate: check the agent's DATA block matches the contract (report only)

  Also provides phase6 preflight validation: parse const DATA, compare keys+values
  to contract, reject forbidden aliases (netIncome, net_profit, etc.).
"""
import re, json, os

# Canonical DATA keys that MUST be present (from phase6 prompt)
CANONICAL_DATA_KEYS = [
    "ticker", "years", "revenue", "netProfit", "grossProfit", "cfo", "capex",
    "inventory", "invGrowth", "eps", "roe", "bvps", "equity", "totalAssets",
    "peHist", "pbHist", "pe5med", "pe5avg", "pe",
]

# Forbidden aliases — if these appear instead of canonical keys, FAIL
FORBIDDEN_ALIASES = {
    "netIncome": "netProfit",
    "net_income": "netProfit",
    "netProfitAT": "netProfit",
    "netIncomeAT": "netProfit",
    "profit": "netProfit",
    "ni": "netProfit",
    "totalAssetsValue": "totalAssets",
    "total_assets": "totalAssets",
    "shareholdersEquity": "equity",
    "ownersEquity": "equity",
}


def serialize_data_block(contract):
    """Deterministically serialize the const DATA JS object from verified-dashboard-data.json.

    Produces: const DATA = {ticker:"VNM", years:[...], revenue:[...], ...};
    Values come directly from the contract — no LLM involvement.
    """
    fin = contract.get("financials", {})
    val = contract.get("valuation", {})
    tech = contract.get("technical", {})
    cp = contract.get("company_profile", {})

    years = fin.get("years", [str(y) for y in contract.get("periods", [])])

    # Build the DATA object with canonical keys
    data = {
        "ticker": contract.get("ticker", ""),
        "years": years,
        "revenue": fin.get("revenue", []),
        "netProfit": fin.get("netProfit", []),
        "grossProfit": fin.get("grossProfit", [None]*len(years)),
        "cfo": fin.get("cfo", [None]*len(years)),
        "capex": fin.get("capex", []),
        "inventory": fin.get("inventory", [None]*len(years)),
        "invGrowth": fin.get("invGrowth", [None]*len(years)),
        "eps": fin.get("eps", []),
        "roe": fin.get("roe", [None]*len(years)),
        "bvps": fin.get("bvps", [None]*len(years)),
        "equity": fin.get("equity", []),
        "totalAssets": fin.get("totalAssets", []),
        "peHist": fin.get("peHist", [None]*len(years)),
        "pbHist": fin.get("pbHist", [None]*len(years)),
        "pe5med": val.get("pe5med"),
        "pe5avg": val.get("pe5avg"),
        "pe": val.get("pe"),
        "peers": contract.get("peers", {"data": []}),
        "peerLabel": contract.get("peerLabel", "P/E"),
        "peerPBMin": contract.get("peerPBMin"),
        "peerPBMax": contract.get("peerPBMax"),
        "tech52wLow": tech.get("tech52wLow") if tech else None,
        "techMA50val": tech.get("techMA50val") if tech else None,
        "techRSI": tech.get("techRSI") if tech else None,
        "techPrice": contract.get("price"),
        "segMix": contract.get("segMix", {"labels": [], "values": []}),
    }

    # Remove None values for cleanliness (JS handles undefined)
    data_clean = {}
    for k, v in data.items():
        if v is not None:
            data_clean[k] = v

    # Serialize to JS (not JSON — JS allows unquoted keys)
    return json.dumps(data_clean, ensure_ascii=False)


def extract_data_block(html):
    """Extract the const DATA = {...} block from HTML. Returns the parsed dict or None."""
    # Match const DATA = {...} (greedy but bounded by ; or </script>)
    patterns = [
        r'const\s+DATA\s*=\s*(\{[^}]*(?:\{[^}]*\}[^}]*)*\})\s*;',
        r'DATA\s*=\s*(\{[^}]*(?:\{[^}]*\}[^}]*)*\})\s*;',
        r'const\s+DATA\s*=\s*(\{.*?\})\s*(?:;|</)',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                # Try parsing as JSON (may need cleanup for JS syntax)
                raw = m.group(1)
                # Convert JS object to JSON: quote unquoted keys
                raw_json = re.sub(r'(\w+)\s*:', r'"\1":', raw)
                raw_json = re.sub(r"'", '"', raw_json)
                # Remove trailing commas
                raw_json = re.sub(r',\s*}', '}', raw_json)
                raw_json = re.sub(r',\s*]', ']', raw_json)
                return json.loads(raw_json), raw
            except (json.JSONDecodeError, Exception):
                continue
    return None, None


def validate_data_keys(html_data):
    """Validate that the DATA object in HTML uses canonical keys, not aliases.

    Returns: {
        'passed': bool,
        'missing_keys': [canonical keys absent],
        'forbidden_aliases_found': {alias: canonical_replacement},
        'extra_keys': [non-canonical keys present],
    }
    """
    if html_data is None:
        return {"passed": False, "error": "no DATA object found in HTML"}

    html_keys = set(html_data.keys())
    canonical = set(CANONICAL_DATA_KEYS)

    # Check for forbidden aliases
    found_aliases = {}
    for alias, canonical_key in FORBIDDEN_ALIASES.items():
        if alias in html_keys and canonical_key not in html_keys:
            found_aliases[alias] = canonical_key

    # Check for missing canonical keys
    missing = canonical - html_keys
    # Don't flag missing optional keys (grossProfit, cfo, etc. may be null)
    required = {"ticker", "years", "revenue", "netProfit", "eps", "totalAssets", "equity"}
    missing_required = required - html_keys

    # Extra non-canonical keys (informational)
    known_extra = {"peers", "peerLabel", "peerPBMin", "peerPBMax",
                   "tech52wLow", "techMA50val", "techRSI", "techPrice",
                   "segMix", "techMA10", "techMA20", "techMA50", "techWeeks",
                   "peerYLabel", "peerYMax"}
    extra = html_keys - canonical - known_extra - set(FORBIDDEN_ALIASES.keys())

    passed = len(found_aliases) == 0 and len(missing_required) == 0
    return {
        "passed": passed,
        "missing_required_keys": sorted(missing_required),
        "forbidden_aliases_found": found_aliases,
        "extra_keys": sorted(extra - set(FORBIDDEN_ALIASES.keys())),
    }


def inject_canonical_data(html, contract):
    """Replace the agent's DATA block with the canonical one from the contract.

    Returns: (modified_html, report) where report describes what was changed.
    """
    canonical_data_js = serialize_data_block(contract)
    canonical_block = f"const DATA = {canonical_data_js};"

    # Find the agent's DATA block
    agent_data, agent_raw = extract_data_block(html)
    report = {"agent_data_found": agent_data is not None}

    # ALWAYS check for and remove duplicate DATA blocks, even if validation passes.
    # Multiple const DATA declarations cause JS errors and confuse the verifier.
    import re as _re
    data_count = len(_re.findall(r'const\s+DATA\s*=', html))
    has_duplicates = data_count > 1

    if agent_data:
        validation = validate_data_keys(agent_data)
        report["validation_before"] = validation

        if validation["passed"] and not has_duplicates:
            # Agent's data is canonical AND single — no replacement needed
            report["action"] = "no_change_needed"
            return html, report

    # Replace ALL existing DATA blocks with the canonical one.
    # CRITICAL: must remove ALL occurrences to prevent duplicate const DATA declarations
    # (which cause JS syntax errors and confuse the verifier).
    # Strategy: find each "const DATA = " or "DATA = " assignment, then match balanced
    # braces to find the end of the object.
    canonical_block_str = f"const DATA = {canonical_data_js};"
    replaced = False

    # Remove all existing DATA assignments by processing <script> blocks.
    # Strategy: collect ALL script blocks, remove ones containing DATA assignment,
    # then insert ONE canonical DATA script block.
    new_html = html
    removed_count = 0
    data_scripts_found = []

    # Find all <script> blocks and classify them
    def process_scripts(text):
        nonlocal removed_count
        result = []
        last_end = 0
        for m in re.finditer(r'<script\b[^>]*>(.*?)</script>', text, re.DOTALL | re.I):
            result.append(text[last_end:m.start()])  # pre-script content
            script_content = m.group(1)
            if re.search(r'(?:const\s+)?DATA\s*=\s*\{', script_content):
                removed_count += 1
                # Skip this script entirely (don't add it back)
            else:
                result.append(m.group(0))  # keep non-DATA scripts
            last_end = m.end()
        result.append(text[last_end:])  # trailing content
        return ''.join(result)

    new_html = process_scripts(new_html)

    # Handle DATA outside scripts (bare assignments)
    while True:
        m = re.search(r'(?:const\s+)?DATA\s*=\s*\{', new_html)
        if not m:
            break
        start = m.end() - 1
        depth = 0
        end = start
        for i in range(start, len(new_html)):
            if new_html[i] == '{': depth += 1
            elif new_html[i] == '}':
                depth -= 1
                if depth == 0: end = i; break
        after = new_html[end+1:end+5]
        semi = 1 if after.startswith(';') else 0
        new_html = new_html[:m.start()] + new_html[end+1+semi:]
        removed_count += 1

    replaced = removed_count > 0
    report["blocks_removed"] = removed_count

    if replaced:
        # Insert the canonical block before the first <script> tag
        script_match = re.search(r'<script', new_html)
        if script_match:
            insert_pos = script_match.start()
            new_html = new_html[:insert_pos] + f"<script>\n{canonical_block_str}\n</script>\n" + new_html[insert_pos:]
        else:
            new_html = new_html.replace("</body>", f"<script>\n{canonical_block_str}\n</script>\n</body>")
    else:
        # No existing DATA found — insert canonical
        script_match = re.search(r'<script', new_html)
        if script_match:
            insert_pos = script_match.start()
            new_html = new_html[:insert_pos] + f"<script>\n{canonical_block_str}\n</script>\n" + new_html[insert_pos:]
        else:
            new_html = new_html.replace("</body>", f"<script>\n{canonical_block_str}\n</script>\n</body>")

    report["action"] = "replaced_agent_data_with_canonical" if agent_data else "inserted_canonical_data"
    report["replaced"] = replaced
    return new_html, report


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 data_contract_enforcer.py <html_file> <contract.json>")
        print("       python3 data_contract_enforcer.py --validate <html_file>")
        sys.exit(1)

    if sys.argv[1] == "--validate":
        html = open(sys.argv[2]).read()
        data, raw = extract_data_block(html)
        result = validate_data_keys(data)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["passed"] else 1)

    html_path, contract_path = sys.argv[1], sys.argv[2]
    html = open(html_path).read()
    contract = json.load(open(contract_path))
    new_html, report = inject_canonical_data(html, contract)
    open(html_path, "w").write(new_html)
    print(json.dumps(report, indent=2, ensure_ascii=False))
