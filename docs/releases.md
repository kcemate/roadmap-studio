# Roadmap Studio Releases

Roadmap Studio releases are offline packages. They contain exactly the generated
`index.html`, the vendored PowerPoint runtime and its license, `release.json`, and
`SHA256SUMS`. Project files, test artifacts, source files, tasks, browser storage,
credentials, and other user-entered data are never packaged.

## 1.7.2 Row Dividers and Web Stretch Scale

Initiative row dividers continue through the pinned selection and name columns.
The web Executive Summary bar ends at the entered stretch goal, matching the
PowerPoint export. Excess is shown separately, and reported totals are unchanged.
Without a stretch goal, both views retain their automatic scale.

## 1.7.1 Initiative Grid and PowerPoint Polish

Initiative names have more room, show an ellipsis when shortened, and expose
the full name on hover. Desktop keeps the row selector and initiative name
together while scrolling. On narrow screens both columns scroll normally.

The PowerPoint Executive Summary bar ends at the entered stretch goal. If
identified value exceeds it, the slide shows the excess separately. Without
a stretch goal, the slide keeps the web tracker scale. The vertical title
accents were removed from the cover and content slides.

## 1.7.0 Audit Release (2026-11)

Implements the 1.6.7 audit: one totals path for every view and export, an explicit
"No goal set" state, Blocked / On Hold / Cancelled statuses with documented total
rules, input and save-time validation that keeps every save loadable, safer recovery,
and editing, export, and accessibility fixes. The PowerPoint deck is rebuilt on slide
masters as a story (title, summary, bridge to goal, timing, projection, pillar
contribution, pillar pages, since last review, decisions needed, register appendix)
with editable native charts. New: sample portfolio, paste rows, initiative commentary,
Since last review, Review badge, filtered exports, and brand settings. Roadmap marks
use the value-type colour plus a status pill everywhere (no black Not Started bars), and
the summary slide uses the web tracker's six-segment bar.

Behavior changes to reported figures are listed in README "Financial Definitions" and
in the pull request. The project format stays v3; files saved by 1.6.7 open unchanged.
The 1.6.4–1.6.7 packaging limitation (content types for missing slide-master parts) is
corrected after writing. Repair-free opening in native Microsoft PowerPoint has not
been verified: decks were rendered in Keynote only.

## 1.6.7 Executive Measurement Scale

The first PowerPoint slide uses the same dollar scale as the Executive Summary
web tracker, including headroom beyond the portfolio and entered goals. For a
$1B goal with up to $1B identified, the measurement bar spans $0 to $1.2B while
the goal marker remains at $1B. Larger portfolios and entered stretch goals
expand the scale using the existing web rules.

Readable dollar ticks make the measurement range explicit. The two headline
blocks, financial totals, goal-based percentages, and independently entered
stretch goals remain unchanged. Both full-deck and current-view exports use
the same scale. The PowerPoint packaging limitation noted below is unchanged.

## 1.6.6 Initiative Register

A read-only register lists every initiative in the current plan, grouped by pillar
with Active before Proposed. It preserves full names, financial values, realized
dollars, timing, owners, and explicit exclusion labels. Shared financial helpers
keep register totals consistent with the rest of the product.

Print / PDF opens the browser's local Save as PDF dialog with a landscape layout
and repeating headings. Export the register alone, or opt into a paginated
PowerPoint appendix. Exceptionally long names use a full-width detail slide.
The 13-gate suite includes seven register-specific checks and PDF text validation.

Known limitation: the existing PowerPoint writer emits content-type declarations
for missing slide-master parts in multi-slide decks. LibreOffice rendering passes,
but repair-free native PowerPoint behavior has not been verified. This issue was
reproduced in 1.6.4 and remains unresolved; it is not fixed by the register feature.

## 1.6.5 Active Category

Active replaces Approved in user-facing controls, summaries, comparisons,
drilldowns, and PowerPoint labels/notes. Legacy storage keys remain compatible;
both Active and Approved imports normalize to the same classification. Proposed,
execution status, calculations, and user-entered initiative names are unchanged.

## 1.6.4 Editable Stretch Goal

Enter an optional Stretch goal directly beneath Portfolio goal. The independent
dollar value is saved with the project, scenarios, baselines, and undo history.
Executive Summary and PowerPoint show both goal markers and identified/realized
percentages against each. Clearing the field removes the stretch measurement;
legacy projects leave it blank. The automatic 20% multiplier is removed.

## 1.6.3 Executive Stretch Goal

The executive PowerPoint slide adds a labeled stretch goal at 120% of the entered
goal and extends its dollar scale to include it. The original goal, identified
opportunity and realized percentages, financial values, and web views are unchanged.
Both full-deck and current-view exports include the marker. Version 1.6.2 is retained.

## 1.6.2 Selection Alignment

The initiative selection column stays in the table layout, with its checkbox and
row number centered in an inner wrapper. Normal and tall rows are covered at
desktop/mobile widths in Chromium, WebKit, and Firefox. Selection, editing,
financial calculations, and the 1.6.1 PowerPoint refinements are preserved.

## 1.6.1 Presentation Refinement

PowerPoint exports now lead with the executive story, followed by rollup,
projection, pillar contribution, and detailed roadmaps. The patch adds balanced
pagination, larger essential text, continuous projection shading, separated
financial columns, and numbered short-bar references. Financial calculations and
web-view layouts are unchanged. Version 1.6.0 remains available for rollback.

## 1.6.0 Reliability Audit

Strict financial and date validation, atomic bounded imports, reconciled totals with
explicit unscheduled and excluded value, recorded actuals with an as-of date,
per-scenario drafts, local recovery, the Review workspace, financial drilldowns,
versioned offline releases, and the automated verification gate.

## Build and verify

The application version is read from the single `APP_VERSION` constant in
`src/app.html`. Do not duplicate or manually pass a release version.

Run a temporary reproducibility and rollback test without retaining artifacts:

```sh
python3 tasks/release.py build --dry-run
```

Create a retained local release:

```sh
python3 tasks/release.py build
```

The command first requires `python3 tasks/build.py --check` to pass, then creates:

- `release/versions/<version>/`: immutable unpacked release.
- `release/archives/roadmap-studio-<version>.zip`: deterministic, uncompressed ZIP archive.
- `release/current/`: stable local folder containing the active release.

Verify either an unpacked package or archive independently:

```sh
python3 tasks/verify_release.py release/current
python3 tasks/verify_release.py release/archives/roadmap-studio-<version>.zip
```

Verification fails nonzero for extra or missing files, a version mismatch, an
invalid checksum, missing package assets, external resource references, or a CSP
that permits network connections, objects, forms, or a base URL.

## Roll back

Keep every approved `release/versions/<version>/` folder. Restore the stable local
folder from one of those immutable versions with:

```sh
python3 tasks/release.py rollback 1.6.0
```

The rollback is staged before replacing `release/current/`, then the selected
package is verified and compared byte-for-byte with the restored current folder.
The command does not change source code or delete versioned archives.

The pre-audit source is also preserved locally on `rollback/pre-audit-1.6` at
`b8497b1`. Keep a pre-upgrade project download when testing an older application:
older builds do not understand every v3 field, and an application rollback is not
a promise of lossless project-schema downgrade.

## Continuous integration

`.github/workflows/ci.yml` runs once per pull-request commit (and on `main`). It
installs `requirements-dev.txt` with pip caching, restores cached Playwright browsers,
and runs `tasks/verify_all.py`: generated-source checks, the feature suite, core and
audit regressions in Chromium/WebKit/Firefox, consistency and feature contracts,
workspace, axe accessibility, exports, presentation design, register, and release
reproducibility/rollback. Every command uses its real exit status. The gate fails if
any tracked file changed during testing, and the job checks `git status --porcelain`
afterwards. Test results and generated decks are uploaded as the
`roadmap-test-artifacts` build artifact instead of being committed.

## GitHub Pages approval gate

`.github/workflows/pages.yml` is manual only. An authorized repository operator
must open **Actions > Publish stable GitHub Pages release > Run workflow** and type
`publish`. The workflow reruns every release gate, packages only `release/current`,
and deploys it to the stable public URL:

`https://<repository-owner>.github.io/<repository-name>/`

**Current state (checked 2026-11-10):** the repository's Pages site uses the legacy
branch source (`main`, `/`). Every merge to `main` therefore publishes the whole
repository at the public URL, including `src/`, `tasks/`, and docs, and this workflow
has never been the deployment path. Opening a pull request does not deploy; merging it
does.

Recommended fix (repository owner): switch **Settings > Pages > Source** to
**GitHub Actions**, optionally add `github-pages` environment reviewers, then run this
workflow to publish only the verified package. The workflow uses GitHub's
short-lived Pages identity token; it defines no application secret and does not
upload Roadmap Studio project data.
