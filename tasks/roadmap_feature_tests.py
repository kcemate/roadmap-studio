#!/usr/bin/env python3
import csv
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "index.html"
TRACKER = ROOT / "tasks" / "roadmap-studio-feature-tracker.csv"
ARTIFACTS = ROOT / "tasks" / "test-artifacts"
RESULTS_JSON = ROOT / "tasks" / "roadmap-studio-test-results.json"
APP_URL = APP.as_uri()

KNOWN_FIXES = {
    "STRUCT-004": {
        "Fix Status": "Fixed",
        "Retest Result": "Passed after adding data-p to pillar move/delete controls.",
        "Notes": "Initial full run found pillar move controls lacked the pillar id needed by the shared structure action handler.",
    },
    "STRUCT-005": {
        "Fix Status": "Fixed",
        "Retest Result": "Passed after adding data-p to pillar move/delete controls.",
        "Notes": "Initial full run found pillar delete controls lacked the pillar id needed by the shared structure action handler.",
    },
}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def seed_state():
    return {
        "v": 1,
        "savedAt": 1893456000000,
        "fileName": "Seed roadmap",
        "fyStart": 6,
        "structure": [
            {
                "id": "p1",
                "name": "Product Requirements",
                "workstreams": [
                    {"id": "w1", "name": "Material Savings"},
                    {"id": "w2", "name": "Transportation Optimization"},
                ],
            },
            {
                "id": "p2",
                "name": "Vertical Integration",
                "workstreams": [{"id": "w3", "name": "Corn"}],
            },
        ],
        "items": [
            {
                "id": "i1",
                "pillarId": "p1",
                "wsId": "w1",
                "name": "Foam Cup Damage",
                "start": "2026-05-18",
                "end": "2026-12-20",
                "valueType": "Savings",
                "value": 920000,
                "realizedPct": 50,
                "milestone": False,
                "status": "On Track",
                "owner": "B. Berry",
            },
            {
                "id": "i2",
                "pillarId": "p1",
                "wsId": "w2",
                "name": "Carrier Contract Risk",
                "start": "2026-09-01",
                "end": "2026-09-01",
                "valueType": "Avoidance",
                "value": 450000,
                "realizedPct": 80,
                "milestone": True,
                "status": "At Risk",
                "owner": "A. Adams",
            },
            {
                "id": "i3",
                "pillarId": "p2",
                "wsId": "w3",
                "name": "Corn Supplier Mapping",
                "start": "2026-10-01",
                "end": "2026-12-31",
                "valueType": "Savings",
                "value": 0,
                "realizedPct": "",
                "milestone": False,
                "status": "Not Started",
                "owner": "B. Berry",
            },
        ],
    }


def projection_state():
    state = seed_state()
    state["fileName"] = "Projection roadmap"
    state["items"] = [
        {
            "id": "ps1",
            "pillarId": "p1",
            "wsId": "w1",
            "name": "Linear Savings",
            "start": "2026-01-01",
            "end": "2026-01-31",
            "valueType": "Savings",
            "value": 31000,
            "realizedPct": 50,
            "milestone": False,
            "status": "On Track",
            "owner": "",
        },
        {
            "id": "ps2",
            "pillarId": "p1",
            "wsId": "w1",
            "name": "Milestone Savings",
            "start": "2026-02-15",
            "end": "2026-02-15",
            "valueType": "Savings",
            "value": 20000,
            "realizedPct": 25,
            "milestone": True,
            "status": "On Track",
            "owner": "",
        },
        {
            "id": "pa1",
            "pillarId": "p1",
            "wsId": "w2",
            "name": "Linear Avoidance",
            "start": "2026-01-16",
            "end": "2026-02-14",
            "valueType": "Avoidance",
            "value": 30000,
            "realizedPct": 100,
            "milestone": False,
            "status": "On Track",
            "owner": "",
        },
        {
            "id": "pa2",
            "pillarId": "p2",
            "wsId": "w3",
            "name": "Milestone Avoidance",
            "start": "2026-03-01",
            "end": "2026-03-01",
            "valueType": "Avoidance",
            "value": 40000,
            "realizedPct": 50,
            "milestone": True,
            "status": "On Track",
            "owner": "",
        },
        {
            "id": "bad1",
            "pillarId": "p2",
            "wsId": "w3",
            "name": "Ignored Blank Value",
            "start": "2026-04-01",
            "end": "2026-04-30",
            "valueType": "Savings",
            "value": "",
            "realizedPct": "",
            "milestone": False,
            "status": "On Track",
            "owner": "",
        },
    ]
    return state


def stacked_chart_state():
    return {
        "v": 1,
        "savedAt": 1893456000000,
        "fileName": "Stacked chart roadmap",
        "fyStart": 6,
        "structure": [
            {"id": "p1", "name": "Product Requirements", "workstreams": [{"id": "w1", "name": "Packaging"}]},
            {"id": "p2", "name": "Vertical Integration", "workstreams": [{"id": "w2", "name": "Commodities"}]},
            {"id": "p3", "name": "Network Design", "workstreams": [{"id": "w3", "name": "Freight"}]},
        ],
        "items": [
            {
                "id": "st1",
                "pillarId": "p1",
                "wsId": "w1",
                "name": "Packaging savings",
                "start": "2026-01-01",
                "end": "2026-03-31",
                "valueType": "Savings",
                "value": 600000,
                "realizedPct": "",
                "milestone": False,
                "status": "On Track",
                "owner": "",
            },
            {
                "id": "st2",
                "pillarId": "p1",
                "wsId": "w1",
                "name": "Packaging avoidance",
                "start": "2026-04-01",
                "end": "2026-06-30",
                "valueType": "Avoidance",
                "value": 400000,
                "realizedPct": "",
                "milestone": False,
                "status": "On Track",
                "owner": "",
            },
            {
                "id": "st3",
                "pillarId": "p2",
                "wsId": "w2",
                "name": "Commodity savings",
                "start": "2026-01-01",
                "end": "2026-03-31",
                "valueType": "Savings",
                "value": 300000,
                "realizedPct": "",
                "milestone": False,
                "status": "On Track",
                "owner": "",
            },
            {
                "id": "st4",
                "pillarId": "p3",
                "wsId": "w3",
                "name": "Network savings",
                "start": "2026-07-01",
                "end": "2026-09-30",
                "valueType": "Savings",
                "value": 100000,
                "realizedPct": "",
                "milestone": False,
                "status": "On Track",
                "owner": "",
            },
            {
                "id": "st5",
                "pillarId": "p3",
                "wsId": "w3",
                "name": "Network avoidance",
                "start": "2026-07-01",
                "end": "2026-09-30",
                "valueType": "Avoidance",
                "value": 100000,
                "realizedPct": "",
                "milestone": False,
                "status": "On Track",
                "owner": "",
            },
        ],
    }


def ppt_same_workstream_state():
    return {
        "v": 1,
        "savedAt": 1893456000000,
        "fileName": "Same workstream PPT",
        "fyStart": 6,
        "structure": [
            {
                "id": "p1",
                "name": "Supply Chain",
                "workstreams": [{"id": "w1", "name": "Packaging"}],
            }
        ],
        "items": [
            {
                "id": "sw1",
                "pillarId": "p1",
                "wsId": "w1",
                "name": "Future Price Renewal Playbook A",
                "start": "2030-07-01",
                "end": "2030-12-31",
                "valueType": "Savings",
                "value": 97000000,
                "realizedPct": "",
                "milestone": False,
                "status": "Not Started",
                "owner": "",
            },
            {
                "id": "sw2",
                "pillarId": "p1",
                "wsId": "w1",
                "name": "Future Price Renewal Playbook B",
                "start": "2030-07-01",
                "end": "2030-12-31",
                "valueType": "Avoidance",
                "value": 65000000,
                "realizedPct": "",
                "milestone": False,
                "status": "Not Started",
                "owner": "",
            },
        ],
    }


class Runner:
    def __init__(self):
        self.results = {}
        self.issues = []
        self.issue_seq = 1

    def record(self, ids, passed, result, issue_note=""):
        if isinstance(ids, str):
            ids = [ids]
        issue_id = ""
        if not passed:
            issue_id = f"ERR-{self.issue_seq:03d}"
            self.issue_seq += 1
            self.issues.append({"id": issue_id, "stories": ids, "note": issue_note or result})
        for story_id in ids:
            self.results[story_id] = {
                "status": "Passed" if passed else "Failed",
                "result": result,
                "issue_id": issue_id,
                "tested_at": now_iso(),
            }

    def check(self, ids, condition, passed_result, failed_result):
        self.record(ids, bool(condition), passed_result if condition else failed_result, failed_result)

    def update_tracker(self):
        with TRACKER.open(newline="") as f:
            rows = list(csv.DictReader(f))
            fields = f.seek(0) or next(csv.reader(TRACKER.open(newline="")))
        untouched = []
        for row in rows:
            res = self.results.get(row["ID"])
            if not res:
                untouched.append(row["ID"])
                continue
            row["Feature Status"] = res["status"]
            row["Latest Test Result"] = res["result"]
            row["Issue ID"] = res["issue_id"]
            row["Fix Status"] = "" if res["status"] == "Passed" else "Needs fix"
            if row["ID"] in KNOWN_FIXES:
                row.update(KNOWN_FIXES[row["ID"]])
        with TRACKER.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        RESULTS_JSON.write_text(
            json.dumps(
                {
                    "generatedAt": now_iso(),
                    "app": str(APP),
                    "tracker": str(TRACKER),
                    "results": self.results,
                    "issues": self.issues,
                    "untested": untouched,
                    "summary": {
                        "passed": sum(1 for r in self.results.values() if r["status"] == "Passed"),
                        "failed": sum(1 for r in self.results.values() if r["status"] == "Failed"),
                        "untested": len(untouched),
                    },
                },
                indent=2,
            )
        )
        return untouched


def reset_artifacts():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for child in ARTIFACTS.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    (ARTIFACTS / "downloads").mkdir()


def new_context(browser, state=None, clear=True):
    context = browser.new_context(
        accept_downloads=True,
        viewport={"width": 1440, "height": 950},
        device_scale_factor=1,
    )
    if clear:
        context.add_init_script("localStorage.clear();")
    if state:
        context.add_init_script(f"localStorage.setItem('roadmapStudio.v1', {json.dumps(json.dumps(state))});")
    page = context.new_page()
    page.goto(APP_URL, wait_until="domcontentloaded")
    return context, page


def text(page, selector):
    return page.locator(selector).text_content(timeout=5000) or ""


def maybe_text(page, selector):
    return text(page, selector) if page.locator(selector).count() else ""


def attr(page, selector, name):
    return page.locator(selector).get_attribute(name, timeout=5000)


def blur(page):
    page.keyboard.press("Tab")
    page.wait_for_timeout(80)


def wait_autosave(page):
    page.wait_for_timeout(550)


def safe_click(locator):
    locator.click(timeout=5000, force=True)


def visible_texts(page, selector):
    return [item.strip() for item in page.locator(selector).all_inner_texts() if item.strip()]


def pptx_negative_extents(path):
    issues = []
    pattern = re.compile(r'\b(?:cx|cy)="-\d+')
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            xml = zf.read(name).decode("utf-8", "ignore")
            matches = pattern.findall(xml)
            if matches:
                issues.append(f"{name}: {', '.join(matches[:4])}")
    return issues


def ppt_text_boxes(slide_xml, needle):
    ns = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    }
    root = ET.fromstring(slide_xml)
    boxes = []
    for shape in root.findall(".//p:sp", ns):
        text_value = "".join(t.text or "" for t in shape.findall(".//a:t", ns))
        if needle not in text_value:
            continue
        off = shape.find(".//a:xfrm/a:off", ns)
        ext = shape.find(".//a:xfrm/a:ext", ns)
        if off is None or ext is None:
            continue
        boxes.append(
            {
                "text": text_value,
                "x": int(off.attrib["x"]) / 914400,
                "y": int(off.attrib["y"]) / 914400,
                "w": int(ext.attrib["cx"]) / 914400,
                "h": int(ext.attrib["cy"]) / 914400,
            }
        )
    return boxes


def run_tests():
    reset_artifacts()
    runner = Runner()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Start screen and static privacy/a11y checks.
        ctx, page = new_context(browser)
        runner.check(
            "START-001",
            page.locator("#scr-start").is_visible()
            and not page.locator("#btnResume").is_visible()
            and page.locator("#btnBlank").is_visible()
            and "Everything stays in this browser" in text(page, ".privacy"),
            "No saved data shows the start screen, hides Resume, and shows the local-only privacy note.",
            "Cold start did not show the expected start state.",
        )
        html = APP.read_text()
        runner.check(
            "PRIVACY-001",
            "Everything stays in this browser. Nothing is uploaded anywhere." in html,
            "Local-only privacy statement is present.",
            "Local-only privacy statement was missing.",
        )
        runner.check(
            "SECURITY-001",
            "cdnjs.cloudflare.com" not in html
            and "ExcelJS" not in html
            and "https://" not in html
            and page.locator("script[src='vendor/pptxgen.bundle.js']").count() == 1
            and page.evaluate("typeof PptxGenJS") == "function"
            and page.locator("#btnImport").count() == 0
            and page.locator("#fileIn").count() == 0
            and page.locator("#exportBtn").count() == 0,
            "External runtime URLs and Excel controls are absent; the local PowerPoint bundle loads.",
            "External runtime URL, missing local PowerPoint bundle, or Excel controls were detected.",
        )
        csp = page.locator("meta[http-equiv='Content-Security-Policy']").get_attribute("content") or ""
        runner.check(
            "SECURITY-002",
            "connect-src 'none'" in csp
            and "default-src 'none'" in csp
            and "script-src 'self' 'unsafe-inline'" in csp
            and "form-action 'none'" in csp
            and "object-src 'none'" in csp
            and "https:" not in csp,
            "Meta CSP blocks connection APIs and external resource origins for the single-file app.",
            "Expected no-egress CSP was missing or allowed external origins.",
        )
        runner.check(
            "ACCESS-001",
            all(token in html for token in [":focus-visible", 'role="tablist"', 'aria-label="Undo"', 'aria-label="Roadmap"', 'aria-label="Savings or avoidance dollar value"']),
            "Basic labels, roles, and visible focus styling are present.",
            "Expected accessibility labels or focus styling were missing.",
        )
        runner.check(
            "A11Y-002",
            "@media (prefers-reduced-motion:reduce)" in html,
            "Reduced-motion CSS guard is present.",
            "Reduced-motion CSS guard was missing.",
        )
        page.click("#btnBlank")
        runner.check(
            ["START-004", "NAV-001", "STRUCT-001"],
            page.locator("#studio").is_visible()
            and page.locator("#segStruct.on").is_visible()
            and visible_texts(page, ".seg button") == ["Structure", "Initiatives", "Roadmap", "Projected Savings", "Stacked Bar Chart"]
            and "1 pillar" in text(page, "#structMeta")
            and "1 workstream" in text(page, "#structMeta"),
            "Blank start creates one pillar/workstream and opens Structure with tabs ordered Structure, Initiatives, Roadmap, Projected Savings, Stacked Bar Chart.",
            "Blank start or tab order did not match expected behavior.",
        )
        page.locator(".pillar-name").first.fill("Autosaved Outline")
        blur(page)
        wait_autosave(page)
        saved_name = page.evaluate("JSON.parse(localStorage.getItem('roadmapStudio.v1')).structure[0].name")
        runner.check(
            "PERSIST-001",
            saved_name == "Autosaved Outline",
            "Autosave writes changed roadmap state to localStorage after edits.",
            "Autosave did not persist the changed outline to localStorage.",
        )
        ctx.close()

        # Autosave restore and brand/start/resume behavior.
        ctx, page = new_context(browser, seed_state())
        runner.check(
            "START-002",
            page.locator("#studio").is_visible()
            and page.locator("#toast.on").is_visible()
            and "Picked up where you left off" in text(page, "#toast"),
            "Saved state auto-restores into studio and shows restore toast.",
            "Saved state did not auto-restore correctly.",
        )
        page.click("#freshBtn")
        runner.check(
            "PERSIST-002",
            page.locator("#scr-start").is_visible() and page.locator("#btnResume").is_visible(),
            "Start fresh from restore toast returns to start while keeping saved data available.",
            "Start fresh from restore toast did not return to the start screen as expected.",
        )
        ctx.close()

        ctx, page = new_context(browser, seed_state())
        page.click("#brandHome")
        runner.check(
            "START-005",
            page.locator("#scr-start").is_visible()
            and page.locator("#btnResume").is_visible(),
            "Brand returns to start screen while leaving the saved session resumable.",
            "Brand control did not return to start screen with saved session available.",
        )
        page.click("#btnResume")
        runner.check(
            "START-003",
            page.locator("#studio").is_visible() and page.locator(".pillar-name").first.input_value() == "Product Requirements",
            "Resume last session reloads saved roadmap data.",
            "Resume last session did not restore saved roadmap data.",
        )
        ctx.close()

        # Structure, undo/redo, and keyboard outline behavior.
        ctx, page = new_context(browser)
        page.click("#btnBlank")
        first_pillar = page.locator(".pillar-name").first
        first_pillar.fill("Operations")
        blur(page)
        undo_enabled = page.locator("#undoBtn").is_enabled()
        page.click("#undoBtn")
        undo_ok = first_pillar.input_value() == "New pillar"
        page.click("#redoBtn")
        redo_ok = first_pillar.input_value() == "Operations"
        runner.check(
            "UNDO-001",
            undo_enabled and undo_ok and redo_ok,
            "Toolbar undo and redo restore and reapply a pillar rename.",
            "Toolbar undo/redo failed on a pillar rename.",
        )
        first_pillar.fill("Finance")
        blur(page)
        page.keyboard.press("Control+Z")
        keyboard_undo = first_pillar.input_value() == "Operations"
        page.keyboard.press("Shift+Control+Z")
        keyboard_redo = first_pillar.input_value() == "Finance"
        runner.check(
            "UNDO-002",
            keyboard_undo and keyboard_redo,
            "Keyboard undo and redo work on editable structure changes.",
            "Keyboard undo/redo did not restore the expected values.",
        )
        runner.check(
            "STRUCT-002",
            first_pillar.input_value() == "Finance",
            "Pillar name edits persist after change events.",
            "Pillar rename did not persist.",
        )
        page.click("#addPillar")
        added_pillar_focused = page.locator(".pillar-name").nth(1).evaluate("el => document.activeElement === el")
        page.locator(".pillar-name").nth(1).fill("Supply")
        blur(page)
        runner.check(
            "STRUCT-003",
            page.locator(".pillar").count() == 2 and added_pillar_focused,
            "Add pillar appends a pillar and focuses the new name input.",
            "Add pillar did not append/focus as expected.",
        )
        safe_click(page.locator(".pillar").nth(1).locator("[data-act='pup']"))
        moved_up = page.locator(".pillar-name").first.input_value() == "Supply"
        safe_click(page.locator(".pillar").first.locator("[data-act='pdown']"))
        moved_down = page.locator(".pillar-name").nth(1).input_value() == "Supply"
        runner.check(
            "STRUCT-004",
            moved_up and moved_down,
            "Pillar up/down controls reorder adjacent pillars.",
            "Pillar reorder controls failed.",
        )
        safe_click(page.locator(".pillar").nth(1).locator("[data-act='pdel']"))
        runner.check(
            "STRUCT-005",
            page.locator(".pillar").count() == 1 and page.locator(".pillar-name").first.input_value() == "Finance",
            "Deleting a pillar removes it and leaves a valid remaining outline.",
            "Pillar delete did not leave the expected outline.",
        )
        ws = page.locator(".ws-name").first
        ws.fill("Packaging")
        blur(page)
        runner.check(
            "STRUCT-006",
            ws.input_value() == "Packaging",
            "Workstream name edits persist after change events.",
            "Workstream rename did not persist.",
        )
        page.click(".add-ws")
        add_ws_ok = page.locator(".ws-name").count() == 2 and page.locator(".ws-name").nth(1).evaluate("el => document.activeElement === el")
        page.locator(".ws-name").nth(1).fill("Transportation")
        blur(page)
        runner.check(
            "STRUCT-007",
            add_ws_ok,
            "Add workstream appends a focused blank workstream.",
            "Add workstream button did not append/focus correctly.",
        )
        page.locator(".ws-name").nth(1).focus()
        page.keyboard.press("Enter")
        runner.check(
            "STRUCT-008",
            page.locator(".ws-name").count() == 3 and page.locator(".ws-name").nth(2).evaluate("el => document.activeElement === el"),
            "Enter in a workstream adds a new workstream below and focuses it.",
            "Enter did not add/focus the next workstream.",
        )
        page.keyboard.press("Backspace")
        runner.check(
            "STRUCT-009",
            page.locator(".ws-name").count() == 2,
            "Backspace on an empty workstream removes it when another workstream remains.",
            "Backspace did not remove the empty workstream.",
        )
        safe_click(page.locator(".ws-row").nth(1).locator("[data-act='wup']"))
        w_moved_up = page.locator(".ws-name").first.input_value() == "Transportation"
        safe_click(page.locator(".ws-row").first.locator("[data-act='wdown']"))
        w_moved_down = page.locator(".ws-name").nth(1).input_value() == "Transportation"
        runner.check(
            "STRUCT-010",
            w_moved_up and w_moved_down,
            "Workstream up/down controls reorder adjacent workstreams.",
            "Workstream reorder controls failed.",
        )
        safe_click(page.locator(".ws-row").nth(1).locator("[data-act='wdel']"))
        runner.check(
            "STRUCT-011",
            page.locator(".ws-name").count() == 1 and page.locator(".ws-name").first.input_value() == "Packaging",
            "Deleting a workstream removes it and leaves a valid fallback lane when needed.",
            "Workstream delete did not leave the expected lane.",
        )
        ctx.close()

        # Initiatives grid behavior.
        ctx, page = new_context(browser)
        page.click("#btnBlank")
        page.click("#segData")
        runner.check(
            "INIT-001",
            "No initiatives yet" in text(page, "#gridBody") and page.locator("#addRow").is_visible(),
            "Initiatives tab shows empty state and Add initiative.",
            "Initiatives empty state was missing.",
        )
        page.click("#addRow")
        runner.check(
            "INIT-002",
            page.locator("tbody tr").count() == 1
            and page.locator("input[data-f='name']").input_value() == "New initiative"
            and page.locator("select[data-f='valueType']").input_value() == "Savings"
            and page.locator("select[data-f='status']").input_value() == "Not Started"
            and page.locator("input[data-f='realizedPct']").input_value() == "",
            "Add initiative creates the expected default row and values.",
            "Add initiative defaults were wrong.",
        )
        page.locator("input[data-f='name']").fill("Freight Audit")
        blur(page)
        runner.check("INIT-003", page.locator("input[data-f='name']").input_value() == "Freight Audit", "Initiative name edit persisted.", "Initiative name edit failed.")
        page.click("#segStruct")
        page.click("#addPillar")
        page.locator(".pillar-name").nth(1).fill("Logistics")
        blur(page)
        page.click("#segData")
        page.locator("select[data-f='pillarId']").select_option(index=1)
        runner.check(
            "INIT-004",
            page.locator("select[data-f='pillarId']").input_value() != "" and page.locator("select[data-f='wsId'] option").count() == 1,
            "Changing pillar reassigns the initiative to the first workstream in that pillar.",
            "Changing pillar did not reset workstream options as expected.",
        )
        page.click("#segStruct")
        page.locator(".add-ws").nth(1).click()
        page.locator(".ws-name").last.fill("Lane B")
        blur(page)
        page.click("#segData")
        ws_options_before = page.locator("select[data-f='wsId'] option").count()
        page.locator("select[data-f='wsId']").select_option(index=1)
        runner.check(
            "INIT-005",
            ws_options_before >= 2 and page.locator("select[data-f='wsId']").input_value() != "",
            "Changing workstream updates the selected workstream.",
            "Changing workstream failed.",
        )
        page.locator("input[data-f='start']").fill("2026-04-15")
        blur(page)
        page.locator("input[data-f='end']").fill("2026-04-01")
        blur(page)
        runner.check(
            "INIT-006",
            page.locator("input[data-f='start']").input_value() == "2026-04-01"
            and page.locator("input[data-f='end']").input_value() == "2026-04-01",
            "Date edits clamp start/end to prevent negative duration.",
            "Date clamping failed when end was set before start.",
        )
        page.locator("input[data-f='milestone']").check()
        runner.check(
            "INIT-007",
            page.locator("input[data-f='end']").is_disabled(),
            "Milestone toggle sets a one-day item and disables End.",
            "Milestone toggle did not disable End.",
        )
        page.locator("select[data-f='status']").select_option("At Risk")
        runner.check("INIT-008", page.locator("select[data-f='status']").input_value() == "At Risk", "Status selection persisted.", "Status selection failed.")
        page.locator("select[data-f='valueType']").select_option("Avoidance")
        runner.check("INIT-009", page.locator("select[data-f='valueType']").input_value() == "Avoidance", "Savings/Avoidance selection persisted.", "Savings/Avoidance selection failed.")
        page.locator("input[data-f='value']").fill("$250,000")
        blur(page)
        runner.check("INIT-010", page.locator("input[data-f='value']").input_value() == "$250,000", "Dollar value parses and formats as USD.", "Dollar value did not format as expected.")
        page.locator("input[data-f='realizedPct']").fill("0.5")
        blur(page)
        runner.check(
            "INIT-014",
            page.locator("input[data-f='realizedPct']").input_value() == "50%"
            and page.evaluate("S.items[0].realizedPct") == 50,
            "Realized percentage accepts fractional entry, stores percent points, and formats with a percent sign.",
            "Realized percentage did not parse or format as expected.",
        )
        page.locator("input[data-f='owner']").fill("Alex")
        blur(page)
        runner.check("INIT-011", page.locator("#ownerList option[value='Alex']").count() == 1, "Owner entry refreshes datalist suggestions.", "Owner datalist did not refresh.")
        page.click("#addRow")
        page.locator("tbody tr").nth(1).locator("input[data-f='name']").fill("Second Initiative")
        blur(page)
        safe_click(page.locator("tbody tr").nth(1).locator("[data-act='up']"))
        moved_row = page.locator("tbody tr").first.locator("input[data-f='name']").input_value() == "Second Initiative"
        safe_click(page.locator("tbody tr").first.locator("[data-act='del']"))
        deleted_row = page.locator("tbody tr").count() == 1
        runner.check("INIT-012", moved_row, "Initiative row up/down control reorders rows.", "Initiative row move failed.")
        runner.check("INIT-013", deleted_row, "Initiative row delete removes the row.", "Initiative row delete failed.")
        ctx.close()

        # Roadmap rendering, totals, tooltip, drag, resize, and status visuals.
        ctx, page = new_context(browser, seed_state())
        page.click("#segRoad")
        page.wait_for_selector("#tlSvg")
        financial_layout_grouped = page.evaluate("""() =>
          document.querySelector('#savingsTotal')?.closest('.impact-stack')?.dataset.impact === 'savings'
          && document.querySelector('#realizedSavingsTotal')?.closest('.impact-stack')?.dataset.impact === 'savings'
          && document.querySelector('#avoidanceTotal')?.closest('.impact-stack')?.dataset.impact === 'avoidance'
          && document.querySelector('#realizedAvoidanceTotal')?.closest('.impact-stack')?.dataset.impact === 'avoidance'
          && getComputedStyle(document.querySelector('.impact-stack')).display === 'grid'
        """)
        runner.check(
            ["ROAD-002", "ROAD-003", "ROAD-004", "ROAD-005", "ROAD-012", "ROAD-013", "ROAD-014"],
            "3 initiatives" in text(page, "#roadMeta")
            and "3 dated" in text(page, "#roadMeta")
            and text(page, "#realizedSavingsTotal") == "$460K"
            and text(page, "#savingsTotal") == "$920K"
            and text(page, "#realizedAvoidanceTotal") == "$360K"
            and text(page, "#avoidanceTotal") == "$450K"
            and financial_layout_grouped
            and "Foam Cup Damage" in text(page, "#tlSvg")
            and "$920K" in text(page, "#tlSvg")
            and "Savings $920K · Avoidance $450K · Realized $820K" in text(page, "#tlSvg")
            and "TODAY" in text(page, "#tlSvg"),
            "Roadmap renders counts, grouped realized financial totals, per-pillar totals, fiscal/quarter layout, today marker, lanes, item labels, and money labels.",
            "Roadmap rendering, metadata, grouped realized financial totals, per-pillar totals, totals, or money labels were wrong.",
        )
        not_started_fill = page.locator(".bar-grab[data-id='i3'][data-kind='move']").get_attribute("fill")
        runner.check(
            "ROAD-011",
            not_started_fill == "#1d1d1f" and "Not Started" in text(page, ".legend"),
            "Not Started roadmap items render black and the legend includes Not Started.",
            f"Not Started roadmap styling was wrong; observed fill {not_started_fill}.",
        )
        page.locator("[data-id='i1']").first.hover()
        runner.check(
            "ROAD-006",
            page.locator("#tip").is_visible()
            and "Foam Cup Damage" in text(page, "#tip")
            and "$920,000" in text(page, "#tip")
            and "B. Berry" in text(page, "#tip"),
            "Roadmap tooltip shows item metadata, full money, status, and owner.",
            "Roadmap tooltip did not show expected metadata.",
        )
        before_collapse_h = float(page.locator("#tlSvg").get_attribute("height"))
        page.locator(".pillar-toggle[data-pillar='p1']").click(force=True)
        wait_autosave(page)
        collapsed_text = text(page, "#tlSvg")
        collapsed_h = float(page.locator("#tlSvg").get_attribute("height"))
        collapsed_saved = page.evaluate("JSON.parse(localStorage.getItem('roadmapStudio.v1')).collapsedPillars.p1 === true")
        collapsed_ok = (
            page.locator(".pillar-toggle[data-pillar='p1']").get_attribute("data-collapsed") == "true"
            and "PRODUCT REQUIREMENTS" in collapsed_text
            and "Foam Cup Damage" not in collapsed_text
            and "Savings $920K · Avoidance $450K · Realized $820K" not in collapsed_text
            and collapsed_h < before_collapse_h
            and collapsed_saved
        )
        page.locator(".pillar-toggle[data-pillar='p1']").click(force=True)
        expanded_text = text(page, "#tlSvg")
        expanded_ok = (
            page.locator(".pillar-toggle[data-pillar='p1']").get_attribute("data-collapsed") == "false"
            and "Foam Cup Damage" in expanded_text
            and "Savings $920K · Avoidance $450K · Realized $820K" in expanded_text
        )
        runner.check(
            "ROAD-010",
            collapsed_ok and expanded_ok,
            "Roadmap pillar bands collapse, persist collapsed state, and expand back to show hidden lanes.",
            "Roadmap pillar collapse/expand behavior failed.",
        )
        page.locator("#tlSvg").evaluate("el => el.getBoundingClientRect().width")
        before_start = page.evaluate("S.items.find(i => i.id === 'i1').start.toISOString().slice(0,10)")
        box = page.locator(".bar-grab[data-id='i1'][data-kind='move']").bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            page.mouse.move(box["x"] + box["width"] / 2 + 70, box["y"] + box["height"] / 2)
            page.mouse.up()
        after_start = page.evaluate("S.items.find(i => i.id === 'i1').start.toISOString().slice(0,10)")
        runner.check(
            "ROAD-007",
            bool(box) and before_start != after_start,
            "Dragging a roadmap item moves its dates.",
            "Dragging a roadmap item did not change its start date.",
        )
        before_end = page.evaluate("S.items.find(i => i.id === 'i1').end.toISOString().slice(0,10)")
        edge = page.locator(".edge[data-id='i1'][data-kind='end']").bounding_box()
        if edge:
            page.mouse.move(edge["x"] + edge["width"] / 2, edge["y"] + edge["height"] / 2)
            page.mouse.down()
            page.mouse.move(edge["x"] + edge["width"] / 2 + 70, edge["y"] + edge["height"] / 2)
            page.mouse.up()
        after_end = page.evaluate("S.items.find(i => i.id === 'i1').end.toISOString().slice(0,10)")
        runner.check(
            "ROAD-008",
            bool(edge) and before_end != after_end,
            "Dragging an end edge changes the item end date.",
            "Dragging an end edge did not change the item end date.",
        )
        before_width = page.locator("#tlSvg").get_attribute("width")
        page.set_viewport_size({"width": 900, "height": 800})
        page.wait_for_timeout(200)
        after_width = page.locator("#tlSvg").get_attribute("width")
        runner.check(
            "ROAD-009",
            before_width != after_width,
            "Roadmap rerenders with different SVG width after viewport resize.",
            "Roadmap SVG width did not change after viewport resize.",
        )
        page.evaluate("S.structure=[]; renderTimeline();")
        runner.check(
            "ROAD-001",
            "Add a pillar in the Structure tab to begin." in text(page, "#tlBox"),
            "Empty structure timeline fallback message renders.",
            "Empty structure fallback message did not render.",
        )
        ctx.close()

        ctx, page = new_context(browser, seed_state())
        page.click("#segRoad")
        page.evaluate("""() => {
          S.items = [
            {id:'r1', pillarId:'p1', wsId:'w1', name:'Sourcing A', start:utc(2026,0,1), end:utc(2026,2,31), valueType:'Savings', value:97000000, realizedPct:50, milestone:false, status:'On Track', owner:''},
            {id:'r2', pillarId:'p1', wsId:'w1', name:'Sourcing B', start:utc(2026,3,1), end:utc(2026,5,30), valueType:'Savings', value:65000000, realizedPct:25, milestone:false, status:'On Track', owner:''},
            {id:'r3', pillarId:'p1', wsId:'w2', name:'Avoidance C', start:utc(2026,6,1), end:utc(2026,8,30), valueType:'Avoidance', value:100000000, realizedPct:100, milestone:false, status:'On Track', owner:''}
          ];
          renderAll();
        }""")
        runner.check(
            ["ROAD-012", "ROAD-013"],
            text(page, "#realizedSavingsTotal") == "$64.8M"
            and text(page, "#savingsTotal") == "$162M"
            and text(page, "#realizedAvoidanceTotal") == "$100M"
            and text(page, "#avoidanceTotal") == "$100M",
            "Realized financial totals sum their own value types precisely and ignore the other value type.",
            "Realized financial total multi-row calculation or precision was wrong.",
        )
        ctx.close()

        # Fiscal year selector.
        ctx, page = new_context(browser, seed_state())
        page.click("#segRoad")
        before_fy = text(page, "#tlSvg")
        page.select_option("#fySelect", "0")
        after_fy = text(page, "#tlSvg")
        runner.check(
            "FY-001",
            before_fy != after_fy and page.locator("#fySelect").input_value() == "0",
            "Fiscal year selector updates the selected month and rerenders quarter/FY labels.",
            "Fiscal year selector did not change the timeline labels.",
        )
        ctx.close()

        # Projected savings tab and calculations.
        ctx, page = new_context(browser, projection_state())
        tabs = visible_texts(page, ".seg button")
        has_projection_tab = page.locator("#segProj").count() == 1
        if has_projection_tab:
            page.click("#segProj")
        projection_visible = has_projection_tab and page.locator("#projStage").is_visible()
        default_projection_date = page.locator("#projectionEndDate").input_value() if page.locator("#projectionEndDate").count() else ""
        default_savings = maybe_text(page, "#projSavings")
        default_avoidance = maybe_text(page, "#projAvoidance")
        default_combined = maybe_text(page, "#projCombined")
        runner.check(
            "PROJ-001",
            tabs == ["Structure", "Initiatives", "Roadmap", "Projected Savings", "Stacked Bar Chart"]
            and projection_visible
            and page.locator("#segProj.on").count() == 1
            and not page.locator("#roadStage").is_visible()
            and not page.locator("#gridStage").is_visible(),
            "Projected Savings tab renders immediately after Roadmap and displays only the projection stage.",
            "Projected Savings tab was missing, out of order, or did not display the projection stage.",
        )
        if page.locator("#projectionEndDate").count():
            page.locator("#projectionEndDate").fill("2026-02-15")
            page.locator("#projectionEndDate").dispatch_event("change")
        selected_projection_date = page.locator("#projectionEndDate").input_value() if page.locator("#projectionEndDate").count() else ""
        selected_projection_savings = maybe_text(page, "#projSavings")
        if page.locator("#projectionEndDate").count():
            page.locator("#projectionEndDate").fill("2025-12-15")
            page.locator("#projectionEndDate").dispatch_event("change")
        before_all_projection_ok = (
            page.locator("#projectionSvg").count() == 1
            and maybe_text(page, "#projSavings") == "$0"
            and maybe_text(page, "#projAvoidance") == "$0"
            and maybe_text(page, "#projCombined") == "$0"
        )
        runner.check(
            "PROJ-002",
            default_projection_date == "2026-03-01"
            and selected_projection_date == "2026-02-15"
            and selected_projection_savings == "$51K"
            and before_all_projection_ok,
            "Projection end date defaults to the latest valid initiative date, can be changed by the user, and still renders zero values before all initiatives.",
            "Projection end date did not default or rerender correctly.",
        )
        runner.check(
            "PROJ-003",
            default_savings == "$51K"
            and page.locator("#projectionSvg [data-series='savings']").count() == 1,
            "Savings-only projection sums only Savings initiatives.",
            "Savings-only projection included wrong values or did not render its trajectory.",
        )
        runner.check(
            "PROJ-004",
            default_avoidance == "$70K"
            and default_combined == "$121K"
            and page.locator("#projectionSvg [data-series='combined']").count() == 1,
            "Savings + Avoidance projection includes both Savings and Avoidance initiatives.",
            "Combined projection did not include the expected savings and avoidance values.",
        )
        if page.locator("#projectionEndDate").count():
            page.locator("#projectionEndDate").fill("2026-02-14")
            page.locator("#projectionEndDate").dispatch_event("change")
        savings_before_milestone = maybe_text(page, "#projSavings")
        if page.locator("#projectionEndDate").count():
            page.locator("#projectionEndDate").fill("2026-02-15")
            page.locator("#projectionEndDate").dispatch_event("change")
        savings_on_milestone = maybe_text(page, "#projSavings")
        runner.check(
            "PROJ-005",
            savings_before_milestone == "$31K" and savings_on_milestone == "$51K",
            "Milestone values contribute their full value on the milestone date.",
            "Milestone values did not accrue on the expected date.",
        )
        if page.locator("#projectionEndDate").count():
            page.locator("#projectionEndDate").fill("2026-01-16")
            page.locator("#projectionEndDate").dispatch_event("change")
        runner.check(
            "PROJ-006",
            maybe_text(page, "#projSavings") == "$15.5K"
            and maybe_text(page, "#projAvoidance") == "$0"
            and maybe_text(page, "#projCombined") == "$15.5K",
            "Ranged values accrue linearly over the initiative duration.",
            "Ranged values did not accrue linearly at the midpoint date.",
        )
        ctx.close()

        ctx, page = new_context(browser)
        page.click("#btnBlank")
        if page.locator("#segProj").count():
            page.click("#segProj")
        runner.check(
            "PROJ-007",
            "No dated financial initiatives" in maybe_text(page, "#projectionEmpty")
            and maybe_text(page, "#projSavings") == "$0"
            and maybe_text(page, "#projAvoidance") == "$0"
            and maybe_text(page, "#projCombined") == "$0",
            "Projection tab shows a helpful empty state and zero summaries when no dated financial initiatives exist.",
            "Projection empty state or zero summaries were missing.",
        )
        ctx.close()

        ctx, page = new_context(browser, projection_state())
        page.click("#segProj")
        headline_ok = (
            maybe_text(page, "#projectionHeadline") == "$121K projected by Mar 1, 2026"
            and "$51K Savings" in maybe_text(page, "#projectionSubhead")
            and "$70K Avoidance" in maybe_text(page, "#projectionSubhead")
        )
        runner.check(
            "PROJ-008",
            headline_ok,
            "Projection headline leads with the selected-date combined total and Savings/Avoidance subhead.",
            "Projection executive headline or subhead was missing or incorrect.",
        )
        if page.locator("#projectionTarget").count():
            page.locator("#projectionTarget").fill("$100,000")
            page.locator("#projectionTarget").dispatch_event("change")
        target_ok = (
            page.locator("#projectionTargetLine").count() == 1
            and page.locator("#projectionTarget").input_value() == "$100,000"
            and "Above target by $21K" in maybe_text(page, "#projectionTargetStatus")
        )
        runner.check(
            "PROJ-009",
            target_ok,
            "Projection target input renders a target line and above/below target status.",
            "Projection target input, target line, or target status failed.",
        )
        realized_default = (
            page.locator("#projectionRealizedToggle").count() == 1
            and page.locator("#projectionRealizedToggle").is_checked()
            and page.locator("#projectionSvg [data-series='realized']").count() == 1
            and maybe_text(page, "#projectionRealizedValue") == "$70.5K"
        )
        if page.locator("#projectionRealizedToggle").count():
            page.locator("#projectionRealizedToggle").uncheck()
        realized_removed = page.locator("#projectionSvg [data-series='realized']").count() == 0
        runner.check(
            "PROJ-010",
            realized_default and realized_removed,
            "Projection realized toggle renders and hides the realized trajectory.",
            "Projection realized overlay toggle did not behave as expected.",
        )
        drivers = visible_texts(page, "#projectionDrivers .driver-row")
        runner.check(
            "PROJ-011",
            len(drivers) >= 3
            and "Milestone Avoidance" in drivers[0]
            and "$40K" in drivers[0]
            and "Linear Savings" in " ".join(drivers),
            "Projection top drivers rank the leading initiatives by selected-date contribution.",
            f"Projection top drivers were missing or wrong: {drivers}",
        )
        default_inspect = maybe_text(page, "#projectionInspect")
        if page.locator("#projectionSvg").count():
            page.evaluate(
                """() => {
                    const svg = document.querySelector('#projectionSvg');
                    const r = svg.getBoundingClientRect();
                    svg.dispatchEvent(new MouseEvent('mousemove', {
                        clientX: r.left + 1,
                        clientY: r.top + r.height / 2,
                        bubbles: true
                    }));
                }"""
            )
        hover_inspect = maybe_text(page, "#projectionInspect")
        runner.check(
            "PROJ-012",
            "Mar 1, 2026" in default_inspect
            and "Jan 1, 2026" in hover_inspect
            and "$0" in hover_inspect
            and "active" in hover_inspect,
            "Projection chart hover updates the date-level inspection readout.",
            "Projection chart inspection did not update on hover.",
        )
        runner.check(
            "PROJ-013",
            page.locator("#projectionSvg [data-series='avoidance-band']").count() == 1
            and "Avoidance lift" in maybe_text(page, ".projection-legend"),
            "Projection chart renders a soft Avoidance lift band between Savings-only and combined trajectories.",
            "Projection chart did not render the Avoidance lift band or legend label.",
        )
        ctx.close()

        # Stacked bar chart tab and pillar concentration calculations.
        ctx, page = new_context(browser, stacked_chart_state())
        tabs = visible_texts(page, ".seg button")
        has_stack_tab = page.locator("#segStack").count() == 1
        if has_stack_tab:
            page.click("#segStack")
        stack_visible = has_stack_tab and page.locator("#stackStage").is_visible()
        stack_stage_text = maybe_text(page, "#stackStage")
        runner.check(
            "STACK-001",
            tabs == ["Structure", "Initiatives", "Roadmap", "Projected Savings", "Stacked Bar Chart"]
            and stack_visible
            and page.locator("#segStack.on").count() == 1
            and not page.locator("#projStage").is_visible()
            and not page.locator("#roadStage").is_visible(),
            "Stacked Bar Chart tab renders after Projected Savings and displays only the stacked chart stage.",
            "Stacked Bar Chart tab was missing, out of order, or did not display its stage.",
        )
        runner.check(
            "STACK-002",
            maybe_text(page, "#stackSavingsTotal") == "$1M"
            and page.locator("#stackSavingsSvg [data-series='savings'][data-pillar='p1']").count() == 1
            and page.locator("#stackSavingsSvg [data-series='savings'][data-pillar='p2']").count() == 1
            and page.locator("#stackSavingsSvg [data-series='savings'][data-pillar='p3']").count() == 1
            and "Product Requirements" in stack_stage_text
            and "$600K" in stack_stage_text
            and "60%" in stack_stage_text
            and "$300K" in stack_stage_text
            and "30%" in stack_stage_text
            and "$100K" in stack_stage_text
            and "10%" in stack_stage_text,
            "Savings-only stacked bar calculates each pillar share of total Savings.",
            "Savings-only stacked bar totals, segments, or percentages were wrong.",
        )
        runner.check(
            "STACK-003",
            maybe_text(page, "#stackCombinedTotal") == "$1.5M"
            and page.locator("#stackCombinedSvg [data-series='combined'][data-pillar='p1']").count() == 1
            and page.locator("#stackCombinedSvg [data-series='combined'][data-pillar='p2']").count() == 1
            and page.locator("#stackCombinedSvg [data-series='combined'][data-pillar='p3']").count() == 1
            and "$1M" in stack_stage_text
            and "66.7%" in stack_stage_text
            and "20%" in stack_stage_text
            and "13.3%" in stack_stage_text,
            "Savings + Avoidance stacked bar calculates each pillar share of total combined impact.",
            "Savings + Avoidance stacked bar totals, segments, or percentages were wrong.",
        )
        ctx.close()

        ctx, page = new_context(browser)
        page.click("#btnBlank")
        if page.locator("#segStack").count():
            page.click("#segStack")
        runner.check(
            "STACK-004",
            "No financial values" in maybe_text(page, "#stackEmpty"),
            "Stacked bar tab shows a useful empty state when there are no positive financial values.",
            "Stacked bar empty state was missing.",
        )
        ctx.close()

        # Project JSON save/open and invalid project.
        ctx, page = new_context(browser, seed_state())
        with page.expect_download() as dl_info:
            page.click("#saveBtn")
        save_download = dl_info.value
        save_path = ARTIFACTS / "downloads" / save_download.suggested_filename
        save_download.save_as(save_path)
        saved = json.loads(save_path.read_text())
        runner.check(
            "PROJECT-001",
            save_path.exists() and saved["fileName"] == "Seed roadmap" and len(saved["items"]) == 3,
            "Save downloads a JSON project file with serialized roadmap state.",
            "Save project JSON was missing or malformed.",
        )
        ctx.close()

        ctx, page = new_context(browser)
        page.set_input_files("#projIn", str(save_path))
        runner.check(
            "PROJECT-002",
            page.locator("#studio").is_visible() and page.locator(".pillar-name").first.input_value() == "Product Requirements",
            "Opening a valid project JSON restores the roadmap.",
            "Opening valid project JSON failed.",
        )
        ctx.close()

        invalid_path = ARTIFACTS / "invalid-project.json"
        invalid_path.write_text('{"structure":[]}')
        ctx, page = new_context(browser)
        page.set_input_files("#projIn", str(invalid_path))
        runner.check(
            "PROJECT-003",
            "valid Roadmap Studio project file" in text(page, "#err"),
            "Invalid project JSON is rejected with a visible error.",
            "Invalid project JSON did not show the expected error.",
        )
        ctx.close()

        # PNG export.
        ctx, page = new_context(browser)
        page.click("#btnBlank")
        dialog_seen = {"value": False, "message": ""}

        def on_dialog(dialog):
            dialog_seen["value"] = True
            dialog_seen["message"] = dialog.message
            dialog.accept()

        page.on("dialog", on_dialog)
        page.click("#pngBtn")
        page.wait_for_timeout(200)
        runner.check(
            "EXPORT-003",
            dialog_seen["value"] and "Open the Roadmap tab first" in dialog_seen["message"],
            "PNG outside Roadmap shows the expected alert.",
            "PNG outside Roadmap did not show expected alert.",
        )
        ctx.close()

        ctx, page = new_context(browser, seed_state())
        page.click("#segRoad")
        page.wait_for_selector("#tlSvg")
        with page.expect_download() as dl_info:
            page.click("#pngBtn")
        png_download = dl_info.value
        png_path = ARTIFACTS / "downloads" / png_download.suggested_filename
        png_download.save_as(png_path)
        runner.check(
            "EXPORT-002",
            png_path.exists() and png_path.stat().st_size > 1000 and png_download.suggested_filename == "roadmap.png",
            "PNG export downloads a non-empty roadmap.png.",
            "PNG export did not produce a valid roadmap.png.",
        )

        with page.expect_download() as dl_info:
            page.click("#pptBtn")
        ppt_download = dl_info.value
        ppt_path = ARTIFACTS / "downloads" / ppt_download.suggested_filename
        ppt_download.save_as(ppt_path)
        with zipfile.ZipFile(ppt_path) as zf:
            slide_names = sorted(name for name in zf.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
            slide_xml = "\n".join(zf.read(name).decode("utf-8", "ignore") for name in slide_names)
            projection_slide_xml = zf.read("ppt/slides/slide3.xml").decode("utf-8", "ignore")
            stacked_slide_xml = zf.read("ppt/slides/slide4.xml").decode("utf-8", "ignore")
        repair_extents = pptx_negative_extents(ppt_path)
        runner.check(
            "EXPORT-004",
            ppt_path.exists()
            and ppt_path.stat().st_size > 1000
            and ppt_download.suggested_filename.endswith(".pptx")
            and len(slide_names) == 4
            and "Product Requirements" in slide_xml
            and "Vertical Integration" in slide_xml
            and "Foam Cup Damage" in slide_xml
            and "SAVINGS" in slide_xml
            and "AVOIDANCE" in slide_xml
            and "REALIZED" in slide_xml
            and "FY2026" in slide_xml
            and "FY2027" in slide_xml,
            "PowerPoint export downloads a deck with one human-readable slide per pillar, including fiscal years.",
            "PowerPoint export did not produce the expected pillar slides.",
        )
        runner.check(
            "EXPORT-006",
            len(slide_names) == 4
            and "Projected savings trajectory" in slide_xml
            and "Savings only" in slide_xml
            and "Savings + Avoidance" in slide_xml
            and "Pillar value concentration" in slide_xml
            and "Product Requirements" in slide_xml,
            "PowerPoint export includes Projected Savings and Stacked Bar Chart slides after the pillar roadmap slides.",
            "PowerPoint export did not include readable projection and stacked chart slides.",
        )
        runner.check(
            "EXPORT-007",
            "Projected by" in projection_slide_xml
            and "Avoidance lift" in projection_slide_xml
            and "Value added by Avoidance" in projection_slide_xml
            and "$1.6M" in projection_slide_xml
            and "$2M" not in projection_slide_xml,
            "PowerPoint projection slide uses a tighter axis, endpoint headline, and Avoidance lift story label.",
            "PowerPoint projection slide did not include the redesigned executive chart story.",
        )
        runner.check(
            "EXPORT-009",
            not repair_extents,
            "PowerPoint export avoids negative XML extents that trigger file repair.",
            f"PowerPoint export contains repair-prone negative XML extents: {repair_extents[:3]}",
        )
        runner.check(
            "EXPORT-008",
            "carries" in stacked_slide_xml
            and "Ranked contribution" in stacked_slide_xml
            and "Dominant pillar" in stacked_slide_xml
            and "Savings-only" in stacked_slide_xml
            and "Total impact" in stacked_slide_xml
            and "Pillar value concentration" in stacked_slide_xml,
            "PowerPoint stacked chart slide uses an insight title, dominant-pillar callout, and shared ranked table.",
            "PowerPoint stacked chart slide did not include the redesigned executive comparison story.",
        )

        page.evaluate(
            """state => {
                deserializeInto(state);
                enterStudio();
                setTab('road');
            }""",
            ppt_same_workstream_state(),
        )
        page.wait_for_selector("#tlSvg")
        with page.expect_download() as dl_info:
            page.click("#pptBtn")
        same_download = dl_info.value
        same_path = ARTIFACTS / "downloads" / same_download.suggested_filename
        same_download.save_as(same_path)
        with zipfile.ZipFile(same_path) as zf:
            same_slide_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8", "ignore")
        same_boxes = ppt_text_boxes(same_slide_xml, "Future Price Renewal Playbook")
        readable_same_workstream_labels = (
            len(same_boxes) == 2
            and len({round(box["y"], 2) for box in same_boxes}) == 2
            and all(box["w"] >= 2.0 for box in same_boxes)
            and all(box["x"] < 11.0 for box in same_boxes)
        )
        runner.check(
            "EXPORT-005",
            same_path.exists()
            and same_path.stat().st_size > 1000
            and readable_same_workstream_labels,
            "PowerPoint export keeps two same-workstream initiative labels in readable stacked lanes.",
            f"Same-workstream PowerPoint labels were not readable; observed boxes: {same_boxes}",
        )

        # Presentation mode.
        page.click("#presentBtn")
        page.wait_for_timeout(300)
        present_ok = page.locator("body.presenting").count() == 1 and not page.locator(".toolbar").is_visible()
        page.click("#darkBtn")
        dark_ok = page.locator("body.dark").count() == 1 and text(page, "#darkBtn") == "Light"
        page.click("#exitPres")
        exit_ok = page.locator("body.presenting").count() == 0
        runner.check("PRESENT-001", present_ok, "Present mode hides editing chrome and shows presentation state.", "Present mode did not enter correctly.")
        runner.check("PRESENT-002", dark_ok, "Dark presentation toggle changes palette state and button label.", "Dark presentation toggle failed.")
        runner.check("PRESENT-003", exit_ok, "Exit presentation clears presentation state.", "Exit presentation failed.")
        ctx.close()

        # Workstream counts after initiative assignment.
        ctx, page = new_context(browser, seed_state())
        counts = text(page, ".outline")
        runner.check(
            "STRUCT-012",
            "1 item" in counts or "2 items" in counts,
            "Structure workstreams show initiative counts for populated lanes.",
            "Workstream initiative counts were not visible.",
        )
        ctx.close()

        browser.close()

    untested = runner.update_tracker()
    return runner, untested


if __name__ == "__main__":
    runner, untested = run_tests()
    print(json.dumps({
        "results": len(runner.results),
        "passed": sum(1 for r in runner.results.values() if r["status"] == "Passed"),
        "failed": sum(1 for r in runner.results.values() if r["status"] == "Failed"),
        "issues": runner.issues,
        "untested": untested,
        "resultsJson": str(RESULTS_JSON),
        "tracker": str(TRACKER),
    }, indent=2))
