#!/usr/bin/env python3
"""Regression contracts for audit sections B (consistency), E (coverage gaps) and G (features)."""
import json
import re
import time
import unittest
import zipfile
from pathlib import Path

from audit_fixes_tests import AppCase, item, notes_texts, project, slide_texts, ROOT

MONEY3 = re.compile(r"-?\$(?:\d{3}|\d{2}(?:\.\d)?|\d(?:\.\d{1,2})?)[KMBT]?")
FIXTURE = ROOT / 'tasks' / 'fixtures' / 'saved-by-1.6.7.roadmap.json'


def deck_xml(path):
    with zipfile.ZipFile(path) as z:
        return {name: z.read(name).decode('utf-8', 'ignore') for name in z.namelist() if name.endswith('.xml') or name.endswith('.rels')}


class ConsistencyTests(AppCase):
    """B: one vocabulary, one formatter family, one reporting date, web/deck parity."""

    def test_B1_B2_B5_names(self):
        self.open_project(project())
        tabs = [t.strip() for t in self.page.locator('.seg button').all_inner_texts()]
        self.assertEqual(tabs, ['Structure', 'Initiatives', 'Executive Summary', 'Portfolio Rollup', 'Projection', 'Pillar Contribution', 'Roadmap', 'Initiative Register'])
        self.page.click('#segRegister')
        self.assertNotIn('Category', self.page.inner_text('#registerBody'))
        self.assertIn('Approval', self.page.inner_text('#registerBody'))

    def test_B4_B9_default_names(self):
        self.page.click('#btnBlank')
        self.assertEqual(self.js('S.fileName'), 'Untitled roadmap')
        self.assertEqual(self.js("exportScenarioName()"), 'Working plan')
        self.assertEqual(self.page.locator('#scenarioSelect option').first.inner_text(), 'Working plan')

    def test_B6_B7_projection_card_captions(self):
        self.open_project(project(items=[item('r', benefitKind='recurring', valueBasis='annual', value=120000, start='2026-01-01', end='2027-12-31', confidence=70)]))
        self.page.click('#segProj')
        self.assertIn('Confidence-weighted', self.page.inner_text('#projSavingsNote'))
        self.assertEqual(self.page.text_content('#projExpectedLabel'), 'Unweighted')
        self.assertIn('recurring', self.page.inner_text('#projAnnualizedNote'))
        self.page.uncheck('#projectionConfidenceToggle')
        self.assertEqual(self.page.text_content('#projExpectedLabel'), 'Confidence-weighted')
        self.assertIn('Planned', self.page.inner_text('#projSavingsNote'))

    def test_B8_column_names_match_headers(self):
        self.open_project(project())
        self.page.click('#segData')
        headers = [t.strip() for t in self.page.locator('#initGrid thead th[data-col] .ws-sort span').all_text_contents()]
        self.page.click('#wsColumns summary')
        options = [t.strip() for t in self.page.locator('#wsColumnOptions label').all_text_contents()]
        self.assertEqual(headers, options)

    def test_B12_one_financial_initiative_count(self):
        self.open_project(project(items=[item('a'), item('b', value=''), item('c', includeInTotals=False), item('d', value='', actualValue=5000, actualAsOf='2026-01-31')]))
        self.page.click('#segExec')
        self.assertTrue(self.page.inner_text('#execMeta').startswith('2 financial initiatives'))
        self.assertEqual(self.js('portfolioTotals().FinancialCount'), 2)

    def test_B15_recurring_shows_annual_and_lifetime(self):
        self.open_project(project(items=[item('r', benefitKind='recurring', valueBasis='annual', value=100000, start='2026-01-01', end='2027-12-31')]))
        self.page.click('#segRoad')
        self.page.locator('.bar-grab[data-id=r]').first.hover()
        tip = self.page.inner_text('#tip')
        self.assertIn('$100K/yr', tip)
        self.assertIn('$200K lifetime', tip)
        self.page.click('#segRegister')
        self.assertIn('$200,000', self.page.inner_text('#registerBody'))
        self.assertIn('$100,000 per year', self.page.inner_text('#registerBody'))

    def test_B16_B19_one_money_and_percent_format_on_report_views(self):
        self.open_project(project(items=[item(f'm{i}', value=v, realizedPct=p) for i, (v, p) in enumerate([(1234567, 33.333), (15400000, 0), (999999, 12.5)])], projectionTarget=1250000))
        for tab, selector in [('segExec', '#execStage .value'), ('segRollup', '#rollupStage .value'), ('segProj', '#projStage .value'), ('segStack', '#stackStage .stack-value')]:
            self.page.click('#' + tab)
            for text in self.page.locator(selector).all_inner_texts():
                self.assertRegex(text.strip(), MONEY3, (tab, text))
        self.page.click('#segExec')
        self.assertIn('$1.25M', self.page.inner_text('#execGoalAmount'))
        self.assertIn('$1.25M', self.page.inner_text('#execHeadline'))

    def test_B20_date_ranges_use_one_separator(self):
        self.open_project(project())
        self.page.click('#segRegister')
        body = self.page.inner_text('#registerBody')
        self.assertIn('Jan 1, 2026 – Dec 31, 2026', body)
        self.assertNotIn('2026 - Dec', body)

    def test_B21_fiscal_label_rule_is_shared(self):
        self.open_project(project(fyStart=0))
        self.page.click('#segRoad')
        svg = self.page.inner_text('#tlBox')
        self.assertNotIn('FY2026', svg)
        texts = ' '.join(slide_texts(self.pptx('current')))
        self.assertNotIn('FY2026', texts)
        self.assertIn('2026', texts)

    def test_B23_B36_reporting_date_everywhere(self):
        self.open_project(project())
        for tab, meta in [('segExec', '#execMeta'), ('segRollup', '#rollupMeta'), ('segProj', '#projMeta'), ('segStack', '#stackMeta'), ('segRoad', '#roadMeta'), ('segRegister', '#registerContext')]:
            self.page.click('#' + tab)
            self.assertIn('Jun 30, 2026', self.page.inner_text(meta), tab)
        self.page.click('#segRoad')
        self.assertIn('AS OF JUN 30, 2026', self.page.inner_text('#tlBox'))

    def test_B25_file_names(self):
        self.open_project(project())
        with self.page.expect_download() as info:
            self.page.click('#saveBtn')
        self.assertEqual(info.value.suggested_filename, 'Audit fixture.roadmap.json')
        with self.page.expect_download(timeout=30000) as info:
            self.js("exportPowerPoint('full')")
        self.assertEqual(info.value.suggested_filename, 'Audit fixture — Deck — 2026-06-30.pptx')

    def test_B26_B27_weighting_and_baseline_labels(self):
        self.open_project(project())
        self.page.click('#baselineBtn')
        self.page.click('#segProj')
        self.page.uncheck('#projectionBaselineToggle')
        texts = slide_texts(self.pptx())
        weighted = [i for i, t in enumerate(texts) if 'Confidence-weighted' in t]
        projection = [i for i, t in enumerate(texts) if 'projected by' in t]
        self.assertEqual(weighted, projection)
        notes = ' '.join(' '.join(n) for n in notes_texts(self.pptx()))
        self.assertIn('Baseline comparison off', notes)
        self.assertNotIn('Baseline comparison on', notes)

    def test_B31_G10_export_options_are_remembered(self):
        self.open_project(project())
        self.page.select_option('#pptScope', 'current')
        self.page.click('#deckOptions summary')
        self.page.check('#exportIncludeRegister')
        self.page.check('#exportApplyFilters')
        self.reload_ok()
        self.assertEqual(self.page.input_value('#pptScope'), 'current')
        self.assertTrue(self.js('S.exportPrefs.includeRegister'))
        self.assertTrue(self.js('S.exportPrefs.applyFilters'))
        self.page.click('#segRegister')
        self.assertTrue(self.page.is_checked('#registerAppendix'))

    def test_B33_undo_covers_plan_data_only(self):
        self.open_project(project())
        self.page.click('#segProj')
        before = self.js('S.history.length')
        self.page.fill('#projectionEndDate', '2026-09-30')
        self.page.dispatch_event('#projectionEndDate', 'change')
        self.page.uncheck('#projectionConfidenceToggle')
        self.assertEqual(self.js('S.history.length'), before + 2)
        self.page.click('#segData')
        self.page.select_option('#filterPillar', 'p2')
        self.page.select_option('#tableDensity', 'compact')
        self.assertEqual(self.js('S.history.length'), before + 2)
        self.page.click('#undoBtn')
        self.assertTrue(self.js('S.weightConfidence'))
        self.assertEqual(self.js('S.filters.pillarId'), 'p2')
        self.page.click('#undoBtn')
        self.assertIsNone(self.js('S.projectionEnd'))

    def test_B35_custom_confidence(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.remove_listener('dialog', self._dialog)
        self.page.once('dialog', lambda d: d.accept('55'))
        self.page.select_option('tr[data-id=i1] [data-f=confidence]', 'custom')
        self.assertEqual(self.js("S.items[0].confidence"), 55)
        options = self.page.locator('tr[data-id=i1] [data-f=confidence] option').all_inner_texts()
        self.assertIn('Custom 55%', options)
        self.assertNotIn('Custom 100%', self.page.locator('tr[data-id=i2] [data-f=confidence] option').all_inner_texts())

    def test_B37_review_hides_grid_controls(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('#wsReviewToggle')
        self.assertFalse(self.page.is_visible('#filterSearch'))
        self.assertFalse(self.page.is_visible('#wsBulkApply'))
        self.assertTrue(self.page.is_visible('#wsReviewToggle'))

    def test_B38_B39_baseline_control_is_explicit(self):
        self.open_project(project())
        self.assertFalse(self.page.is_visible('#baselinePill'))
        self.page.click('#baselineBtn')
        self.assertEqual(self.page.get_attribute('#baselinePill', 'aria-label'), 'Clear baseline')
        self.assertEqual(self.page.inner_text('#baselineBtn'), 'Update baseline')

    def test_B40_B41_legacy_status_and_owner_length(self):
        self.open_project(project(items=[{**item('l'), 'status': 'not started', 'approval': ''}]))
        self.assertEqual(self.js("approvalStatus(S.items[0])"), 'Proposed')
        self.page.click('#segData')
        self.assertEqual(self.cell('owner', 'l').get_attribute('maxlength'), '120')

    def test_B42_rollup_empty_state_for_undated_portfolio(self):
        self.open_project(project(items=[item('u', start='', end='')]))
        self.page.click('#segRollup')
        self.assertTrue(self.page.is_visible('#rollupEmpty'))
        self.assertIn('no complete dates', self.page.inner_text('#rollupEmpty'))

    def test_B43_columns_menu_closes(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('#wsColumns summary')
        self.page.keyboard.press('Escape')
        self.assertFalse(self.js("$('wsColumns').open"))
        self.page.click('#wsColumns summary')
        self.page.click('#gridStage h2')
        self.assertFalse(self.js("$('wsColumns').open"))

    def test_B44_B45_B46_B47_keyboard_and_aria(self):
        self.open_project(project())
        self.page.click('#segStruct')
        self.page.focus('[data-act=pdel][data-p=p1]')
        self.page.wait_for_timeout(300)
        self.assertEqual(self.js("getComputedStyle(document.querySelector('.pillar[data-p=p1] .tools')).opacity"), '1')
        self.assertEqual(self.page.get_attribute('[data-act=pdel][data-p=p1]', 'aria-label'), 'Delete pillar Pillar One')
        self.page.click('#segData')
        self.page.click('#wsReviewToggle')
        self.page.focus('[data-review-view=exceptions]')
        self.page.keyboard.press('ArrowRight')
        self.assertEqual(self.js('S.workspace.reviewView'), 'changes')
        self.assertEqual(self.js("document.activeElement.dataset.reviewView"), 'changes')
        self.page.click('#wsReviewToggle')
        self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.click('#drawerClose')
        self.assertIsNone(self.page.get_attribute('#itemDrawer', 'aria-modal'))
        self.page.click('#segProj')
        self.assertIsNone(self.page.get_attribute('#projectionHeadline', 'role'))

    def test_B48_focus_returns_to_roadmap_bar(self):
        self.open_project(project())
        self.page.click('#segRoad')
        self.page.focus('.bar-grab[data-id=i1]')
        self.page.keyboard.press('Enter')
        self.page.click('#drawerDone')
        self.assertEqual(self.js("document.activeElement.dataset.id"), 'i1')


class FeatureTests(AppCase):
    """G: sample, paste, commentary, since last review, statuses, filtered exports, review badge, brand."""

    def test_G1_sample_portfolio(self):
        self.page.click('#btnSample')
        self.assertEqual(self.js('S.fileName'), 'Sample portfolio')
        for tab in ['segExec', 'segRollup', 'segProj', 'segStack', 'segRoad', 'segRegister', 'segData', 'segStruct']:
            self.page.click('#' + tab)
        self.assertGreater(self.js('S.items.length'), 10)
        self.assertTrue(self.js('goalStatus().set'))

    def test_G2_paste_rows(self):
        self.open_project(project(items=[]))
        self.page.click('#segData')
        self.page.click('#pasteRows')
        text = 'Initiative\tPillar\tWorkstream\tStart\tEnd\tValue\tType\tOwner\tStatus\n' \
               'Freight audit\tPillar One\tWS One\t2026-02-01\t2026-08-31\t$250,000\tSavings\tA. Chen\tOn track\n' \
               'New lane program\tLogistics\tCarriers\t3/1/2026\t12/31/2026\t1.2M\tAvoidance\tB. Diaz\tBlocked\n' \
               'Broken row\tPillar One\tWS One\t2026-05-01\t2026-01-01\t10\tSavings\t\t\n'
        self.page.fill('#pasteText', text)
        preview = self.page.inner_text('#pastePreview')
        self.assertIn('2 initiatives ready', preview)
        self.assertIn('Creates 1 pillar: Logistics', preview)
        self.assertIn('Row 4', preview)
        before = self.js('S.history.length')
        self.page.click('#pasteApply')
        self.assertEqual(self.js('S.items.length'), 2)
        self.assertEqual(self.js('S.history.length'), before + 1)
        self.assertEqual(self.js("S.items[1].status"), 'Blocked')
        self.assertEqual(self.js("S.items[1].value"), 1200000)
        self.assertEqual(self.js("pillarOf(S.items[1].pillarId).name"), 'Logistics')
        self.reload_ok()
        self.assertEqual(self.js('S.items.length'), 2)
        self.page.click('#undoBtn') if self.js('S.history.length') else None

    def test_G2_paste_rejects_comma_separated_text(self):
        self.open_project(project(items=[]))
        self.page.click('#segData')
        self.page.click('#pasteRows')
        self.page.fill('#pasteText', 'Initiative,Pillar\nA,B\n')
        self.assertIn('comma-separated', self.page.inner_text('#pastePreview'))
        self.assertTrue(self.page.is_disabled('#pasteApply'))

    def test_G3_commentary_persists_and_reaches_deck(self):
        self.open_project(project())
        self.page.click('#segData')
        self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.fill('#dNextStep', 'Sign the carrier contract by May')
        self.page.fill('#dDecision', 'Approve the second carrier')
        self.page.fill('#dNotes', 'Context for the steering committee.')
        self.page.click('#drawerDone')
        self.reload_ok()
        self.assertEqual(self.js("S.items[0].notes"), 'Context for the steering committee.')
        texts = slide_texts(self.pptx())
        notes = ' '.join(' '.join(n) for n in notes_texts(self.pptx()))
        self.assertTrue(any('decision needed' in t for t in texts))
        self.assertTrue(any('Approve the second carrier' in t for t in texts))
        self.assertIn('Next step: Sign the carrier contract by May', notes)

    def test_G4_since_last_review(self):
        self.open_project(project())
        self.page.click('#baselineBtn')
        self.page.click('#segData')
        self.edit('value', '1500000')
        self.edit('end', '2027-03-31')
        self.page.click('#wsReviewToggle')
        self.page.click('[data-review-view=changes]')
        body = self.page.inner_text('#workspaceReviewBody')
        self.assertIn('+$500K', body)
        self.assertIn('Dates slipped', body)
        self.assertIn('+90 days', body)
        texts = slide_texts(self.pptx())
        self.assertTrue(any(t.startswith('Since ') and '+$500K' in t for t in texts))

    def test_G6_status_rules(self):
        self.open_project(project(items=[item('a'), item('c', status='Cancelled', value=400000), item('b', status='Blocked', value=200000), item('h', status='On Hold', value=100000)]))
        t = self.js('portfolioTotals()')
        self.assertEqual(t['Total'], 1300000)
        self.assertEqual(t['Excluded'], 400000)
        self.page.click('#segData')
        self.page.click('#wsReviewToggle')
        body = self.page.inner_text('#workspaceReviewBody')
        self.assertIn('Needs a decision', body)
        self.assertIn('Blocked', body)
        self.assertIn('On Hold', body)
        self.assertEqual(self.js("projectionFinancialItems().map(i=>i.source.id).includes('c')"), False)

    def test_G11_filtered_export(self):
        self.open_project(project(projectionTarget=5000000))
        self.page.click('#segData')
        self.page.select_option('#filterPillar', 'p2')
        self.js("S.exportPrefs.applyFilters=true")
        texts = slide_texts(self.pptx())
        joined = '\n'.join(texts)
        self.assertNotIn('Item i1', joined)
        self.assertIn('Item i3', joined)
        self.assertNotIn('$5M goal', joined)
        xml = deck_xml(self.pptx())
        self.assertTrue(any('Filtered · Pillar: Pillar Two' in v for k, v in xml.items() if 'slideLayout' in k or 'slideMaster' in k))
        self.assertEqual(self.js('S.items.length'), 3)
        self.assertEqual(self.js('S.projectionTarget'), 5000000)

    def test_G15_review_badge_and_checks(self):
        self.open_project(project(items=[item('a', status='Complete'), item('b', approval='Proposed', actualValue=10000, actualAsOf='2026-05-01'), item('c', start='2026-05-01', end='2026-01-01'.replace('2026-01-01', '2026-06-01'))]))
        self.assertEqual(self.page.get_attribute('#segData', 'data-badge'), str(self.js('exceptionCount()')))
        self.page.click('#segData')
        self.page.click('#wsReviewToggle')
        body = self.page.inner_text('#workspaceReviewBody')
        self.assertIn('Complete, but nothing is realized', body)
        self.assertIn('Proposed, but $10K of actuals are recorded', body)

    def test_brand_settings_reach_masters(self):
        self.open_project(project())
        self.js("S.brand={accent:'#7A1F5C',font:'Georgia',logo:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',logoAspect:1}")
        xml = deck_xml(self.pptx())
        masters = ' '.join(v for k, v in xml.items() if 'slideLayout' in k or 'slideMaster' in k)
        self.assertIn('7A1F5C', masters)
        self.assertIn('typeface="Georgia"', xml['ppt/theme/theme1.xml'])
        with zipfile.ZipFile(self.pptx()) as z:
            self.assertTrue(any(n.startswith('ppt/media/') for n in z.namelist()))
        self.reload_ok()
        self.assertEqual(self.js('S.brand.accent'), '#7A1F5C')


class CoverageTests(AppCase):
    """E23: save-reload boundaries, compatibility, version agreement, scale."""

    def test_save_reload_boundary_values(self):
        items = [item('lo', start='1900-01-01', end='1900-01-01', value=0, realizedPct=0),
                 item('hi', start='2200-12-31', end='2200-12-31', value=1e15, realizedPct=100, confidence=0),
                 item('cents', value=1234.56, realizedPct=33.3333)]
        self.open_project(project(items=items))
        self.reload_ok()
        self.assertEqual(self.js("S.items.map(i=>[isoDate(i.start),i.value,i.realizedPct])"), [['1900-01-01', 0, 0], ['2200-12-31', 1e15, 100], ['2026-01-01', 1234.56, 33.3333]])
        self.page.click('#segData')
        self.page.click('tr[data-id=cents] [data-act=edit]')
        self.page.click('#drawerDone')
        self.assertEqual(self.js("S.items[2].value"), 1234.56)
        self.assertEqual(self.js("S.items[2].realizedPct"), 33.3333)

    def test_limits_round_trip(self):
        structure = [{'id': f'p{i}', 'name': f'P{i}', 'workstreams': [{'id': f'w{i}_{j}', 'name': 'W'} for j in range(200 if i == 0 else 1)]} for i in range(100)]
        items = [item(f'x{n}', pillarId='p0', wsId='w0_0') for n in range(5000)]
        self.open_project(project(structure=structure, items=items))
        self.reload_ok()
        self.assertEqual(self.js('[S.structure.length,S.structure[0].workstreams.length,S.items.length]'), [100, 200, 5000])

    def test_file_saved_by_1_6_7_opens_unchanged(self):
        saved = json.loads(FIXTURE.read_text())
        self.page.locator('#projIn').set_input_files(str(FIXTURE))
        self.page.wait_for_function("()=>S.view==='studio'")
        self.assertEqual(self.js('S.items.length'), len(saved['items']))
        self.assertEqual(self.js('S.scenarios.length'), 1)
        self.assertTrue(self.js('!!S.baseline'))
        self.assertEqual(self.js("S.editDrafts.i3.name"), 'Unsaved name')
        self.assertEqual(self.js("S.items[1].creditedToId"), 'i1')
        t = self.js('portfolioTotals()')
        self.assertEqual(t['Excluded'], 450000)
        self.reload_ok()

    def test_v1_v2_v3_files_load(self):
        for v in (1, 2, 3):
            state = project(fileName=f'Version {v}')
            state['v'] = v
            self.open_project(state)
            self.assertEqual(self.js('S.items.length'), 3)
        legacy = project(fileName='Fraction file', items=[item('f', realizedPct=0.5, confidence=0.7)])
        legacy['percentageUnit'] = 'fraction'
        self.open_project(legacy)
        self.assertEqual(self.js("[S.items[0].realizedPct,S.items[0].confidence]"), [50, 70])

    def test_version_agreement(self):
        version = self.js('APP_VERSION')
        self.assertIn(f'# Roadmap Studio {version}', (ROOT / 'README.md').read_text())
        self.assertIn(f'## {version}', (ROOT / 'docs' / 'releases.md').read_text())
        self.assertIn(f'v{version}', self.page.content())

    def test_scale_smoke_2000_initiatives(self):
        structure = [{'id': f'p{i}', 'name': f'Pillar {i}', 'workstreams': [{'id': f'w{i}_{j}', 'name': f'WS {j}'} for j in range(4)]} for i in range(8)]
        items = [item(f's{n}', pillarId=f'p{n % 8}', wsId=f'w{n % 8}_{n % 4}', start=f'202{5 + n % 3}-0{1 + n % 9}-01', end=f'202{6 + n % 3}-0{1 + n % 9}-28', value=10000 + n, confidence=[100, 70, 40][n % 3]) for n in range(2000)]
        self.open_project(project(structure=structure, items=items))
        for tab in ['segExec', 'segRollup', 'segProj', 'segStack', 'segRoad', 'segData']:
            started = time.monotonic()
            self.page.click('#' + tab)
            self.assertLess(time.monotonic() - started, 4.0, tab)
        started = time.monotonic()
        self.edit('value', '25000', id='s5')
        self.assertLess(time.monotonic() - started, 3.0)


if __name__ == '__main__':
    unittest.main(verbosity=1)
