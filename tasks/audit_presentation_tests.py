#!/usr/bin/env python3
"""Focused PowerPoint regressions for the approved executive presentation contract."""
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "index.html"
from test_paths import artifact_dir
OUT = artifact_dir("presentation")
EMU = 914400
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
CORE_LINE_COLORS = {"188038", "2563EB"}
MONEY_PERCENT = re.compile(r"\$[^\n]*[·|][^\n]*%")
# Three significant figures with the unit promoted after rounding (audit A21, F2.9).
MONEY3 = re.compile(r"-?\$(?:\d{3}|\d{2}(?:\.\d)?|\d(?:\.\d{1,2})?)[KMBT]?")


def initiative(item_id, pillar_id, workstream_id, name, start, end, value_type,
               value, approval="Approved", realized=25):
    return {
        "id": item_id,
        "pillarId": pillar_id,
        "wsId": workstream_id,
        "name": name,
        "start": start,
        "end": end,
        "valueType": value_type,
        "value": value,
        "realizedPct": realized,
        "confidence": 100,
        "includeInTotals": True,
        "milestone": start == end,
        "status": "On Track" if approval == "Approved" else "Not Started",
        "approval": approval,
        "owner": "Portfolio Office",
    }


def base_state(name, structure, items, target=0):
    return {
        "v": 2,
        "savedAt": 1780000000000,
        "fileName": name,
        "fyStart": 6,
        "structure": structure,
        "items": items,
        "projectionTarget": target,
        "projectionEnd": "2027-12-31",
        "roadmapGroup": "structure",
        "collapsedPillars": {},
        "asOfDate": "2026-09-04",
        "weightConfidence": False,
        "showBaseline": False,
        "projectionShowRealized": False,
        "baseline": None,
        "scenarios": [],
    }


def sparse_state():
    structure = [{
        "id": "sparse-pillar",
        "name": "Sparse Portfolio",
        "workstreams": [{"id": "sparse-workstream", "name": "Short Commitments"}],
    }]
    items = [
        initiative("short-1", "sparse-pillar", "sparse-workstream",
                   "Contract reset with complete original wording", "2026-09-01", "2026-09-02",
                   "Savings", 125000, "Approved", 40),
        initiative("short-2", "sparse-pillar", "sparse-workstream",
                   "Demand hedge with complete original wording", "2026-09-03", "2026-09-03",
                   "Avoidance", 85000, "Proposed", 0),
        initiative("long-1", "sparse-pillar", "sparse-workstream",
                   "Supplier collaboration program preserving the complete original initiative name",
                   "2026-10-01", "2027-06-30", "Savings", 300000, "Approved", 20),
    ]
    return base_state("Sparse presentation contract", structure, items, target=3000000)


def four_pillar_state():
    names = ["Procurement", "Operations", "Technology", "Commercial"]
    structure = []
    items = []
    for index, name in enumerate(names, start=1):
        pillar_id, workstream_id = f"four-p{index}", f"four-w{index}"
        structure.append({
            "id": pillar_id,
            "name": name,
            "workstreams": [{"id": workstream_id, "name": f"{name} delivery"}],
        })
        items.extend([
            initiative(f"four-a{index}", pillar_id, workstream_id, f"{name} approved initiative",
                       "2026-07-01", "2027-03-31", "Savings", 100000 * index,
                       "Approved", 30),
            initiative(f"four-proposed{index}", pillar_id, workstream_id, f"{name} proposed initiative",
                       "2027-04-01", "2027-09-30", "Avoidance", 50000 * index,
                       "Proposed", 0),
        ])
    state = base_state("Four pillar presentation contract", structure, items, target=5000000)
    state["stretchGoal"] = 7500000
    return state


def many_pillar_state():
    structure = []
    items = []
    for index in range(1, 17):
        pillar_id, workstream_id = f"many-p{index:02d}", f"many-w{index:02d}"
        name = f"Contribution Pillar {index:02d}"
        structure.append({
            "id": pillar_id,
            "name": name,
            "workstreams": [{"id": workstream_id, "name": f"Workstream {index:02d}"}],
        })
        items.extend([
            initiative(f"many-s{index:02d}", pillar_id, workstream_id, f"Savings item {index:02d}",
                       "2026-07-01", "2027-03-31", "Savings", (18-index) * 100000,
                       "Approved", 10),
            initiative(f"many-a{index:02d}", pillar_id, workstream_id, f"Avoidance item {index:02d}",
                       "2027-04-01", "2027-09-30", "Avoidance", (18-index) * 25000,
                       "Proposed", 0),
        ])
    return base_state("Many pillar presentation contract", structure, items, target=50000000)


def dense_state():
    structure = [{
        "id": "dense-pillar",
        "name": "Dense Delivery Portfolio",
        "workstreams": [{"id": "dense-workstream", "name": "Sequenced Delivery"}],
    }]
    items = []
    for index in range(1, 29):
        items.append(initiative(
            f"dense-{index:02d}", "dense-pillar", "dense-workstream",
            f"Dense initiative {index:02d} complete reference name",
            "2026-07-01", "2027-12-31", "Savings" if index % 2 else "Avoidance",
            40000 + index * 1000, "Approved" if index % 3 else "Proposed", 15,
        ))
    return base_state("Dense presentation contract", structure, items, target=10000000)


def slide_names(path):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist()
                 if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
    return sorted(names, key=lambda name: int(Path(name).stem.replace("slide", "")))


def rgb_values(node, path):
    return [value.attrib["val"].upper() for value in node.findall(path, NS)
            if value.attrib.get("val")]


def deck_data(path):
    slides = []
    negative_extents = []
    autofit = []
    with zipfile.ZipFile(path) as archive:
        for slide_index, name in enumerate(slide_names(path), start=1):
            raw = archive.read(name).decode("utf-8", "ignore")
            root = ET.fromstring(raw)
            shapes = []
            for shape in root.findall(".//p:sp", NS):
                text = "".join(node.text or "" for node in shape.findall(".//a:t", NS))
                xfrm = shape.find("./p:spPr/a:xfrm", NS)
                record = {
                    "text": text,
                    "object_name": "",
                    "x": None,
                    "y": None,
                    "w": None,
                    "h": None,
                    "font_sizes": [int(node.attrib["sz"]) / 100 for node in shape.findall(".//*[@sz]", NS)
                                   if node.attrib.get("sz", "").isdigit()],
                    "text_colors": rgb_values(shape, ".//p:txBody//a:solidFill/a:srgbClr"),
                    "fill_colors": rgb_values(shape, "./p:spPr/a:solidFill/a:srgbClr"),
                    "line_colors": rgb_values(shape, "./p:spPr/a:ln/a:solidFill/a:srgbClr"),
                    "geometry": "",
                }
                properties = shape.find("./p:nvSpPr/p:cNvPr", NS)
                if properties is not None:
                    record["object_name"] = properties.attrib.get("name", "")
                geometry = shape.find("./p:spPr/a:prstGeom", NS)
                if geometry is not None:
                    record["geometry"] = geometry.attrib.get("prst", "")
                elif shape.find("./p:spPr/a:custGeom", NS) is not None:
                    record["geometry"] = "custom"
                if xfrm is not None:
                    off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
                    if off is not None and ext is not None:
                        record.update({
                            "x": int(off.attrib["x"]) / EMU,
                            "y": int(off.attrib["y"]) / EMU,
                            "w": int(ext.attrib["cx"]) / EMU,
                            "h": int(ext.attrib["cy"]) / EMU,
                        })
                shapes.append(record)
            slides.append({"index": slide_index, "name": name, "raw": raw, "shapes": shapes,
                           "text": "\n".join(shape["text"] for shape in shapes if shape["text"])})
            negative_extents.extend(re.findall(r'\b(?:cx|cy)="-\d+', raw))
            if "<a:normAutofit" in raw:
                autofit.append(name)
        notes = "\n".join(
            archive.read(name).decode("utf-8", "ignore")
            for name in archive.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        )
    return {"path": path, "slides": slides, "notes": notes,
            "negative_extents": negative_extents, "autofit": autofit}


def new_page(browser, state):
    context = browser.new_context(accept_downloads=True, viewport={"width": 1440, "height": 900})
    context.add_init_script("localStorage.clear();")
    context.add_init_script(
        f"localStorage.setItem('roadmapStudio.v1', {json.dumps(json.dumps(state))});"
    )
    page = context.new_page()
    page.goto(APP.as_uri(), wait_until="domcontentloaded")
    page.evaluate("state => { deserializeInto(state); enterStudio(); renderAll(); }", state)
    return context, page


def export_deck(browser, state, filename, scope="full", tab="road"):
    context, page = new_page(browser, state)
    try:
        page.evaluate("tab => setTab(tab)", tab)
        page.evaluate("scope => { S.exportScope=scope; const el=document.querySelector('#pptScope'); if(el) el.value=scope; }", scope)
        before = page.evaluate("JSON.stringify({...serializeState(), savedAt: 0})")
        with page.expect_download(timeout=30000) as download_info:
            page.click("#pptBtn")
        path = OUT / filename
        download_info.value.save_as(path)
        assert page.evaluate("JSON.stringify({...serializeState(), savedAt: 0})") == before, (
            "PowerPoint export changed the saved project state"
        )
        deck = deck_data(path)
        page.evaluate("setTab('exec')")
        deck['stretch_axis_labels'] = page.evaluate(
            "Array.from({length:5},(_,i)=>fmtGoalMoney(executiveStretchGoalValue()*i/4))")
        deck['executive_axis'] = page.evaluate("""() => {
            const maximum=niceProjectionMax(Math.max(executiveSummaryData().totals.Total,
                executiveGoalValue(),executiveStretchGoalValue()||0));
            const track=document.querySelector('#execBarClip rect');
            const ratio=id=>{
                const marker=document.querySelector(`#${id} line`);
                return track&&marker?(Number(marker.getAttribute('x1'))-Number(track.getAttribute('x')))/Number(track.getAttribute('width')):null;
            };
            return {maximum,goalRatio:ratio('execGoalMarker'),stretchRatio:ratio('execStretchMarker'),
                labels:Array.from({length:5},(_,i)=>fmtGoalMoney(maximum*i/4))};
        }""")
        return deck
    finally:
        context.close()


def find_slide(deck, *needles):
    matches = [slide for slide in deck["slides"] if all(needle.lower() in slide["text"].lower() for needle in needles)]
    assert len(matches) == 1, f"expected one slide containing {needles}, found {[slide['index'] for slide in matches]}"
    return matches[0]


def slides_with_exact_text(deck, text):
    return [slide for slide in deck["slides"] if text_shapes(slide, text, exact=True)]


def slides_with_title_prefix(deck, text):
    return [slide for slide in deck["slides"] if any(
        shape["object_name"] == "slide-title" and shape["text"].startswith(text)
        for shape in slide["shapes"]
    )]


def normalized_text(value):
    return " ".join(value.split())


def text_shapes(slide, needle, exact=False):
    if exact:
        return [shape for shape in slide["shapes"] if shape["text"].strip().lower() == needle.lower()]
    return [shape for shape in slide["shapes"] if needle.lower() in shape["text"].lower()]


def min_font(shape):
    return min(shape["font_sizes"]) if shape["font_sizes"] else 0


def is_neutral(color):
    if len(color) != 6:
        return False
    channels = [int(color[index:index + 2], 16) for index in (0, 2, 4)]
    return max(channels) - min(channels) <= 16


def collapsed_text(value):
    return re.sub(r"\s+", "", value)


def check_executive_contract(deck):
    slide = exec_slide(deck)
    headline = [shape for shape in slide["shapes"]
                if "opportun" in shape["text"].lower() and max(shape["font_sizes"] or [0]) >= 26]
    assert headline, "executive headline does not explicitly frame the portfolio as opportunity"
    assert all("achiev" not in shape["text"].lower() for shape in headline), headline
    labels = {
        "opportunity": text_shapes(slide, "opportunity"),
        "realized": text_shapes(slide, "realized"),
    }
    for label, shapes in labels.items():
        large = [shape for shape in shapes if shape["w"] and shape["w"] >= 3.5]
        assert large, f"executive {label} block is not retained as a large central block"
    metrics = [shape for shape in slide["shapes"]
               if "%" in shape["text"] and max(shape["font_sizes"] or [0]) >= 40]
    assert len(metrics) >= 2, f"expected two prominent executive metrics, found {[(s['text'], s['font_sizes']) for s in metrics]}"


def check_executive_stretch_goal(deck, goal, total, stretch, expected_labels, expected_percentages, stretch_percentages):
    slide = exec_slide(deck)
    shapes = {shape["object_name"]: shape for shape in slide["shapes"]}
    scale = stretch or deck['executive_axis']['maximum']
    labels = []
    kinds = ("goal", "stretch") if stretch else ("goal",)
    for kind, value, label in zip(kinds, (goal, stretch), expected_labels):
        marker = shapes.get(f"executive-{kind}-marker")
        if value <= scale:
            assert marker is not None, f"missing {kind} marker for entered goal {goal}"
            assert abs(marker["x"] - (.76 + value / scale * 11.82)) < .001, marker
        else:
            assert marker is None, f"off-scale {kind} marker was drawn"
        amount = shapes.get(f"executive-{kind}-amount")
        assert amount and amount["text"] == label, (kind, amount, label)
        caption = shapes.get(f"executive-{kind}-label")
        expected_caption = "STRETCH GOAL" if kind == "stretch" else ("GOAL" if value <= scale else "GOAL (OFF SCALE)")
        assert caption and caption["text"] == expected_caption, caption
        for shape in (amount, caption):
            assert min_font(shape) >= 14, shape
            assert .55 <= shape["x"] and shape["x"] + shape["w"] <= 12.8, shape
            labels.append(shape)
    for index, left in enumerate(labels):
        for right in labels[index + 1:]:
            dx = min(left["x"] + left["w"], right["x"] + right["w"]) - max(left["x"], right["x"])
            dy = min(left["y"] + left["h"], right["y"] + right["h"]) - max(left["y"], right["y"])
            assert dx < .001 or dy < .001, f"goal labels overlap: {left['text']} and {right['text']}"
    metrics = [shape["text"] for shape in slide["shapes"]
               if "%" in shape["text"] and max(shape["font_sizes"] or [0]) >= 40]
    assert metrics == expected_percentages, f"original-goal percentages changed: {metrics}"
    if stretch:
        for kind, expected in zip(("identified", "realized"), stretch_percentages):
            metric = shapes.get(f"executive-stretch-{kind}")
            assert metric and metric["text"] == f"{expected} of stretch goal", metric
        assert "Stretch goal entered independently" in deck["notes"]
    else:
        assert not any(name.startswith('executive-stretch-') for name in shapes), "cleared stretch still exported"
    assert "120% of the entered goal" not in deck["notes"]
    assert "STRETCH (+20%)" not in slide["text"]


def check_executive_measurement_axis(deck, total, expected_max=None, stretch=None, goal=None):
    slide = exec_slide(deck)
    shapes = {shape['object_name']: shape for shape in slide['shapes']}
    web = deck['executive_axis']
    if expected_max is not None:
        assert web['maximum'] == expected_max, web
    scale = stretch or web['maximum']
    track = shapes.get('executive-bar-track')
    assert track, 'missing measurement bar track'
    labels = []
    for i, label in enumerate(deck['stretch_axis_labels'] if stretch else web['labels']):
        tick = shapes.get(f'executive-axis-tick:{i}')
        caption = shapes.get(f'executive-axis-label:{i}')
        assert tick and abs(tick['x']-(track['x']+track['w']*i/4)) < .001, tick
        assert caption and caption['text'] == label, (caption, label)
        assert min_font(caption) >= 14, caption
        assert caption['x'] >= .55 and caption['x']+caption['w'] <= 12.8, caption
        labels.append(caption)
    for kind in ('goal', 'stretch'):
        ratio = ((1 if kind == 'stretch' else goal / scale) if stretch else web[f'{kind}Ratio'])
        if ratio is not None and ratio <= 1:
            marker = shapes[f'executive-{kind}-marker']
            assert abs((marker['x']-track['x'])/track['w']-ratio) < .0001, (kind, marker, web)
        marker = shapes.get(f'executive-{kind}-marker')
        if marker:
            for label in slide['shapes']:
                # Labels inside the bar must avoid the marker; stage labels sit above the marker's top end.
                if label['object_name'].startswith(('executive-segment-label:', 'executive-stage-label:')) and label['y'] + label['h'] > marker['y']:
                    assert not label['x'] < marker['x'] < label['x']+label['w'], (
                        f"{kind} marker crosses {label['text']} bar label", marker, label)
    # 1.7.0 shares the web tracker's six stage colours (audit B28): realized, active remaining, proposed remaining.
    bar_colors = {'0E5A27', '1E3A8A', '188038', '2563EB', 'A8D5B5', 'A9C1F5'}
    segments = [s for s in slide['shapes'] if s['y'] is not None and abs(s['y']-track['y']) < .001
                and set(s['fill_colors']) & bar_colors]
    if total:
        right = max(s['x']+s['w'] for s in segments)
        assert abs((right-track['x'])/track['w']-min(1,total/scale)) < .001, (right, web)
    assert bool(shapes.get('summary-stretch-overflow')) == bool(stretch and total > stretch)
    for label in labels:
        for other in slide['shapes']:
            if other is label or not other['text'] or other['x'] is None:
                continue
            dx = min(label['x']+label['w'],other['x']+other['w'])-max(label['x'],other['x'])
            dy = min(label['y']+label['h'],other['y']+other['h'])-max(label['y'],other['y'])
            assert dx < .001 or dy < .001, f"axis label overlaps: {label['text']} / {other['text']}"


def stretch_cases():
    cases = []
    for name, goal, total, stretch, labels, percentages, stretch_percentages in [
        ("billion", 1e9, 900e6, 1.5e9, ("$1B", "$1.5B"), ["90%", "22.5%"], ["60%", "15%"]),
        ("precise", 1e9, 900e6, 1.75e9, ("$1B", "$1.75B"), ["90%", "22.5%"], ["51.4%", "12.9%"]),
        ("above", 1e6, 20e6, 3e6, ("$1M", "$3M"), ["2000%", "500%"], ["666.7%", "166.7%"]),
        ("small", 125, 100, 200, ("$125", "$200"), ["80%", "20%"], ["50%", "12.5%"]),
        ("goal-off-scale", 200, 100, 125, ("$200", "$125"), ["50%", "12.5%"], ["80%", "20%"]),
        ("empty", 250e6, 0, 400e6, ("$250M", "$400M"), ["0%", "0%"], ["0%", "0%"]),
        ("no-goal", 0, 500e6, '', (), [], []),
        ("cleared", 1e9, 900e6, '', ("$1B",), ["90%", "22.5%"], []),
        ("goal-reached", 1e9, 1e9, '', ("$1B",), ["100%", "25%"], []),
        ("beyond-scale", 1e9, 1.3e9, '', ("$1B",), ["130%", "32.5%"], []),
    ]:
        state = four_pillar_state()
        state["fileName"] = f"Stretch goal example - {name} (sample data)"
        state["projectionTarget"] = goal
        state["stretchGoal"] = stretch
        for item in state["items"]:
            item["value"] *= total / 1500000
            item["realizedPct"] = 25
        cases.append((name, state, goal, total, stretch, labels, percentages, stretch_percentages))
    return cases


def exec_slide(deck):
    matches = [slide for slide in deck["slides"] if any(shape["object_name"] == "executive-bar-track" for shape in slide["shapes"])]
    assert len(matches) == 1, f"expected one executive summary slide, found {[slide['index'] for slide in matches]}"
    return matches[0]


def slide_title(slide):
    return next((shape["text"] for shape in slide["shapes"] if shape["object_name"] == "slide-title"), "")


def chart_parts(path):
    """Native chart parts with their slide, series names, axis settings and embedded workbook table ranges."""
    charts = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        content_types = archive.read("[Content_Types].xml").decode()
        for slide_index, name in enumerate(slide_names(path), start=1):
            rels_name = f"ppt/slides/_rels/{Path(name).name}.rels"
            if rels_name not in names:
                continue
            rels = archive.read(rels_name).decode()
            for target in re.findall(r'relationships/chart" Target="([^"]+)"', rels):
                part = target.lstrip("/") if target.startswith("/") else "ppt/" + target.replace("../", "")
                xml = archive.read(part).decode()
                chart_rels = archive.read(part.replace("charts/", "charts/_rels/") + ".rels").decode()
                book = re.search(r'Target="([^"]+\.xlsx)"', chart_rels).group(1)
                book_part = "ppt/" + book.replace("../", "")
                with zipfile.ZipFile(archive.open(book_part)) as workbook:
                    refs = [re.search(r'ref="([^"]+)"', workbook.read(n).decode()).group(1)
                            for n in workbook.namelist() if n.startswith("xl/tables/") and n.endswith(".xml")]
                charts.append({
                    "slide": slide_index, "part": part, "xml": xml,
                    "series": re.findall(r"<c:tx>\s*<c:strRef>.*?<c:v>([^<]*)</c:v>", xml, re.S),
                    "types": re.findall(r"<c:(barChart|lineChart|areaChart|scatterChart)>", xml),
                    "major_unit": [float(v) for v in re.findall(r'<c:majorUnit val="([^"]+)"', xml)],
                    "max": [float(v) for v in re.findall(r'<c:max val="([^"]+)"', xml)],
                    "table_refs": refs,
                    "content_type": f'PartName="/{part}"' in content_types,
                })
    return charts


def round_step(value):
    exponent = 10 ** math.floor(math.log10(value))
    return any(abs(value - base * exponent) < 1e-6 * exponent for base in (1, 2, 2.5, 5, 10))


def check_executive_no_goal(deck):
    slide = exec_slide(deck)
    names = {shape["object_name"] for shape in slide["shapes"]}
    assert "executive-goal-marker" not in names, "a goal marker was drawn although no goal is set"
    assert "No goal set" in slide["text"], "the summary does not say that no goal is set"
    assert "$1B" not in slide["text"] and "1,000,000,000" not in deck["notes"], "a default goal leaked into the deck"


def check_full_order(deck, roadmap_marker):
    """Story order (audit F2.3): title, summary, bridge, timing, projection, contribution, pillar pages."""
    order = {}
    for slide in deck["slides"]:
        names = {shape["object_name"] for shape in slide["shapes"]}
        title = slide_title(slide)
        if "deck-title" in names or "deck-subtitle" in names:
            order.setdefault("title", slide["index"])
        elif "executive-bar-track" in names:
            order.setdefault("summary", slide["index"])
        elif any(name.startswith("bridge-value:") for name in names):
            order.setdefault("bridge", slide["index"])
        elif title.startswith("Portfolio Rollup"):
            order.setdefault("timing", slide["index"])
        elif any(name.startswith("projection-label:") for name in names) or title.startswith("Projection"):
            order.setdefault("projection", slide["index"])
        elif any(name.startswith("contribution-") for name in names) or title.startswith("Pillar Contribution"):
            order.setdefault("contribution", slide["index"])
        elif any(name.startswith("initiative-label:") for name in names):
            order.setdefault("roadmap", slide["index"])
    expected = ["title", "summary", "bridge", "timing", "projection", "contribution", "roadmap"]
    assert all(key in order for key in expected), order
    assert [order[key] for key in expected] == sorted(order[key] for key in expected), order
    assert order["title"] == 1 and order["summary"] == 2, order
    assert roadmap_marker.upper() in "\n".join(slide["text"] for slide in deck["slides"] if slide["index"] >= order["roadmap"]).upper()


def check_four_pillar_rollup(deck):
    """Timing slide (audit F1.8): pillars on one page up to five; dates on the time axis, no dollar labels on bars."""
    slides = slides_with_title_prefix(deck, "Portfolio Rollup")
    assert len(slides) == 1, f"four pillars should share one timing page, found {[slide['index'] for slide in slides]}"
    for name in ["Procurement", "Operations", "Technology", "Commercial"]:
        matches = [shape for shape in slides[0]["shapes"] if shape["object_name"].startswith("rollup-pillar:") and shape["text"] == name]
        assert len(matches) == 1, f"rollup did not preserve {name}: {matches}"
        assert min_font(matches[0]) >= 14, f"rollup pillar label {name} is below 14 pt"
    bars = [shape for shape in slides[0]["shapes"] if shape["object_name"].startswith("rollup-bar:")]
    assert bars and all("$" not in shape["text"] for shape in bars), "rollup bars carry dollar labels on a time axis"
    assert any(text_shapes(slides[0], "Active")) and any(text_shapes(slides[0], "Proposed")), "rollup lacks Active/Proposed labels"
    assert not any(text_shapes(slide, "Approved", exact=True) for slide in slides), "legacy category label leaked into PowerPoint"
    assert "Active value:" in deck["notes"], "PowerPoint notes lost Active classification"
    assert "approved initiative" in deck["notes"], "renaming categories must not rewrite user-entered initiative names"


def check_projection_contract(deck):
    """Projection (audit F2.7): one native, editable line chart with round axis ticks and direct labels."""
    charts = [chart for chart in chart_parts(deck["path"]) if "lineChart" in chart["types"]]
    assert len(charts) == 1, f"expected one native projection chart, found {len(charts)}"
    chart = charts[0]
    assert {"Savings + Avoidance", "Savings only"} <= set(chart["series"]), chart["series"]
    assert chart["major_unit"] and all(round_step(step) for step in chart["major_unit"]), chart["major_unit"]
    assert all(not ref.endswith("'") for ref in chart["table_refs"]), chart["table_refs"]
    assert chart["content_type"], "chart part is missing its content type"
    slide = deck["slides"][chart["slide"] - 1]
    labels = [shape for shape in slide["shapes"] if shape["object_name"].startswith("projection-value:")]
    assert len(labels) >= 2 and all(MONEY3.fullmatch(shape["text"]) for shape in labels), [shape["text"] for shape in labels]
    assert "Expected" not in slide["text"] and "Annualized" not in slide["text"], "Expected/Annualized remain redundant projection boxes"
    assert "Expected" in deck["notes"] and "Annualized" in deck["notes"], "projection notes lost Expected/Annualized metadata"
    assert "Sep 4, 2026" in slide["text"] and "Unweighted" in slide["text"], "projection lacks visible reporting date and weighting"


def check_roadmap_references(deck):
    """Pillar pages (audit F2.6): readable names with status pills and a value column; full detail in notes."""
    assert "Sep 4, 2026" in deck["notes"] and "Unweighted" in deck["notes"] or "not confidence-weighted" in deck["notes"], "roadmap notes lost the reporting context"
    roadmap = [slide for slide in deck["slides"] if any(shape["object_name"].startswith("initiative-label:") for shape in slide["shapes"])]
    assert roadmap, "missing roadmap pages"
    for name in ["Contract reset with complete original wording", "Demand hedge with complete original wording", "Supplier collaboration program preserving the complete original initiative name"]:
        assert name in deck["notes"], f"speaker notes lost original name: {name}"
    labels = [shape for slide in roadmap for shape in slide["shapes"] if shape["object_name"].startswith("initiative-label:")]
    for shape in labels:
        assert shape["text"].strip() not in {"...", "…"}, "roadmap contains an ellipsis-only label"
        assert min_font(shape) >= 14, f"roadmap name {shape['text']} is below 14 pt"
        item_id = shape["object_name"].split(":", 1)[1]
        assert any(other["object_name"] == f"initiative-status:{item_id}" for slide in roadmap for other in slide["shapes"]), f"missing status pill for {item_id}"
        assert any(other["object_name"] == f"initiative-value:{item_id}" for slide in roadmap for other in slide["shapes"]), f"missing value cell for {item_id}"
    assert len({shape["object_name"] for shape in labels}) == len(labels), "an initiative appears twice on the roadmap"


def check_contribution_contract(deck):
    """Pillar Contribution (audit F2.7/F2.8): native stacked value bars plus separate dollar and share columns."""
    slides = [slide for slide in deck["slides"] if any(shape["object_name"].startswith("contribution-dollar:") for shape in slide["shapes"])]
    assert slides, "missing contribution section"
    charts = [chart for chart in chart_parts(deck["path"]) if chart["slide"] in {slide["index"] for slide in slides}]
    assert len(charts) == len(slides) and all("barChart" in chart["types"] for chart in charts), "contribution pages need one native bar chart each"
    assert all(set(chart["series"]) == {"Realized", "Active remaining", "Proposed remaining"} for chart in charts), [chart["series"] for chart in charts]
    names = [shape["text"] for slide in slides for shape in slide["shapes"] if shape["object_name"].startswith("contribution-pillar:")]
    expected = [f"Contribution Pillar {index:02d}" for index in range(1, 17)]
    assert len(names) == len(expected) and all(collapsed_text(full).startswith(collapsed_text(shown).rstrip("…")) for shown, full in zip(names, expected)), names
    for slide in slides:
        for shape in slide["shapes"]:
            if shape["object_name"].startswith("contribution-dollar:"):
                assert MONEY3.fullmatch(shape["text"]), shape["text"]
            if shape["object_name"].startswith("contribution-share:"):
                assert re.fullmatch(r"\d+(\.\d)?%|<0\.1%", shape["text"]), shape["text"]


def check_dense_pagination(deck):
    """Dense pillars paginate at up to ten rows, repeating the workstream header (audit F2.6)."""
    roadmap = [slide for slide in deck["slides"] if any(shape["object_name"].startswith("initiative-label:") for shape in slide["shapes"])]
    assert len(roadmap) >= 2, "dense roadmap was not paginated"
    seen = []
    for slide in roadmap:
        rows = [shape for shape in slide["shapes"] if shape["object_name"].startswith(("initiative-label:", "workstream-header:"))]
        assert len(rows) <= 10, f"dense roadmap slide {slide['index']} has {len(rows)} rows"
        assert any(shape["object_name"].startswith("workstream-header:") and "SEQUENCED DELIVERY" in shape["text"] for shape in rows), f"slide {slide['index']} lost the workstream header"
        seen.extend(shape["object_name"] for shape in rows if shape["object_name"].startswith("initiative-label:"))
    assert len(seen) == len(set(seen)) == 28, f"dense pagination lost or duplicated rows: {len(seen)}"


def check_typography_tiers(decks):
    """One type scale (audit F2.1): titles 28 pt, body 14 pt, captions no smaller than 10 pt."""
    for deck in decks:
        for slide in deck["slides"]:
            for shape in slide["shapes"]:
                if not shape["text"].strip():
                    continue
                if shape["object_name"] == "slide-title":
                    assert min_font(shape) == 28, f"slide title is not 28 pt on slide {slide['index']}"
                elif shape["object_name"].startswith(("initiative-label:", "rollup-pillar:", "contribution-pillar:", "initiative-value:")):
                    assert min_font(shape) >= 14, f"primary row {shape['text']} is below 14 pt"
                elif shape["font_sizes"]:
                    assert min_font(shape) >= 10, f"{deck['path'].name} slide {slide['index']} has text below 10 pt: {shape['text']!r}"


def check_ooxml_safety(decks):
    for deck in decks:
        assert not deck["negative_extents"], f"{deck['path'].name} has negative OOXML extents: {deck['negative_extents'][:4]}"
        assert not deck["autofit"], f"{deck['path'].name} uses shrink-to-fit in {deck['autofit']}"
        with zipfile.ZipFile(deck["path"]) as archive:
            names = set(archive.namelist())
            declared = re.findall(r'PartName="/([^"]+)"', archive.read("[Content_Types].xml").decode())
        missing = [part for part in declared if part not in names]
        assert not missing, f"{deck['path'].name} declares content types for missing parts: {missing[:4]}"
        for chart in chart_parts(deck["path"]):
            assert chart["content_type"], f"{deck['path'].name}: {chart['part']} lacks a content type"
            assert all(re.fullmatch(r"[A-Z]+\d+:[A-Z]+\d+", ref) for ref in chart["table_refs"]), f"{deck['path'].name}: invalid chart workbook range {chart['table_refs']}"


def check_text_bounds(decks):
    """Every text box stays on the slide and above the footer rule."""
    for deck in decks:
        for slide in deck["slides"]:
            for shape in slide["shapes"]:
                if shape["x"] is None or not shape["text"].strip():
                    continue
                assert shape["x"] >= 0 and shape["x"] + shape["w"] <= 13.34, (deck["path"].name, slide["index"], shape["text"][:40])
                assert shape["y"] >= 0 and shape["y"] + shape["h"] <= 7.5, (deck["path"].name, slide["index"], shape["text"][:40])


class Results:
    def __init__(self):
        self.failures = []
        self.count = 0

    def check(self, name, callback):
        self.count += 1
        try:
            callback()
            print(f"PASS {name}")
        except Exception as error:  # Keep the baseline run diagnostic instead of stopping early.
            self.failures.append((name, str(error)))
            print(f"FAIL {name}: {error}")


def main():
    if not APP.exists():
        raise SystemExit(f"generated application is missing: {APP}")
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        sparse = export_deck(browser, sparse_state(), "sparse-full.pptx")
        four = export_deck(browser, four_pillar_state(), "four-pillar-full.pptx")
        many = export_deck(browser, many_pillar_state(), "many-pillar-full.pptx")
        dense = export_deck(browser, dense_state(), "dense-full.pptx")
        projection = export_deck(browser, sparse_state(), "projection-current.pptx", "current", "proj")
        stretch = [(export_deck(browser, state, f"stretch-{name}.pptx", "current", "exec"),
                    goal, total, stretch_goal, labels, percentages, stretch_percentages)
                   for name, state, goal, total, stretch_goal, labels, percentages, stretch_percentages in stretch_cases()]
        browser.close()

    results = Results()
    results.check("executive_two_block_opportunity_story", lambda: check_executive_contract(four))
    results.check("executive_full_deck_stretch_goal", lambda: check_executive_stretch_goal(
        four, 5000000, 1500000, 7500000, ("$5M", "$7.5M"), ["30%", "6%"], ["20%", "4%"]
    ))
    results.check("executive_full_deck_measurement_axis", lambda: check_executive_measurement_axis(four, 1500000, stretch=7500000, goal=5000000))
    def check_no_title_bars():
        with zipfile.ZipFile(four["path"]) as archive:
            for name in archive.namelist():
                if not name.startswith(("ppt/slideLayouts/", "ppt/slideMasters/")) or not name.endswith(".xml"):
                    continue
                root = ET.fromstring(archive.read(name))
                for shape in root.findall(".//p:sp/p:spPr", NS):
                    geom = shape.find("a:prstGeom", NS)
                    assert not (geom is not None and geom.get("prst") == "rect" and
                                shape.find("a:solidFill", NS) is not None), name
    results.check("slide_masters_have_no_title_bars", check_no_title_bars)
    for deck, goal, total, stretch_goal, labels, percentages, stretch_percentages in stretch:
        def check_current(deck=deck, goal=goal, total=total, stretch_goal=stretch_goal, labels=labels, percentages=percentages, stretch_percentages=stretch_percentages):
            assert len(deck["slides"]) == 1, "current executive export is not one slide"
            if not goal:
                check_executive_no_goal(deck)
                return
            check_executive_stretch_goal(deck, goal, total, stretch_goal, labels, percentages, stretch_percentages)
            expected_max = 1.2e9 if deck['path'].stem in ('stretch-cleared', 'stretch-goal-reached') else None
            check_executive_measurement_axis(deck, total, expected_max, stretch_goal, goal)
        results.check(deck["path"].stem, check_current)
    results.check("full_deck_narrative_order", lambda: check_full_order(sparse, "Short Commitments"))
    results.check("four_pillar_timing_one_page_no_dollars_on_time_axis", lambda: check_four_pillar_rollup(four))
    results.check("projection_native_chart_round_ticks", lambda: check_projection_contract(projection))
    results.check("current_projection_is_one_slide", lambda: (
        len(projection["slides"]) == 1 or (_ for _ in ()).throw(AssertionError(
            f"current projection exported {len(projection['slides'])} slides"
        ))
    ))
    results.check("roadmap_status_pills_value_column_and_full_notes", lambda: check_roadmap_references(sparse))
    results.check("contribution_native_chart_separate_columns", lambda: check_contribution_contract(many))
    results.check("dense_roadmap_ten_rows_per_page", lambda: check_dense_pagination(dense))
    results.check("presentation_type_scale_28_14_10", lambda: check_typography_tiers([sparse, four, many, dense]))
    results.check("text_inside_slide_bounds", lambda: check_text_bounds([sparse, four, many, dense, projection]))
    results.check("ooxml_positive_extents_without_autofit", lambda: check_ooxml_safety(
        [sparse, four, many, dense, projection] + [case[0] for case in stretch]
    ))

    if results.failures:
        print(f"RED audit presentation tests: {len(results.failures)} failed, {results.count-len(results.failures)} passed")
        for name, error in results.failures:
            print(f"- {name}: {error}")
        return 1
    print(f"GREEN audit presentation tests: {results.count} passed")
    for deck in [sparse, four, many, dense, projection]:
        print(deck["path"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
