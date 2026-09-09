#!/usr/bin/env python3
"""Regression coverage for the workspace audit upgrade."""

import copy
import json
import os
import subprocess
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright
from verify_release import source_version


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "index.html"
ARTIFACTS = ROOT / "tasks" / "test-artifacts" / "workspace-audit"


def seed_state():
    state = {
        "v": 3,
        "savedAt": 1788523200000,
        "fileName": "Workspace audit",
        "fyStart": 6,
        "asOfDate": "2026-09-04",
        "projectionTarget": 1_500_000,
        "structure": [
            {"id": "p1", "name": "Customer", "workstreams": [{"id": "w1", "name": "Retention"}]},
            {"id": "p2", "name": "Operations", "workstreams": [{"id": "w2", "name": "Automation"}]},
        ],
        "items": [
            {
                "id": "i1", "pillarId": "p1", "wsId": "w1", "name": "Zulu renewal", "owner": "",
                "status": "At Risk", "approval": "Proposed", "start": "2026-01-01", "end": "2026-04-01",
                "valueType": "Savings", "value": 600000, "cost": 100000, "actualValue": 100000, "actualAsOf": "2026-01-01",
                "benefitKind": "one-time", "valueBasis": "lifetime", "recognitionMethod": "linear",
                "includeInTotals": True, "realizedPct": 10, "confidence": 70, "milestone": False,
            },
            {
                "id": "i2", "pillarId": "p2", "wsId": "w2", "name": "Alpha workflow", "owner": "Dana",
                "status": "On Track", "approval": "Approved", "start": "2026-06-01", "end": "2027-05-31",
                "valueType": "Avoidance", "value": 350000, "actualValue": 50000, "actualAsOf": "2026-08-20",
                "benefitKind": "recurring", "valueBasis": "annual", "recognitionMethod": "completion",
                "includeInTotals": True, "realizedPct": 20, "confidence": 100, "milestone": False,
            },
            {
                "id": "i3", "pillarId": "p1", "wsId": "w1", "name": "Middle duplicate", "owner": "Lee",
                "status": "Not Started", "approval": "Proposed", "start": "2027-01-01", "end": "2027-03-31",
                "valueType": "Savings", "value": 350000, "actualValue": "", "actualAsOf": "",
                "benefitKind": "one-time", "valueBasis": "lifetime", "recognitionMethod": "upfront",
                "includeInTotals": False, "creditedToId": "i1", "exclusionReason": "Counted in linked item", "realizedPct": 0,
                "confidence": 40, "milestone": False,
            },
            {
                "id": "i4", "pillarId": "p2", "wsId": "w2", "name": "Missing value", "owner": "Mina",
                "status": "On Track", "approval": "Approved", "start": "2026-10-01", "end": "2026-12-01",
                "valueType": "Savings", "value": "", "actualValue": "", "actualAsOf": "",
                "includeInTotals": True, "realizedPct": 0, "confidence": 100, "milestone": False,
            },
            {
                "id": "i5", "pillarId": "p2", "wsId": "w2", "name": "Reversed rollout", "owner": "Mina",
                "status": "On Track", "approval": "Approved", "start": "2026-10-01", "end": "2026-12-01",
                "valueType": "Savings", "value": 125000, "actualValue": "", "actualAsOf": "",
                "benefitKind": "one-time", "valueBasis": "lifetime", "recognitionMethod": "linear",
                "includeInTotals": True, "realizedPct": 0, "confidence": 100, "milestone": False,
            },
            {
                "id": "i6", "pillarId": "p2", "wsId": "w2", "name": "Actual without date", "owner": "Mina",
                "status": "On Track", "approval": "Approved", "start": "2026-06-01", "end": "2026-08-01",
                "valueType": "Savings", "value": 80000, "actualValue": 20000, "actualAsOf": "2026-08-01",
                "benefitKind": "one-time", "valueBasis": "lifetime", "recognitionMethod": "linear",
                "includeInTotals": True, "realizedPct": 0, "confidence": 100, "milestone": False,
            },
            {
                "id": "i7", "pillarId": "p1", "wsId": "w1", "name": "Excluded credit target", "owner": "Lee",
                "status": "Complete", "approval": "Approved", "start": "2026-01-01", "end": "2026-02-01",
                "valueType": "Savings", "value": 350000, "actualValue": "", "actualAsOf": "",
                "benefitKind": "one-time", "valueBasis": "lifetime", "recognitionMethod": "completion",
                "includeInTotals": False, "creditedToId": "i1", "exclusionReason": "Counted in renewal", "realizedPct": 0,
                "confidence": 100, "milestone": False,
            },
        ],
        "scenarios": [
            {
                "id": "sc1", "name": "Conservative", "savedAt": 1785844800000,
                "payload": {
                    "projectionTarget": 1_400_000,
                    "items": [
                        {"id": "i1", "name": "Zulu renewal", "value": 500000, "start": "2026-02-01", "end": "2026-05-01", "approval": "Proposed"},
                        {"id": "i2", "name": "Alpha workflow", "value": 300000, "start": None, "end": None, "approval": "Proposed"},
                    ],
                },
            },
            {
                "id": "sc2", "name": "Accelerated", "savedAt": 1788436800000,
                "payload": {
                    "projectionTarget": 1_600_000,
                    "items": [
                        {"id": "i1", "name": "Zulu renewal", "value": 750000, "start": "2025-12-01", "end": "2026-03-01", "approval": "Approved"},
                        {"id": "i2", "name": "Alpha workflow", "value": 350000, "start": "2026-06-01", "end": "2026-09-01", "approval": "Approved"},
                    ],
                },
            },
        ],
        "workspace": {},
    }
    by_id = {item["id"]: item for item in state["items"]}
    scenario_changes = {
        "sc1": {
            "i1": {"value": 500000, "start": "2026-02-01", "end": "2026-05-01", "approval": "Proposed"},
            "i2": {"value": 300000, "start": "2026-07-01", "end": "2027-06-30", "approval": "Proposed"},
        },
        "sc2": {
            "i1": {"value": 750000, "start": "2025-12-01", "end": "2026-03-01", "approval": "Approved"},
            "i2": {"value": 350000, "start": "2026-06-01", "end": "2026-09-01", "approval": "Approved"},
        },
    }
    for scenario in state["scenarios"]:
        items = []
        for item_id in ("i1", "i2"):
            item = copy.deepcopy(by_id[item_id])
            item.update(scenario_changes[scenario["id"]][item_id])
            items.append(item)
        scenario["payload"].update({"fyStart": 6, "structure": copy.deepcopy(state["structure"]), "items": items})
    return state


class WorkspaceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "tasks/build.py"], cwd=ROOT, check=True, capture_output=True, text=True)
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browser = getattr(cls.pw, os.environ.get("ROADMAP_BROWSER", "chromium")).launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        state = json.dumps(seed_state())
        self.page.goto(APP.as_uri())
        self.page.evaluate("state => localStorage.setItem('roadmapStudio.v1', state)", state)
        self.page.reload()
        self.page.evaluate("initWorkspace(); refreshWorkspace(); setTab('data')")

    def tearDown(self):
        self.page.close()

    def test_public_hook_contract_and_workspace_state(self):
        hooks = self.page.evaluate("""() => ({
            init: typeof initWorkspace, refresh: typeof refreshWorkspace,
            grid: typeof enhanceGrid, drawer: typeof enhanceDrawer,
            sort: typeof workspaceSortedItems,
            workspace: S.workspace
        })""")
        self.assertEqual({hooks[k] for k in ("init", "refresh", "grid", "drawer", "sort")}, {"function"})
        self.assertIn("sort", hooks["workspace"])
        self.assertIn("layouts", hooks["workspace"])
        self.assertEqual(self.page.locator("#workspaceVersion").inner_text(), f"v{source_version()}")
        self.assertEqual(self.page.locator("#wsAsOfDate").input_value(), "2026-09-04")

    def test_reporting_date_change_has_complete_undo(self):
        before = self.page.evaluate("S.history.length")
        self.page.fill("#wsAsOfDate", "2026-10-15")
        self.page.dispatch_event("#wsAsOfDate", "change")
        self.assertEqual(self.page.evaluate("S.asOfDate"), "2026-10-15")
        self.assertEqual(self.page.evaluate("S.history.length"), before + 1)
        self.page.evaluate("undo()")
        self.assertEqual(self.page.evaluate("S.asOfDate"), "2026-09-04")

    def test_stable_sort_and_accessible_headers(self):
        result = self.page.evaluate("""() => {
            S.workspace.sort={key:'value',dir:'asc'};
            const sorted=workspaceSortedItems([S.items[0],S.items[1],S.items[2]]).map(it=>it.id);
            renderGrid(); enhanceGrid();
            const th=document.querySelector('th[data-col=value]');
            return {sorted, aria:th.getAttribute('aria-sort'), button:!!th.querySelector('button.ws-sort')};
        }""")
        self.assertEqual(result["sorted"], ["i2", "i3", "i1"])
        self.assertEqual(result["aria"], "ascending")
        self.assertTrue(result["button"])

    def test_select_all_filtered_and_bulk_change_is_one_undo(self):
        self.page.select_option("#filterStatus", "On Track")
        self.page.locator("#wsSelectAll").check()
        self.assertEqual(self.page.locator("tbody [data-ws-select]:checked").count(), 4)
        before = self.page.evaluate("S.history.length")
        self.page.select_option("#wsBulkField", "approval")
        self.page.select_option("#wsBulkValue", "Proposed")
        self.page.click("#wsBulkApply")
        changed = self.page.evaluate("S.items.filter(it=>['i2','i4','i5','i6'].includes(it.id)).map(it=>it.approval)")
        self.assertEqual(changed, ["Proposed", "Proposed", "Proposed", "Proposed"])
        self.assertEqual(self.page.evaluate("S.history.length"), before + 1)
        self.page.evaluate("S.items.find(it=>it.id==='i2').name='Renamed after bulk'; renderAll()")
        self.page.click("[data-toast-action=undo]")
        restored = self.page.evaluate("""() => ({
            approvals:S.items.filter(it=>['i2','i4','i5','i6'].includes(it.id)).map(it=>it.approval),
            name:S.items.find(it=>it.id==='i2').name
        })""")
        self.assertEqual(restored["approvals"], ["Approved", "Approved", "Approved", "Approved"])
        self.assertEqual(restored["name"], "Renamed after bulk")

    def test_selection_column_tracks_row_center_and_height(self):
        self.page.evaluate("""() => {
            const template=S.items[0];
            S.items=Array.from({length:24},(_,i)=>({...template,id:`alignment-${i}`,name:`Initiative ${i+1}`}));
            renderAll();setTab('data');
        }""")
        for width in [1440, 390]:
            self.page.set_viewport_size({"width": width, "height": 1000 if width == 1440 else 844})
            for height in [0, 72]:
                with self.subTest(width=width, row_height=height):
                    rows = self.page.evaluate("""height => {
                        const rows=[...document.querySelectorAll('table.grid tbody tr[data-id]')];
                        rows.forEach(row=>row.style.height=height?`${height}px`:'');
                        document.querySelector('#gridStage .grid-wrap').scrollTop=180;
                        const center=el=>{const r=el.getBoundingClientRect();return r.top+r.height/2;};
                        return rows.map(row=>{
                            const cell=row.querySelector('.rownum'),check=cell.querySelector('[data-ws-select]');
                            return {id:row.dataset.id,display:getComputedStyle(cell).display,
                                rowHeight:row.getBoundingClientRect().height,cellHeight:cell.getBoundingClientRect().height,
                                checkboxDelta:center(check)-center(row.querySelector('[data-f=name]')),
                                numberDelta:center(cell.querySelector('span'))-center(check)};
                        });
                    }""", height)
                    for row in rows:
                        self.assertEqual(row["display"], "table-cell", row)
                        self.assertLessEqual(abs(row["cellHeight"] - row["rowHeight"]), 1, row)
                        self.assertLessEqual(abs(row["checkboxDelta"]), 1, row)
                        self.assertLessEqual(abs(row["numberDelta"]), 1, row)

    def test_selection_checkbox_keyboard_and_header_state(self):
        checkbox = self.page.locator('table.grid tbody [data-ws-select]').first
        checkbox.focus()
        checkbox.press("Space")
        self.assertTrue(checkbox.is_checked())
        self.assertTrue(self.page.locator('#wsSelectAll').evaluate('el=>el.indeterminate'))
        self.assertEqual(self.page.locator('#wsSelectionCount').inner_text(), '1 selected')
        self.page.locator('#wsSelectAll').check()
        self.assertEqual(self.page.locator('tbody [data-ws-select]:checked').count(), self.page.locator('tbody [data-ws-select]').count())
        self.page.locator('#wsSelectAll').uncheck()
        self.assertEqual(self.page.locator('tbody [data-ws-select]:checked').count(), 0)

    def test_named_layout_persists_and_hides_columns(self):
        self.page.evaluate("""() => {
            document.querySelector('#wsColumnOptions input[value=value]').click();
            workspaceSaveLayout('Delivery review');
            enhanceGrid();
        }""")
        data = self.page.evaluate("""() => ({
            names:S.workspace.layouts.map(x=>x.name),
            hidden:getComputedStyle(document.querySelector('th[data-col=value]')).display,
            saved:JSON.parse(serializeState().workspace.layouts[0].columns.length > 0)
        })""")
        self.assertIn("Delivery review", data["names"])
        self.assertEqual(data["hidden"], "none")
        self.assertTrue(data["saved"])

    def test_financial_drilldown_reconciles_populations_and_formula(self):
        self.page.evaluate("S.items.find(it=>it.id==='i2').start=null; S.items.find(it=>it.id==='i2').end=null; setTab('exec'); refreshWorkspace()")
        self.page.click("#execTotal")
        dialog = self.page.locator("#workspaceDrilldown")
        self.assertTrue(dialog.is_visible())
        self.assertEqual(dialog.locator("[data-population=included]").count(), 5)
        self.assertEqual(dialog.locator("[data-population=excluded]").count(), 2)
        self.assertEqual(dialog.locator("[data-population=undated]").count(), 1)
        self.assertIn("Formula", dialog.inner_text())
        self.assertIn("implementation cost", dialog.inner_text().lower())
        self.assertIn("$100K", dialog.inner_text())
        self.assertIn("$500K", dialog.inner_text())
        self.assertIn("Sep 4, 2026", dialog.inner_text())
        self.assertEqual(dialog.get_attribute("aria-modal"), "true")
        self.page.click("#workspaceDrilldownClose")
        self.page.click("#execRealized")
        self.assertIn("Recorded actual", dialog.inner_text())

    def test_compare_reports_value_date_approval_and_goal_deltas(self):
        self.page.click("#wsReviewToggle")
        self.page.click("[data-review-view=compare]")
        self.page.select_option("#wsCompareA", "sc1")
        self.page.select_option("#wsCompareB", "sc2")
        text = self.page.locator("#workspaceReviewBody").inner_text()
        for expected in ("$250K", "Dec 1, 2025", "Proposed", "Active", "$200K"):
            self.assertIn(expected, text)

    def test_exception_queue_covers_requested_categories(self):
        self.page.evaluate("""() => {
            const item=id=>S.items.find(entry=>entry.id===id);
            item('i5').end=parseAnyDate('2026-09-01','end',S.fyStart);
            item('i2').start=null; item('i2').end=null;
            item('i6').actualAsOf='';
            item('i3').creditedToId='i7';
        }""")
        self.page.click("#wsReviewToggle")
        text = self.page.locator("#workspaceReviewBody").inner_text()
        self.assertNotIn("Resolve reporting gaps", self.page.locator("#workspaceReview").inner_text())
        for expected in ("Missing inputs", "Overdue", "Stale actuals", "Exclusion link"):
            self.assertIn(expected, text)
        self.assertIn("Zulu renewal", text)
        self.assertIn("Middle duplicate", text)
        self.assertIn("End date precedes start date", text)
        self.assertIn("Annual recurring value needs complete timing", text)
        self.assertIn("Actual has no as-of date", text)
        self.assertIn("Credited initiative is also excluded", text)

    def test_local_recovery_versions_are_available_from_review(self):
        recovery = [{"name": "Earlier board plan", "date": 1788436800000, "data": "{}"}]
        self.page.evaluate("value => localStorage.setItem('roadmapStudio.recovery.v1', JSON.stringify(value))", recovery)
        self.page.click("#wsReviewToggle")
        self.page.click("[data-review-view=recovery]")
        self.assertIn("Earlier board plan", self.page.locator("#workspaceReviewBody").inner_text())
        self.assertEqual(self.page.locator("[data-recovery-index]").count(), 1)

    def test_mobile_workspace_has_no_horizontal_page_overflow(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.evaluate("setTab('proj'); refreshWorkspace()")
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)
        self.page.screenshot(path=str(ARTIFACTS / "workspace-390.png"), full_page=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
