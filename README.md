# Roadmap Studio

Roadmap Studio is a local-first browser app for turning pillars, workstreams, and initiatives into an executive-ready roadmap and financial story.

It is designed for sensitive planning work: roadmap data stays in the browser, project files are saved locally as JSON, and the app does not need a backend or build step.

## Current Feature Set

- Build a roadmap from editable pillars and workstreams.
- Track initiatives by pillar, workstream, start/end date, milestone flag, status, owner, financial type, dollar value, and realized percentage.
- Classify financial impact as `Savings` or `Avoidance`.
- Show planned and realized totals for Savings and Avoidance in the roadmap header.
- Show each expanded pillar's Savings, Avoidance, and Realized rollups directly inside the roadmap view.
- Collapse or expand roadmap pillars to showcase one pillar at a time.
- Render `Not Started` initiatives in black so they are distinct from savings and avoidance work.
- Drag roadmap bars and edges to adjust initiative timing.
- Save and reopen roadmap project files locally.
- Export the roadmap view to PNG.
- Export a PowerPoint deck with one slide per pillar plus financial summary slides.

## Analytics Views

Roadmap Studio now includes dedicated executive analytics tabs:

- `Projected Savings`: projects cumulative value through a selected date.
- `Savings only` trajectory: includes only Savings initiatives.
- `Savings + Avoidance` trajectory: includes both Savings and Avoidance initiatives.
- Milestone initiatives recognize full value on the milestone date.
- Ranged initiatives accrue value linearly from start through end.
- Optional realized overlay compares planned value with realized value.
- Top drivers identify the initiatives carrying the selected-date projection.
- `Stacked Bar Chart`: shows pillar concentration as percent of total value.
- Stacked bars are available for both Savings only and Savings + Avoidance.

## PowerPoint Export

The PowerPoint export is built for leadership review:

- One readable roadmap slide per pillar.
- Fiscal-year and quarter headers.
- Savings, Avoidance, and Realized metric cards.
- Multiple initiatives in the same workstream stack into readable lanes.
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
- Native SVG rendering for roadmap, projection, and stacked bar charts.
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

- `87 passed`
- `0 failed`
- `0 untested`
