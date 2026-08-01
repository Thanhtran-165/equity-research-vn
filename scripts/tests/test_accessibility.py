#!/usr/bin/env python3
"""Accessibility + runtime-render static tests (W4-2 — Wave 4).

Kiểm trên file HTML build (không cần browser):
1. viewport meta (mobile)
2. prefers-reduced-motion (nhạy cảm chuyển động)
3. canvas có aria-label/role (screen reader)
4. màu tương phản: --text vs --bg (WCAG AA ~4.5:1)
Chạy: python3 scripts/tests/test_accessibility.py [report.html]
"""
import os, re, sys

DEFAULT = "/Users/bobo/ZCodeProject/ctd-v4flash/CTD_Complete_Report.html"

def contrast(hex1, hex2):
    def lum(h):
        h = h.lstrip("#")
        r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
        def f(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = f(r), f(g), f(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1, l2 = sorted((lum(hex1), lum(hex2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

def run():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    html = open(path).read()
    fails = []

    # 1. viewport
    if not re.search(r'<meta[^>]*name=["\']viewport["\']', html):
        fails.append("thiếu viewport meta (mobile)")

    # 2. reduced motion
    if "prefers-reduced-motion" not in html:
        fails.append("thiếu @media prefers-reduced-motion")

    # 3. canvas accessibility: aria-label hoặc role=img
    canvases = re.findall(r'<canvas[^>]*>', html)
    no_aria = [c[:60] for c in canvases if 'aria-label' not in c and 'role=' not in c]
    if no_aria:
        fails.append(f"{len(no_aria)}/{len(canvases)} canvas thiếu aria-label/role — screen reader không đọc được: {no_aria[:2]}")

    # 4. contrast chữ chính vs nền
    m = re.search(r"--text:\s*(#[0-9a-fA-F]{6})", html)
    bg = re.search(r"--bg-0:\s*(#[0-9a-fA-F]{6})", html)
    if m and bg:
        ratio = contrast(m.group(1), bg.group(1))
        if ratio < 4.5:
            fails.append(f"contrast text/bg = {ratio:.2f}:1 < 4.5 (WCAG AA)")

    if fails:
        print("❌ ACCESSIBILITY FAIL:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"✅ ACCESSIBILITY OK — {len(canvases)} canvas, viewport ✓, reduced-motion ✓, contrast ≥4.5 ✓")

if __name__ == "__main__":
    run()
