- [x] Redesign PowerPoint slides with a more presentation-ready visual hierarchy.
- [x] Add fiscal year labels above quarter markers.
- [x] Keep one readable roadmap slide per pillar.
- [x] Render the generated deck for visual inspection.
- [x] Run full validation.

## Review

- Redesigned the PowerPoint export around a large pillar title, metric cards, fiscal-year bands, quarter labels, and a cleaner roadmap canvas.
- Added explicit FY labels to the PPT axis so years are not missing.
- Rendered both sample slides through headless Office to PNG for visual inspection.
- Updated `EXPORT-004` coverage to require fiscal years in the generated deck.
- Full Playwright behavior suite: 65 passed, 0 failed, 0 untested.
