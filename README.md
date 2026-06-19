# Roadmap Studio

Roadmap Studio is a browser-based planning tool for turning pillars, workstreams, and initiatives into an executive-ready roadmap.

It is built for teams that need to track timing, ownership, status, and savings/avoidance economics without sending sensitive planning data to a server.

## What It Does

- Builds a roadmap from a simple pillar and workstream structure.
- Tracks initiatives with dates, owner, status, milestone flag, savings/avoidance type, and dollar value.
- Renders an interactive SVG timeline with drag-to-adjust dates.
- Shows savings and avoidance totals directly in the roadmap header.
- Colors roadmap initiatives by impact type: green for savings and blue for avoidance.
- Exports and imports Excel workbooks for stakeholder handoff.
- Saves work locally in the browser.
- Includes presentation mode and PNG export.

## Why It Matters

Roadmaps often split across spreadsheets, slide decks, and status meetings. Roadmap Studio keeps the planning model and executive view in one place: edit the data once, and the roadmap redraws itself.

The app is intentionally client-side so teams can use it with sensitive project data without a backend.

## Tech Notes

- Single-file HTML/CSS/JavaScript app.
- SVG-based timeline renderer.
- Excel import/export powered by ExcelJS.
- Local persistence through browser storage.
- No build step and no backend required.

## Run Locally

Open `index.html` in a browser.

The app stores data in your browser. Use the built-in Save button to download a project file you can reopen later.
