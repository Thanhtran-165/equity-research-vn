#!/usr/bin/env python3
"""Browser QA for the generated investor report."""

import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE = Path("/Users/bobo/ZCodeProject/equity-volume-breadth")
HTML = BASE / "index.html"
OUT = BASE / "qa" / "plain_language" / "browser_qa.json"
SHOTS = BASE / "screenshots"


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    results = {
        "html_sha256": hashlib.sha256(HTML.read_bytes()).hexdigest(),
        "viewports": {},
        "console_errors": [],
        "overflow_issues": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, width, height in (
            ("desktop", 1440, 1100),
            ("mobile-390", 390, 844),
            ("small-320", 320, 800),
        ):
            page = browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(HTML.as_uri(), wait_until="networkidle")
            page.wait_for_timeout(1500)

            state = page.evaluate(
                """() => {
                    const canvases = [...document.querySelectorAll('canvas')];
                    const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
                    const navTargets = [...document.querySelectorAll('#mm a[href^="#"]')]
                      .map(a => a.getAttribute('href').slice(1));
                    return {
                      canvas_count: canvases.length,
                      canvas_rendered: canvases.filter(c => c.width > 0 && c.height > 0).length,
                      canvas_details: canvases.map(c => ({id:c.id,w:c.offsetWidth,h:c.offsetHeight})),
                      scrollWidth: document.documentElement.scrollWidth,
                      innerWidth: innerWidth,
                      duplicate_ids: [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))],
                      missing_nav_targets: navTargets.filter(id => !document.getElementById(id)),
                      conclusion_present: !!document.getElementById('ketluan'),
                    };
                }"""
            )
            state["overflow"] = state["scrollWidth"] > state["innerWidth"]
            state["console_errors"] = errors
            results["viewports"][name] = state
            if errors:
                results["console_errors"].append({"viewport": name, "errors": errors})
            if state["overflow"]:
                results["overflow_issues"].append({"viewport": name})

            page.screenshot(path=str(SHOTS / f"{name}-hero.png"))
            page.screenshot(path=str(SHOTS / f"{name}-full.png"), full_page=True)
            if name == "desktop":
                page.locator("#ketluan").screenshot(path=str(SHOTS / "desktop-conclusion.png"))
                page.locator("#oos").screenshot(path=str(SHOTS / "desktop-oos.png"))
            page.close()
        browser.close()

    states = list(results["viewports"].values())
    results["gate_summary"] = {
        "charts_rendered_ok": all(s["canvas_count"] == 3 and s["canvas_rendered"] == 3 for s in states),
        "zero_console_errors": not results["console_errors"],
        "no_horizontal_overflow": not results["overflow_issues"],
        "no_duplicate_ids": all(not s["duplicate_ids"] for s in states),
        "nav_targets_resolve": all(not s["missing_nav_targets"] for s in states),
        "conclusion_present": all(s["conclusion_present"] for s in states),
    }
    results["gate_summary"]["overall_pass"] = all(results["gate_summary"].values())
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(json.dumps(results["gate_summary"], ensure_ascii=False))
    if not results["gate_summary"]["overall_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
