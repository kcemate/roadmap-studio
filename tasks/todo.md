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
