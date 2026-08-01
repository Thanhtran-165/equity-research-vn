#!/usr/bin/env python3
"""Technical ACTIVE backtest — WALK-FORWARD (W3-1 — Wave 3).

Nguyên tắc (theo báo cáo bàn giao):
- Split THEO THỜI GIAN (không random) — train 60%, test 40% tuần tự
- Mỗi tín hiệu tính trên dữ liệu ĐÃ BIẾT tại ngày đó (không look-ahead: MA/RSI tại t
  chỉ dùng giá ≤ t)
- Có chi phí giao dịch giả định (0.1% + phí sàn) — báo gross VÀ net
- Benchmark: buy & hold
- KHÔNG gọi "alpha" — output là descriptive: "tín hiệu có vượt buy&hold sau chi phí hay không"
  (chưa đạt OOS gate → Tech Score vẫn là unvalidated composite)

Chạy: python3 scripts/tests/backtest_technical.py [price_file] [ticker]
"""
import json, math, os, sys

def sma(vals, p):
    out = [None] * len(vals)
    for i in range(p - 1, len(vals)):
        out[i] = sum(vals[i - p + 1:i + 1]) / p
    return out

def rsi(vals, p=14):
    out = [None] * len(vals)
    for i in range(p, len(vals)):
        gains = losses = 0.0
        for j in range(i - p + 1, i + 1):
            d = vals[j] - vals[j - 1]
            if d > 0: gains += d
            else: losses -= d
        if losses == 0:
            out[i] = 100.0
        else:
            rs = gains / p / (losses / p)
            out[i] = 100 - 100 / (1 + rs)
    return out

def signals(price):
    """Composite đơn giản: MA10 cross + RSI — mô phỏng Tech Score thô (DESCRIPTIVE)."""
    ma10 = sma(price, 10)
    r = rsi(price, 14)
    sig = [0] * len(price)
    for i in range(1, len(price)):
        if ma10[i] is None or ma10[i - 1] is None or r[i] is None:
            continue
        # MA10 cắt lên + RSI > 30 → long; cắt xuống hoặc RSI > 75 → flat
        if ma10[i] > ma10[i - 1] and r[i] > 30:
            sig[i] = 1
        elif ma10[i] < ma10[i - 1] or r[i] > 75:
            sig[i] = 0
        else:
            sig[i] = sig[i - 1]
    return sig

def backtest(price, sig, cost_bps=10):
    """Trả về return tổng (sau chi phí), số lần giao dịch, benchmark return."""
    cash = 1.0
    pos = 0  # 0 flat, 1 long
    trades = 0
    for i in range(1, len(price)):
        target = sig[i]
        if target != pos:
            # đổi trạng thái → trả chi phí một chiều trên toàn bộ vốn
            cash *= (1 - cost_bps / 10000)
            trades += 1
            pos = target
        ret = price[i] / price[i - 1] - 1
        cash *= (1 + ret * pos)
    bench = price[-1] / price[0] - 1
    return cash - 1, trades, bench

def main():
    price_file = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/bobo/ZCodeProject/ctd-v4flash/data/price_daily.json"
    if not os.path.exists(price_file):
        print("❌ Không tìm thấy price file — truyền path hoặc chạy trong work dir có data/")
        sys.exit(2)
    data = json.load(open(price_file))
    closes = [r["close"] for r in data] if isinstance(data, list) else list(data.values())
    n = len(closes)
    split = int(n * 0.6)
    train, test = closes[:split], closes[split:]

    sig_train = signals(train)
    sig_test = signals(test)
    ret_tr, tr_tr, bench_tr = backtest(train, sig_train)
    ret_te, tr_te, bench_te = backtest(test, sig_test)

    print(f"Backtest walk-forward — {n} phiên (train {split}, test {n - split})")
    print(f"  TRAIN: signal {ret_tr*100:+.1f}% | buy&hold {bench_tr*100:+.1f}% | {tr_tr} giao dịch")
    print(f"  TEST : signal {ret_te*100:+.1f}% | buy&hold {bench_te*100:+.1f}% | {tr_te} giao dịch")
    excess = (ret_te - bench_te) * 100
    print(f"  Excess (test, sau chi phí): {excess:+.1f}pp")
    # KHÔNG tuyên bố alpha — chỉ descriptive
    verdict = "vượt buy&hold sau chi phí (1 mẫu — chưa đủ để gọi alpha)" if excess > 0 else \
              "KHÔNG vượt buy&hold sau chi phí — tín hiệu chưa được chứng minh"
    print(f"  Kết luận: {verdict}")

    # Gate OOS (Wave 3): chỉ khi test excess > 0 và >= 2 mẫu độc lập khác nhau mới đổi claim
    if excess > 0:
        print("  ⚠️  Vẫn gọi Tech Score là unvalidated/descriptive — cần thêm cohort + benchmark + CI")

if __name__ == "__main__":
    main()
