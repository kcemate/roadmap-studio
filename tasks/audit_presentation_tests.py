#!/usr/bin/env python3
"""Focused PowerPoint regressions for the approved executive presentation contract."""
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "index.html"
OUT = Path("/tmp/roadmap-presentation-regression-tests")
EMU = 914400
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
CORE_LINE_COLORS = {"188038", "2563EB"}
MONEY_PERCENT = re.compile(r"\$[^\n]*[·|][^\n]*%")


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
        return deck_data(path)
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
    slide = find_slide(deck, "opportunity", "realized")
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
    slide = find_slide(deck, "opportunity", "realized")
    shapes = {shape["object_name"]: shape for shape in slide["shapes"]}
    scale = max(goal, stretch or 0, total, 1)
    labels = []
    kinds = ("goal", "stretch") if stretch else ("goal",)
    for kind, value, label in zip(kinds, (goal, stretch), expected_labels):
        marker = shapes.get(f"executive-{kind}-marker")
        assert marker is not None, f"missing {kind} marker for entered goal {goal}"
        assert abs(marker["x"] - (.76 + value / scale * 11.82)) < .001, marker
        amount = shapes.get(f"executive-{kind}-amount")
        assert amount and amount["text"] == label, (kind, amount, label)
        caption = shapes.get(f"executive-{kind}-label")
        assert caption and caption["text"] == ("GOAL" if kind == "goal" else "STRETCH GOAL"), caption
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


def stretch_cases():
    cases = []
    for name, goal, total, stretch, labels, percentages, stretch_percentages in [
        ("billion", 1e9, 900e6, 1.5e9, ("$1B", "$1.5B"), ["90%", "22.5%"], ["60%", "15%"]),
        ("precise", 1e9, 900e6, 1.75e9, ("$1B", "$1.75B"), ["90%", "22.5%"], ["51.4%", "12.9%"]),
        ("above", 1e6, 20e6, 3e6, ("$1M", "$3M"), ["2000%", "500%"], ["666.7%", "166.7%"]),
        ("small", 125, 100, 200, ("$125", "$200"), ["80%", "20%"], ["50%", "12.5%"]),
        ("empty", 250e6, 0, 400e6, ("$250M", "$400M"), ["0%", "0%"], ["0%", "0%"]),
        ("default", 0, 500e6, 2e9, ("$1B", "$2B"), ["50%", "12.5%"], ["25%", "6.3%"]),
        ("cleared", 1e9, 900e6, '', ("$1B",), ["90%", "22.5%"], []),
    ]:
        state = four_pillar_state()
        state["fileName"] = f"Stretch goal example - {name} (sample data)"
        state["projectionTarget"] = goal
        state["stretchGoal"] = stretch
        for item in state["items"]:
            item["value"] *= total / 1500000
            item["realizedPct"] = 25
        cases.append((name, state, goal or 1e9, total, stretch, labels, percentages, stretch_percentages))
    return cases


def check_full_order(deck, roadmap_marker):
    executive = find_slide(deck, "opportunity", "realized")["index"]
    rollups = [slide["index"] for slide in slides_with_title_prefix(deck, "Portfolio Rollup")]
    assert rollups, "missing Portfolio Rollup section"
    projection_matches = [slide for slide in deck["slides"] if any(
        shape["object_name"].startswith("projection-line:") for shape in slide["shapes"]
    )]
    assert len(projection_matches) == 1, f"expected one projection slide, found {[slide['index'] for slide in projection_matches]}"
    projection = projection_matches[0]["index"]
    contributions = [slide["index"] for slide in deck["slides"] if any(
        shape["object_name"].startswith("contribution-dollar:") for shape in slide["shapes"]
    )]
    assert contributions, "missing Contribution section"
    roadmap = find_slide(deck, roadmap_marker)["index"]
    assert executive == 1 and min(rollups) == 2, (executive, rollups)
    assert executive < min(rollups) <= max(rollups) < projection < min(contributions) <= max(contributions) < roadmap, {
        "Executive": executive,
        "Rollup": rollups,
        "Projection": projection,
        "Contribution": contributions,
        "Roadmaps": roadmap,
    }


def check_four_pillar_rollup(deck):
    slides = slides_with_title_prefix(deck, "Portfolio Rollup")
    assert len(slides) == 2, f"four pillars should produce two rollup pages, found {[slide['index'] for slide in slides]}"
    names = ["Procurement", "Operations", "Technology", "Commercial"]
    page_counts = []
    for slide in slides:
        page_counts.append(len([shape for shape in slide["shapes"] if shape["object_name"].startswith("rollup-pillar:")]))
    assert page_counts == [2, 2], f"four-pillar rollup is not split 2+2: {page_counts}"
    for index, name in enumerate(names, start=1):
        matches = [shape for slide in slides for shape in slide["shapes"]
                   if shape["object_name"] == f"rollup-pillar:four-p{names.index(name) + 1}"]
        assert len(matches) == 1, f"rollup did not preserve {name}: {matches}"
        assert min_font(matches[0]) >= 18, f"rollup row label {name} is below 18 pt"
    for label in ["Active", "Proposed"]:
        matches = [shape for slide in slides for shape in text_shapes(slide, label, exact=True)]
        assert matches, f"missing explicit {label} row label"
        colors = [color for shape in matches for color in shape["text_colors"]]
        assert colors and all(is_neutral(color) for color in colors), f"{label} uses non-neutral label colors: {colors}"
    assert not any(text_shapes(slide, "Approved", exact=True) or text_shapes(slide, "APPROVED", exact=True) for slide in slides), "legacy category label leaked into PowerPoint"
    assert any(text_shapes(slide, "Realized") for slide in slides), "rollup lacks an explicit Realized label"
    assert "Selected as active:" in deck["notes"], "PowerPoint notes lost Active classification"
    assert "Selected as approved:" not in deck["notes"], "PowerPoint notes retain the old category"
    assert "approved initiative" in deck["notes"], "renaming categories must not rewrite user-entered initiative names"


def check_projection_contract(deck):
    slide = find_slide(deck, "Savings only", "Savings + Avoidance")
    lines = [shape for shape in slide["shapes"]
             if shape["geometry"] == "line" and CORE_LINE_COLORS.intersection(shape["line_colors"])]
    by_color = defaultdict(list)
    for shape in lines:
        for color in CORE_LINE_COLORS.intersection(shape["line_colors"]):
            by_color[color].append(shape)
    assert all(by_color[color] for color in CORE_LINE_COLORS), f"projection core lines are not native OOXML lines: {dict(by_color)}"
    centers = [shape["y"] + (shape["h"] or 0) / 2 for shape in lines if shape["y"] is not None]
    assert centers and max(centers) - min(centers) >= 1.2, f"far target flattened the trajectory to {max(centers) - min(centers):.2f} inches"
    areas = [shape for shape in slide["shapes"]
             if shape["geometry"] == "custom" and "2563EB" in shape["fill_colors"]]
    assert areas, "Savings-to-total area is not one smooth native polygon"
    target = text_shapes(slide, "Target")
    assert target and any(shape["y"] is not None and shape["y"] + (shape["h"] or 0) <= 2.1 for shape in target), (
        "far target label is not displayed outside the graph", target,
    )
    labels = [shape for shape in slide["shapes"] if shape["text"] and any(
        token in shape["text"] for token in ["Savings only", "Savings + Avoidance", "Target"]
    )]
    for index, left in enumerate(labels):
        if None in (left["x"], left["y"], left["w"], left["h"]):
            continue
        for right in labels[index + 1:]:
            if None in (right["x"], right["y"], right["w"], right["h"]):
                continue
            overlap_x = min(left["x"] + left["w"], right["x"] + right["w"]) - max(left["x"], right["x"])
            overlap_y = min(left["y"] + left["h"], right["y"] + right["h"]) - max(left["y"], right["y"])
            assert overlap_x <= 0 or overlap_y <= 0, f"projection labels collide: {left['text']!r}, {right['text']!r}"
    visible = slide["text"]
    assert "Expected" not in visible and "Annualized" not in visible, "Expected/Annualized remain redundant projection boxes"
    assert "Expected" in deck["notes"] and "Annualized" in deck["notes"], "projection notes lost Expected/Annualized metadata"
    assert "Sep 4, 2026" in visible and "Unweighted" in visible, "projection lacks visible reporting date and weighting"


def check_roadmap_references(deck):
    slide = find_slide(deck, "Short Commitments")
    expected = [
        ("short-1", "Contract reset with complete original wording", 125000, True),
        ("short-2", "Demand hedge with complete original wording", 85000, True),
        ("long-1", "Supplier collaboration program preserving the complete original initiative name", 300000, False),
    ]
    assert "Sep 4, 2026" in deck["notes"] and "Unweighted" in deck["notes"], (
        "roadmap notes lost reporting date or weighting context"
    )
    for index, (item_id, name, value, must_show_full_name) in enumerate(expected, start=1):
        assert name in deck["notes"], f"speaker notes lost original name: {name}"
        value_tokens = {str(value), f"{value:,}", f"${value:,}", f"${value // 1000}K"}
        assert any(token in deck["notes"] or token in slide["text"] for token in value_tokens), (
            f"visible reference row and notes lost original value {value}", value_tokens,
        )
        visible = [shape for shape in slide["shapes"]
                   if shape["object_name"] == f"initiative-label:{item_id}"]
        assert len(visible) == 1, f"expected exactly one external initiative label for {name}, found {len(visible)}"
        if must_show_full_name:
            assert collapsed_text(normalized_text(visible[0]["text"]).removeprefix(f"{index:02d} ")) == collapsed_text(name), (
                f"external initiative label lost its readable name: {visible[0]['text']}"
            )
        else:
            measured = collapsed_text(normalized_text(visible[0]["text"]).removeprefix(f"{index:02d} ").rstrip(". …"))
            assert measured and collapsed_text(name).startswith(measured), f"long external label is not a measured prefix: {visible[0]['text']}"
        assert min(min_font(shape) for shape in visible) >= 18, f"roadmap reference row for {name} is below 18 pt"
    bar_names = {shape["object_name"] for shape in slide["shapes"] if shape["object_name"].startswith("initiative-bar:")}
    assert bar_names == {"initiative-bar:short-1", "initiative-bar:short-2", "initiative-bar:long-1"}, bar_names
    for index, item_id in enumerate(["short-1", "short-2"], start=1):
        bar_labels = [shape for shape in slide["shapes"] if shape["object_name"] in {
            f"initiative-bar-label:{item_id}", f"initiative-reference:{item_id}"
        }]
        assert len(bar_labels) == 1 and bar_labels[0]["text"].strip() == f"{index:02d}", (
            f"short bar {item_id} is not linked to zero-padded reference {index:02d}", bar_labels,
        )
    assert all(shape["text"].strip() not in {"...", "…"} for shape in slide["shapes"]), "roadmap contains an ellipsis-only label"


def check_contribution_contract(deck):
    contribution_slides = [slide for slide in deck["slides"] if any(
        shape["object_name"].startswith("contribution-dollar:") for shape in slide["shapes"]
    )]
    assert contribution_slides, "missing contribution section"
    text = "\n".join(slide["text"] for slide in contribution_slides)
    assert sum(normalized_text(shape["text"]) == "100% composition"
               for slide in contribution_slides for shape in slide["shapes"]) == 2, (
        "both composition bars are not explicitly labeled 100%"
    )
    assert "Both bars represent 100%, not equal dollar values" in text, "normalization basis is not explicit"
    assert not MONEY_PERCENT.search(text), "contribution table still merges dollar and percentage values"
    headers = [shape["text"].strip() for slide in contribution_slides for shape in slide["shapes"]]
    assert any(header in {"$", "Value", "Amount"} or "Dollar" in header for header in headers), "missing separate dollar-value column"
    assert any("%" in header or "Share" in header for header in headers), "missing separate percentage column"
    expected_order = []
    for index in range(1, 17):
        name = f"Contribution Pillar {index:02d}"
        matches = [shape for slide in contribution_slides for shape in slide["shapes"]
                   if shape["object_name"] == f"contribution-pillar:many-p{index:02d}"]
        assert len(matches) == 1, f"contribution pagination did not preserve {name} exactly once"
        measured = collapsed_text(normalized_text(matches[0]["text"]).rstrip(". …"))
        assert measured and collapsed_text(name).startswith(
            measured
        ), f"contribution row for {name} is not meaningful: {matches[0]['text']}"
        assert min_font(matches[0]) >= 18, f"contribution row {name} is below 18 pt"
        expected_order.append(f"many-p{index:02d}")
    for kind in ["savings", "combined"]:
        dollars = [shape["object_name"].rsplit(":", 1)[-1] for slide in contribution_slides for shape in slide["shapes"]
                   if shape["object_name"].startswith(f"contribution-dollar:{kind}:")]
        shares = [shape["object_name"].rsplit(":", 1)[-1] for slide in contribution_slides for shape in slide["shapes"]
                  if shape["object_name"].startswith(f"contribution-share:{kind}:")]
        assert dollars == expected_order, f"{kind} dollar rows do not use overall Combined-desc order: {dollars}"
        assert shares == expected_order, f"{kind} share rows do not use overall Combined-desc order: {shares}"


def check_dense_pagination(deck):
    appearances = Counter()
    slide_indexes = set()
    for index in range(1, 29):
        item_id = f"dense-{index:02d}"
        name = f"Dense initiative {index:02d} complete reference name"
        for slide in deck["slides"]:
            if any(shape["object_name"] == f"initiative-label:{item_id}" for shape in slide["shapes"]):
                appearances[item_id] += 1
                slide_indexes.add(slide["index"])
        assert name in deck["notes"], f"dense notes lost {name}"
    missing = [f"dense-{index:02d}" for index in range(1, 29)
               if appearances[f"dense-{index:02d}"] != 1]
    assert not missing, f"dense pagination lost or duplicated external labels: {missing}"
    assert len(slide_indexes) >= 2, "dense roadmap was not paginated"
    roadmap_slides = [slide for slide in deck["slides"] if any(
        shape["object_name"].startswith("initiative-label:dense-") for shape in slide["shapes"]
    )]
    for slide in roadmap_slides:
        row_count = sum(shape["object_name"].startswith("initiative-label:dense-") for shape in slide["shapes"])
        assert row_count <= 4, f"dense roadmap slide {slide['index']} has {row_count} body rows"
        assert "Sequenced Delivery" in slide["text"], f"slide {slide['index']} lost repeated workstream context"


def check_typography_tiers(decks):
    for deck in decks:
        ticks = []
        for slide in deck["slides"]:
            for shape in slide["shapes"]:
                name = shape["object_name"]
                if name == "slide-title":
                    assert min_font(shape) >= 26, f"slide title is below 26 pt on slide {slide['index']}"
                if name.startswith(("initiative-label:", "rollup-pillar:")):
                    assert min_font(shape) >= 18, f"primary row {name} is below 18 pt"
                if name.startswith(("contribution-dollar:", "contribution-share:")):
                    assert min_font(shape) >= 16, f"secondary label {name} is below 16 pt"
                if re.search(r"(?:^|\s)(?:FY\d{2,4}|Q[1-4])(?:\s|$)", shape["text"]):
                    ticks.append(shape)
        assert ticks, f"{deck['path'].name} did not expose fiscal tick labels"
        assert all(min_font(shape) >= 14 for shape in ticks), (
            f"{deck['path'].name} has ticks below 14 pt",
            [(shape["text"], shape["font_sizes"]) for shape in ticks if min_font(shape) < 14],
        )


def check_ooxml_safety(decks):
    for deck in decks:
        assert not deck["negative_extents"], f"{deck['path'].name} has negative OOXML extents: {deck['negative_extents'][:4]}"
        assert not deck["autofit"], f"{deck['path'].name} uses shrink-to-fit in {deck['autofit']}"


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
    for deck, goal, total, stretch_goal, labels, percentages, stretch_percentages in stretch:
        def check_current(deck=deck, goal=goal, total=total, stretch_goal=stretch_goal, labels=labels, percentages=percentages, stretch_percentages=stretch_percentages):
            assert len(deck["slides"]) == 1, "current executive export is not one slide"
            check_executive_stretch_goal(deck, goal, total, stretch_goal, labels, percentages, stretch_percentages)
        results.check(deck["path"].stem, check_current)
    results.check("full_deck_narrative_order", lambda: check_full_order(sparse, "Short Commitments"))
    results.check("four_pillar_rollup_2_plus_2", lambda: check_four_pillar_rollup(four))
    results.check("projection_native_lines_area_and_far_target", lambda: check_projection_contract(projection))
    results.check("current_projection_is_one_slide", lambda: (
        len(projection["slides"]) == 1 or (_ for _ in ()).throw(AssertionError(
            f"current projection exported {len(projection['slides'])} slides"
        ))
    ))
    results.check("roadmap_numbered_references_and_full_notes", lambda: check_roadmap_references(sparse))
    results.check("contribution_normalization_columns_and_pagination", lambda: check_contribution_contract(many))
    results.check("dense_roadmap_pagination", lambda: check_dense_pagination(dense))
    results.check("presentation_typography_18_16_14", lambda: check_typography_tiers([sparse, four, many, dense]))
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
