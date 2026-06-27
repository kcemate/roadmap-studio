#!/usr/bin/env python3
import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
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
            writer = csv.DictWriter(f, fieldnames=fields)
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


def attr(page, selector, name):
    return page.locator(selector).get_attribute(name, timeout=5000)


def blur(page):
    page.keyboard.press("Tab")
    page.wait_for_timeout(80)


def wait_autosave(page):
    page.wait_for_timeout(550)


def safe_click(locator):
    locator.click(timeout=5000, force=True)


def make_excel_fixture(page, path, rows):
    make_excel_fixture_with_headers(
        page,
        path,
        ['Pillar', 'Workstream', 'Initiative', 'Start', 'End', 'Status', 'Owner', 'Savings / Avoidance', '$ Value', '% Realized', 'Milestone'],
        rows,
    )


def make_excel_fixture_with_headers(page, path, headers, rows):
    page.wait_for_function("window.ExcelJS !== undefined", timeout=20000)
    data = page.evaluate(
        """async ({headers, rows}) => {
            const wb = new ExcelJS.Workbook();
            const ws = wb.addWorksheet('Roadmap');
            ws.addRow(headers);
            rows.forEach(row => ws.addRow(row));
            const buf = await wb.xlsx.writeBuffer();
            return Array.from(new Uint8Array(buf));
        }""",
        {"headers": headers, "rows": rows},
    )
    path.write_bytes(bytes(data))


def xlsx_dimension(path):
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("xl/worksheets/sheet1.xml")
    root = ET.fromstring(xml)
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    dim = root.find("x:dimension", ns)
    return dim.attrib.get("ref", "") if dim is not None else ""


def max_col_from_dimension(ref):
    if ":" in ref:
        ref = ref.split(":")[-1]
    match = re.match(r"([A-Z]+)", ref)
    if not match:
        return 0
    col = 0
    for ch in match.group(1):
        col = col * 26 + ord(ch) - 64
    return col


def visible_texts(page, selector):
    return [item.strip() for item in page.locator(selector).all_inner_texts() if item.strip()]


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
            and visible_texts(page, ".seg button") == ["Structure", "Initiatives", "Roadmap"]
            and "1 pillar" in text(page, "#structMeta")
            and "1 workstream" in text(page, "#structMeta"),
            "Blank start creates one pillar/workstream and opens Structure with tabs ordered Structure, Initiatives, Roadmap.",
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
            ["ROAD-002", "ROAD-003", "ROAD-004", "ROAD-005", "ROAD-012", "ROAD-013"],
            "3 initiatives" in text(page, "#roadMeta")
            and "3 dated" in text(page, "#roadMeta")
            and text(page, "#realizedSavingsTotal") == "$460K"
            and text(page, "#savingsTotal") == "$920K"
            and text(page, "#realizedAvoidanceTotal") == "$360K"
            and text(page, "#avoidanceTotal") == "$450K"
            and financial_layout_grouped
            and "Foam Cup Damage" in text(page, "#tlSvg")
            and "$920K" in text(page, "#tlSvg")
            and "TODAY" in text(page, "#tlSvg"),
            "Roadmap renders counts, grouped realized financial totals, fiscal/quarter layout, today marker, lanes, item labels, and money labels.",
            "Roadmap rendering, metadata, grouped realized financial totals, totals, or money labels were wrong.",
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
            and collapsed_h < before_collapse_h
            and collapsed_saved
        )
        page.locator(".pillar-toggle[data-pillar='p1']").click(force=True)
        expanded_text = text(page, "#tlSvg")
        expanded_ok = (
            page.locator(".pillar-toggle[data-pillar='p1']").get_attribute("data-collapsed") == "false"
            and "Foam Cup Damage" in expanded_text
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

        # Excel import and export.
        ctx, page = new_context(browser)
        excel_fixture = ARTIFACTS / "import-fixture.xlsx"
        missing_pillar_fixture = ARTIFACTS / "missing-pillar.xlsx"
        try:
            make_excel_fixture(
                page,
                excel_fixture,
                [
                    ["Product Requirements", "Damage Reduction", "Foam Cup Damage", "Q4 FY2026", "Q2 FY2027", "On Track", "B. Berry", "Savings", "$920,000", "50%", False],
                    ["Product Requirements", "Transportation", "Carrier Risk", "9/1/2026", "9/1/2026", "red", "A. Adams", "Avoidance", "450K", 0.8, "x"],
                ],
            )
            make_excel_fixture_with_headers(
                page,
                missing_pillar_fixture,
                ["Workstream", "Initiative", "Start", "End"],
                [["Damage Reduction", "No Pillar Initiative", "2026-01-01", "2026-02-01"]],
            )
            excel_ready = True
        except Exception as exc:
            excel_ready = False
            excel_error = str(exc)
        if excel_ready:
            page.set_input_files("#fileIn", str(excel_fixture))
            page.wait_for_selector("#studio")
            page.click("#segRoad")
            import_ok = (
                "2 initiatives" in text(page, "#roadMeta")
                and text(page, "#realizedSavingsTotal") == "$460K"
                and text(page, "#savingsTotal") == "$920K"
                and text(page, "#realizedAvoidanceTotal") == "$360K"
                and text(page, "#avoidanceTotal") == "$450K"
                and "Foam Cup Damage" in text(page, "#tlSvg")
            )
            runner.record(["IMPORT-001", "IMPORT-004"], import_ok, "Excel import parsed structure, initiatives, quarter/date/status/value fields." if import_ok else "Excel import did not produce expected roadmap.", "" if import_ok else "Excel import output was wrong.")
        else:
            runner.record(["IMPORT-001", "IMPORT-004"], False, f"ExcelJS was unavailable for fixture generation: {excel_error}", f"ExcelJS unavailable: {excel_error}")
        ctx.close()

        ctx, page = new_context(browser)
        txt_file = ARTIFACTS / "not-excel.txt"
        txt_file.write_text("not excel")
        page.set_input_files("#fileIn", str(txt_file))
        runner.check(
            "IMPORT-002",
            "Excel workbook" in text(page, "#err"),
            "Non-Excel import is rejected with the expected error.",
            "Non-Excel import did not show the expected error.",
        )
        ctx.close()

        if excel_ready:
            ctx, page = new_context(browser)
            page.set_input_files("#fileIn", str(missing_pillar_fixture))
            page.wait_for_selector("#err", state="visible", timeout=5000)
            runner.check(
                "IMPORT-003",
                "Pillar column" in text(page, "#err"),
                "Workbook missing Pillar column is rejected with a helpful error.",
                "Workbook missing Pillar column was not rejected as expected.",
            )
            ctx.close()
        else:
            runner.record("IMPORT-003", False, "Skipped because ExcelJS fixture generation failed.", "ExcelJS fixture generation failed.")

        ctx, page = new_context(browser, seed_state())
        try:
            page.wait_for_function("window.ExcelJS !== undefined", timeout=20000)
            with page.expect_download() as dl_info:
                page.click("#exportBtn")
            export_download = dl_info.value
            export_path = ARTIFACTS / "downloads" / export_download.suggested_filename
            export_download.save_as(export_path)
            dim = xlsx_dimension(export_path)
            export_ok = export_path.exists() and max_col_from_dimension(dim) <= 11 and "scaffold" in export_download.suggested_filename
            runner.record(
                "EXPORT-001",
                export_ok,
                f"Export Excel downloaded {export_download.suggested_filename} with worksheet dimension {dim}.",
                f"Export Excel created an unexpected worksheet dimension {dim}.",
            )
        except Exception as exc:
            runner.record("EXPORT-001", False, f"Export Excel failed: {exc}", f"Export Excel failed: {exc}")
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
