#!/usr/bin/env python3
"""Focused regressions for audited PowerPoint, PNG, and presentation behavior."""
import json
import os
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/roadmap-export-implementation-tests")
APP = ROOT / "index.html"
EMU = 914400
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def build_app():
    subprocess.run(["python3", str(ROOT / "tasks" / "build.py")], cwd=ROOT, check=True)


def dense_state():
    items = []
    for index in range(32):
        items.append(
            {
                "id": f"dense-{index + 1:02d}",
                "pillarId": "p1",
                "wsId": "w1",
                "name": f"Dense {index + 1:02d} decision-ready initiative",
                "start": "2026-08-01",
                "end": "2027-03-31",
                "valueType": "Savings" if index % 2 == 0 else "Avoidance",
                "value": 100000 + index * 1000,
                "realizedPct": 25,
                "confidence": 70,
                "includeInTotals": True,
                "milestone": False,
                "status": "At Risk" if index % 7 == 0 else "On Track",
                "approval": "Approved" if index % 3 else "Proposed",
                "owner": f"Owner {(index % 4) + 1}",
            }
        )
    items.append(
        {
            "id": "undated-01",
            "pillarId": "p1",
            "wsId": "w2",
            "name": "Undated governance decision",
            "start": "",
            "end": "",
            "valueType": "Savings",
            "value": 25000,
            "realizedPct": 0,
            "confidence": 100,
            "includeInTotals": True,
            "milestone": False,
            "status": "Not Started",
            "approval": "Proposed",
            "owner": "Governance",
        }
    )
    payload = {
        "fyStart": 6,
        "structure": [
            {
                "id": "p1",
                "name": "Enterprise transformation",
                "workstreams": [
                    {"id": "w1", "name": "Simultaneous delivery portfolio"},
                    {"id": "w2", "name": "Governance and controls"},
                ],
            }
        ],
        "items": items,
        "projectionTarget": 8000000,
        "projectionEnd": "2027-03-31",
        "roadmapGroup": "owner",
        "collapsedPillars": {},
        "asOfDate": "2026-09-04",
    }
    baseline = json.loads(json.dumps(payload))
    baseline["savedAt"] = 1780000000000
    for item in baseline["items"]:
        item["value"] = round(item["value"] * 0.5)
    return {
        "v": 2,
        "savedAt": 1780000000000,
        "fileName": "FY27 Board Roadmap",
        **payload,
        "weightConfidence": True,
        "showBaseline": True,
        "projectionShowRealized": True,
        "baseline": baseline,
        "scenarios": [
            {
                "id": "sc-downside",
                "name": "Downside scenario",
                "savedAt": 1780000000000,
                "payload": payload,
            }
        ],
    }


def long_name_state():
    state = dense_state()
    state["fileName"] = "Long export labels"
    pillar = "Pillar " + "M" * 240
    workstream = "Workstream " + "M" * 240
    initiative = "Initiative " + "M" * 240
    state["structure"] = [
        {"id": "p1", "name": pillar, "workstreams": [{"id": "w1", "name": workstream}]}
    ]
    state["items"] = [
        {
            "id": "long-1",
            "pillarId": "p1",
            "wsId": "w1",
            "name": initiative,
            "start": "2026-08-01",
            "end": "2027-03-31",
            "valueType": "Savings",
            "value": 125000,
            "realizedPct": 10,
            "confidence": 100,
            "includeInTotals": True,
            "milestone": False,
            "status": "On Track",
            "approval": "Approved",
            "owner": "Owner",
        }
    ]
    state["baseline"] = None
    state["scenarios"] = []
    return state, pillar[:240], workstream[:240], initiative[:240]


def new_page(browser, state):
    context = browser.new_context(
        accept_downloads=True,
        viewport={"width": 1440, "height": 900},
        device_scale_factor=1,
    )
    context.add_init_script("localStorage.clear();")
    context.add_init_script(
        f"localStorage.setItem('roadmapStudio.v1', {json.dumps(json.dumps(state))});"
    )
    page = context.new_page()
    page.goto(APP.as_uri(), wait_until="domcontentloaded")
    page.evaluate("state => { deserializeInto(state); enterStudio(); S.activeScenarioId='sc-downside'; renderScenarioUI(); }", state)
    return context, page


def download_ppt(page, name, scope="full"):
    page.evaluate("scope => { S.exportScope=scope; const el=document.querySelector('#pptScope'); if(el)el.value=scope; }", scope)
    with page.expect_download() as info:
        page.click("#pptBtn")
    path = OUT / name
    info.value.save_as(path)
    return path


def slide_names(path):
    with zipfile.ZipFile(path) as zf:
        return sorted(
            (name for name in zf.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")),
            key=lambda name: int(Path(name).stem.replace("slide", "")),
        )


def slide_xml(path, name):
    with zipfile.ZipFile(path) as zf:
        return zf.read(name)


def text_shapes(path):
    shapes = []
    for slide_index, name in enumerate(slide_names(path), start=1):
        root = ET.fromstring(slide_xml(path, name))
        for shape in root.findall(".//p:sp", NS):
            text = "".join(node.text or "" for node in shape.findall(".//a:t", NS))
            properties = shape.find("./p:nvSpPr/p:cNvPr", NS)
            xfrm = shape.find("./p:spPr/a:xfrm", NS)
            if xfrm is None:
                continue
            off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
            if off is None or ext is None:
                continue
            sizes = [
                int(node.attrib["sz"]) / 100
                for node in shape.findall(".//*[@sz]", NS)
                if node.attrib.get("sz", "").isdigit()
            ]
            shapes.append(
                {
                    "slide": slide_index,
                    "text": text,
                    "object_name": properties.attrib.get("name", "") if properties is not None else "",
                    "x": int(off.attrib["x"]) / EMU,
                    "y": int(off.attrib["y"]) / EMU,
                    "w": int(ext.attrib["cx"]) / EMU,
                    "h": int(ext.attrib["cy"]) / EMU,
                    "sizes": sizes,
                    "colors": [
                        node.attrib["val"].upper()
                        for node in shape.findall(".//p:txBody//a:solidFill/a:srgbClr", NS)
                        if node.attrib.get("val")
                    ],
                }
            )
    return shapes


def all_text(path):
    return "\n".join(shape["text"] for shape in text_shapes(path))


def is_neutral(color):
    channels = [int(color[index:index + 2], 16) for index in (0, 2, 4)]
    return max(channels) - min(channels) <= 16


def assert_explicit_sans_theme(path):
    with zipfile.ZipFile(path) as zf:
        theme = zf.read("ppt/theme/theme1.xml").decode("utf-8", "ignore")
        slides = "\n".join(
            zf.read(name).decode("utf-8", "ignore") for name in slide_names(path)
        )
    assert '<a:majorFont><a:latin typeface="Arial"' in theme, "heading theme font was not explicit Arial"
    assert '<a:minorFont><a:latin typeface="Arial"' in theme, "body theme font was not explicit Arial"
    assert "Aptos Display" not in slides, "slide text retained a platform-dependent heading font"


def test_dense_pagination(page):
    page.evaluate("S.roadmapGroup='structure'; renderAll();")
    page.click("#segRoad")
    deck = download_ppt(page, "dense-full.pptx")
    shapes = text_shapes(deck)
    dense = [shape for shape in shapes if shape["object_name"].startswith("initiative-label:dense-")]
    assert len(dense) == 32, f"expected every dense row once, got {len(dense)}"
    roadmap_labels = [shape for shape in shapes if shape["object_name"].startswith("initiative-label:")]
    assert len({shape["slide"] for shape in roadmap_labels}) >= 9, "dense pillar was not paginated at four rows per slide"
    for slide_index in {shape["slide"] for shape in roadmap_labels}:
        assert len([shape for shape in roadmap_labels if shape["slide"] == slide_index]) <= 4
        assert any(shape["slide"] == slide_index and "Simultaneous" in shape["text"] and "portfolio" in shape["text"] for shape in shapes), (
            f"workstream context was not repeated on dense roadmap slide {slide_index}"
        )
    assert max(shape["y"] + shape["h"] for shape in dense) <= 7.35, "timeline text left slide bounds"
    assert min(min(shape["sizes"]) for shape in dense if shape["sizes"]) >= 18, "timeline body fell below 18 pt"
    undated = [shape for shape in shapes if shape["object_name"] == "initiative-label:undated-01"]
    assert len(undated) == 1 and "Undated" in undated[0]["text"] and "decision" in undated[0]["text"], (
        "undated initiative was silently omitted", undated
    )
    assert_explicit_sans_theme(deck)
    return deck


def test_scope_context_and_projection(page):
    page.click("#segProj")
    page.wait_for_selector("#projectionSvg")
    deck = download_ppt(page, "projection-current.pptx", "current")
    text = all_text(deck)
    assert len(slide_names(deck)) == 1, "current-view projection should export one slide"
    for expected in [
        "FY27 Board Roadmap",
        "Downside scenario",
        "Current view",
        "As of Sep 4, 2026",
        "Confidence weighted",
        "Target $8M",
        "Baseline",
    ]:
        assert expected in text, f"missing projection/context label: {expected}"
    assert "Expected" not in text and "Annualized" not in text, "projection retained redundant Expected/Annualized boxes"
    with zipfile.ZipFile(deck) as zf:
        notes = "\n".join(
            zf.read(name).decode("utf-8", "ignore")
            for name in zf.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        )
    assert "Expected" in notes and "Annualized" in notes, "projection notes lost Expected/Annualized metadata"
    return deck


def test_owner_grouping(page):
    page.evaluate("S.roadmapGroup='owner'; renderAll();")
    page.click("#segRoad")
    deck = download_ppt(page, "roadmap-current.pptx", "current")
    text = all_text(deck)
    with zipfile.ZipFile(deck) as zf:
        notes = "\n".join(
            zf.read(name).decode("utf-8", "ignore")
            for name in zf.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        )
    assert "Owner 1" in text and "Owner 4" in text, "current owner grouping was not exported"
    assert "Grouping: Owner" in notes, "grouping context was not retained in notes"
    assert "Simultaneous delivery portfolio" not in text, "current owner view reverted to structure grouping"
    return deck


def test_browser_presentation(page):
    page.evaluate("S.roadmapGroup='owner'; renderAll();")
    page.click("#segRoad")
    page.click("#presentBtn")
    page.wait_for_timeout(250)
    observed = page.evaluate(
        """() => {
            const stage=document.querySelector('.stage'), box=document.querySelector('#tlBox');
            const context=document.querySelector('#presentationContext');
            const matrix=getComputedStyle(box).transform;
            const scale=matrix==='none'?1:new DOMMatrix(matrix).a;
            return {
                scale,
                overflow:getComputedStyle(stage).overflowY,
                scrollHeight:stage.scrollHeight,
                clientHeight:stage.clientHeight,
                context:context?.textContent||'',
                contextVisible:!!context&&getComputedStyle(context).display!=='none'
            };
        }"""
    )
    assert observed["scale"] == 1, f"presentation was scaled to {observed['scale']}"
    assert observed["overflow"] in {"auto", "scroll"}, observed
    assert observed["scrollHeight"] > observed["clientHeight"], "dense presentation did not remain scrollable"
    assert observed["contextVisible"], "stable presentation context was missing"
    for expected in ["FY27 Board Roadmap", "Downside scenario", "As of Sep 4, 2026", "Owner"]:
        assert expected in observed["context"], f"presentation context missing {expected}"
    page.click("#exitPres")


def test_png_context(page):
    page.click("#segRoad")
    svg_height = page.locator("#tlSvg").evaluate("el => el.height.baseVal.value")
    with page.expect_download() as info:
        page.click("#pngBtn")
    assert info.value.suggested_filename == "roadmap.png"
    path = OUT / "roadmap-context.png"
    info.value.save_as(path)
    image = Image.open(path)
    assert image.height > svg_height * 2 + 100, "PNG did not reserve a visible context header"
    return path


def test_long_names_without_autofit(browser):
    state, pillar, workstream, initiative = long_name_state()
    context, page = new_page(browser, state)
    page.evaluate("S.roadmapGroup='structure'; renderAll();")
    page.click("#segRoad")
    deck = download_ppt(page, "long-labels.pptx")
    with zipfile.ZipFile(deck) as zf:
        slides = "\n".join(
            zf.read(name).decode("utf-8", "ignore") for name in slide_names(deck)
        )
        notes = "\n".join(
            zf.read(name).decode("utf-8", "ignore")
            for name in zf.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
        )
    assert "<a:normAutofit" not in slides, "PowerPoint retained shrink-to-fit instructions"
    assert pillar not in slides and workstream not in slides and initiative not in slides
    for full_name in [pillar, workstream, initiative]:
        assert full_name in notes, "full truncated name was not retained in speaker notes"
    named = [shape for shape in text_shapes(deck) if shape["text"].startswith(("Pillar ", "Workstream ", "Initiative "))]
    initiative_labels = [shape for shape in text_shapes(deck) if shape["object_name"] == "initiative-label:long-1"]
    assert len(initiative_labels) == 1 and min(initiative_labels[0]["sizes"]) >= 18
    context.close()


def test_legacy_export_contracts(browser):
    from roadmap_feature_tests import (
        exclusion_state,
        ppt_portfolio_rollup_stage_state,
        ppt_same_workstream_state,
        seed_state,
    )

    context, page = new_page(browser, seed_state())
    page.click("#segRoad")
    deck = download_ppt(page, "compat-full-deck.pptx")
    shapes = text_shapes(deck)
    text = all_text(deck)
    for expected in [
        "Savings only",
        "Savings + Avoidance",
        "100% composition",
        "Both bars represent 100%, not equal dollar values",
        "Contribution",
        "Product Requirements",
        "2 initiatives",
    ]:
        assert expected.lower() in text.lower(), f"replacement export story label missing: {expected}"
    executive = min(shape["slide"] for shape in shapes if "opportunity" in shape["text"].lower())
    rollup = min(shape["slide"] for shape in shapes if shape["text"] == "Portfolio Rollup")
    projection = min(shape["slide"] for shape in shapes if shape["text"] == "Savings only")
    contribution = min(shape["slide"] for shape in shapes if "contribution" in shape["text"].lower())
    roadmap = min(shape["slide"] for shape in shapes if shape["object_name"] == "initiative-label:i1")
    assert executive == 1 and rollup == 2
    assert executive < rollup < projection < contribution < roadmap
    context.close()

    context, page = new_page(browser, ppt_same_workstream_state())
    page.click("#segRoad")
    deck = download_ppt(page, "compat-narrow-labels.pptx")
    shapes = text_shapes(deck)
    boxes = [shape for shape in shapes if shape["object_name"] in {
        "initiative-label:sw1", "initiative-label:sw2"
    }]
    assert len(boxes) == 2 and len({round(box["y"], 2) for box in boxes}) == 2, boxes
    assert all(min(box["sizes"]) >= 18 for box in boxes), boxes
    assert {shape["object_name"] for shape in shapes if shape["object_name"].startswith("initiative-bar:sw")} == {
        "initiative-bar:sw1", "initiative-bar:sw2"
    }
    assert all(shape["text"].strip() not in {"...", "…"} for shape in shapes)
    context.close()

    context, page = new_page(browser, ppt_portfolio_rollup_stage_state())
    page.click("#segRollup")
    deck = download_ppt(page, "compat-rollup.pptx")
    shapes = text_shapes(deck)
    rollup_slides = {
        shape["slide"] for shape in shapes
        if shape["object_name"] == "slide-title" and shape["text"].startswith("Portfolio Rollup")
    }
    assert len(rollup_slides) == 2
    pillar_rows = [shape for shape in shapes if shape["object_name"].startswith("rollup-pillar:")]
    assert len(pillar_rows) == 4
    assert sorted(sum(shape["slide"] == slide for shape in pillar_rows) for slide in rollup_slides) == [2, 2]
    assert min(min(shape["sizes"]) for shape in pillar_rows) >= 18
    for expected in ["Active", "Proposed", "Realized"]:
        matches = [shape for shape in shapes if shape["slide"] in rollup_slides and (
            shape["text"] == expected or expected == "Realized" and shape["text"].startswith("Realized ")
        )]
        assert matches, expected
        if expected != "Realized":
            assert all(shape["colors"] and all(is_neutral(color) for color in shape["colors"]) for shape in matches)
    context.close()

    context, page = new_page(browser, exclusion_state())
    page.click("#segRoad")
    deck = download_ppt(page, "compat-exclusion.pptx")
    shapes = text_shapes(deck)
    aggregate_slides = {1}
    aggregate_slides.update(shape["slide"] for shape in shapes if shape["text"] == "Portfolio Rollup")
    aggregate_slides.update(shape["slide"] for shape in shapes if shape["text"] == "Savings only")
    aggregate_slides.update(
        shape["slide"] for shape in shapes
        if shape["object_name"].startswith("contribution-dollar:")
    )
    for index in aggregate_slides:
        slide_text = "\n".join(shape["text"] for shape in shapes if shape["slide"] == index)
        assert "$920K" in slide_text and "$1.4M" not in slide_text, (index, slide_text)
    excluded = [shape for shape in shapes if shape["object_name"] == "initiative-label:i2"]
    assert len(excluded) == 1 and "Carrier Contract Risk" in excluded[0]["text"]
    excluded_slide = excluded[0]["slide"]
    assert "$450K" in "\n".join(shape["text"] for shape in shapes if shape["slide"] == excluded_slide)
    context.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if os.environ.get("ROADMAP_TEST_SKIP_BUILD") != "1":
        build_app()
    artifacts = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context, page = new_page(browser, dense_state())
        try:
            artifacts.append(test_dense_pagination(page))
            artifacts.append(test_scope_context_and_projection(page))
            artifacts.append(test_owner_grouping(page))
            test_browser_presentation(page)
            artifacts.append(test_png_context(page))
        finally:
            context.close()
        test_legacy_export_contracts(browser)
        test_long_names_without_autofit(browser)
        browser.close()
    print("PASS audit export tests")
    for artifact in artifacts:
        print(artifact)


if __name__ == "__main__":
    main()
