- [x] Reproduce the PowerPoint repair warning against a freshly exported roadmap deck.
- [x] Inspect the projected savings slide XML for invalid or risky PowerPoint geometry.
- [x] Add a regression check that validates exported PPTX XML before visual assertions.
- [x] Patch the projection slide generator to avoid repair-prone shapes and out-of-bounds labels.
- [x] Redesign the projection slide into a simpler executive view with more chart breathing room.
- [x] Run `python3 tasks/roadmap_feature_tests.py`.
- [x] Render the exported deck and inspect the projected savings slide.
- [x] Update lessons and review notes with the fix and validation.

## Planned Spec

- Primary defect: exported PowerPoint decks must open without PowerPoint needing to repair the file.
- Likely risk areas: diagonal line segments, zero-height/very small shapes, transparent fills, and labels near slide/chart boundaries on the projected savings slide.
- Visual direction: make the slide a presenter-ready financial trajectory page, not a dense dashboard. Prioritize the final projected value, Savings-only line, Savings + Avoidance line, and Avoidance lift.
- Keep the app local-only and avoid new dependencies or network calls.

## Review

- Confirmed RED first: `EXPORT-009` failed on the current export with negative `cy` extents in `ppt/slides/slide3.xml`.
- Added `EXPORT-009` to validate that exported PPTX XML does not contain negative `cx` or `cy` extents.
- Added a safe PowerPoint line helper that normalizes line geometry to positive extents and uses flips for rising diagonal segments.
- Reworked the Projected Savings PowerPoint slide into a wider executive chart with a light KPI strip, full-width trajectory, in-chart Avoidance lift callout, and clamped endpoint labels.
- Final validation: `python3 tasks/roadmap_feature_tests.py` returned 87 passed, 0 failed, 0 untested.
- Package validation: the generated PPTX has no negative XML extents and all XML files pass `xmllint --noout`.
- Visual validation: rendered `Seed roadmap — roadmap.pptx` to PDF/PNG and inspected `tasks/test-artifacts/projection-repair-render/seed-slide-3.png`.
- Note: the bundled `slides_test.py` could not run because `pdf2image` is not installed in this environment; LibreOffice/PDF/PNG rendering was used instead.
