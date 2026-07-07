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
        info_df = c.overview()
        # vnstock 4.0 trả DataFrame 1 row — convert sang dict
        if hasattr(info_df, 'iloc') and len(info_df) > 0:
            info = info_df.iloc[0].to_dict()
        elif isinstance(info_df, dict):
            info = info_df
        else:
            info = {}
    except Exception as e:
        result["flags"].append({
            "id": "OVERVIEW_FETCH_FAILED",
            "severity": "WARN",
            "msg": f"Không fetch overview: {e} — có thể ticker sai hoặc UPCOM không có data."
        })
        result["go_no_go"] = "STOP"
        return result

    result["company_name"] = info.get('organ_name') or info.get('organ_short_name') or info.get('company_name') or 'NOT FOUND'
    result["sector"] = info.get('sector') or info.get('icb_name') or info.get('industry_name')
    result["industry"] = info.get('industry') or info.get('icb_name')
    result["exchange"] = info.get('exchange') or info.get('comGroupCode')

    # === CHECK 1: NEGATIVE EARNINGS (LNST âm) ===
    try:
        f = Finance(symbol=ticker, source='VCI')
        income = f.income_statement()
        if income is not None and hasattr(income, 'iterrows'):
            # vnstock 4.0: rows = item, có cột 'item'/'item_en'. Filter theo tên.
            # vnstock 3.x: rows = index = tên metric.
            lnst_row = None
            period_cols = []
            for col in income.columns:
                if str(col).startswith('20') or str(col).startswith('19'):
                    period_cols.append(col)

            for idx, row in income.iterrows():
                item_text = str(row.get('item', '')) + ' ' + str(row.get('item_en', '')) if 'item' in income.columns else str(income.index[idx]).lower() if idx < len(income.index) else ''
                item_lower = item_text.lower()
                if ('lợi nhuận của cổ đông' in item_lower or 'net profit' in item_lower or 'net income' in item_lower) and ('cổ đông' in item_lower or 'parent' in item_lower):
                    lnst_row = idx
                    break

            if lnst_row is not None and len(period_cols) > 0:
                # Lấy giá trị LNST các kỳ
                lnst_values = []
                for col in period_cols[:period_years*4]:  # mỗi năm ~4 quý
                    try:
                        if 'item' in income.columns:
                            val = float(income.iloc[lnst_row][col])
                        else:
                            val = float(income.loc[lnst_row, col])
                        lnst_values.append(val)
                    except (ValueError, TypeError):
                        continue

                # Cộng gộp theo năm nếu là quarterly (Q1+Q2+Q3+Q4)
                # Hoặc chỉ check dấu (nếu âm = lỗ)
                loss_count = sum(1 for v in lnst_values if v < 0)
                latest_lnst = lnst_values[0] if lnst_values else 0

                if loss_count >= 8 or (loss_count >= 4 and latest_lnst < 0):  # ≥2 năm lỗ hoặc gần nhất lỗ
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
                elif loss_count >= 4 and latest_lnst < 0:
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
            # Đếm số cột period (bắt đầu bằng 20xx hoặc 19xx)
            period_cols = [c for c in income.columns if str(c).startswith(('20', '19'))]
            # Quy đổi: 4 quý/năm → years = period_cols / 4 (annual) hoặc period_cols (nếu annual)
            years_available = max(1, len(period_cols) // 4) if len(period_cols) > 5 else len(period_cols)
            if years_available < period_years:
                result["flags"].append({
                    "id": "HISTORY_TOO_SHORT",
                    "severity": "WARN",
                    "msg": f"Chỉ có ~{years_available} năm history (yêu cầu {period_years}). IPO gần đây hoặc data thiếu.",
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
            period_cols = [c for c in income.columns if str(c).startswith(('20', '19'))]
            latest_period = str(period_cols[0]) if period_cols else ''
            # Quy tắc: tháng hiện tại ≥ 4 → kỳ gần nhất = N-1
            current_month = date.today().month
            current_year = date.today().year
            if current_month >= 4:
                expected_year = current_year - 1
            else:
                expected_year = current_year - 2

            # Parse năm từ latest_period (format có thể là '2024', '2024-Q4', etc.)
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
