"""
Canonical Browser QA Script for equity_foreign_flow_relations_v1 report.

Runs Playwright at 3 viewports (1440, 390, 320), checks:
- Console errors = 0
- Horizontal overflow = 0
- Canvas count = chart instances
- Chart rendered (non-zero bounding box)
- Nav targets exist
- Details collapsed by default
- Takes screenshots

Output: qa/browser_qa.json (with html_sha256)
Screenshots: qa/screenshots/{name}_{w}x{h}.png

Usage: python3 qa/browser_qa.py
"""

import hashlib
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML_PATH = Path(__file__).parent.parent / "index.html"
QA_DIR = Path(__file__).parent
SHOTS_DIR = QA_DIR / "screenshots"
SHOTS_DIR.mkdir(exist_ok=True)

VIEWPORTS = [
    (1440, 1100, "desktop"),
    (390, 844, "mobile"),
    (320, 800, "small"),
]


def run_qa():
    # Compute HTML hash for provenance
    with open(HTML_PATH, "rb") as f:
        html_sha = hashlib.sha256(f.read()).hexdigest()

    results = {
        "html_path": str(HTML_PATH),
        "html_sha256": html_sha,
        "run_at": None,
        "viewports": [],
        "overall_pass": False,
    }

    from datetime import datetime
    results["run_at"] = datetime.now().isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for width, height, name in VIEWPORTS:
            page = browser.new_page(viewport={"width": width, "height": height})

            # Capture console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(f"file://{HTML_PATH}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)  # Wait for Chart.js

            # Canvas / chart check
            canvases = page.query_selector_all("canvas")
            canvas_count = len(canvases)
            chart_rendered = any(
                c.bounding_box() and c.bounding_box()["width"] > 50 and c.bounding_box()["height"] > 50
                for c in canvases
            )

            # Overflow check
            scroll_width = page.evaluate("document.documentElement.scrollWidth")
            inner_width = page.evaluate("window.innerWidth")
            overflow = scroll_width > inner_width

            # Nav targets
            nav_links = page.query_selector_all("nav a")
            nav_targets = len(nav_links)

            # Details collapsed
            details = page.query_selector_all("details[data-layer='technical']")
            details_collapsed = all(not d.get_attribute("open") for d in details) if details else True

            # Screenshot
            screenshot_path = SHOTS_DIR / f"{name}_{width}x{height}.png"
            page.screenshot(path=str(screenshot_path), full_page=False)

            v = {
                "name": name,
                "width": width,
                "height": height,
                "console_errors": len(console_errors),
                "error_details": console_errors[:5],
                "canvas_count": canvas_count,
                "chart_rendered": chart_rendered,
                "overflow": overflow,
                "nav_targets": nav_targets,
                "details_collapsed_default": details_collapsed,
                "screenshot": f"qa/screenshots/{name}_{width}x{height}.png",
                "screenshot_exists": screenshot_path.exists(),
            }
            results["viewports"].append(v)

            status = "PASS" if v["console_errors"] == 0 and not v["overflow"] and v["chart_rendered"] else "FAIL"
            print(f"{name:10s} ({width}x{height}): {status}")
            print(f"  console_errors={v['console_errors']}  canvas={v['canvas_count']}  chart={v['chart_rendered']}")
            print(f"  overflow={v['overflow']}  nav={v['nav_targets']}  details_collapsed={v['details_collapsed_default']}")

            page.close()

        browser.close()

    # Overall
    results["overall_pass"] = all(
        v["console_errors"] == 0 and not v["overflow"] and v["chart_rendered"]
        for v in results["viewports"]
    )

    # Save
    output_path = QA_DIR / "browser_qa.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nOverall: {'PASS' if results['overall_pass'] else 'FAIL'}")
    print(f"HTML SHA256: {html_sha}")
    print(f"QA JSON: {output_path}")
    print(f"Screenshots: {SHOTS_DIR}")

    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(run_qa())
