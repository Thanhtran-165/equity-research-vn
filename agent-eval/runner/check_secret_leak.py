#!/usr/bin/env python3
"""Scan a workspace for accidental API-key / secret leakage into artifacts."""
import sys, os, re, json
ws = sys.argv[1]
config_key = ""
try:
    config_key = json.load(open(os.path.expanduser("~/.zcode/cli/config.json")))["provider"]["builtin:zai-coding-plan"]["options"]["apiKey"]
except Exception: pass
patterns = [r"sk-[A-Za-z0-9]{20,}", r"78ad4d3f[A-Za-z0-9]*"]  # generic sk- + this key's prefix
if config_key and len(config_key)>10:
    patterns.append(re.escape(config_key[:12]))  # first 12 chars of the actual key
leaks = []
for f in os.listdir(ws):
    p = os.path.join(ws, f)
    if not os.path.isfile(p): continue
    try:
        txt = open(p, errors="ignore").read()
        for pat in patterns:
            for m in re.finditer(pat, txt):
                leaks.append({"file": f, "match": m.group(0)[:8]+"...", "pattern": pat[:20]})
    except Exception: pass
print(json.dumps({"workspace": ws, "secret_leak_detected": bool(leaks), "leaks": leaks[:5]}, indent=2))
sys.exit(1 if leaks else 0)
