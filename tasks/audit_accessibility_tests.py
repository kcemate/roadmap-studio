#!/usr/bin/env python3
"""Browser accessibility gate for Roadmap Studio's major workspace surfaces."""

import json
import os
import subprocess
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

from audit_workspace_tests import APP, ROOT, seed_state


DEFAULT_AXE_PATH = Path("/tmp/roadmap-audit-tools/node_modules/axe-core/axe.min.js")
AXE_PATH = Path(os.environ.get("AXE_PATH", DEFAULT_AXE_PATH))
VIEWPORTS = ((390, 844), (1440, 1000))
MAJOR_VIEWS = ("struct", "data", "road", "exec", "rollup", "proj", "stack")


class AccessibilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AXE_PATH.is_file():
            raise RuntimeError(
                f"axe-core bundle not found at {AXE_PATH}. "
                "Set AXE_PATH to a local axe.min.js test dependency."
            )
        subprocess.run(["python3", "tasks/build.py"], cwd=ROOT, check=True, capture_output=True, text=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "browser"):
            cls.browser.close()
        if hasattr(cls, "playwright"):
            cls.playwright.stop()

    def axe_violations(self, page):
        result = page.evaluate(
            "async () => await axe.run(document, {resultTypes: ['violations']})"
        )
        return [
            {
                "id": violation["id"],
                "impact": violation["impact"],
                "help": violation["help"],
                "nodes": [
                    {"target": node["target"], "failureSummary": node.get("failureSummary", "")}
                    for node in violation["nodes"]
                ],
            }
            for violation in result["violations"]
            if violation.get("impact") in {"serious", "critical"}
        ]

    def scan(self, page, width, surface, console_errors):
        violations = self.axe_violations(page)
        overflow = page.evaluate(
            "Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)"
        )
        failures = []
        if violations:
            failures.append(f"axe violations: {json.dumps(violations, indent=2)}")
        if overflow:
            failures.append(f"page overflow: {overflow}px")
        if console_errors:
            failures.append(f"console errors: {console_errors}")
        if failures:
            self.fail(f"{width}px {surface}: " + "\n".join(failures))

    def test_major_views_drawer_review_and_drilldown(self):
        for width, height in VIEWPORTS:
            with self.subTest(width=width):
                page = self.browser.new_page(viewport={"width": width, "height": height})
                console_errors = []
                page.on(
                    "console",
                    lambda message: console_errors.append(f"console {message.type}: {message.text}")
                    if message.type in {"warning", "error"}
                    else None,
                )
                page.on("pageerror", lambda error: console_errors.append(f"pageerror: {error}"))
                page.goto(APP.as_uri())
                page.evaluate(
                    "state => localStorage.setItem('roadmapStudio.v1', state)",
                    json.dumps(seed_state()),
                )
                page.reload()
                page.add_script_tag(path=str(AXE_PATH))

                for view in MAJOR_VIEWS:
                    page.evaluate("view => setTab(view)", view)
                    self.scan(page, width, view, console_errors)

                page.evaluate("setTab('data'); openDrawer('i1')")
                self.scan(page, width, "drawer", console_errors)
                page.evaluate("closeDrawer(true)")

                page.evaluate(
                    "S.workspace.reviewOpen=true; S.workspace.reviewView='exceptions'; setTab('data'); refreshWorkspace()"
                )
                self.scan(page, width, "review", console_errors)

                page.evaluate("setTab('exec'); refreshWorkspace()")
                page.click("#execTotal")
                self.scan(page, width, "financial drilldown", console_errors)
                page.close()


if __name__ == "__main__":
    if not AXE_PATH.is_file():
        raise SystemExit(
            f"axe-core bundle not found at {AXE_PATH}. "
            "Set AXE_PATH to a local axe.min.js test dependency."
        )
    unittest.main(verbosity=2)
