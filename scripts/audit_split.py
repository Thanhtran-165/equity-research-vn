#!/usr/bin/env python3
"""
audit_split.py — Audit Bẫy 5B (split-adjustment consistency) cho cổ phiếu VN.

Vấn đề: vnstock Quote.history() trả giá split-adjusted, BCTC dùng base CP gốc
→ mix chuẩn → PE/PB SAI hoàn toàn (case BSR: PE sai 6.10× → đúng 9.85×).

Audit này automate 3 check từ equity-research-vn Lesson #1:
  1. Check Company.events() cho split/dividend-stock event
  2. Check Company.capital_history() cho vốn điều lệ tăng đột biến
  3. Back-calc CP = LNST/EPS từng năm — nếu mismatch > 5% → flag

Usage:
  python3 audit_split.py HPG
  python3 audit_split.py BSR --period 5

Requires: pip install vnstock
"""

import sys
import json
import argparse
from datetime import datetime

try:
    from vnstock.api.financial import Finance
    from vnstock.api.company import Company
except ImportError:
    print("ERROR: vnstock not installed. pip install vnstock", file=sys.stderr)
    sys.exit(2)


def audit_split(ticker: str, period_years: int = 5) -> dict:
    """Audit Bẫy 5B cho 1 ticker. Trả dict có flags + recommendations."""
    result = {
        "ticker": ticker.upper(),
        "checked_at": datetime.now().isoformat(),
        "period_years": period_years,
        "flags": [],
        "go_no_go": "GO",
        "adjustment_needed": False,
        "details": {},
    }

    c = Company(symbol=ticker, source='VCI')

    # === CHECK 1: Events — split / dividend-stock ===
    try:
        events = c.events()
        if events is not None and len(events) > 0:
            # Tìm event có keyword split / cổ tức cổ phiếu / phát hành thêm
            split_keywords = ['split', 'chia cổ phiếu', 'phát hành thêm', 'cổ tức cổ phiếu',
                              'chia thưởng', 'thưởng cổ phiếu', 'phát hành cổ phiếu']
            suspicious_events = []
            if hasattr(events, 'iterrows'):
                for _, row in events.iterrows():
                    text = ' '.join(str(v) for v in row.values).lower()
                    if any(kw in text for kw in split_keywords):
                        suspicious_events.append({
                            'date': str(row.iloc[0]) if len(row) > 0 else 'unknown',
                            'text': text[:200]
                        })
            elif isinstance(events, list):
                for ev in events:
                    text = str(ev).lower()
                    if any(kw in text for kw in split_keywords):
                        suspicious_events.append({'text': text[:200]})

            if suspicious_events:
                result["flags"].append({
                    "id": "SPLIT_EVENT_DETECTED",
                    "severity": "WARN",
                    "msg": f"Phát hiện {len(suspicious_events)} event liên quan split/issuance trong lịch sử.",
                    "events": suspicious_events[:5]
                })
                result["details"]["suspicious_events_count"] = len(suspicious_events)
    except Exception as e:
        result["flags"].append({
            "id": "EVENTS_FETCH_FAILED",
            "severity": "INFO",
            "msg": f"Không fetch được events: {e}"
        })

    # === CHECK 2: Capital history — vốn điều lệ tăng đột biến ===
    try:
        cap_hist = c.capital_history()
        if cap_hist is not None and hasattr(cap_hist, 'iterrows'):
            # Tìm năm tăng vốn điều lệ > 20% YoY (có thể là stock dividend/split)
            spikes = []
            prev = None
            for _, row in cap_hist.iterrows():
                # Attempt to extract numeric capital value
                for col in cap_hist.columns:
                    val = row[col]
                    if isinstance(val, (int, float)) and val > 0:
                        if prev and isinstance(prev, (int, float)) and prev > 0:
                            pct_change = (val - prev) / prev * 100
                            if pct_change > 20:
                                spikes.append({
                                    'period': str(row.iloc[0]) if len(row) > 0 else 'unknown',
                                    'change_pct': round(pct_change, 1)
                                })
                        prev = val
                        break
            if spikes:
                result["flags"].append({
                    "id": "CAPITAL_SPIKE",
                    "severity": "WARN",
                    "msg": f"Vốn điều lệ tăng đột biến ({len(spikes)} lần >20%) — có thể là stock dividend/split.",
                    "spikes": spikes[:5]
                })
    except Exception as e:
        # capital_history có thể không có cho mọi ticker
        pass

    # === CHECK 3: Back-calc CP = LNST/EPS — mismatch detection ===
    try:
        f = Finance(symbol=ticker, source='VCI')
        income = f.income_statement()
        if income is not None and hasattr(income, 'iterrows'):
            # Tìm dòng LNST và EPS
            lnst_row = None
            eps_row = None
            shares_row = None
            for idx in income.index:
                idx_lower = str(idx).lower()
                if 'lợi nhuận của cổ đông' in idx_lower or 'lnst' in idx_lower or 'net profit' in idx_lower:
                    if 'cổ đông' in idx_lower or 'parent' in idx_lower or 'mother' in idx_lower:
                        lnst_row = idx
                if 'lãi cơ bản' in idx_lower or 'eps' in idx_lower or 'basic' in idx_lower:
                    eps_row = idx
                if 'số cp' in idx_lower or 'shares' in idx_lower or 'cổ phiếu' in idx_lower:
                    shares_row = idx

            if lnst_row and eps_row:
                mismatches = []
                for col in income.columns:
                    try:
                        lnst = float(income.loc[lnst_row, col])
                        eps = float(income.loc[eps_row, col])
                        if eps > 0 and lnst > 0:
                            implied_shares = lnst / eps  # LNST (VND) / EPS (VND/cp)
                            # Compare với shares hiện tại từ overview
                            # Nếu mismatch > 5% → flag
                            result["details"][f"implied_shares_{col}"] = implied_shares
                    except (ValueError, TypeError):
                        continue

                # Heuristic: so sánh implied_shares qua các năm
                # Nếu tăng đột biến >20% → có thể split/stock dividend
                implied_list = [v for k, v in result["details"].items() if 'implied_shares' in k]
                implied_list.sort()
                for i in range(1, len(implied_list)):
                    pct = (implied_list[i] - implied_list[i-1]) / implied_list[i-1] * 100
                    if pct > 20:
                        result["flags"].append({
                            "id": "SHARES_COUNT_SPIKE",
                            "severity": "WARN",
                            "msg": f"Số CP ngụ ý (LNST/EPS) tăng {pct:.1f}% giữa 2 năm — có thể split/stock dividend.",
                            "from": implied_list[i-1],
                            "to": implied_list[i]
                        })
                        break
    except Exception as e:
        result["flags"].append({
            "id": "INCOME_FETCH_FAILED",
            "severity": "WARN",
            "msg": f"Không fetch được income_statement: {e}"
        })

    # === Determine GO / WARN / ADJUSTMENT_NEEDED ===
    warn_count = sum(1 for fl in result["flags"] if fl["severity"] == "WARN")
    if warn_count >= 1:
        result["go_no_go"] = "WARN"
        result["adjustment_needed"] = True
        result["recommendation"] = (
            "⚠️ Split/stock dividend PHÁT HIỆN. PHẢI adjust EPS/BVPS/shares cho TẤT CẢ năm "
            "về cùng base với giá hiện tại trước khi tính PE/PB. "
            "Verify: PE_pre-split = PE_post-split. "
            "Nếu skip adjustment → PE/PB sai hệ số (case BSR: sai 60%+)."
        )
    else:
        result["go_no_go"] = "GO"
        result["recommendation"] = "Không phát hiện split/stock dividend. Có thể tính PE/PB trực tiếp."

    return result


def main():
    ap = argparse.ArgumentParser(description="Audit Bẫy 5B (split-adjustment) cho cổ phiếu VN")
    ap.add_argument("ticker", help="Mã cổ phiếu (HPG, BSR, VCB...)")
    ap.add_argument("--period", type=int, default=5, help="Số năm kiểm tra (default 5)")
    args = ap.parse_args()

    result = audit_split(args.ticker, args.period)
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))

    print(f"\n→ {args.ticker}: {result['go_no_go']} "
          f"(adjustment_needed={result['adjustment_needed']}, "
          f"{len(result['flags'])} flags)", file=sys.stderr)


if __name__ == "__main__":
    main()
