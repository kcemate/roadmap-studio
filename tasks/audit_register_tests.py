"""Initiative register coverage, using synthetic data only."""
import json
import sys
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_presentation_tests import deck_data
from roadmap_feature_tests import seed_state

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/tmp/roadmap-register-tests')

def register_state(count=46):
    state=seed_state()
    template=state['items'][0]
    state['items']=[dict(template,id=f'reg-{i}',name=f'Initiative {i:02d}: distribution network improvements',
        value=100000+i,owner='Portfolio Office',approval='Approved' if i%2 else 'Proposed',
        realizedPct=25,includeInTotals=i!=0) for i in range(count)]
    if count:
        state['items'][0].update(name='Excluded initiative with a value already captured elsewhere',start=None,end=None)
    state['fileName']='Initiative register sample'
    state['asOfDate']='2026-09-09'
    return state

class RegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(exist_ok=True)
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()
    def setUp(self):
        self.ctx=self.browser.new_context(accept_downloads=True,viewport={'width':1440,'height':1000})
        self.page=self.ctx.new_page();self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto((ROOT/'index.html').as_uri());self.load(register_state())
    def tearDown(self):
        self.ctx.close();self.assertEqual(self.errors,[])
    def load(self,state):
        self.page.locator('#projIn').set_input_files({'name':'sample.json','mimeType':'application/json','buffer':json.dumps(state).encode()})
    def open_register(self):
        self.assertEqual(self.page.locator('#segRegister').count(),1,'Register tab missing')
        self.page.click('#segRegister')
    def test_complete_readonly_register_and_totals(self):
        self.page.evaluate("S.filters.q='does not match';S.collapsedPillars={p1:true}")
        self.open_register()
        self.assertEqual(self.page.locator('.register-row').count(),46)
        self.assertEqual(self.page.locator('#registerBody input,#registerBody select').count(),0)
        rows=self.page.locator('.register-row').all_text_contents()
        self.assertTrue(all('Active' in r for r in rows[:23]))
        self.assertIn('Excluded from portfolio totals',' '.join(rows))
        self.assertIn('Unscheduled',' '.join(rows))
        self.assertEqual(self.page.evaluate('initiativeRegisterData().totals.Total'),sum(100000+i for i in range(1,46)))
        self.assertIn('Sep 9, 2026',self.page.inner_text('#registerContext'))
    def test_updates_and_mobile_full_names(self):
        self.open_register()
        name='Full initiative name '+('W'*90)+' <script>window.BAD=1</script>'
        self.page.evaluate("name=>{S.items[1].name=name;S.items[1].value=7654321;renderAll()}",name)
        for width in [1440,390]:
            self.page.set_viewport_size({'width':width,'height':1000})
            row=self.page.locator('.register-row[data-id="reg-1"]')
            self.assertIn(name,row.inner_text());self.assertIn('$7,654,321',row.inner_text())
            self.assertFalse(self.page.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
            self.page.screenshot(path=str(OUT/f'register-{width}.png'),full_page=True)
        self.assertIsNone(self.page.evaluate('window.BAD'))
    def test_pillar_groups_and_scenario_refresh(self):
        state=register_state(6)
        for item in state['items'][3:]:item.update(pillarId='p2',wsId='w3',valueType='Avoidance')
        self.load(state);self.open_register()
        self.assertEqual(self.page.locator('.register-group').count(),2)
        data=self.page.evaluate('initiativeRegisterData()')
        self.assertEqual(sum(g['totals']['Total'] for g in data['groups']),data['totals']['Total'])
        self.page.once('dialog',lambda d:d.accept('Base'));self.page.click('#scenarioSaveBtn')
        first=self.page.evaluate('S.activeScenarioId')
        self.page.once('dialog',lambda d:d.accept('Alternative'));self.page.click('#scenarioSaveBtn')
        self.page.evaluate('S.items[1].value=500000;renderAll()')
        self.assertIn('$500,000',self.page.locator('[data-id="reg-1"].register-row').inner_text())
        self.page.once('dialog',lambda d:d.accept());self.page.evaluate('id=>loadScenario(id)',first)
        self.open_register()
        self.assertIn('$100,001',self.page.locator('[data-id="reg-1"].register-row').inner_text())
        self.assertEqual(self.page.locator('.register-row').count(),6)
    def test_empty_state_and_print_trigger(self):
        self.load(register_state(0));self.open_register()
        self.assertIn('No initiatives yet',self.page.inner_text('#registerBody'))
        self.load(register_state());self.open_register()
        self.page.evaluate('window.print=()=>{window.printRequested=true}')
        self.page.click('#registerPrint')
        self.assertTrue(self.page.evaluate('window.printRequested'))
        self.page.evaluate("window.dispatchEvent(new Event('afterprint'))")
        self.assertFalse(self.page.evaluate("document.body.classList.contains('register-print')"))
    def test_pdf_contains_all_rows_and_repeated_headers(self):
        self.open_register();self.page.evaluate('prepareRegisterPrint()')
        self.page.pdf(path=str(OUT/'register.pdf'),prefer_css_page_size=True,print_background=True)
        import fitz
        with fitz.open(OUT/'register.pdf') as doc:
            self.assertGreater(len(doc),1)
            text='\n'.join(page.get_text() for page in doc)
            for i in range(1,46):self.assertIn(f'Initiative {i:02d}',text)
            self.assertIn('Excluded from portfolio totals',text)
            for page in doc:
                self.assertGreater(page.rect.width,page.rect.height)
                self.assertIn('Initiative',page.get_text())
                self.assertIn('Sep 9, 2026',page.get_text())
                self.assertNotIn('Start from a blank',page.get_text())
    def test_ppt_long_names_are_complete_and_inside_bounds(self):
        state=register_state(3)
        name='Long initiative '+('W'*205)+' final words'
        state['items'][1].update(name=name,owner='Accountable department lead '+('wide owner '*7))
        self.load(state);self.open_register();self.page.select_option('#pptScope','current')
        deck=self.export('register-long.pptx')
        shape=next(s for slide in deck['slides'] for s in slide['shapes'] if s['object_name']=='register-row:reg-1:0')
        self.assertEqual(''.join(shape['text'].split()),''.join(name.split()))
        for slide in deck['slides']:
            for s in slide['shapes']:
                if s['object_name'].startswith('register-row:'):
                    self.assertGreaterEqual(min(s['font_sizes']),16)
                    self.assertLessEqual(s['x']+s['w'],12.8)
                    self.assertLessEqual(s['y']+s['h'],6.83)
    def export(self,name):
        with self.page.expect_download() as download:self.page.click('#pptBtn')
        path=OUT/name;download.value.save_as(path);return deck_data(path)
    def test_ppt_current_and_optional_appendix(self):
        self.open_register();self.page.select_option('#pptScope','current')
        deck=self.export('register.pptx')
        text='\n'.join(slide['text'] for slide in deck['slides'])
        for i in range(1,46):self.assertIn(f'Initiative {i:02d}',text)
        self.assertIn('Excluded from portfolio totals',text)
        self.assertGreater(len(deck['slides']),1)
        self.assertFalse(deck['negative_extents'])
        self.page.select_option('#pptScope','full')
        base=self.export('full-default.pptx')
        self.assertFalse(any('register-row:' in s['object_name'] for slide in base['slides'] for s in slide['shapes']))
        self.page.check('#registerAppendix')
        extended=self.export('full-appendix.pptx')
        self.assertEqual(len(extended['slides']),len(base['slides'])+len(deck['slides']))
        for slide in extended['slides'][len(base['slides']):]:self.assertIn('Initiative Register',slide['text'])

if __name__=='__main__':unittest.main(verbosity=2)
