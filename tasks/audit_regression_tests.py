#!/usr/bin/env python3
"""Regression contracts for the financial and data-safety audit."""
import json
import os
import random
import sys
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
from roadmap_feature_tests import seed_state

ROOT = Path(__file__).resolve().parents[1]

class AuditRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = getattr(cls.pw, os.environ.get('ROADMAP_BROWSER','chromium')).launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop()

    def setUp(self):
        self.ctx = self.browser.new_context(accept_downloads=True,viewport={'width':1440,'height':900})
        self.page = self.ctx.new_page()
        self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto((ROOT/'index.html').as_uri())
        self.load(seed_state())

    def tearDown(self):
        self.ctx.close()
        self.assertEqual(self.errors,[], 'Unexpected application errors')

    def load(self,state):
        self.page.locator('#projIn').set_input_files({'name':'synthetic.roadmap.json','mimeType':'application/json','buffer':json.dumps(state).encode()})
        self.page.wait_for_timeout(50)

    def cell(self,field,id='i1'):
        return self.page.locator(f'tr[data-id="{id}"] [data-f="{field}"]')

    def edit(self,field,value,id='i1'):
        self.cell(field,id).fill(value);self.page.keyboard.press('Tab')

    def test_01_percentage_roundtrip(self):
        self.page.click('#segData');self.edit('value','100000')
        for entry,expected in [('1%',1),('0.5%',0.5),('1.5%',1.5),('0%',0),('100%',100),('0.5',50)]:
            self.edit('realizedPct',entry)
            self.assertEqual(self.page.evaluate('realizedItemValue(S.items[0])'),1000*expected,entry)
            self.page.evaluate('deserializeInto(serializeState());renderAll()')
            self.assertEqual(self.page.evaluate('S.items[0].realizedPct'),expected,entry)

    def test_02_import_is_inert(self):
        s=seed_state();old=s['structure'][0]['id'];new='p" data-audit-canary="yes" onpointerenter="window.__auditCanary=42" data-x="'
        s['structure'][0]['id']=new
        for it in s['items']:
            if it['pillarId']==old:it['pillarId']=new
        self.load(s);self.page.click('#segStruct')
        nodes=self.page.locator('[data-audit-canary=yes]')
        if nodes.count():nodes.first.hover()
        self.assertEqual(self.page.evaluate('window.__auditCanary||0'),0)
        self.assertEqual(nodes.count(),0)
        self.assertEqual(self.page.evaluate('S.items.length'),3)

    def test_03_import_atomic_and_bounded(self):
        before=self.page.evaluate('JSON.stringify(S.items)')
        bad=seed_state();bad['structure'][0]['workstreams']=None
        self.load(bad)
        self.assertEqual(self.page.evaluate('JSON.stringify(S.items)'),before)
        self.assertEqual(self.page.evaluate('S.structure[0].workstreams.length'),2)
        self.assertEqual(self.errors,[])

    def test_04_undated_totals_reconcile(self):
        self.page.click('#segData');self.edit('start','')
        self.assertEqual(self.page.evaluate('portfolioRollupData().totals.Total'),1370000)
        self.assertEqual(self.page.evaluate('portfolioFinancialTotals().Undated'),920000)

    def test_05_actuals_do_not_change_with_confidence(self):
        self.page.evaluate("S.items[0].confidence=40;S.items[0].realizedPct=50;S.weightConfidence=true")
        weighted=self.page.evaluate("projectionTotalsAt(projectionFinancialItems(),utc(2030,0,1)).Realized")
        self.page.evaluate('S.weightConfidence=false')
        self.assertEqual(weighted,self.page.evaluate('projectionTotalsAt(projectionFinancialItems(),utc(2030,0,1)).Realized'))
        self.assertEqual(weighted,820000)

    def test_06_scenario_drafts_and_deletions(self):
        self.page.click('#segData')
        for name in ['Base','Upside']:
            self.page.once('dialog',lambda d,n=name:d.accept(n));self.page.click('#scenarioSaveBtn')
        ids=self.page.evaluate('S.scenarios.map(s=>s.id)')
        self.edit('value','1600000')
        for id in ids:
            self.page.once('dialog',lambda d:d.accept());self.page.select_option('#scenarioSelect',id)
        self.assertEqual(self.page.evaluate('S.items[0].value'),1600000)
        self.page.once('dialog',lambda d:d.accept());self.page.click('tr[data-id=i3] [data-act=del]')
        self.page.once('dialog',lambda d:d.accept());self.page.select_option('#scenarioSelect',ids[0])
        self.assertFalse(self.page.evaluate("S.items.some(i=>i.id==='i3')"))

    def test_07_deletion_undo_is_specific(self):
        self.page.click('#segData');self.page.once('dialog',lambda d:d.accept());self.page.click('tr[data-id=i3] [data-act=del]')
        self.edit('name','New name after deletion')
        self.page.click('[data-toast-action=undo]')
        self.assertTrue(self.page.evaluate("S.items.some(i=>i.id==='i3')"))
        self.assertEqual(self.page.evaluate('S.items[0].name'),'New name after deletion')

    def test_08_baseline_undo(self):
        self.page.click('#baselineBtn');self.assertTrue(self.page.evaluate('!!S.baseline'))
        self.page.click('#undoBtn');self.assertFalse(self.page.evaluate('!!S.baseline'))

    def test_09_incomplete_dates_do_not_crash(self):
        self.page.click('#segData');self.edit('end','');self.page.click('#segRoad')
        self.assertEqual(self.errors,[])
        self.assertEqual(self.page.evaluate('S.items[0].end'),None)
        self.assertEqual(self.page.locator('#tlSvg').count(),1)

    def test_10_invalid_money_is_not_silently_coerced(self):
        self.page.click('#segData');self.edit('value','100abc')
        self.assertEqual(self.page.evaluate('S.items[0].value'),920000)
        self.assertEqual(self.cell('value').get_attribute('aria-invalid'),'true')

    def test_11_uncommitted_draft_survives_reload(self):
        self.page.click('#segData');self.cell('name').fill('Draft before leaving')
        self.page.wait_for_timeout(500)
        self.page.once('dialog',lambda d:d.accept());self.page.reload();self.page.click('#segData')
        self.assertEqual(self.cell('name').input_value(),'Draft before leaving')
        self.page.keyboard.press('Tab')

    def test_12_recorded_actual_asof(self):
        self.page.evaluate("Object.assign(S.items[0],{actualValue:12345,actualAsOf:'2026-08-01',realizedPct:90,confidence:40})")
        self.assertEqual(self.page.evaluate('realizedItemValue(S.items[0],utc(2026,6,31))'),0)
        self.assertEqual(self.page.evaluate('realizedItemValue(S.items[0],utc(2026,7,1))'),12345)

    def test_13_benefit_basis_and_recognition(self):
        values=self.page.evaluate("""()=>{const it={...S.items[0],start:utc(2026,0,1),end:utc(2026,11,31),value:100000,benefitKind:'recurring',valueBasis:'annual',recognitionMethod:'completion'};const fin=projectionFinancialItems([it],{weightConfidence:false})[0];return [itemValue(it),projectedValueAt(fin,utc(2026,5,1)),projectedValueAt(fin,utc(2026,11,31))]}""")
        self.assertEqual(values,[100000,0,100000])

    def test_14_new_financial_fields_roundtrip(self):
        fields={'benefitKind':'recurring','valueBasis':'annual','recognitionMethod':'upfront','actualValue':1234,'actualAsOf':'2026-08-01','creditedToId':'i2','exclusionReason':'Captured in carrier contract'}
        self.page.evaluate('(fields)=>Object.assign(S.items[0],fields)',fields)
        self.page.evaluate('deserializeInto(serializeState())')
        for k,v in fields.items():self.assertEqual(self.page.evaluate('(k)=>S.items[0][k]',k),v)

    def test_15_money_and_percent_invariants(self):
        rng=random.Random(42)
        rows=[{'value':rng.randint(0,10000000),'realizedPct':rng.choice([0,0.1,0.5,1,1.5,50,100]),'valueType':rng.choice(['Savings','Avoidance']),'includeInTotals':rng.choice([True,False])} for _ in range(80)]
        expected=sum(r['value']*r['realizedPct']/100 for r in rows if r['includeInTotals'])
        actual=self.page.evaluate('(rows)=>portfolioFinancialTotals(rows).Realized',rows)
        self.assertAlmostEqual(actual,expected,places=5)

    def test_16_legacy_fraction_import_explicit(self):
        s=seed_state();s['percentageUnit']='fraction'
        for item in s['items']:
            if item['realizedPct']!='':item['realizedPct']/=100
        s['items'][0]['realizedPct']=0.01
        self.load(s)
        self.assertEqual(self.page.evaluate('S.items[0].realizedPct'),1)
        self.page.evaluate('deserializeInto(serializeState())')
        self.assertEqual(self.page.evaluate('S.items[0].realizedPct'),1)

    def test_17_unsupported_or_orphan_import_keeps_project(self):
        for change in ['future','orphan','duplicate']:
            s=seed_state()
            if change=='future':s['v']=999
            elif change=='orphan':s['items'][0]['wsId']='missing'
            else:s['items'][1]['id']='i1'
            self.load(s)
            self.assertEqual(self.page.evaluate('S.items.length'),3)
            self.assertEqual(self.page.evaluate('S.items[1].id'),'i2')
        self.assertEqual(self.errors,[])

    def test_18_undo_redo_preserves_configuration(self):
        self.page.evaluate("pushUndo();S.asOfDate='2026-01-01';S.projectionTarget=5000000;S.workspace={density:'compact'};renderAll();undo()")
        self.assertEqual(self.page.evaluate('S.asOfDate'),'')
        self.page.evaluate('redo()')
        self.assertEqual(self.page.evaluate('S.asOfDate'),'2026-01-01')
        self.assertEqual(self.page.evaluate('S.projectionTarget'),5000000)

    def test_19_actuals_drawer_roundtrip(self):
        self.page.click('#segData');self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.fill('#dActual','12345');self.page.fill('#dActualAsOf','2026-08-01');self.page.click('#drawerDone')
        self.assertEqual(self.page.evaluate('realizedItemValue(S.items[0])'),12345)
        self.page.evaluate('deserializeInto(serializeState())')
        self.assertEqual(self.page.evaluate('S.items[0].actualValue'),12345)

    def test_20_recovery_before_replacement(self):
        self.page.evaluate('autosave()')
        next_state=seed_state();next_state['fileName']='Different project'
        self.load(next_state)
        self.assertGreaterEqual(self.page.evaluate('localRecoveryProjects().length'),1)
        self.page.once('dialog',lambda d:d.accept())
        self.page.evaluate('restoreRecovery(0)')
        self.assertEqual(self.page.evaluate('S.fileName'),'Seed roadmap')

    def test_21_long_name_and_owner_collapse(self):
        self.page.click('#segRoad');self.page.click('#groupOwner')
        before=self.page.locator('#tlSvg').get_attribute('height')
        self.page.locator('.pillar-toggle').first.click()
        self.assertLess(int(self.page.locator('#tlSvg').get_attribute('height')),int(before))

    def test_22_drawer_accessible_focus(self):
        self.page.click('#segData');self.page.click('tr[data-id=i1] [data-act=edit]')
        self.assertEqual(self.page.locator('#itemDrawer').get_attribute('aria-modal'),'true')
        missing=self.page.evaluate("[...document.querySelectorAll('#drawerBody input,#drawerBody select')].filter(e=>!e.getAttribute('aria-label')&&!e.labels?.length).map(e=>e.id)")
        self.assertEqual(missing,[])
        self.page.locator('#drawerDone').focus();self.page.keyboard.press('Tab')
        self.assertTrue(self.page.evaluate("!!document.activeElement.closest('#itemDrawer')"))

    def test_23_draft_drawer_reopens(self):
        self.page.click('#segData');self.page.click('tr[data-id=i1] [data-act=edit]');self.page.fill('#dName','Protected drawer draft')
        self.page.wait_for_timeout(500);self.page.once('dialog',lambda d:d.accept());self.page.reload()
        self.assertEqual(self.page.locator('#dName').input_value(),'Protected drawer draft')

    def test_24_phase_and_benefit_date_validation(self):
        self.page.click('#segData');self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.fill('#dEnd','2025-01-01');self.page.click('#drawerDone')
        self.assertEqual(self.page.locator('#dEnd').get_attribute('aria-invalid'),'true')
        self.assertEqual(self.page.evaluate('isoDate(S.items[0].end)'),'2026-12-20')

    def test_25_actuals_percentage_is_derived(self):
        self.page.evaluate("Object.assign(S.items[0],{value:100000,actualValue:25000,actualAsOf:'2026-01-01',realizedPct:90});renderAll()")
        self.page.click('#segData')
        self.assertTrue(self.cell('realizedPct').is_disabled())
        self.assertEqual(self.cell('realizedPct').input_value(),'25%')
        self.assertIn('actual',self.cell('realizedPct').get_attribute('title').lower())

    def test_26_import_rejects_reversed_dates(self):
        state=seed_state();state['items'][0]['end']='2025-01-01'
        self.load(state)
        self.assertEqual(self.page.evaluate('isoDate(S.items[0].end)'),'2026-12-20')

    def test_27_legacy_confidence_names(self):
        state=seed_state();state['items'][0]['confidence']='Low'
        self.load(state)
        self.assertEqual(self.page.evaluate('S.items[0].confidence'),40)

    def test_28_calendar_year_recurring_value(self):
        values=self.page.evaluate("""() => ['2024','2025','2026'].map(year=>{
          const it={value:120000,benefitKind:'recurring',valueBasis:'annual',start:year+'-01-01',end:year+'-12-31'};
          return [itemValue(it),annualizedValue(it)];
        })""")
        self.assertEqual(values,[[120000,120000]]*3)

    def test_29_wide_letters_stay_inside_timeline_bounds(self):
        self.page.evaluate("S.structure[0].name='M'.repeat(240);S.items[0].name='M'.repeat(240);S.items[0].start=utc(2026,11,19);renderAll();setTab('road')")
        bounds=self.page.evaluate("""() => {
          const label=document.querySelector('.bar-label[data-id=i1]'),bar=document.querySelector('rect.bar-grab[data-id=i1]');
          const a=label.getBBox(),b=bar.getBBox(),name=document.querySelector('.pillar-toggle text:nth-of-type(2)').getBBox();
          return {labelRight:a.x+a.width,barRight:b.x+b.width,nameRight:name.x+name.width,width:Number(document.querySelector('#tlSvg').getAttribute('width'))};
        }""")
        self.assertLessEqual(bounds['labelRight'],bounds['barRight'])
        self.assertLessEqual(bounds['nameRight'],bounds['width'])

    def test_30_optional_costs_and_net_benefit(self):
        self.page.click('#segData');self.page.click('tr[data-id=i1] [data-act=edit]')
        self.page.fill('#dValue','100000');self.page.fill('#dCost','12000');self.page.click('#drawerDone')
        self.page.evaluate('deserializeInto(serializeState())')
        self.assertEqual(self.page.evaluate('S.items[0].cost'),12000)
        self.assertEqual(self.page.evaluate('netBenefit(S.items[0])'),88000)
        self.assertEqual(self.page.evaluate('itemValue(S.items[0])'),100000)

    def test_31_drawer_preserves_custom_confidence(self):
        self.page.evaluate('S.items[0].confidence=55;renderAll()')
        self.page.click('#segData');self.page.click('tr[data-id=i1] [data-act=edit]');self.page.click('#drawerDone')
        self.assertEqual(self.page.evaluate('S.items[0].confidence'),55)

    def test_32_accessible_tabs_and_baseline_control(self):
        self.assertEqual(self.page.locator('#segData').get_attribute('aria-controls'),'gridStage')
        self.assertEqual(self.page.locator('#gridStage').get_attribute('role'),'tabpanel')
        self.page.locator('#segStruct').focus();self.page.keyboard.press('ArrowRight')
        self.assertEqual(self.page.evaluate('S.tab'),'data')
        self.assertEqual(self.page.locator('#baselinePill').evaluate('(el)=>el.tagName'),'BUTTON')

    def test_33_project_name_is_undoable(self):
        self.page.fill('#projectName','New report name');self.page.keyboard.press('Tab')
        self.page.evaluate('undo()')
        self.assertEqual(self.page.evaluate('S.fileName'),'Seed roadmap')

    def test_34_invalid_drawer_draft_import_is_atomic(self):
        state=seed_state();state['fileName']='Must not replace current project'
        state['drawerDraft']={'id':'i1','values':{},'phases':[None]}
        self.load(state)
        self.assertEqual(self.page.evaluate('S.fileName'),'Seed roadmap')

    def enter_stretch(self, value):
        self.assertEqual(self.page.locator('#execStretchInput').count(),1,'Stretch goal field is missing')
        self.page.fill('#execStretchInput',value);self.page.keyboard.press('Tab')

    def test_35_editable_stretch_fields_and_measurements(self):
        self.page.evaluate("S.projectionTarget=1500000;S.asOfDate='2030-01-01';setTab('exec')")
        self.enter_stretch('2M')
        self.assertEqual(self.page.evaluate('S.stretchGoal'),2000000)
        self.assertEqual(self.page.input_value('#execStretchInput'),'$2,000,000')
        self.assertEqual(self.page.inner_text('#execStretchAmount'),'$2M')
        self.assertEqual(self.page.inner_text('#execStretchProgress'),'68.5% identified · 41% realized')
        self.assertEqual(self.page.inner_text('#execGoalProgress'),'91.3% identified · 54.7% realized')
        self.assertEqual(self.page.get_attribute('#execStretchMarker','data-goal'),'2000000')
        for tab, goal_id, stretch_id in [('exec','execGoalInput','execStretchInput'),('proj','projectionTarget','projectionStretchGoal')]:
            self.page.evaluate('tab=>setTab(tab)',tab)
            a=self.page.locator('#'+goal_id).bounding_box();b=self.page.locator('#'+stretch_id).bounding_box()
            self.assertGreaterEqual(b['y'],a['y']+a['height'])
            self.assertAlmostEqual(a['x'],b['x'],delta=1)
        self.page.fill('#projectionStretchGoal','2.5M');self.page.keyboard.press('Tab')
        self.page.evaluate("setTab('exec')")
        self.assertEqual(self.page.inner_text('#execStretchAmount'),'$2.5M')

    def test_36_stretch_save_open_autosave_and_undo(self):
        self.page.evaluate("setTab('exec')");self.enter_stretch('2M')
        self.page.evaluate('undo()');self.assertEqual(self.page.evaluate('S.stretchGoal'),'')
        self.page.evaluate('redo()');self.assertEqual(self.page.evaluate('S.stretchGoal'),2000000)
        with self.page.expect_download() as dl:
            self.page.click('#saveBtn')
        saved=json.loads(Path(dl.value.path()).read_text())
        self.assertEqual(saved['stretchGoal'],2000000)
        self.load(saved);self.assertEqual(self.page.evaluate('S.stretchGoal'),2000000)
        self.page.evaluate('autosave()');self.page.reload()
        self.assertEqual(self.page.evaluate('S.stretchGoal'),2000000)

    def test_37_stretch_scenarios_baseline_and_legacy(self):
        self.page.evaluate("setTab('exec')");self.enter_stretch('2M')
        self.page.once('dialog',lambda d:d.accept('Base'));self.page.click('#scenarioSaveBtn')
        first=self.page.evaluate('S.activeScenarioId')
        self.page.once('dialog',lambda d:d.accept('Upside'));self.page.click('#scenarioSaveBtn')
        second=self.page.evaluate('S.activeScenarioId');self.enter_stretch('3M')
        for scenario,expected in [(first,2000000),(second,3000000),(first,2000000)]:
            self.page.once('dialog',lambda d:d.accept());self.page.evaluate('id=>loadScenario(id)',scenario)
            self.assertEqual(self.page.evaluate('S.stretchGoal'),expected)
        self.page.evaluate('setBaseline();deserializeInto(serializeState())')
        self.assertEqual(self.page.evaluate('S.baseline.stretchGoal'),2000000)
        self.assertEqual(self.page.evaluate('S.scenarios.map(sc=>sc.payload.stretchGoal)'),[2000000,3000000])
        self.load(seed_state());self.assertEqual(self.page.evaluate('S.stretchGoal'),'')
        self.page.evaluate("setTab('exec')")
        self.assertEqual(self.page.locator('#execStretchMarker').count(),0)

    def test_38_stretch_invalid_and_clear(self):
        self.page.evaluate("setTab('exec')");self.enter_stretch('2M')
        for invalid in ['-1','bad','1e99']:
            self.enter_stretch(invalid)
            self.assertEqual(self.page.get_attribute('#execStretchInput','aria-invalid'),'true')
            self.assertEqual(self.page.evaluate('S.stretchGoal'),2000000)
            state=seed_state();state['stretchGoal']=invalid;state['fileName']='Invalid import'
            self.load(state);self.assertEqual(self.page.evaluate('S.stretchGoal'),2000000)
            self.assertEqual(self.page.evaluate('S.fileName'),'Seed roadmap')
        self.enter_stretch('')
        self.assertEqual(self.page.evaluate('S.stretchGoal'),'')
        self.assertIsNone(self.page.get_attribute('#execStretchInput','aria-invalid'))
        self.assertEqual(self.page.locator('#execStretchMarker').count(),0)
        self.assertFalse(self.page.locator('#execStretchMetric').is_visible())
        self.page.evaluate("S.projectionTarget=4000000;renderExecutiveSummary()")
        self.assertEqual(self.page.evaluate('executiveStretchGoalValue()'),'')

    def test_39_stretch_independent_of_goal_and_responsive(self):
        self.page.evaluate("S.projectionTarget=1500000;setTab('exec')");self.enter_stretch('1500001')
        for width in [1440,390]:
            self.page.set_viewport_size({'width':width,'height':900});self.page.evaluate('renderExecutiveSummary()')
            geometry=self.page.evaluate("""() => {
                const svg=$('execTrackerSvg'),a=$('execGoalMarker').querySelector('text').getBBox(),b=$('execStretchMarker').querySelector('text').getBBox();
                return {overflow:document.documentElement.scrollWidth>innerWidth+1,w:svg.viewBox.baseVal.width,
                  boxes:[a,b].map(r=>({x:r.x,y:r.y,w:r.width,h:r.height}))};
            }""")
            self.assertFalse(geometry['overflow'])
            a,b=geometry['boxes']
            for box in [a,b]:self.assertTrue(box['x']>=0 and box['x']+box['w']<=geometry['w'])
            self.assertLessEqual(a['y']+a['h'],b['y'])
        self.page.fill('#execGoalInput','3M');self.page.keyboard.press('Tab')
        self.assertEqual(self.page.evaluate('S.stretchGoal'),1500001)
        self.assertEqual(self.page.evaluate('executiveGoalValue()'),3000000)

    def test_40_stretch_goal_label_preserves_entered_precision(self):
        self.page.evaluate("setTab('exec')");self.enter_stretch('1.75B')
        self.assertEqual(self.page.inner_text('#execStretchAmount'),'$1.75B')
        self.assertIn('$1.75B',self.page.text_content('#execStretchMarker'))
        self.enter_stretch('1500001')
        self.assertEqual(self.page.inner_text('#execStretchAmount'),'$1,500,001')

    def test_41_active_category_labels_and_legacy_roundtrip(self):
        self.page.click('#segData')
        self.assertEqual(self.cell('approval').locator('option').all_text_contents(),['Active','Proposed'])
        before=self.page.evaluate('portfolioFinancialTotals()')
        self.cell('approval').select_option(label='Active')
        self.page.evaluate('deserializeInto(serializeState());renderAll()')
        self.assertEqual(self.page.evaluate('portfolioFinancialTotals()'),before)
        self.assertEqual(self.page.evaluate('approvalStatus(S.items[0])'),'Approved')
        self.page.select_option('#wsBulkField','approval')
        self.assertEqual(self.page.locator('#wsBulkValue option').all_text_contents(),['Active','Proposed'])
        for tab,stage in [('exec','#execStage'),('rollup','#rollupStage')]:
            self.page.evaluate('tab=>setTab(tab)',tab)
            text=self.page.text_content(stage)
            self.assertIn('Active',text)
            self.assertNotRegex(text,r'(?i)\bapproved\b')
        self.assertIn('Active',self.page.text_content('#rollupSvg title'))

    def test_42_active_import_alias_preserves_explicit_classification(self):
        state=seed_state();state['items'][0]['approval']='Active';state['items'][0]['status']='Not Started'
        self.load(state)
        self.assertEqual(self.page.evaluate('approvalStatus(S.items[0])'),'Approved')
        self.assertEqual(self.page.evaluate('portfolioFinancialTotals().Approved'),1370000)
        self.page.evaluate('deserializeInto(serializeState());renderAll()')
        self.assertEqual(self.page.evaluate('approvalStatus(S.items[0])'),'Approved')

    def test_43_active_drawer_and_financial_drilldown(self):
        self.page.evaluate("openDrawer('i1')")
        self.assertEqual(self.page.locator('#dApproval option').all_text_contents(),['Active','Proposed'])
        self.page.select_option('#dApproval',label='Proposed')
        self.page.evaluate('commitDrawer();closeDrawer(true)')
        self.assertEqual(self.page.evaluate('approvalStatus(S.items[0])'),'Proposed')
        self.page.evaluate("openDrawer('i1')")
        self.page.select_option('#dApproval',label='Active')
        self.page.evaluate("commitDrawer();closeDrawer(true);setTab('exec')")
        self.page.click('#execApproved')
        self.assertEqual(self.page.inner_text('#workspaceDrilldownTitle'),'Active value')
        self.assertIn('Active',self.page.inner_text('#workspaceDrilldownBody'))
        self.assertNotIn('Approved',self.page.inner_text('#workspaceDrilldownBody'))
        self.assertEqual(self.page.evaluate('portfolioFinancialTotals().Approved'),1370000)

class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.records=[]
    def addSuccess(self,test):super().addSuccess(test);self.records.append({'test':test.id(),'status':'Passed'})
    def addFailure(self,test,error):super().addFailure(test,error);self.records.append({'test':test.id(),'status':'Failed','error':self._exc_info_to_string(error,test)})
    def addError(self,test,error):super().addError(test,error);self.records.append({'test':test.id(),'status':'Failed','error':self._exc_info_to_string(error,test)})

if __name__=='__main__':
    program=unittest.main(verbosity=2,exit=False,testRunner=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult))
    browser=os.environ.get('ROADMAP_BROWSER','chromium')
    report=json.dumps({'browser':browser,'results':program.result.records,'passed':sum(r['status']=='Passed' for r in program.result.records),'failed':sum(r['status']=='Failed' for r in program.result.records)},indent=2)+'\n'
    (ROOT/'tasks'/'audit-regression-results.json').write_text(report)
    (ROOT/'tasks'/f'audit-regression-{browser}-results.json').write_text(report)
    sys.exit(not program.result.wasSuccessful())
