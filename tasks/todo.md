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

# Deep Bugle Label + Navigation Update

## Scope
- [x] Add RED coverage for contained browser and PowerPoint roadmap labels.
- [x] Keep ranged initiative labels inside their bars with distinguishing ellipsis at narrow widths.
- [x] Preserve full initiative details in the browser tooltip.
- [x] Move desktop view tabs into a full-width second header row while retaining the mobile horizontal toolbar.
- [x] Run the full suite and inspect desktop, mobile, and rendered PowerPoint output.
- [x] Publish and live-test a new HereNow build.

## Review
- Source baseline is the exact `deep-bugle-ft8g.here.now` / PR #2 build at commit `298e70f`.
- Milestone labels remain outside their diamonds because the marker has no readable interior label area.
- Strict RED-GREEN verification finished at **89 passed / 0 failed / 0 untested**.
- Desktop and 390px browser captures show the requested navigation structure with no page or console errors.
- The generated same-workstream deck rendered both compact labels on one line and passed `slides_test.py` with no overflow.
- Deployment `https://olive-virtue-k6m2.here.now/` returned HTTP 200 for the app and local PowerPoint runtime; live testing confirmed the 96px desktop sub-tab header and contained labels with no console errors.

# Portfolio Rollup

## Scope
- [x] Add RED coverage and feature tracker rows for the rollup view and PowerPoint slide.
- [x] Add a Portfolio Rollup tab immediately after Roadmap.
- [x] Derive Approved from every started status and Proposed from Not Started.
- [x] Show pillar-level Approved, Proposed, and Realized totals for Savings and Avoidance together.
- [x] Render each initiative across every active calendar year with realized progress layered on its bar.
- [x] Add one executive, Apple-like Portfolio Rollup slide to PowerPoint.
- [x] Run the full suite and inspect desktop, mobile, and rendered PowerPoint output.
- [x] Publish and live-test a new HereNow build.

## Review
- Strict RED-GREEN verification finished at **95 passed / 0 failed / 0 untested**.
- Approval remains derived rather than persisted, so v1/v2 project files and saved scenarios stay backward compatible.
- Desktop and 390px captures show correct totals, separate approval lanes, full 2026–2030 spans, and mobile horizontal scrolling with no console errors.
- The five-slide PowerPoint rendered the new Portfolio Rollup slide and passed `slides_test.py` with no overflow or repair-prone negative extents.
- Deployment `https://sonic-charm-p3f2.here.now/` returned HTTP 200 for the app and PowerPoint runtime; live testing confirmed scenarios, rollup totals, bar-to-drawer interaction, and zero console errors.

# Selectable Approval

## Scope
- [x] Add RED coverage for selecting and persisting Approved/Proposed.
- [x] Replace the derived approval label with an initiative select control.
- [x] Preserve legacy status-based defaults for project files without approval data.
- [x] Confirm rollup totals, scenarios, project save/open, and PowerPoint use the explicit selection.
- [x] Publish and live-test a new HereNow build.

## Review
- Strict RED-GREEN verification finished at **95 passed / 0 failed / 0 untested**.
- Legacy files without approval data normalize from status; explicit selections then persist independently.
- Browser QA confirmed full dropdown labels, drawer editing, scenario restore, autosave serialization, and immediate rollup reclassification with zero console errors.
- PowerPoint QA confirmed the rollup slide uses the reclassified Approved and Proposed totals.
- Deployment `https://coral-guitar-traa.here.now/` returned HTTP 200 for the app and PowerPoint runtime; live testing confirmed selectable defaults, persisted overrides, reclassified totals, scenarios, and zero console errors.

# Aggregate Portfolio Rollup

## Scope
- [x] Add RED coverage for exactly one Approved and one Proposed row per pillar.
- [x] Aggregate count, value, Savings, Avoidance, realized value, and date span by pillar/approval.
- [x] Remove initiative-level marks and visible initiative names from Portfolio Rollup.
- [x] Mirror the aggregate design on the PowerPoint rollup slide.
- [x] Run regression, desktop/mobile, and rendered PowerPoint QA.
- [x] Publish and live-test a new HereNow build.

## Review
- Portfolio Rollup now renders at the requested decision level: exactly one Approved lane and one Proposed lane per pillar, with no initiative-level visual marks.
- Each aggregate bar spans the earliest start through latest end and shows initiative count, total value, Savings/Avoidance mix, and aggregate realized progress.
- Approval remains explicitly selectable per initiative and legacy files still default from initiative status when approval is absent.
- Strict RED-GREEN verification finished at **96 passed / 0 failed / 0 untested**.
- Desktop and 390px browser captures show the aggregate layout without overlap; the PowerPoint rollup slide passed `slides_test.py` with no overflow.
- Deployment `https://karma-sequin-ppbr.here.now/` returned HTTP 200 for the app and local PowerPoint runtime; live Playwright checks confirmed scenarios, aggregate totals and spans, no initiative-level labels, and zero console errors.

# Portfolio Rollup Label Readability

## Scope
- [x] Add a regression case for multiple initiatives in a narrow aggregate span.
- [x] Replace SVG glyph compression with width-aware concise labels.
- [x] Preserve the full count and financial breakdown in the bar tooltip.
- [x] Run the full suite and inspect desktop/mobile rollup output.
- [x] Publish and live-test a corrected HereNow build.

## Review
- Root cause was SVG `textLength` with `spacingAndGlyphs`, which distorted long summaries to fit narrow date spans.
- Aggregate bars now choose the longest natural-width label that fits: full breakdown, count/value, or compact count/value; bars that cannot fit even the compact label remain unlabeled and use the tooltip.
- The full aggregate breakdown, dates, realized value, and contributor names remain available in the bar tooltip.
- Strict RED-GREEN verification finished at **97 passed / 0 failed / 0 untested**.
- Desktop and 390px captures of a three-initiative one-month span show normal text proportions and zero browser errors.
- Deployment `https://jade-donkey-xd8e.here.now/` returned HTTP 200 for the app and PowerPoint runtime; live checks confirmed the compact label, complete tooltip, scenarios, and zero compressed SVG text or console errors.

# Portfolio Rollup PowerPoint Redesign

## Scope
- [x] Add a four-pillar, five-year stage-readability regression.
- [x] Replace the dashboard-like header with a tighter executive hierarchy.
- [x] Increase pillar, lane, timeline, and financial summary typography.
- [x] Move short-span labels into readable external callouts.
- [x] Render every slide and inspect the rollup at full resolution.
- [x] Run the full suite and publish a verified HereNow build.

## Review
- The rollup now opens with a dynamic approval-share takeaway and a clean total portfolio anchor instead of four small dashboard cards.
- Approved, Proposed, and Realized values use 18pt headline type; timeline years use 13pt; pillar names use 15pt; lane and bar labels use 10.5–11pt.
- Short bars keep their true date width and connect to a 1.72–2.45 inch external callout, eliminating truncated or 5pt shrink-to-fit labels.
- Each pillar header carries its Savings, Avoidance, and Realized mix, so timing bars no longer have to function as dense data tables.
- The seven-slide stress-test deck rendered cleanly at full resolution and passed `slides_test.py` with no overflow or repair-prone geometry.
- Strict RED-GREEN verification finished at **98 passed / 0 failed / 0 untested**.
- Deployment `https://merry-jubilee-943r.here.now/` returned HTTP 200 for the app and PowerPoint runtime; a live seven-slide export preserved the 11pt callout, 15pt pillar headings, and repair-safe OOXML with zero console errors.

# Portfolio Rollup PowerPoint Web Parity

## Scope
- [x] Update the PowerPoint regression to require the web tab hierarchy and copy.
- [x] Mirror the four web metric cards and stage heading.
- [x] Mirror the legend, year grid, pillar bands, approval lanes, and colors.
- [x] Reuse compact in-bar labels for short spans without shrink-to-fit.
- [x] Render and compare the web tab and PowerPoint slide at full resolution.
- [x] Run the full suite and publish a verified HereNow build.

## Review
- The Portfolio Rollup PowerPoint now uses the web tab's `Portfolio Rollup` heading and adjacent initiative/year meta instead of a separate approval-share narrative.
- The four metric cards reproduce the web labels, values, color marks, and notes: Total Portfolio, Approved, Proposed, and Realized.
- The chart reproduces the web legend, calendar-year columns, alternating pillar bands, Approved/Proposed lanes, aggregate bars, and green realized overlays.
- PowerPoint-specific text measurement uses the same full/medium/compact selection order as the web SVG; short spans show compact labels such as `3 · $0` without `fit: shrink` or external callouts.
- Side-by-side 1600px web and 1600×900 PowerPoint renders were inspected at full resolution; the slide passed `slides_test.py` with no overflow or repair-prone geometry.
- Strict RED-GREEN verification finished at **98 passed / 0 failed / 0 untested**.
- Deployment `https://merry-pocket-haap.here.now/` returned HTTP 200 for the app and PowerPoint runtime; a live seven-slide export preserved the web title, four card notes, compact short-span label, and repair-safe OOXML with zero console errors.

# Scenario Portfolio Preservation

## Scope
- [x] Add a regression using 46 initiatives with an older 40-item scenario.
- [x] Recover initiatives and structure found in any saved scenario when switching.
- [x] Keep selected-scenario values authoritative for matching initiative IDs.
- [x] Prevent duplicates across repeated scenario switches.
- [x] Persist the merged 46-item portfolio through autosave.
- [x] Run the full suite and browser-level scenario QA.
- [x] Publish and live-test a new HereNow build.

## Review
- Root cause was `loadScenario()` replacing `S.items` and `S.structure` with an older complete snapshot.
- Scenario loading now builds a stable-ID union from the selected snapshot, active portfolio, and all saved scenarios; the selected snapshot remains authoritative for matching IDs.
- The regression starts from an already-reduced 40-item active plan, recovers all 46 from the newer scenario, switches repeatedly, and confirms 46 unique initiatives plus the newer structure remain in autosave.
- Strict RED-GREEN verification finished at **99 passed / 0 failed / 0 untested**.
- Deployment `https://lilac-chant-t3kf.here.now/` retained all 46 initiatives after switching to the older scenario, loaded the local PowerPoint runtime, and produced zero console errors.

# Executive Dollar Tracker

## Scope
- [x] Add RED coverage and tracker rows for the Executive Summary tab.
- [x] Place Executive Summary between Roadmap and Portfolio Rollup.
- [x] Reconcile Total Portfolio into non-overlapping Realized, Approved Remaining, and Proposed Remaining segments.
- [x] Split every stage into Savings and Avoidance without double-counting.
- [x] Add a dollar axis and editable goal marker defaulting to $1B.
- [x] Add a useful empty state and responsive desktop/mobile layout.
- [x] Run the full suite and inspect the final view in-browser.

## Review
- Executive Summary now leads with a dynamic above/below-goal headline, followed by Total Portfolio, Approved, Proposed, and Realized metrics.
- The single tracker contains six mutually exclusive segments: Realized, Approved Remaining, and Proposed Remaining, each split into Savings and Avoidance; the segment sum is asserted against Total Portfolio.
- The dollar axis defaults to a $1B goal when no target is saved, and editing the goal updates the shared projection target without a schema change.
- Desktop and 390px visual QA confirmed the complete goal marker remains visible, metric text does not overflow, the page does not create horizontal overflow, and there are zero console errors.
- Strict RED-GREEN verification finished at **103 passed / 0 failed / 0 untested**.

# Executive Summary PowerPoint

## Scope
- [x] Add RED coverage and a tracker row for a web-parity Executive Summary slide.
- [x] Export Executive Summary as slide 1 and Portfolio Rollup as slide 2.
- [x] Mirror the dynamic goal-gap headline and four portfolio metrics.
- [x] Mirror the six mutually exclusive tracker segments and dollar axis.
- [x] Mirror the Savings/Avoidance key, maturity shading, goal marker, and breakdown.
- [x] Render the generated deck and inspect the slide at full resolution.
- [x] Run overflow, repair-safety, and full regression verification.

## Review
- PowerPoint now opens with Executive Summary, follows with Portfolio Rollup, then presents pillar roadmaps, Projected Savings, and Value Concentration.
- The opening slide uses native editable PowerPoint shapes and mirrors the web view's dark goal-gap banner, four metrics, six maturity/value-type segments, dollar axis, current total, and goal marker.
- The stage stress-test rendered a `$939M` portfolio against the `$1B` goal with 35pt title type and a 25pt goal-gap headline; every section remained readable at 1600×900.
- The eight-slide rendered deck passed `slides_test.py` with no overflow, and OOXML checks found no repair-prone negative geometry.
- Strict RED-GREEN verification finished at **105 passed / 0 failed / 0 untested**.
