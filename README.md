# Roadmap Studio

Roadmap Studio is a local-first browser app for turning pillars, workstreams, and initiatives into an executive-ready roadmap and financial story.

It is designed for sensitive planning work: roadmap data stays in the browser, project files are saved locally as JSON, and the app does not need a backend or build step.

## Current Feature Set

- Build a roadmap from editable pillars and workstreams.
- **Drag-and-drop** pillars and workstreams to reorder structure (button reorder still available).
- Track initiatives by pillar, workstream, start/end date, milestone flag, status, owner, financial type, dollar value, realized percentage, and **confidence**.
- Choose `Approved` or `Proposed` for each initiative; legacy projects default `Not Started` to Proposed and started work to Approved.
- **Initiative filters + search** by text, status, owner, pillar, and Savings/Avoidance.
- **Resizable columns** and comfortable/compact density on the initiatives table.
- Classify financial impact as `Savings` or `Avoidance`.
- Show planned and realized totals for Savings and Avoidance in the roadmap header.
- **Health / risk summary panel** with counts and $ impact by status.
- Show each expanded pillar's Savings, Avoidance, and Realized rollups directly inside the roadmap view.
- Collapse or expand roadmap pillars (or owner lanes) to showcase one group at a time.
- **Owner swimlane view** — group the roadmap by owner instead of structure.
- Render `Not Started` initiatives in black so they are distinct from savings and avoidance work.
- Drag roadmap bars and edges to adjust initiative timing.
- Keep ranged initiative names inside their roadmap bars with concise, distinguishing labels and full details on hover.
- **Click a roadmap bar** to open a side **edit drawer** (dates, finance, confidence, time-phased realization).
- **Time-phased realization** schedule (cumulative % by date) with single-% fallback.
- **Confidence / probability weighting** (High / Med / Low) for expected-value projections.
- **Scenario snapshots** and a frozen **baseline** for plan-vs-baseline comparison.
- Save and reopen roadmap project files locally.
- Export the roadmap view to PNG.
- Export a PowerPoint deck with one slide per pillar plus financial summary slides.

## Analytics Views

Roadmap Studio includes dedicated executive analytics tabs:

- `Executive Summary`: reconciles the full portfolio into one dollar tracker toward an editable goal, split into Realized, Approved Remaining, and Proposed Remaining Savings/Avoidance value.
- `Portfolio Rollup`: shows one aggregate Approved and Proposed timeline bar per pillar, including initiative count, Savings/Avoidance breakdown, and realized progress.
- `Projected Savings`: projects cumulative value through a selected date.
- `Savings only` trajectory: includes only Savings initiatives.
- `Savings + Avoidance` trajectory: includes both Savings and Avoidance initiatives.
- Milestone initiatives recognize full value on the milestone date.
- Ranged initiatives accrue value linearly from start through end.
- Optional realized overlay compares planned value with realized value (supports time-phased phases).
- Optional **confidence weighting** and **baseline** trajectory overlay.
- **Expected** (confidence-weighted) and **annualized run-rate** metric cards.
- Top drivers identify the initiatives carrying the selected-date projection.
- `Stacked Bar Chart`: shows pillar concentration as percent of total value.
- Stacked bars are available for both Savings only and Savings + Avoidance.

## PowerPoint Export

The PowerPoint export is built for leadership review:

- Executive Summary opens the deck with the portfolio goal gap, four headline metrics, and the reconciled Savings/Avoidance dollar tracker.
- Portfolio Rollup follows as slide 2 before the pillar-level roadmap detail.
- One readable roadmap slide per pillar.
- Fiscal-year and quarter headers.
- Savings, Avoidance, and Realized metric cards.
- Multiple initiatives in the same workstream stack into readable lanes.
- Narrow PowerPoint roadmap bars use contained, single-line initiative labels.
- Portfolio approval slide with pillar lanes, Approved/Proposed value, realized progress, and calendar-year spans.
- Projected Savings slide with endpoint labels and Avoidance lift.
- Pillar value concentration slide with stacked bars and ranked contribution.
- Repair-safe PowerPoint geometry for generated trajectory lines.

## Privacy And Security

- No backend.
- No project data upload.
- No external runtime scripts.
- No ExcelJS/CDN dependency.
- Local PowerPoint writer vendored in `vendor/`.
- Browser-enforced Content Security Policy blocks network egress APIs.
- Project save/open uses local JSON files selected by the user.

## Tech Notes

- Single-file HTML/CSS/JavaScript app in `index.html`.
- Native SVG rendering for roadmap, portfolio rollup, projection, and stacked bar charts.
- Local persistence through browser storage.
- PowerPoint export via local `vendor/pptxgen.bundle.js`.
- Playwright-based regression suite in `tasks/roadmap_feature_tests.py`.

## Run Locally

Open `index.html` in a browser.

The app stores autosave data in your browser. Use `Save` to download a `.roadmap.json` project file and `Open` to load it into a newer version.

## Test

```bash
python3 tasks/roadmap_feature_tests.py
```

Latest local verification:

- `98 passed`
- `0 failed`
- `0 untested`
