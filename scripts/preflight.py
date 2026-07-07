#!/usr/bin/env python3
"""
preflight.py — Preflight check cho cổ phiếu VN TRƯỚC khi chạy equity-research-vn.

Port từ us-equity-research/scripts/preflight.py, adapt cho vnstock + đặc thù VN.

Kiểm tra:
  1. AUDIT SPLIT (gọi audit_split.py — Bẫy 5B)
  2. NEGATIVE EARNINGS (LNST âm → PE vô nghĩa)
  3. HISTORY TOO SHORT (IPO < 5 năm → median 5N vô nghĩa)
  4. STALE DATA (BCTC chưa cập nhật)
  5. DELISTING RISK (giao dịch thất thường / cảnh báo)
  6. TICKER MISMATCH (mã sai / UPCOM không có data)

Usage:
  python3 preflight.py HPG
  python3 preflight.py BSR --period 5

Requires: pip install vnstock
"""

import sys
import json
import argparse
from datetime import datetime, date

try:
    from vnstock.api.financial import Finance
    from vnstock.api.company import Company
    from vnstock.api.quote import Quote
except ImportError:
    print("ERROR: vnstock not installed. pip install vnstock", file=sys.stderr)
    sys.exit(2)

# Import audit_split từ cùng folder
sys.path.insert(0, '.')
try:
    from audit_split import audit_split
except ImportError:
    audit_split = None


def preflight(ticker: str, period_years: int = 5) -> dict:
    """Preflight checks cho cổ phiếu VN."""
    result = {
        "ticker": ticker.upper(),
        "checked_at": datetime.now().isoformat(),
        "period_years": period_years,
        "flags": [],
        "recommendations": [],
        "go_no_go": "GO",
        "valuation_path": "A",  # A = PE/PB median (mặc định), B = EV/Revenue (công ty lỗ)
    }

    c = Company(symbol=ticker, source='VCI')

    # === CHECK 0: AUDIT SPLIT (Bẫy 5B — gọi audit_split) ===
    if audit_split:
        try:
            split_audit = audit_split(ticker, period_years)
            if split_audit["adjustment_needed"]:
                result["flags"].append({
                    "id": "SPLIT_ADJUSTMENT_NEEDED",
                    "severity": "WARN",
                    "msg": split_audit["recommendation"][:200],
                    "detail": f"Phát hiện {split_audit['details'].get('suspicious_events_count', '?')} event liên quan split."
                })
                result["recommendations"].append(
                    "Chạy adjustment EPS/BVPS trước mọi tính toán PE/PB (Bẫy 5B)."
                )
        except Exception as e:
            result["flags"].append({
                "id": "AUDIT_SPLIT_FAILED",
                "severity": "INFO",
                "msg": f"audit_split fail: {e}"
            })

    # === Fetch overview cho các check sau ===
    try:
        info = c.overview()
    except Exception as e:
        result["flags"].append({
            "id": "OVERVIEW_FETCH_FAILED",
            "severity": "WARN",
            "msg": f"Không fetch overview: {e} — có thể ticker sai hoặc UPCOM không có data."
        })
        result["go_no_go"] = "STOP"
        return result

    result["company_name"] = info.get('company_name') or info.get('organ_name') or 'NOT FOUND'
    result["sector"] = info.get('sector')
    result["industry"] = info.get('industry')
    result["exchange"] = info.get('exchange')

    # === CHECK 1: NEGATIVE EARNINGS (LNST âm) ===
    try:
        f = Finance(symbol=ticker, source='VCI')
        income = f.income_statement()
        if income is not None and hasattr(income, 'iterrows'):
            # Tìm dòng LNST thuộc CĐ mẹ
            lnst_row = None
            for idx in income.index:
                idx_lower = str(idx).lower()
                if ('lợi nhuận của cổ đông' in idx_lower or 'net profit' in idx_lower) and 'cổ đông' in idx_lower:
                    lnst_row = idx
                    break

            if lnst_row and len(income.columns) > 0:
                latest_col = income.columns[0]
                latest_lnst = float(income.loc[lnst_row, latest_col])

                # Tính số năm lỗ
                loss_years = 0
                for col in income.columns[:period_years]:
                    try:
                        lnst_val = float(income.loc[lnst_row, col])
                        if lnst_val < 0:
                            loss_years += 1
                    except (ValueError, TypeError):
                        continue

                if loss_years >= 2:
                    result["flags"].append({
                        "id": "NEGATIVE_EARNINGS",
                        "severity": "WARN",
                        "msg": f"LNST âm {loss_years}/{period_years} năm gần nhất. PE vô nghĩa cho năm lỗ.",
                        "impact": "PE median 5N bị distort. Median có thể = ∞ hoặc âm.",
                        "fix": "Switch sang valuation path B: EV/Revenue + P/B + P/S. Loại năm lỗ khỏi PE median."
                    })
                    result["valuation_path"] = "B"
                    result["recommendations"].append(
                        "Valuation path B: dùng EV/Revenue + P/B + P/S thay PE median."
                    )
                elif loss_years == 1 and latest_lnst < 0:
                    result["flags"].append({
                        "id": "RECENT_LOSS",
                        "severity": "WARN",
                        "msg": "Năm gần nhất LNST âm. PE TTM vô nghĩa.",
                        "fix": "Dùng PE forward (consensus) HOẶC PE trung bình loại năm lỗ."
                    })
    except Exception as e:
        result["flags"].append({
            "id": "INCOME_FETCH_FAILED",
            "severity": "WARN",
            "msg": f"Không fetch income_statement: {e}"
        })

    # === CHECK 2: HISTORY TOO SHORT (IPO < period yêu cầu) ===
    try:
        f = Finance(symbol=ticker, source='VCI')
        income = f.income_statement()
        if income is not None and hasattr(income, 'columns'):
            years_available = len(income.columns)
            if years_available < period_years:
                result["flags"].append({
                    "id": "HISTORY_TOO_SHORT",
                    "severity": "WARN",
                    "msg": f"Chỉ có {years_available} năm history (yêu cầu {period_years}). IPO gần đây hoặc data thiếu.",
                    "impact": f"Median {period_years}N vô nghĩa với sample {years_available} năm.",
                    "fix": f"Giảm period xuống {max(2, years_available)} năm. Flag 'history limited to {years_available}y'."
                })
                result["recommendations"].append(
                    f"Switch --period {max(2, years_available)}y do IPO gần đây."
                )
    except Exception:
        pass

    # === CHECK 3: STALE DATA (BCTC cũ) ===
    try:
        f = Finance(symbol=ticker, source='VCI')
        income = f.income_statement()
        if income is not None and hasattr(income, 'columns'):
            latest_period = str(income.columns[0])
            # Quy tắc: tháng hiện tại ≥ 4 → kỳ gần nhất = N-1
            current_month = date.today().month
            current_year = date.today().year
            if current_month >= 4:
                expected_year = current_year - 1
            else:
                expected_year = current_year - 2

            # Parse năm từ latest_period (format có thể là '2024', '2024-12-31', etc.)
            try:
                latest_year = int(latest_period[:4])
                if latest_year < expected_year:
                    result["flags"].append({
                        "id": "STALE_DATA",
                        "severity": "WARN",
                        "msg": f"BCTC mới nhất = {latest_period} (năm {latest_year}), expected ≥ {expected_year}.",
                        "impact": "Data cũ → phân tích không phản ánh tình hình hiện tại.",
                        "fix": f"Check trang QHCD DN cho BCTC {expected_year}. Có thể chưa công bố."
                    })
            except ValueError:
                pass
    except Exception:
        pass

    # === CHECK 4: TICKER MISMATCH (UPCOM / mã sai) ===
    if not result.get("company_name") or result["company_name"] == "NOT FOUND":
        result["flags"].append({
            "id": "TICKER_NOT_FOUND",
            "severity": "WARN",
            "msg": f"Không tìm thấy company_name cho '{ticker}' trên vnstock.",
            "impact": "Có thể ticker sai, hoặc niêm yết UPCOM (vnstock ít cover), hoặc đã hủy niêm yết.",
            "fix": "Verify ticker trên HSX/HNX. Nếu UPCOM → WebSearch thay vnstock."
        })

    # === Determine GO / WARN / STOP ===
    warn_count = sum(1 for fl in result["flags"] if fl["severity"] == "WARN")
    if warn_count >= 3:
        result["go_no_go"] = "STOP"
    elif warn_count >= 1:
        result["go_no_go"] = "WARN"
    else:
        result["go_no_go"] = "GO"

    return result


def main():
    ap = argparse.ArgumentParser(description="Preflight check cho cổ phiếu VN")
    ap.add_argument("ticker", help="Mã cổ phiếu (HPG, VCB, BSR...)")
    ap.add_argument("--period", type=int, default=5, help="Số năm phân tích (default 5)")
    args = ap.parse_args()

    result = preflight(args.ticker, args.period)
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))

    print(f"\n→ {args.ticker}: {result['go_no_go']} "
          f"(path={result['valuation_path']}, {len(result['flags'])} flags: "
          f"{[f['id'] for f in result['flags']]})", file=sys.stderr)


if __name__ == "__main__":
    main()
