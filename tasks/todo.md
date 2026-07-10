# Feature build: P0/P1 product upgrades

## Scope
- [x] Initiative filters + search
- [x] Resizable / denser initiatives table
- [x] Click roadmap bar → edit drawer
- [x] Scenario / baseline snapshots
- [x] Time-phased realization
- [x] Owner swimlane view
- [x] Health / risk summary panel
- [x] Run-rate & annualization
- [x] Confidence / probability weighting
- [x] Drag-and-drop structure

## Review
- Implemented in `index.html` (schema v2, backward compatible open of v1 files).
- Manual Playwright walkthrough of all 10 features with no page errors.
- Regression suite: `87 passed`, `0 failed`.
- README updated to describe the new capabilities.

## Notes
- Grouping control uses `.road-seg` (not `.seg`) so main tab order tests stay stable.
- Time-phased phases are cumulative % of full value; empty phases fall back to single `% Realized`.
- Baseline is a frozen plan payload; projection can overlay it when present.
