#!/usr/bin/env python3
"""Regression contracts for the 1.6.7 audit (section A: broken behaviour).

Each test is named after the audit item it reproduces. Tests drive the built
index.html in a real browser and assert the corrected contract.
"""
import json
import os
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP_URL = (ROOT / 'index.html').as_uri()
LS_KEY = 'roadmapStudio.v1'


def project(items=None, structure=None, **extra):
    base = {
        'v': 3, 'percentageUnit': 'points', 'fileName': 'Audit fixture', 'fyStart': 6,
        'structure': structure if structure is not None else [
            {'id': 'p1', 'name': 'Pillar One', 'workstreams': [{'id': 'w1', 'name': 'WS One'}, {'id': 'w2', 'name': 'WS Two'}]},
            {'id': 'p2', 'name': 'Pillar Two', 'workstreams': [{'id': 'w3', 'name': 'WS Three'}]},
        ],
        'items': items if items is not None else [item('i1'), item('i2', valueType='Avoidance', value=500000), item('i3', pillarId='p2', wsId='w3', approval='Proposed', value=250000)],
        'asOfDate': '2026-06-30',
    }
    base.update(extra)
    return base


def item(id, **kw):
    out = {'id': id, 'pillarId': 'p1', 'wsId': 'w1', 'name': f'Item {id}', 'start': '2026-01-01', 'end': '2026-12-31',
           'status': 'On Track', 'approval': 'Approved', 'valueType': 'Savings', 'value': 1000000, 'confidence': 100}
    out.update(kw)
    return out


class AppCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = getattr(cls.pw, os.environ.get('ROADMAP_BROWSER', 'chromium')).launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.ctx = self.browser.new_context(accept_downloads=True, viewport={'width': 1440, 'height': 900})
        self.page = self.ctx.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.prompts = []
        self.page.on('dialog', self._dialog)
        self.page.goto(APP_URL)

    def _dialog(self, dialog):
        if dialog.type == 'prompt':
            self.prompts.append(dialog.message)
            dialog.accept(f'Named {len(self.prompts)}')
        else:
            dialog.accept()

    def tearDown(self):
        self.ctx.close()
        self.assertEqual(self.errors, [], 'Unexpected application errors')

    # helpers
    def open_project(self, state):
        self.page.locator('#projIn').set_input_files({'name': 'fixture.roadmap.json', 'mimeType': 'application/json',
                                                      'buffer': json.dumps(state).encode()})
        self.page.wait_for_function("name=>S.view==='studio'&&S.fileName===name", arg=state.get('fileName', 'Audit fixture'), timeout=30000)

    def store_and_reload(self, state):
        self.page.evaluate('([k,p])=>localStorage.setItem(k,JSON.stringify(p))', [LS_KEY, state])
        self.page.reload()

    def flush(self):
        self.page.evaluate('()=>{if(_saveT){clearTimeout(_saveT);_saveT=null;autosave();}}')

    def reload_ok(self):
        self.flush()
        self.page.reload()
        self.page.wait_for_timeout(100)
        self.assertEqual(self.page.evaluate('S.view'), 'studio', self.page.inner_text('#err'))

    def js(self, expr, arg=None):
        return self.page.evaluate(expr, arg) if arg is not None else self.page.evaluate(expr)

    def cell(self, field, id='i1'):
        return self.page.locator(f'tr[data-id="{id}"] [data-f="{field}"]')

    def edit(self, field, value, id='i1'):
        self.cell(field, id).fill(value)
        self.page.keyboard.press('Tab')

    def pptx(self, scope='full'):
        with self.page.expect_download(timeout=30000) as info:
            self.js(f"exportPowerPoint('{scope}')")
        path = Path(tempfile.mkdtemp(prefix='roadmap-audit-')) / 'deck.pptx'
        info.value.save_as(path)
        return path


def slide_texts(path):
    with zipfile.ZipFile(path) as z:
        names = sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)], key=lambda n: int(re.findall(r'\d+', n)[0]))
        return [' '.join(re.findall(r'<a:t>([^<]*)</a:t>', z.read(n).decode())) for n in names]


def notes_texts(path):
    with zipfile.ZipFile(path) as z:
        names = sorted([n for n in z.namelist() if re.match(r'ppt/notesSlides/notesSlide\d+\.xml$', n)], key=lambda n: int(re.findall(r'\d+', n)[0]))
        out = []
        for n in names:
            xml = z.read(n).decode()
            out.append([''.join(re.findall(r'<a:t>([^<]*)</a:t>', p)) for p in re.findall(r'<a:p>.*?</a:p>', xml, re.S)])
        return out


class DataLossTests(AppCase):
    """A1: values that save must load; snapshots and recovery must not lose work."""

    def test_A1_out_of_range_grid_date_is_rejected(self):
        self.open_project(project())
        self.page.click('#segData')
        self.edit('end', '2500-06-01')
        self.assertEqual(self.cell('end').get_attribute('aria-invalid'), 'true')
        self.assertEqual(self.js("isoDate(S.items.find(i=>i.id==='i1').end)"), '2026-12-31')
        self.reload_ok()

    def test_A1_out_of_range_projection_and_reporting_dates_are_rejected(self):
        self.open_project(project())
        self.page.click('#segProj')
        self.page.fill('#projectionEndDate', '2300-01-01')
        self.page.dispatch_event('#projectionEndDate', 'change')
        self.assertNotEqual(self.js('S.projectionEnd'), '2300-01-01')
        self.page.click('#segData')
        self.page.fill('#wsAsOfDate', '2300-01-01')
        self.page.dispatch_event('#wsAsOfDate', 'change')
        self.assertEqual(self.js('S.asOfDate'), '2026-06-30')
        self.reload_ok()

    def test_A1_out_of_range_drawer_dates_are_rejected(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.fill('#dActual', '5000')
        self.page.fill('#dActualAsOf', '2300-01-01')
        self.page.click('#drawerDone')
        self.assertTrue(self.js("$('itemDrawer').classList.contains('on')"))
        self.assertEqual(self.page.get_attribute('#dActualAsOf', 'aria-invalid'), 'true')
        self.page.fill('#dActualAsOf', '2026-05-01')
        self.page.fill('#dStart', '1800-01-01')
        self.page.click('#drawerDone')
        self.assertEqual(self.page.get_attribute('#dStart', 'aria-invalid'), 'true')
        self.assertEqual(self.js("isoDate(S.items[0].start)"), '2026-01-01')
        self.reload_ok()

    def test_A1_structure_limits_are_enforced_on_input(self):
        self.open_project(project(items=[]))
        self.page.click('#segStruct')
        self.js("for(let i=0;i<120;i++)$('addPillar').click()")
        self.assertEqual(self.js('S.structure.length'), 100)
        self.js("for(let i=0;i<230;i++)document.querySelector('.add-ws').click()")
        self.assertEqual(self.js('S.structure[0].workstreams.length'), 200)
        self.reload_ok()

    def test_A1_deleted_markers_stay_loadable(self):
        self.open_project(project(items=[]))
        self.page.click('#scenarioSaveBtn')
        for _ in range(3):
            self.js("""()=>{const p=S.structure[0],w=p.workstreams[0];for(let i=0;i<2000;i++)S.items.push({id:uid('i'),pillarId:p.id,wsId:w.id,name:'x'+i,start:null,end:null,valueType:'Savings',value:'',includeInTotals:true,realizedPct:'',confidence:100,phases:[],milestone:false,status:'Not Started',approval:'Proposed',owner:''});saveWorkingScenario();pushUndo();S.items=[];renderAll();showUndoToast('Deleted');}""")
        self.assertLessEqual(self.js('S.deletedIds.length'), 5000)
        self.reload_ok()

    def test_A1_autosave_never_replaces_last_loadable_save(self):
        self.open_project(project())
        self.flush()
        good = self.js(f"localStorage.getItem('{LS_KEY}')")
        self.js("S.items[0].start=utc(2600,0,1);S.items[0].end=utc(2600,5,1);scheduleSave()")
        self.flush()
        self.assertEqual(self.js(f"localStorage.getItem('{LS_KEY}')"), good)
        self.assertFalse(self.js("$('saveWarning').hidden"))
        self.assertIn('2200', self.page.inner_text('#saveWarning'))

    def test_A2_undo_restores_without_resanitizing(self):
        self.open_project(project())
        self.js("S.items[0].name='Bad '+'x'.repeat(400);pushUndo();S.items[0].name='after';renderAll()")
        self.js('undo()')
        self.assertTrue(self.js("S.items[0].name.startsWith('Bad ')"))
        self.assertEqual(self.js('S.items[0].name.length'), 404)

    def test_A3_large_backup_does_not_empty_recovery(self):
        self.open_project(project())
        self.flush()
        self.js("localStorage.setItem('roadmapStudio.recovery.v1',JSON.stringify([{name:'Older',date:1,data:JSON.stringify(serializeState())}]))")
        big = project(items=[item(f'b{n}', name='N' * 200, owner='O' * 100) for n in range(2600)], fileName='Big')
        self.open_project(big)
        self.flush()
        self.open_project(project())
        versions = self.js('localRecoveryProjects().map(v=>v.name)')
        self.assertGreaterEqual(len(versions), 1)

    def test_A4_project_too_large_for_recovery_is_reported(self):
        self.open_project(project(items=[item(f'b{n}', name='N' * 230, owner='O' * 110) for n in range(4800)], fileName='Huge'))
        self.flush()
        self.open_project(project())
        self.assertIn('recovery', self.page.inner_text('#toast').lower())

    def test_A5_large_import_reports_storage_limit_instead_of_silent_failure(self):
        self.open_project(project())
        self.flush()
        huge = project(items=[item(f'h{n}', name='N' * 239, owner='O' * 119, exclusionReason='R' * 480) for n in range(5000)], fileName='Huge import')
        self.open_project(huge)
        self.flush()
        if not self.js("$('saveWarning').hidden"):
            self.assertIn('MB', self.page.inner_text('#saveWarning'))
        else:
            self.assertEqual(json.loads(self.js(f"localStorage.getItem('{LS_KEY}')"))['fileName'], 'Huge import')

    def test_A6_deleting_active_scenario_keeps_working_plan(self):
        self.open_project(project())
        self.page.click('#segData')
        self.edit('value', '7777')
        self.page.click('#scenarioSaveBtn')
        sc = self.js('S.scenarios[0].id')
        self.edit('value', '4444')
        self.page.click('#scenarioDeleteBtn')
        self.assertIsNone(self.js('S.activeScenarioId'))
        self.assertFalse(self.js(f"S.scenarios.some(s=>s.id==='{sc}')"))
        # The working plan saved before the scenario became active comes back.
        self.assertEqual(self.js("S.items.find(i=>i.id==='i1').value"), 7777)

    def test_A7_deleted_structure_stays_deleted_across_scenarios(self):
        self.open_project(project())
        self.page.click('#scenarioSaveBtn')
        self.page.click('#segStruct')
        self.page.click('[data-act=pdel][data-p=p2]')
        self.page.click('#scenarioSaveBtn')
        first = self.js('S.scenarios[0].id')
        self.page.select_option('#scenarioSelect', first)
        self.assertFalse(self.js("S.structure.some(p=>p.id==='p2')"))
        self.page.click('#segStruct')
        self.page.click('[data-act=wdel][data-w=w2]')
        self.page.select_option('#scenarioSelect', self.js('S.scenarios[1].id'))
        self.page.select_option('#scenarioSelect', first)
        self.assertFalse(self.js("S.structure.some(p=>p.workstreams.some(w=>w.id==='w2'))"))
        self.reload_ok()

    def test_A8_restored_drawer_draft_with_new_pillar_keeps_valid_workstream(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.select_option('#dPillar', 'p2')
        self.reload_ok()
        self.page.wait_for_selector('#itemDrawer.on')
        self.assertEqual(self.page.input_value('#dWs'), 'w3')
        self.page.click('#drawerDone')
        self.assertEqual(self.js("S.items.find(i=>i.id==='i1').wsId"), 'w3')
        self.reload_ok()

    def test_A9_deleted_credit_target_does_not_return(self):
        state = project(items=[item('i1'), item('i2', includeInTotals=False, creditedToId='i1', exclusionReason='Counted in i1')])
        self.open_project(state)
        self.page.click('#scenarioSaveBtn')
        self.page.select_option('#scenarioSelect', '__working')
        self.assertIsNone(self.js('S.activeScenarioId'))
        self.page.click('#segData')
        self.page.click('tr[data-id=i1] [data-act=del]')
        self.page.select_option('#scenarioSelect', self.js('S.scenarios[0].id'))
        self.assertEqual(self.js("S.items.find(i=>i.id==='i2').creditedToId"), '')
        self.reload_ok()

    def test_A10_empty_structure_is_offered_for_resume(self):
        self.store_and_reload(project(structure=[], items=[]))
        self.page.wait_for_timeout(100)
        if self.js('S.view') == 'studio':
            return
        self.assertTrue(self.page.is_visible('#btnResume'))


class NumberTests(AppCase):
    """A2: every view derives from one totals path."""

    def awkward(self):
        return project(items=[
            item('zero', value='', actualValue=200000, actualAsOf='2026-03-01'),
            item('over', value=100000, actualValue=150000, actualAsOf='2026-03-01'),
            item('excl', value=300000, includeInTotals=False, creditedToId='over', exclusionReason='Duplicate'),
            item('undated', value=400000, start='', end='', approval='Proposed'),
            item('prop', value=600000, approval='Proposed', confidence=40),
            item('rec', value=120000, benefitKind='recurring', valueBasis='annual', start='2026-01-01', end='2027-12-31', valueType='Avoidance'),
        ], projectionTarget=2000000)

    def test_A11_A14_A15_all_views_agree(self):
        self.open_project(self.awkward())
        t = self.js('portfolioTotals()')
        self.assertEqual(t['Total'], 100000 + 400000 + 600000 + 240000)
        self.assertEqual(t['Realized'], 350000)
        self.assertEqual(t['RealizedBeyondPlan'], 250000)
        self.assertEqual(t['Excluded'], 300000)
        self.assertEqual(t['Undated'], 400000)
        self.assertEqual(t['FinancialCount'], 5)
        exec_data = self.js('executiveSummaryData()')
        self.assertEqual(exec_data['totals']['Total'], t['Total'])
        self.assertEqual(exec_data['totals']['Realized'], t['Realized'])
        self.assertEqual(self.js('portfolioRollupData().totals.Total'), t['Total'])
        self.assertEqual(self.js('portfolioRollupData().totals.Realized'), t['Realized'])
        self.assertEqual(self.js('initiativeRegisterData().totals.Total'), t['Total'])
        self.assertEqual(self.js('initiativeRegisterData().totals.Realized'), t['Realized'])
        self.assertEqual(self.js("stackedBreakdown('combined').total"), t['Total'])
        self.assertEqual(self.js("stackedBreakdown('savings').total"), t['Savings'])
        self.assertEqual(self.js('pptFinancialTotals(S.items).Total'), t['Total'])
        # The executive bar shows each planned dollar once.
        self.assertEqual(sum(s['value'] for s in exec_data['segments']), t['Total'])
        self.page.click('#segExec')
        realized_text = self.page.inner_text('#execRealized')
        self.assertIn('beyond plan', self.page.inner_text('#execRealizedNote').lower())
        self.page.click('#segRollup')
        self.assertEqual(self.page.inner_text('#rollupRealized'), realized_text)

    def test_A11_one_goal_basis_for_executive_and_projection(self):
        self.open_project(self.awkward())
        gap = self.js('goalStatus().gap')
        self.assertEqual(gap, 2000000 - self.js('portfolioTotals().Total'))
        self.page.click('#segExec')
        head = self.page.inner_text('#execHeadline')
        self.page.click('#segProj')
        status = self.page.inner_text('#projectionTargetStatus')
        money = self.js('g=>fmtMoneyShort(Math.abs(g))', gap)
        self.assertIn(money, head)
        self.assertIn(money, status)

    def test_A12_A34_no_goal_is_explicit(self):
        self.open_project(project())
        self.page.click('#segExec')
        self.assertEqual(self.page.input_value('#execGoalInput'), '')
        self.assertIn('no goal', self.page.inner_text('#execHeadline').lower())
        self.assertNotIn('$1B', self.page.inner_text('#execStage'))
        self.page.click('#segProj')
        self.assertEqual(self.page.input_value('#projectionTarget'), '')
        notes = ' '.join(' '.join(n) for n in notes_texts(self.pptx()))
        self.assertNotIn('1,000,000,000', notes)
        self.assertIn('No goal set', notes)

    def test_A13_unknown_statuses_are_not_on_track(self):
        statuses = ['Blocked', 'Delayed', 'On hold', 'Cancelled', 'Deferred', 'Paused', 'Mystery state']
        self.open_project(project(items=[item(f's{i}', status=s) for i, s in enumerate(statuses)]))
        got = self.js('S.items.map(i=>i.status)')
        self.assertNotIn('On Track', got)
        self.assertEqual(got[:6], ['Blocked', 'At Risk', 'On Hold', 'Cancelled', 'On Hold', 'On Hold'])
        self.assertEqual(self.js("S.items[6].importedStatus"), 'Mystery state')

    def test_A16_stacked_savings_segment_drills_savings_only(self):
        self.open_project(project())
        self.page.click('#segStack')
        self.page.click('#stackSavingsSvg .stack-segment[data-pillar=p1]', force=True)
        self.assertEqual(self.page.inner_text('.ws-drill-summary b'), self.js("fmtMoneyShort(portfolioTotals(S.items.filter(i=>i.pillarId==='p1')).Savings)"))

    def test_A17_projection_drill_matches_card(self):
        self.open_project(project(projectionEnd='2026-03-31'))
        self.page.click('#segProj')
        card = self.page.inner_text('#projCombined')
        self.page.click('#projCombined')
        self.assertEqual(self.page.inner_text('.ws-drill-summary b'), card)

    def test_A18_compare_uses_lifetime_values_and_explicit_no_goal(self):
        self.open_project(project(items=[item('rec', value=100000, benefitKind='recurring', valueBasis='annual', start='2026-01-01', end='2027-12-31')]))
        self.page.click('#scenarioSaveBtn')
        self.page.click('#segData')
        self.page.click('#wsReviewToggle')
        self.page.click('[data-review-view=compare]')
        text = self.page.inner_text('#workspaceReviewBody')
        self.assertIn('$200K', text)
        self.assertIn('No goal set', text)

    def test_A19_zero_goal_means_no_goal_everywhere(self):
        self.open_project(project(projectionTarget=0))
        self.page.click('#segProj')
        self.assertTrue(self.page.inner_text('#projectionTargetStatus').strip().startswith('No goal set'))
        self.page.click('#segExec')
        self.assertIn('no goal', self.page.inner_text('#execHeadline').lower())

    def test_A20_typed_fraction_interpretation_is_explicit(self):
        self.open_project(project())
        self.page.click('#segData')
        self.edit('realizedPct', '0.5')
        self.assertEqual(self.js("S.items[0].realizedPct"), 50)
        self.assertIn('50%', self.page.inner_text('#toast'))
        self.assertIn('0.5%', self.page.inner_text('#toast'))

    def test_A21_money_rounding_promotes_units(self):
        self.page.click('#btnBlank')
        cases = [(999999, '$1M'), (999500, '$1M'), (999_499_999, '$999M'), (999_999_999, '$1B'), (1_500_000_000_000, '$1.5T'),
                 (15_400_000, '$15.4M'), (15_000_000, '$15M'), (1_250_000, '$1.25M'), (731_300, '$731K'), (950, '$950'), (-2500, '-$2.5K'), (0, '$0')]
        for value, expected in cases:
            self.assertEqual(self.js('v=>fmtMoneyShort(v)', value), expected, value)

    def test_A22_quarter_start_loads_as_first_day(self):
        self.open_project(project(items=[item('q', start='Q1 FY26', end='Q2 FY26')]))
        self.assertEqual(self.js("isoDate(S.items[0].start)"), '2025-07-01')
        self.assertEqual(self.js("isoDate(S.items[0].end)"), '2025-12-31')


class EditingTests(AppCase):
    """A3: editing interactions."""

    def drag(self, src, dst):
        self.js("""([a,b])=>{const s=document.querySelector(a),t=document.querySelector(b),dt=new DataTransfer();
          s.dispatchEvent(new DragEvent('dragstart',{bubbles:true,dataTransfer:dt}));
          t.dispatchEvent(new DragEvent('dragover',{bubbles:true,cancelable:true,dataTransfer:dt}));
          t.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));
          s.dispatchEvent(new DragEvent('dragend',{bubbles:true,dataTransfer:dt}));}""", [src, dst])

    def test_A23_workstream_drag_reorders_workstreams(self):
        self.open_project(project())
        self.page.click('#segStruct')
        self.drag('.ws-row[data-w=w2]', '.ws-row[data-w=w1]')
        self.assertEqual(self.js("S.structure[0].workstreams.map(w=>w.id)"), ['w2', 'w1'])
        self.assertEqual(self.js("S.structure.map(p=>p.id)"), ['p1', 'p2'])

    def test_A31_invalid_structure_drag_adds_no_undo_step(self):
        self.open_project(project())
        self.page.click('#segStruct')
        before = self.js('S.history.length')
        self.drag('.ws-row[data-w=w3]', '.ws-row[data-w=w1]')
        self.assertEqual(self.js('S.history.length'), before)

    def test_A24_dragging_bar_without_end_date(self):
        self.open_project(project(items=[item('i1', end='')]))
        self.page.click('#segRoad')
        bar = self.page.locator('.bar-grab[data-id=i1]').first.bounding_box()
        self.page.mouse.move(bar['x'] + 4, bar['y'] + bar['height'] / 2)
        self.page.mouse.down()
        for dx in range(1, 6):
            self.page.mouse.move(bar['x'] + 4 + dx * 20, bar['y'] + bar['height'] / 2)
        self.page.mouse.up()
        self.assertNotEqual(self.js("isoDate(S.items[0].start)"), '2026-01-01')

    def test_A25_reverted_cell_leaves_no_draft(self):
        self.open_project(project())
        self.page.click('#segData')
        self.cell('name').fill('Changed')
        self.cell('name').fill('Item i1')
        self.assertEqual(self.js('Object.keys(S.editDrafts).length'), 0)

    def test_A26_rejected_draft_is_marked_invalid_after_render(self):
        self.open_project(project())
        self.page.click('#segData')
        self.edit('value', '12abc')
        self.js('renderAll()')
        self.assertEqual(self.cell('value').get_attribute('aria-invalid'), 'true')

    def test_A27_bulk_edit_skips_filtered_out_rows(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.check('#wsSelectAll')
        self.page.select_option('#filterPillar', 'p2')
        self.page.select_option('#wsBulkField', 'status')
        self.page.select_option('#wsBulkValue', 'At Risk')
        self.page.click('#wsBulkApply')
        self.assertEqual(self.js("S.items.map(i=>i.status)"), ['On Track', 'On Track', 'At Risk'])

    def test_A28_row_moves_are_disabled_while_sorted(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('th[data-col=value] .ws-sort')
        self.assertTrue(self.page.is_disabled('tr[data-id=i1] [data-act=up]'))
        self.assertTrue(self.page.is_disabled('tr[data-id=i1] [data-act=down]'))

    def test_A29_layout_selector_reflects_custom_and_builtin_clears_sort(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('th[data-col=value] .ws-sort')
        self.assertEqual(self.page.input_value('#wsLayout'), 'custom')
        self.page.select_option('#wsLayout', 'all')
        self.assertEqual(self.js('S.workspace.sort.key'), '')

    def test_A30_toast_undo_restores_pillar_position(self):
        self.open_project(project(structure=[
            {'id': 'p1', 'name': 'A', 'workstreams': [{'id': 'w1', 'name': 'a'}]},
            {'id': 'p2', 'name': 'B', 'workstreams': [{'id': 'w3', 'name': 'b'}]},
            {'id': 'p3', 'name': 'C', 'workstreams': [{'id': 'w4', 'name': 'c'}]}], items=[]))
        self.page.click('#segStruct')
        self.page.click('[data-act=pdel][data-p=p1]')
        self.page.click('[data-toast-action=undo]')
        self.assertEqual(self.js('S.structure.map(p=>p.id)'), ['p1', 'p2', 'p3'])

    def test_A32_enter_in_text_cell_keeps_focus_in_grid(self):
        self.open_project(project())
        self.page.click('#segData')
        self.cell('name').fill('Renamed')
        self.page.keyboard.press('Enter')
        self.assertEqual(self.js("document.activeElement.dataset.f"), 'name')
        self.assertEqual(self.js("S.items[0].name"), 'Renamed')

    def test_A33_new_pillar_names_survive_undo_and_reload(self):
        self.open_project(project(items=[]))
        self.page.click('#segStruct')
        self.page.click('#addPillar')
        name = self.js('S.structure.at(-1).name')
        self.assertTrue(name)
        self.js('pushUndo();S.fileName="x";undo()')
        self.assertEqual(self.js('S.structure.at(-1).name'), name)
        self.reload_ok()
        self.assertEqual(self.js('S.structure.at(-1).name'), name)

    def test_A34_fiscal_year_selector_refreshes_after_undo(self):
        self.open_project(project())
        self.page.select_option('#fySelect', '0')
        self.page.click('#undoBtn')
        self.assertEqual(self.page.input_value('#fySelect'), '6')

    def test_A35_blank_outline_resets_project_settings(self):
        self.open_project(project(fyStart=2, colWidths={'name': 400}))
        self.page.click('#brandHome')
        self.page.click('#btnBlank')
        self.assertEqual(self.js('S.fyStart'), 6)
        self.assertEqual(self.js('S.colWidths.name'), 260)

    def test_A36_start_error_clears(self):
        self.page.locator('#projIn').set_input_files({'name': 'bad.json', 'mimeType': 'application/json', 'buffer': b'{bad'})
        self.assertTrue(self.page.inner_text('#err'))
        self.page.click('#btnBlank')
        self.page.click('#brandHome')
        self.assertEqual(self.page.inner_text('#err'), '')


class ExportTests(AppCase):
    """A4: export and presentation."""

    def test_A37_png_handles_very_wide_timelines(self):
        self.open_project(project(items=[item('a', start='1990-01-01', end='1990-02-01'), item('b', start='2150-01-01', end='2150-02-01')]))
        self.page.click('#segRoad')
        with self.page.expect_download(timeout=30000) as info:
            self.page.click('#pngBtn')
        self.assertTrue(info.value.suggested_filename.endswith('.png'))

    def test_A38_png_uses_current_data(self):
        self.open_project(project())
        self.page.click('#segRoad')
        self.page.click('#segData')
        self.edit('name', 'Fresh name for PNG')
        self.js("()=>{window.__png=null;const orig=XMLSerializer.prototype.serializeToString;XMLSerializer.prototype.serializeToString=function(n){const s=orig.call(this,n);window.__png=s;return s;};}")
        with self.page.expect_download():
            self.page.click('#pngBtn')
        self.assertIn('Fresh name for PNG', self.js('window.__png'))

    def test_A39_slide_notes_are_separated(self):
        self.open_project(project())
        for paragraphs in notes_texts(self.pptx()):
            joined = '\n'.join(paragraphs)
            self.assertNotRegex(joined, r'Roadmap Studio \d+\.\d+\.\d+\S')
            self.assertNotRegex(joined, r'Grouping: \w+[A-Z]')

    def test_A40_enter_on_bar_while_presenting_does_not_open_drawer(self):
        self.open_project(project())
        self.page.click('#segRoad')
        self.page.click('#presentBtn')
        self.page.focus('.bar-grab[data-id=i1]')
        self.page.keyboard.press('Enter')
        self.assertFalse(self.js("$('itemDrawer').classList.contains('on')"))

    def test_A41_clicking_segment_label_opens_drilldown(self):
        self.open_project(project())
        self.page.click('#segStack')
        box = self.page.locator('#stackCombinedSvg .stack-segment[data-pillar=p1]').bounding_box()
        self.page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        self.assertTrue(self.js("$('workspaceDrilldown').open"))


if __name__ == '__main__':
    unittest.main(verbosity=1)
