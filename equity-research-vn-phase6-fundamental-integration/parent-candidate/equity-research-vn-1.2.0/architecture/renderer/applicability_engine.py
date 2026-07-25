#!/usr/bin/env python3
"""
applicability_engine.py — Shared applicability decision engine.

Architecture Phase B component #1.
Produces a single applicability decision (with decision_hash) that ALL layers
must use: IR builder, section registry, chart builder, renderer, verifier.

No carve-outs in individual gates. One decision, one hash, everywhere.
"""
import hashlib, json

# Registered applicability rules
RULES = {
    "INSURANCE_REVENUE_NOT_GENERIC_SALES": {
        "subject": "revenue",
        "sectors": ["Insurance", "Bảo hiểm", "Financial Services"],
        "condition": "no generic 'Sales' column in income_statement CSV",
        "result": "NOT_APPLICABLE",
    },
    "BANKING_REVENUE_NOT_GENERIC_SALES": {
        "subject": "revenue",
        "sectors": ["Banking", "Ngân hàng"],
        "condition": "banks use interest income, not generic sales",
        "result": "NOT_APPLICABLE",
    },
    "NO_RELEVANT_CORPORATE_ACTION_EVIDENCE": {
        "subject": "audit_split",
        "sectors": ["*"],
        "condition": "no stock split / bonus shares / rights issue in events.csv or overview.json",
        "result": "NOT_APPLICABLE",
    },
    "TECH_MODE_ACTIVE": {
        "subject": "tech_active",
        "sectors": ["*"],
        "condition": "technical_active.json has mode=ACTIVE and tech_score",
        "result": "APPLICABLE",
    },
    "TECH_MODE_PROFILE": {
        "subject": "tech_profile",
        "sectors": ["*"],
        "condition": "technical_profile.json has mode=PROFILE",
        "result": "APPLICABLE",
    },
}

# Sector detection from overview.json
def detect_sector(overview):
    """Return normalized sector string from overview dict."""
    sector = str(overview.get("sector", "")).strip()
    if not sector:
        sector = str(overview.get("industry_name", "")).strip()
    # Normalize common Vietnamese sector names
    sector_lower = sector.lower()
    if "bảo hiểm" in sector_lower or "insurance" in sector_lower:
        return "Insurance"
    if "ngân hàng" in sector_lower or "banking" in sector_lower or "bank" in sector_lower:
        return "Banking"
    if "bán lẻ" in sector_lower or "retail" in sector_lower:
        return "Retail"
    if "công nghệ" in sector_lower or "technology" in sector_lower:
        return "Technology"
    if "thép" in sector_lower or "steel" in sector_lower:
        return "Steel"
    if "bất động sản" in sector_lower or "real estate" in sector_lower:
        return "Real Estate"
    if "điện" in sector_lower or "power" in sector_lower or "utility" in sector_lower:
        return "Utilities"
    if "hóa chất" in sector_lower or "chemical" in sector_lower:
        return "Chemicals"
    if "dầu khí" in sector_lower or "oil" in sector_lower or "gas" in sector_lower:
        return "Energy"
    if "hàng không" in sector_lower or "airline" in sector_lower:
        return "Airlines"
    if "nông" in sector_lower or "agri" in sector_lower or "rubber" in sector_lower:
        return "Agriculture"
    if "dược" in sector_lower or "pharma" in sector_lower:
        return "Pharma"
    if "xây dựng" in sector_lower or "construction" in sector_lower:
        return "Construction"
    if "tiêu dùng" in sector_lower or "consumer" in sector_lower or "food" in sector_lower:
        return "Consumer"
    if "đa ngành" in sector_lower or "diversified" in sector_lower or "conglomerate" in sector_lower:
        return "Diversified"
    return sector or "Unknown"


def decide(subject, ticker, sector, field_status=None, source_evidence=None):
    """Produce a single applicability decision with decision_hash.

    Args:
        subject: "revenue", "audit_split", "tech_active", "tech_profile", etc.
        ticker: ticker symbol
        sector: normalized sector string (from detect_sector)
        field_status: status from data contract (e.g., "NOT_APPLICABLE" for revenue)
        source_evidence: dict of evidence (events.csv content, technical_active.json, etc.)

    Returns:
        {
            "decision_id": "...",
            "subject": "...",
            "ticker": "...",
            "sector": "...",
            "status": "APPLICABLE" | "NOT_APPLICABLE" | "UNRESOLVED",
            "rule_id": "...",
            "evidence": {...},
            "decision_hash": "sha256..."
        }
    """
    # Revenue applicability
    if subject == "revenue":
        if field_status == "NOT_APPLICABLE":
            if sector in ("Insurance", "Banking"):
                rule_id = "INSURANCE_REVENUE_NOT_GENERIC_SALES" if sector == "Insurance" else "BANKING_REVENUE_NOT_GENERIC_SALES"
            else:
                rule_id = "GENERIC_REVENUE_NOT_RESOLVED"
            status = "NOT_APPLICABLE"
        else:
            rule_id = "GENERIC_REVENUE_APPLICABLE"
            status = "APPLICABLE"

    # Audit-split applicability
    elif subject == "audit_split":
        # Check source evidence for corporate actions
        events = (source_evidence or {}).get("events", [])
        has_split = any(
            "split" in str(e).lower() or "chia cổ phiếu" in str(e).lower()
            or "bonus" in str(e).lower() or "phát hành thêm" in str(e).lower()
            for e in events
        )
        if has_split:
            status = "APPLICABLE"
            rule_id = "CORPORATE_ACTION_DETECTED"
        else:
            status = "NOT_APPLICABLE"
            rule_id = "NO_RELEVANT_CORPORATE_ACTION_EVIDENCE"

    # Tech mode applicability
    elif subject == "tech_active":
        tech_data = (source_evidence or {}).get("technical_active", {})
        if tech_data.get("mode") == "ACTIVE" and "tech_score" in tech_data:
            status = "APPLICABLE"
            rule_id = "TECH_MODE_ACTIVE"
        else:
            status = "NOT_APPLICABLE"
            rule_id = "TECH_MODE_NOT_ACTIVE"

    elif subject == "tech_profile":
        tech_data = (source_evidence or {}).get("technical_profile", {})
        if tech_data.get("mode") == "PROFILE":
            status = "APPLICABLE"
            rule_id = "TECH_MODE_PROFILE"
        else:
            status = "NOT_APPLICABLE"
            rule_id = "TECH_MODE_NO_PROFILE"

    else:
        status = "APPLICABLE"
        rule_id = "DEFAULT_APPLICABLE"

    # Build decision
    decision = {
        "decision_id": f"{ticker}_{subject}",
        "subject": subject,
        "ticker": ticker,
        "sector": sector,
        "status": status,
        "rule_id": rule_id,
        "evidence": {
            "field_status": field_status,
            "source_evidence_keys": list((source_evidence or {}).keys()),
            "sector": sector,
        },
    }
    # Compute decision hash — all layers must use this exact hash
    hash_input = json.dumps({
        "subject": subject, "ticker": ticker, "sector": sector,
        "status": status, "rule_id": rule_id,
    }, sort_keys=True)
    decision["decision_hash"] = hashlib.sha256(hash_input.encode()).hexdigest()

    return decision


def decide_all(ticker, sector, field_statuses, source_evidence):
    """Produce all applicability decisions for a ticker.

    Args:
        field_statuses: {"revenue": "VALID", "net_profit": "VALID", ...}
        source_evidence: {"events": [...], "technical_active": {...}, ...}

    Returns:
        {"revenue": decision, "audit_split": decision, "tech_active": decision, ...}
    """
    subjects = ["revenue", "audit_split", "tech_active", "tech_profile"]
    decisions = {}
    for subject in subjects:
        decisions[subject] = decide(
            subject=subject,
            ticker=ticker,
            sector=sector,
            field_status=field_statuses.get(subject),
            source_evidence=source_evidence,
        )
    return decisions
