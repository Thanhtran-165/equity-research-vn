"""P0-04 (Wave 1): security test — input độc hại không thể injection qua runner/verifier."""
import importlib.util, os, sys, subprocess

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

runner = load("runner", "/Users/bobo/.zcode/skills/equity-research-vn/scripts/run_phase.py")
ver = load("ver", "/Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py")

fails = []
canary = "/tmp/pwn_canary.txt"
if os.path.exists(canary): os.remove(canary)

# 1. Ticker độc hại — phải bị reject
evil_tickers = ["CTD; touch /tmp/pwn_canary.txt", "CTD && touch /tmp/pwn_canary.txt",
                "CTD$(touch /tmp/pwn_canary.txt)", "`touch /tmp/pwn_canary.txt`",
                "CTD\ntouch /tmp/pwn_canary.txt", "CTD'"]
for t in evil_tickers:
    for fn in (runner.validate_inputs, ver.run_command_safe if hasattr(ver, "run_command_safe") else None):
        if fn is None: continue
        try:
            if fn.__name__ == "validate_inputs":
                fn(t, None)
            else:
                fn("echo hi", t, None)
            fails.append(f"runner.validate_inputs không chặn ticker độc hại: {t!r}")
        except ValueError:
            pass
# verifier TICKER_RE
for t in evil_tickers:
    if ver.TICKER_RE_SAFE.fullmatch(t):
        fails.append(f"verifier allowlist không chặn: {t!r}")

# 2. Report path ngoài work dir — reject
try:
    runner.validate_inputs("CTD", "/etc/passwd")
    fails.append("runner: report ngoài work dir không bị chặn")
except ValueError:
    pass
# verifier: path có metacharacter → command chạy argv (không shell) → lệnh fail sạch, không side effect
try:
    code, _ = ver.run_command_safe("printf '%s' $REPORT", "CTD", "/tmp/evil; touch /tmp/pwn_canary.txt")
    if os.path.exists(canary):
        fails.append("CANARY BỊ TẠO qua REPORT path — shell injection!")
except (ValueError, FileNotFoundError):
    pass

# 3. Canary: nếu injection chạy được, file sẽ được tạo — phải KHÔNG tồn tại
if os.path.exists(canary):
    fails.append("CANARY BỊ TẠO — shell injection xảy ra!")
    os.remove(canary)

# 4. Command hợp lệ vẫn chạy đúng (pipe thủ công) — REQ-010 dạng wc/tr
code, out = runner.run_command_safe("printf 'a\\nb\\n' | wc -l | tr -d ' '", "CTD", None)
if code != 0 or out.strip() != "2":
    fails.append(f"pipe thủ công sai: code={code} out={out!r} (kỳ vọng 2)")

if fails:
    print("❌ SECURITY TEST FAIL:")
    for f in fails: print("  -", f)
    sys.exit(1)
print("✅ SECURITY OK — ticker độc hại bị chặn, path ngoài work dir bị chặn, canary không bị tạo, pipe thủ công đúng")
