# HBC 2022 Independent Share Bridge

**Ticker:** HBC (Hoa Binh Construction)
**Period:** FY2022 (loss year, NPAT = -2,606 tỷ VND)
**Purpose:** Independent verification of weighted-average shares WITHOUT using provider-reported EPS.

## 1. Problem

Provider (vnstock) reports HBC EPS 2022 = -9,846 VND. Engine derives weighted shares = NPAT / EPS = 264,690,790. This is DERIVED_INPUT — cannot be used as independent oracle for EPS validation.

## 2. Independent reconstruction

**Source:** Balance sheet — paid-in capital (vốn góp) — NOT provider EPS.

| Item | Value | Source |
|---|---|---|
| Paid-in capital end 2021 | 2,424,157,840,000 VND | Balance sheet 2021 |
| Paid-in capital end 2022 | 2,741,332,700,000 VND | Balance sheet 2022 |
| Par value | 10,000 VND/share | HOSE standard |
| Beginning shares (end 2021) | 242,415,784 | paid-in 2021 / par |
| Ending shares (end 2022) | 274,133,270 | paid-in 2022 / par |
| **Midpoint weighted (independent)** | **258,274,527** | (beginning + ending) / 2 |

## 3. Bridge comparison

| Metric | Value |
|---|---|
| Derived from provider EPS | 264,690,790 |
| Independently reconstructed | 258,274,527 |
| Absolute difference | 6,416,263 |
| Relative difference | **2.5%** |
| Tolerance | 15% (midpoint is approximation) |
| **Tieout** | **PASS** |

## 4. Corporate action evidence

Paid-in capital increased by 317 tỷ VND (2,424 → 2,741 tỷ) = share issuance during 2022. This confirms HBC issued ~31.7 million new shares, explaining the difference between beginning and ending share counts.

## 5. Non-circular confirmation

The independent reconstruction uses **only** balance sheet paid-in capital + par value. It does NOT use:
- Provider EPS
- Provider NPAT
- Any income statement field

The 2.5% difference between midpoint and provider-derived weighted is expected because:
- Midpoint assumes issuance at mid-year
- Actual issuance timing varies
- Weighted-average depends on exact issuance dates

This confirms the derived weighted shares are in the correct range, validated independently.

## 6. Conclusion

HBC share bridge = **PASS**. HBC qualifies as negative-EPS edge case.
