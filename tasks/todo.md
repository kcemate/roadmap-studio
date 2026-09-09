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

# Executive View Preview Only

## Plan
- [x] Freeze production code, remote publishing, and deployment work.
- [x] Define a one-glance executive narrative with a plain-language takeaway, one primary visual, and mutually exclusive metrics.
- [x] Create a review-only visual prototype using non-production placeholder values.
- [x] Render and inspect the prototype at presentation size.
- [ ] Obtain explicit approval before changing Roadmap Studio or publishing any build.

## Review
- Created `/tmp/roadmap-studio-exec-preview/executive-view-preview.pptx` and a direct 1920×1080 PNG render for review only.
- The design uses one takeaway title, one portfolio-to-goal bar, and three mutually exclusive segments: Savings, Avoidance, and Remaining to goal. Labels and color meanings appear directly on the bar and again in one short key.
- The deck ZIP structure validates without errors. The standard Office renderer is unavailable in this environment, so the prototype was visually checked from the artifact engine's direct PNG output.
- No production source code, GitHub state, or here.now deployment changed in this preview-only phase.

# Executive View Preview Revision

## Plan
- [x] Reject the placeholder-led dashboard composition.
- [x] Reframe the slide around one source-derived executive takeaway.
- [x] Build one dominant portfolio-to-goal visual with directly labeled Savings and Avoidance.
- [x] Render at full presentation size and remove any clipping or visual noise.
- [x] Share the review artifact without implementing or deploying it.

## Review
- Revised preview uses the latest visible Roadmap Studio values: $701.3M Savings, $344.4M Avoidance, a $1B goal, $197.2M Approved, $846M Proposed, and $80.1M Realized.
- The slide now has one stage-readable claim, one directly labeled value bar, and a small secondary approval/status line. The Savings/Avoidance split and goal marker require no separate legend.
- The 1920×1080 direct render was inspected at full size. All text is single-line, labels are contained, and the PowerPoint archive validates without errors.
- Production source, GitHub, and here.now remain unchanged pending approval.

# Executive View Keynote Revision

## Plan
- [x] Remove the analytics-screen visual language from the revised preview.
- [x] Build a high-contrast keynote composition with one message and one visual.
- [x] Keep the source-derived values and clarify the approval/realized relationship.
- [x] Inspect the full-size render and PowerPoint package.
- [x] Share for approval without implementing or deploying.

## Review
- Rebuilt the preview as a dark keynote slide with one spoken takeaway, a single Savings/Avoidance value bar, and one goal marker.
- Approved, Proposed, and Realized are subordinate to the main story; Realized is explicitly labeled as within Approved to prevent additive misreading.
- The 1920×1080 render was inspected at full size. The title, bar labels, goal marker, and status values are contained and single-line.
- The PowerPoint archive validates without errors. Production source, GitHub, and here.now remain unchanged pending approval.

# Executive View Bar Geometry

## Plan
- [x] Replace independently rounded category segments with one continuous bar.
- [x] Keep only the outer left and right corners rounded.
- [x] Render and verify the square Savings/Avoidance junction.

## Review
- The Savings/Avoidance bar now has one rounded left edge, one rounded right edge, and a square internal junction.
- The corrected 1920×1080 render was inspected and the PowerPoint archive validates without errors.

# Executive View PowerPoint Integration

## Plan
- [x] Preserve the approved one-bar narrative and adapt it to the existing light PowerPoint design system.
- [x] Add failing regression coverage for the live opening slide and export order.
- [x] Replace the old dashboard-style Executive Summary PowerPoint slide.
- [x] Verify dynamic above/below-goal copy, live values, and repair-safe geometry.
- [x] Render the full deck and inspect the Executive View beside Portfolio Rollup.

## Review
- Every PowerPoint export now opens with a light, keynote-style Executive View that matches the existing deck and uses the project's live portfolio values.
- The slide leads with one dynamic above/below-goal takeaway, one continuous Savings/Avoidance bar, a direct goal marker, and a subordinate Approved/Proposed/Realized-to-date status line.
- The bar has rounded outer ends and a square internal Savings/Avoidance junction; direct labels keep the meaning legible without relying on color alone.
- Portfolio Rollup remains slide 2. All eight slides in the generated deck were rendered and visually inspected, and the PowerPoint archive validates without repair errors.
- Strict RED-GREEN verification finished at **106 passed / 0 failed / 0 untested**. No deployment or GitHub publish was performed.

# Initiative Total Exclusion

## Plan
- [x] Add tracker rows and failing coverage for the row control, backward-compatible persistence, financial views, and PowerPoint.
- [x] Add an `In totals` switch to each initiative row, defaulted on for existing and newly created initiatives.
- [x] Exclude opted-out values from all Savings, Avoidance, Realized, projection, rollup, concentration, roadmap header, and PowerPoint totals.
- [x] Keep excluded initiatives visible on roadmaps and preserve their entered values, dates, status, approval, and initiative counts.
- [x] Run the full browser suite, visually inspect desktop/mobile behavior, and validate the generated PowerPoint package.
- [x] Publish the verified single-file build to a new here.now URL and verify the live page.

## Review
- Every initiative row now has an accessible `In totals` switch. It defaults on for new and legacy items and persists through project saves, autosave, undo/redo, and scenario payloads.
- Switching it off preserves the initiative, entered value, timing, roadmap mark, approval, and counts while contributing zero to every financial aggregation and PowerPoint total.
- Desktop and 390px mobile browser QA found no console errors or page overflow. The excluded state is visually distinct and the switch remains operable by pointer and keyboard.
- The generated six-slide exclusion deck was rendered and inspected: `$450K` remains on the excluded initiative's pillar roadmap while Executive View, Portfolio Rollup, pillar metrics, Projected Savings, and Value Concentration reconcile to `$920K`.
- A long dominant-pillar PowerPoint title uncovered during QA was widened to prevent wrapping into the subtitle. The `.pptx` archive validates without errors.
- Strict RED-GREEN verification finished at **109 passed / 0 failed / 0 untested**.
- Published the exact verified `index.html` to `https://opaque-tinsel-x3cf.here.now/`; the live file hash matches local and returns HTTP 200. This anonymous build expires in 24 hours unless claimed.

# Hosted PowerPoint Runtime Fix

## Plan
- [x] Reproduce the hosted export failure and identify the missing runtime asset.
- [x] Confirm the local PowerPoint bundle exists and the prior live asset URL returns 404.
- [x] Publish `index.html` together with the complete vendored PowerPoint runtime path.
- [x] Verify the live page, runtime asset, and an actual PowerPoint download.

## Review
- Root cause: the previous here.now package contained only `index.html`, but the CSP-compliant app loads `vendor/pptxgen.bundle.js` from the same origin. The missing file left `PptxGenJS` undefined.
- Republished the complete runtime package to `https://topaz-parcel-zzpb.here.now/`; live `index.html` and `vendor/pptxgen.bundle.js` hashes match local exactly.
- Hosted browser smoke testing confirms `PptxGenJS` is a function, PowerPoint downloads successfully, the six-slide archive has no negative extents, and there are no console errors.

# Executive View Realization Preview

## Plan
- [x] Keep production source unchanged and create a review-only slide artifact.
- [x] Show Identified Opportunity and Realized in Actuals as percentages of the $1B goal above the bar.
- [x] Split the continuous bar into Savings, Realized Savings, Avoidance, and Realized Avoidance without double counting.
- [x] Add a direct four-color legend and retain the neutral remaining-to-goal segment.
- [x] Render and inspect the full-size preview before sharing it for approval.

## Review
- Built the review-only slide from the existing portfolio fixture: `$939.0M` identified (`93.9%` of the `$1B` goal) and `$31.9M` realized (`3.2%` of goal).
- The continuous bar separates realized savings, remaining savings, realized avoidance, remaining avoidance, and the `$61.0M` goal gap without double counting realized value.
- Added a direct four-color legend plus numeric realized labels so the very small realized-avoidance segment remains understandable.
- Rendered and visually inspected the slide at full size. The presentation overflow test passes and the PPTX package validates without errors.
- No production implementation, commit, push, or deployment was performed.

# Executive View Centered KPI Preview

## Plan
- [x] Keep this revision isolated to the review artifact.
- [x] Recompose Identified Opportunity and Realized in Actuals as two equal, centered blocks.
- [x] Render and inspect the revised slide for hierarchy, clipping, and overlap.
- [x] Share a temporary image preview without modifying or committing Roadmap Studio.

## Review
- Reframed the two requested measures as equal 470px-wide center blocks with 52pt percentage figures and plain-language dollar subtitles.
- Kept the four-color legend and continuous goal bar immediately below the blocks so the slide reads from outcome to composition.
- Full-size visual inspection found no clipping or overlap. The presentation overflow test and PPTX archive validation both pass.
- This remains a review-only artifact; Roadmap Studio production code was not modified or committed.

# Centered Executive View Implementation And Publish

## Plan
- [x] Add regression coverage for the centered Identified Opportunity and Realized in Actuals blocks in the Executive View PowerPoint slide.
- [x] Implement the approved centered-block composition using live portfolio values and the existing four-part financial color system.
- [x] Run the full Roadmap Studio test suite and validate the generated PowerPoint package.
- [x] Render and visually inspect the exported Executive View slide at full size.
- [x] Publish the complete app package, including the vendored PowerPoint runtime, to a new here.now URL.
- [x] Verify the live app assets and an actual hosted PowerPoint download before reporting the URL.

## Review
- Executive View now centers two equal large blocks for Identified Opportunity and Realized in Actuals, each calculated as a percentage of the live portfolio goal with its corresponding dollar value.
- The continuous bar and legend distinguish realized savings, remaining savings, realized avoidance, and remaining avoidance without double counting realized value.
- Corrected sub-1% goal percentage formatting uncovered by the new export test; `$1.4M` against `$1B` now reads `0.1%`, not `13.7%`.
- Full regression suite passes at **110 passed / 0 failed / 0 untested**. The browser-generated deck passes overflow and ZIP integrity validation and was visually inspected at full size.
- Published the complete package to `https://ebony-cobble-bphm.here.now/`. Hosted `index.html` and `vendor/pptxgen.bundle.js` hashes match the verified local package.
- Live browser smoke testing confirms the PowerPoint runtime loads, an eight-slide deck downloads, the centered blocks and four legend labels are present, no negative extents exist, and no console errors occur.

# GitHub Publish Latest Roadmap Studio

## Plan
- [x] Audit the working tree and exclude generated cache files.
- [x] Confirm GitHub authentication, repository, default branch, and current PR state.
- [x] Verify the complete intentional diff and final test result.
- [x] Commit the latest Roadmap Studio product, tests, tracker, and documentation changes.
- [x] Push the feature branch and open a pull request against `main`.
- [x] Confirm checks and merge into `main` when safe.

## Review
- Committed the complete intentional scope as `28f9d65` and excluded generated `tasks/__pycache__/` files.
- Pushed `agent/executive-view-export` and opened PR `#4` against `main`.
- GitHub reports the PR as cleanly mergeable with no required checks or review blocks; the locally recorded regression suite remains **110 passed / 0 failed / 0 untested**.

# Reliability-First Product Upgrade

## Plan
- [x] Verify the current `main` baseline and add tracker rows for the reliability improvements.
- [x] Add failing browser tests for grid focus retention, bounded scrolling, sticky headers, and filter-aware row creation.
- [x] Add failing browser tests for native text undo, drawer dismissal protection, autosave failure visibility, scenario deletion selection, and destructive-action confirmation.
- [x] Add failing browser tests for clearer save language, editable project title, save-state feedback, and keyboard-visible row actions.
- [x] Implement the smallest shared interaction and persistence changes needed to pass the new tests.
- [x] Run the full regression suite and inspect desktop/mobile interaction states in the browser.
- [x] Run the frontend design detector and document final verification results.

## Review
- Strict RED-GREEN verification began at **110 passed / 10 expected failures** and finished at **120 passed / 0 failed / 0 untested**.
- Initiative editing now preserves Tab flow, keeps large tables and both scrollbars inside the viewport, restores sticky headers, and creates new rows in the active pillar/filter context.
- Native text undo is no longer intercepted; application redo supports Ctrl/Cmd+Y outside editable controls; keyboard-focused row actions are visible.
- Dirty drawer edits require confirmation before dismissal, destructive deletes require confirmation and offer a seven-second Undo action, and the drawer returns focus after saving.
- Autosave failures now surface a persistent recovery warning with a project download action. The toolbar shows an editable persisted project name, save state, distinct `Snapshot` and `Download` actions, and an explicit selected-scenario delete control.
- Desktop QA at 1440×900 verified the 60-row grid remains inside the viewport (`bottom 876px`) with no body overflow. Mobile QA at 390×844 verified contained horizontal grid scrolling and a collision-free horizontally scrollable toolbar.
- The Impeccable detector ran in degraded regex mode because its optional HTML parser modules were unavailable; it reported only two pre-existing easing-token warnings and no new targeted UI anti-patterns.

# GitHub Publish Reliability Upgrade

## Plan
- [x] Fetch GitHub and confirm the branch starts from current `origin/main`.
- [x] Confirm the working tree contains only the intended product, test, tracker, and review changes.
- [x] Verify the recorded full-suite result and check the diff for formatting errors.
- [x] Commit and push `agent/reliability-first-ux`.
- [x] Open and verify a pull request against `main`.

## Review
- Committed the intentional five-file upgrade as `a6d5ebc` and pushed `agent/reliability-first-ux` to GitHub.
- Opened pull request `#5`, **Harden Roadmap Studio editing and data safety**, against `main`.
- GitHub reports the PR as `MERGEABLE` with a `CLEAN` merge state and no configured status checks.
- The branch retains the verified **120 passed / 0 failed / 0 untested** result and contains no unrelated files.

# Product Audit, September 4

## Plan
- [x] Walk through every product view using disposable browser test data.
- [x] Probe financial inputs, save/open, scenarios, undo, and exports for failure cases.
- [x] Inspect accessibility, desktop/mobile layout, and larger portfolios.
- [x] Cross-check findings against source and prepare a concise prioritized assessment.

## Review
- Read-only product audit completed against the current source and `fancy-buddha-rjbf.here.now`, with disposable synthetic data. No production code, user data, remote branch, or live deployment changed.
- Existing regression suite rerun with outputs isolated under `/tmp/roadmap-product-audit/regression`: **120 passed / 0 failed / 0 untested**.
- Independent failure tests reproduced percent inflation, mismatched undated totals, confidence-discounted actuals, scenario draft/deletion problems, incorrect deletion Undo, uncommitted text loss, missing-end crashes, and executable imported ID attributes.
- Visual/accessibility checks covered all seven views, 390-1920px widths, 60- and 1,000-initiative portfolios, and the drawer. Dense exported PowerPoint content extended below slide bounds; mobile projection metrics and long roadmap headings overflowed.
- Evidence-backed assessment and verification limits: `/tmp/roadmap-product-audit/report.md`. Detailed browser manifest, stress captures, regression output, and independently rendered export evidence remain outside the repository.

# Roadmap Studio 1.6: All Thirteen Audit Improvements

## Plan
- [x] Preserve rollback branch `rollback/pre-audit-1.6` at `b8497b1` and create the detailed contract in `tasks/audit-upgrade-plan.md`.
- [x] Add failing financial, import, scenario, undo, validation, and persistence regression tests before implementation.
- [x] Implement financial/data-safety foundations, independent actuals, benefit basis, and exclusion links.
- [x] Complete readable exports and browser presentation navigation.
- [x] Complete responsive/accessibility fixes, drilldowns, bulk edits, layouts, comparisons, and exceptions.
- [x] Complete versioned packaging, rollback, documentation, and automated release gates.
- [x] Run integrated regression, supported-browser, visual, and package verification; resolve regressions.

## Review
- Core regression baseline: 12 failures, 3 errors, 1 pass on the audited build. Final frozen-build verification passed: 120 existing checks, 34 core regressions in each of Chromium/WebKit/Firefox, 10 workspace tests, 7 export checks, and the accessibility sweep. Actual output is recorded in tasks/audit-integration-results.json.
- Real axe-core 4.10.3 scans now pass at 390px and 1440px across seven views, the drawer, review, and financial drilldown, with no serious/critical findings or console errors.
- Legacy date editing now rejects reversed dates with an inline error instead of silently moving another date; its regression assertion was updated to verify the new approved validation behavior.
- No live site or remote repository has been changed during this build.
- PowerPoint renders were inspected for dense workstreams, long names, the two-block Executive View, projection, and paginated Portfolio Rollup. Native Microsoft PowerPoint was unavailable; no native repair-dialog claim is made.
- The 1,000-row grid rendered in approximately 701 ms locally, with all rows, no page overflow, and no application errors. This is a lab observation, not a field-performance guarantee.
- Impeccable detector ran in degraded regex mode and reported two existing spring-token warnings; actual axe-core scans covered contrast separately.
- Built and verified the five-file 1.6.0 release ZIP/current folder. Reproducible archive SHA-256: dc20adcff1fa7651af14ee2d7ab8c5f73861124431bff1c1fe4f16d033286c54. Original app assets are retained in release/archives/pre-audit-b8497b1.zip.

# Publish Roadmap Studio 1.6 to a New HereNow Site

## Plan
- [x] Confirm user deployment authorization and verify the current application-only release package.
- [x] Publish the complete release to a new HereNow URL without modifying previous sites.
- [x] Verify live application/runtime assets and a real PowerPoint download using disposable data.
- [x] Record the verified URL and hosting lifetime; share the link with the user.

## Review
- Source/build freshness and the five-file release package passed verification before publishing.
- Deployment is authorized by the user's request, "Deploy a new here.now"; GitHub changes are out of scope.
- Published https://steady-canyon-zvjb.here.now/ as a new anonymous site. The publisher reports expiry at 2026-09-08T21:10:53.736Z; a claim link was returned for the user to retain it permanently. No previous site or GitHub remote was modified.
- All five hosted release files verified. HereNow adds social-preview meta tags to HTML; after accounting only for those parsed meta tags, the application HTML matches the verified release exactly. The runtime, license, manifest, and checksums match byte-for-byte.
- Live Chromium smoke passed all seven tabs at 1440px and 390px (14 combinations), with no page overflow, app errors, console warnings/errors, or failed requests. Observed app requests were only the hosted HTML and its local PowerPoint runtime.
- A real live PowerPoint download produced a valid seven-slide, 237235-byte archive. Synthetic browser-only verification data was not published. Inspected screenshot: /tmp/roadmap-1.6-herenow-smoke/executive-live.png; downloaded deck: /tmp/roadmap-1.6-herenow-smoke/live-export.pptx.

# PowerPoint Presentation Refinement, September 7

## Plan
- [x] Add failing regressions for balanced pagination, label collisions, short-bar references, composition order, and narrative slide order.
- [x] Refine executive, rollup, projection, contribution, and roadmap layouts with readable type and explicit color meanings.
- [x] Preserve all financial calculations, two centered executive blocks, and complete initiative content; retain details in notes/reference pages.
- [x] Render sparse, four-pillar, dense, long-label, short-duration, and above-goal portfolios; inspect and fix visual defects.
- [x] Run full integration verification and build a versioned local 1.6.1 release with a representative preview deck.

## Contract And Review
- Scope: local PowerPoint export implementation and regression coverage. No deployment, GitHub push, or change to existing web views is authorized by this request.
- Keep green Savings, blue Avoidance, darker realized portions, and black Not Started roadmap bars. Rollup approval uses labeled neutral treatments; pillar-composition colors have a separate explicit legend.
- Presentation order: Executive Summary, Portfolio Rollup, Projected Savings, Pillar Contribution, detailed roadmap pages. Preserve current-view export.
- Key financial values/names must remain available, including exclusions, undated items, scenarios, baselines, recurring value context, and reporting date.
- Stop condition: real full-suite pass and visually verified exports. No test weakening, no source edits during the final verification run, no claim of native PowerPoint validation when only LibreOffice is available.
- New presentation regressions started RED (8 failed, 2 passed) and now pass all 10 focused checks; export-specific legacy assertions now describe the approved order, pagination, and readable external-reference contract.
- Real exported decks were rendered in LibreOffice and inspected at 1440px, including sparse, four-pillar, 16-pillar, 28-initiative, above-goal, and baseline/actuals cases. Rendering caught and resolved roadmap label crowding and the above-goal marker crossing the legend. Source financial calculations were not changed.
- Consolidated verification passed all 10 gates: 120 existing checks, 34 core regressions per Chromium/WebKit/Firefox, 10 workspace tests, accessibility, exports, 10 new presentation checks, and reproducible release/rollback verification. The app hash stayed unchanged throughout: b5865b6fb354e431b77c4a7563d772b252d71e4b95bb397493d921f502de9851.
- Updated legacy tests to identify slides by their role rather than shared labels or fixed positions, and to read the current version instead of hardcoding v1.6.0. Restored the pinned axe-core 4.10.3 test-only dependency outside the repository before the final passing run.
- Built local release/versions/1.6.1, release/current, and release/archives/roadmap-studio-1.6.1.zip. Archive SHA-256: 98450a226c2efb36195a0b6682da77fc1110cc5ec8a3bcb21ee62cf6e1f23892. Version 1.6.0 is retained unchanged for rollback.
- A nine-slide synthetic example deck and PDF are available in /Users/giovanni/.codex/visualizations/2026/06/15/019ecbc0-e357-7372-9008-821fb444e5cd/roadmap-studio-1.6.1. Additional rendered test evidence remains in /tmp/roadmap-ppt-refinement/final. Native Microsoft PowerPoint was unavailable; no native repair-dialog claim is made.
- Nothing was deployed, committed, or pushed. Existing web-view layouts and financial/editing code outside the export module match 1.6.0 exactly after normalizing the version constant.

# Publish Roadmap Studio 1.6.1, September 8

## Plan
- [x] Confirm the application-only release matches the fully tested 1.6.1 build.
- [x] Publish to a new HereNow site without changing existing sites or GitHub.
- [x] Verify hosted files, desktop/mobile views, and an actual PowerPoint download.
- [x] Record the live URL, hosting lifetime, and validation result.

## Review
- Route: HereNow publishing skill, scoped to the user's explicit "Make a new here.now" request.
- Generated-source and five-file release checks pass. Application SHA-256 matches the successful consolidated verification report: b5865b6fb354e431b77c4a7563d772b252d71e4b95bb397493d921f502de9851.
- Publish only release/current. Project data, browser storage, test fixtures, source files, and internal notes are excluded.
- Publisher finalized a new anonymous site at https://ground-hollow-pmqa.here.now/, expiring 2026-09-09T13:25:55.657Z. A one-time claim link was returned for the user; no prior site or GitHub state was changed.
- All five hosted files verified against the release. HTML matches after ignoring only hosting-added social metadata; other assets match byte-for-byte.
- Live Chromium checks passed for all seven tabs at 1440px and 390px, with no page overflow, application errors, console warnings/errors, or failed requests. Only the hosted HTML and local PowerPoint runtime were requested by the app.
- Live PowerPoint download produced a valid nine-slide, 369146-byte deck with the new executive blocks and 2+2 rollup pagination. Evidence and screenshots: /tmp/roadmap-1.6.1-live-smoke/report.json. Synthetic verification data stayed in an isolated browser and was not uploaded.

# Initiative Selection Alignment, September 8

## Plan
- [x] Reproduce checkbox/row-number misalignment and add a failing geometric regression.
- [x] Restore table-cell alignment while preserving row selection and table density.
- [x] Verify normal/tall rows, scrolling, selection, and desktop/mobile rendering across browsers.
- [x] Record results and prepare a versioned local fix; no deployment or GitHub push.

## Review
- Scope: the Initiatives grid selection column. Preserve financial logic, existing row editing, and the 1.6.1 PowerPoint refinements.
- Root cause: the selection td used display:grid, detaching its height and alignment from the table row. Restored native table-cell layout and moved the checkbox/number grid into an inner wrapper.
- RED confirmed the checkbox was 9.5px above its initiative on normal rows and 23.25px above on 72px rows. The new geometry and keyboard-selection regressions now pass.
- Desktop (1440px) and mobile (390px) visual/geometry checks passed in Chromium, WebKit, and Firefox: checkbox/name centers match exactly, with no page overflow. Compact-density rerenders preserve both vertical and horizontal scroll positions in all six combinations. Evidence: /tmp/roadmap-selection-alignment.
- Full verification passed all 12 gates, including 120 existing checks, 34 core tests per browser, 12 workspace tests, two additional selection tests per WebKit/Firefox, accessibility, exports, 10 presentation checks, and release/rollback verification. Application SHA-256 stayed unchanged throughout: ab5055f966ce250b54d796518160e30318f771a3f619d3de8b0bc8ab00a27f44.
- Built and verified the five-file local release/versions/1.6.2 package, release/current, and release/archives/roadmap-studio-1.6.2.zip. Version 1.6.1 remains retained for rollback. Nothing was deployed, committed, or pushed.

# Executive PowerPoint Stretch Goal, September 8

## Plan
- [x] Add failing regressions for a stretch goal of entered goal times 1.2, marker placement, and unchanged original-goal percentages.
- [x] Update only the executive PowerPoint layout to include the labeled stretch marker and a sufficient dollar scale.
- [x] Render and inspect actual exports for below-goal, above-stretch, small-goal, and empty portfolios; run the complete verification suite.
- [x] Build a versioned local release and record the results without deployment or GitHub changes.

## Contract And Review
- Route: repository export implementation, with the Presentations inspection/verification workflow and the existing vendored export runtime.
- Scope: Executive Summary PowerPoint slide in full-deck and current-view downloads. A separate Stretch goal (+20%) equals 120% of the entered goal; the original goal, two headline percentages, portfolio values, web views, and saved project state remain unchanged.
- Preserve the approved two-block composition and financial color legend. Verify meaningful labels without clipping or overlap, including when portfolio value exceeds both targets.
- Six new goal regressions started RED; all 16 presentation checks now pass. Coverage includes $1B to $1.2B, $125 to $150, above-stretch totals, zero opportunity, the existing default goal, accurate marker positions, caption bounds, unchanged percentages, both export scopes, and saved-state preservation.
- Updated three legacy executive assertions from the former one-line goal label to exact, separately named original-goal and stretch-goal amount/caption checks. All other requirements remain enforced.
- Inspected real LibreOffice slide renders at 1440px for below-goal, above-stretch, small-goal, and empty portfolios. Both markers/captions and the financial legend remain legible, with no clipping or overlap. Evidence: /tmp/roadmap-stretch-preview. Native Microsoft PowerPoint was not available; package integrity reports zero findings, and export regressions confirm no negative OOXML extents or shrink-to-fit.
- Consolidated verification passed all 12 gates, including 120 existing features, 34 core regressions per browser, 12 workspace tests, selection checks in WebKit/Firefox, accessibility, exports, 16 presentation checks, and release/rollback. Application hash stayed unchanged throughout: 0cd2c130f3073b81210937e323d5a0a1a2f2aa484a7814437f264a6a90bd0574.
- Built and verified release/versions/1.6.3, release/current, and release/archives/roadmap-studio-1.6.3.zip. Archive SHA-256: 7b96c1efd71d3ac34b776f96af61a66f5f7de1d508b2c13e888abde7701a02bd. Version 1.6.2 is retained. No deployment, GitHub push, or live-site changes were made.

# GitHub Update 1.6.6, September 9

- [x] Inspect local changes, fetch origin, and identify the existing PR without changing main.
- [x] Include the complete source/build/test changes and current release documentation; add the missing PDF test dependency to CI.
- [x] Verify the staged diff, commit intentionally, and fast-forward the existing PR branch on GitHub.
- [x] Confirm the remote commit and report the PR/main status.
- [x] Correct the Mac-only native undo test shortcut exposed by Linux CI and verify the follow-up.

## GitHub Review
- Published the complete 1.6.6 source at 90bacad on existing PR #5, agent/reliability-first-ux. Main remains at 46f2699; no merge or deployment was performed.
- All 13 local application verification gates passed. GitHub CI exposed a test portability issue: native select-all and undo used Meta on Linux. Use Playwright's ControlOrMeta for those native field shortcuts without changing application code or the assertion.
- Follow-up local regression run: 120 passed, 0 failed, 0 untested. GitHub checks rerun on the follow-up push; application source and release remain unchanged.

# Publish 1.6.6, September 9

- [x] Verify the immutable release package and publish a new here.now site with all five application/runtime files.
- [x] Confirm the live source matches the release apart from hosting-added social metadata; open the register with 46 synthetic initiatives and verify its PowerPoint download.
- Published https://thorny-ivory-dqqf.here.now/ using the user's requested new-site flow. Anonymous hosting expires September 10, 2026 at 12:02:16 UTC. Claim link supplied privately in the task response. No project data or test artifacts published; no GitHub changes. The existing PowerPoint package warning is unchanged.

# Initiative Register, September 9

## Plan
- [x] Add failing coverage for complete read-only rows, grouping, totals, responsive layout, print pagination, and optional PowerPoint output.
- [x] Add an Initiative Register tab, shared data model, local landscape Print / PDF, and optional paginated PowerPoint appendix.
- [x] Run all verification gates; inspect desktop/mobile, actual PDF pages, and rendered PowerPoint register pages.
- [x] Record findings and package a versioned local release. Do not deploy or push.

## Design And Review
- Extend the existing operational visual system with an unframed, six-column read-only table. Retain full names, reporting date, scenario, pillar subtotals, and explicit excluded-from-totals labels.
- All initiatives in the current scenario appear regardless of grid filters, zero/undated values, or inclusion settings. Within each pillar, Active precedes Proposed; names sort alphabetically within classification.
- Shared financial helpers define totals and realization. Excluded rows remain visible but do not enter portfolio/pillar totals. PDF uses local browser printing with repeated headings; PowerPoint is opt-in for a full deck or available alone from the register.
- Added src/register.js and src/register.css through the existing local build includes, plus one accessible tab beside Initiatives. No runtime dependency or schema migration was added. Print / PDF opens the browser's local dialog; the user selects Save as PDF rather than receiving an automatic PDF download.
- Seven new register checks cover all 46 synthetic rows regardless of grid filters, grouped totals, scenario refresh, empty/unscheduled/excluded states, full names/XSS safety, mobile geometry, PDF text and repeated reporting context, standalone PPT, opt-in appendix, and long-name slide bounds. RED failed before the tab existed. Updated exact existing navigation assertions to include the new eighth tab; all other assertions stay enforced.
- All 13 final gates passed, with the application unchanged throughout: 82e00fec10ab4c3e4a8120f9ec585541dbfc2a064a189833238c9189efdbcbd7. Includes 120 existing features, 43 core checks in three engines, workspace/selection/accessibility/export checks, 18 existing presentation checks, seven register checks, and reproducible release/rollback.
- Additional Chromium/WebKit/Firefox checks at 1440px and 390px passed with all 46 rows, no page overflow, and no application errors. A separate axe scan of the new register passed on desktop/mobile. Inspected actual landscape PDF pages, normal and extreme-name PowerPoint renders, and settled browser screenshots. Evidence: /tmp/roadmap-register-tests. Very long names use a full-width detail slide instead of shrinking/truncating text.
- The previously recorded PowerPoint package content-type/slide-master warning remains outside this feature's scope. LibreOffice rendering and application export tests pass, but native Microsoft PowerPoint repair-free behavior is not verified; do not report the legacy packaging issue as fixed.
- Built and verified local release/versions/1.6.6, release/current, and release/archives/roadmap-studio-1.6.6.zip. Version 1.6.5 remains retained. Nothing deployed, committed, pushed, or uploaded.

# Active Category Naming, September 9

## Plan
- [x] Add regressions for Active labels, legacy classifications, controls, and exports.
- [x] Rename display labels across views, comparisons, drilldowns, and PowerPoint without changing financial semantics or stored category keys.
- [x] Verify all tests and inspect browser/PowerPoint output; package the local release.

## Review
- Scope: Approved becomes Active; Proposed and execution status remain unchanged. Preserve user-entered text and old saved projects. No deployment or GitHub changes.
- Added three core regressions for Active labels, legacy save/import behavior, explicit Active imports, grid/bulk/drawer controls, and financial drilldowns. Initial label and import checks failed before implementation. Display-specific legacy assertions now require Active; canonical financial keys and category assertions remain Approved for backward compatibility.
- Final full verification passed all 12 gates: 120 existing features, 43 core checks in each of Chromium/WebKit/Firefox, workspace/selection/accessibility checks, exports, 18 presentation checks, and release/rollback verification. Application remained unchanged throughout: e71d5a44c595042e792b7d38fe6c13fffb6dce557a68b1c621095698c468878f. An initial run hit a transient existing stretch-goal input test failure; its isolated rerun and the complete subsequent run passed without production changes.
- Visually inspected desktop/mobile labels and actual LibreOffice-rendered Portfolio Rollup slides. Evidence: /tmp/roadmap-active-preview. Notes tests confirm category labels changed while user-entered names containing "approved" remain intact.
- Separate package-integrity inspection found eight content-type overrides referencing absent slideMaster2.xml through slideMaster9.xml in the nine-slide fixture. A fresh export from immutable 1.6.4 reproduced the identical eight findings, so this is a pre-existing export packaging issue, not introduced by the rename. It remains unresolved and should be addressed separately; do not claim repair-free native PowerPoint verification.
- Built local 1.6.5 with 1.6.4 retained for rollback. No deployment, commit, push, or remote changes.

# Editable Stretch Goal, September 8

## Plan
- [x] Add failing regressions for editable goals, web/PPT measurements, validation, clearing, and saved-state/scenario/undo round trips.
- [x] Add an optional Stretch goal field beneath Portfolio goal and use one shared entered value across the Executive Summary and PowerPoint.
- [x] Inspect desktop/mobile views and rendered PowerPoint slides; run all verification gates.
- [x] Package a local versioned release and record results; no deployment or GitHub changes.

## Contract And Review
- Route: existing source/model/export patterns, Impeccable layout guidance, and the Presentations render-and-verify workflow.
- Stretch goal is an independently entered positive dollar amount, optional when blank, with no automatic 20% fallback. Add it beneath Portfolio goal in both existing goal-entry locations.
- Keep financial totals and original-goal percentages unchanged. Show the entered stretch marker and identified/realized percentages against it on the web and executive PowerPoint. Preserve both large PowerPoint headline blocks.
- Persist the optional field through save/open, autosave, scenarios, baselines, and undo/redo; legacy projects load without a stretch goal. Reject invalid imported/input amounts without replacing existing data.
- RED confirmed all five initial UI/persistence regressions failed without the field and seven presentation checks rejected the automatic multiplier. The follow-up precision regression caught $1.75B being displayed as $1.8B; goal-specific formatting now preserves precise amounts in web/PPT labels.
- Added six durable core regressions covering field placement in both views, percentages and markers, file download/open, autosave, undo/redo, scenario switching, baseline snapshots, legacy import, invalid/cleared values, independent goal changes, responsive label bounds, and precision. All 40 core tests pass in Chromium, WebKit, and Firefox.
- All 18 presentation checks pass, including full/current export, custom stretch amounts, goal-independent percentages, optional/cleared targets, small/large/empty portfolios, precision, state preservation, and repair-safe geometry. The earlier automatic-goal assertion is replaced by explicit entered-goal coverage; legacy inputs no longer imply a stretch value.
- Inspected desktop/mobile Executive Summary and goal-entry controls, plus actual LibreOffice PowerPoint renders. Twelve browser/view/viewport combinations have no page overflow or application errors. Evidence: /tmp/roadmap-editable-stretch-preview. Package inspection reports zero structural findings; no native Microsoft PowerPoint validation is claimed. The layout detector returned no findings in degraded regex mode, so screenshot and browser geometry checks remain authoritative.
- Full verification passed all 12 gates with the application unchanged throughout: fdbacb47fd1fa520fd07c633d75ef59c032f8f6d533df42c5c0d0c8f869f48af. Built and verified the five-file release/versions/1.6.4 package, release/current, and release/archives/roadmap-studio-1.6.4.zip (SHA-256 614c216b0b40b35d80f607f0d6c193c15b6e32a131c6d26aa83da1fadc994be3). Version 1.6.3 remains retained. Nothing was deployed, committed, or pushed.
