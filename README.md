# Roadmap Studio 1.7.0

A local-first app for turning strategic pillars, workstreams, and initiatives into an executive roadmap and a defensible financial story.

Open `index.html` in a browser. No server or account is required. Keep the adjacent `vendor/` folder: it contains the offline PowerPoint writer, which loads the first time you export. Use **Download** for a portable `.roadmap.json` project file; browser autosave is not a substitute for a backup.

## What's New in 1.7.0

- **One set of numbers.** Every view, drilldown, register, and export derives from one totals path. Executive Summary, Projection, Portfolio Rollup, Pillar Contribution, the register, and the deck agree on identified value, realized value, counts, and the goal gap.
- **No assumed goal.** With no portfolio goal (or a goal of zero) the app says "No goal set" instead of measuring against $1B.
- **Statuses** Blocked, On Hold, and Cancelled, with explicit rules for totals. Unrecognized imported statuses load as Not Started and are flagged for review instead of becoming On Track.
- **Safer saving.** Out-of-range values are rejected where they are typed; autosave never replaces the last loadable save; recovery copies never crowd out the primary save; deleting the active scenario returns to the working plan.
- **A story deck.** Title, summary, bridge to goal, timing, projection, pillar contribution, pillar pages, since last review, decisions needed, and an optional register appendix, on slide masters with editable native charts and data-driven titles. Optional accent colour, font, and logo.
- **Review features.** Sample portfolio, paste rows copied from a spreadsheet, next step / decision needed / notes per initiative, a "Since last review" comparison against the baseline, a Review badge with more checks, and filters that can carry into exports.
- **Faster.** Projection is computed in one sweep, single-cell edits redraw one row, dragging redraws one bar, and the PowerPoint writer loads on demand.

Earlier releases are summarized in [docs/releases.md](docs/releases.md).

## Views

**Structure** manages pillars and workstreams. **Initiatives** holds names, timing, approval, status, owners, financial type/value, realization, confidence, and inclusion in totals; **Paste rows** adds initiatives copied from a spreadsheet. CSV or Excel file import is intentionally not supported. The detail drawer contains actuals, benefit economics, recognition, exclusion links, dated realization phases, next step, decision needed, and notes.

**Executive Summary** shows identified opportunity and realized value against the goal. **Portfolio Rollup** shows when each pillar's Active and Proposed work runs, by fiscal year. **Projection** shows planned Savings and Savings + Avoidance over time, with confidence weighting, realized value, goal, and baseline context. **Pillar Contribution** compares pillar shares of Savings and of Savings + Avoidance. **Roadmap** groups work by pillar or owner and supports drag-based timing. Bars use the Savings/Avoidance colour with a darker realized share; a pill beside each bar names its status, and an amber outline marks At Risk or Blocked work. The same marks appear in PNG, Present mode, and on slides. **Initiative Register** lists every initiative with exact dollars and prints to PDF.

**Review**, opened from Initiatives, contains exceptions, Since last review, scenario comparison, and local recovery. Every report view shows its reporting ("as of") date.

## Financial Definitions

| Concept | Definition |
| --- | --- |
| Identified value | Included lifetime Savings plus Avoidance, Active and Proposed, unweighted. Undated work stays in the total. This is the one basis for every goal comparison. |
| Included | An initiative counts in totals unless it is marked "Excluded from portfolio totals" or its status is Cancelled. |
| Statuses | Not Started, On Track, At Risk, Blocked, On Hold, Complete: in totals. Cancelled: excluded from every total, projection, and goal measure. At Risk and Blocked are flagged as risks; Blocked and On Hold appear in Review under "Needs a decision". |
| Financial initiative | An included initiative with planned value or recorded realization. Initiative counts on financial views use this definition. |
| Undated | No start, no end (unless a milestone), or an end before the start. Undated work cannot be projected or placed on a timeline. |
| Goal | A positive dollar amount. Blank or zero means "No goal set". Gap = goal − identified value. |
| Annual recurring input | Converted to full dated duration using calendar-year proration. Requires complete dates. |
| One-time value | Full entered benefit, not an annual run-rate. |
| Planned recognition | Linear across the range, full value at completion, or full value upfront. Milestones recognize on their date. |
| Realized | Recorded actual dollars through the reporting date; without actuals, dated cumulative phases, otherwise the realized percentage. Never confidence-weighted and never added to identified value. |
| Realized beyond plan | Actuals above an initiative's planned value are reported separately. Bars that show each planned dollar once cap realized value at plan; the Realized total includes every recorded dollar. |
| Expected / weighted | Planned value multiplied by confidence. Only the Projection view and slide apply weighting, and they say so. |
| Net benefit | Lifetime planned value minus optional total implementation cost. Gross headlines are not silently netted. |
| Excluded work | Visible on the roadmap but excluded from financial totals; a credited initiative and reason explain why. |

**Formats.** Summaries, charts, and slides show money to three significant figures with the unit promoted after rounding ($999.5K shows as $1M). Inputs, the register, and slide notes show exact dollars, keeping cents. Goal amounts appear as entered ($1.75B, or $1,500,001 when not exactly compact). Percentages show at most one decimal. Date ranges use an en dash.

**Percentages.** Stored percentages are percentage points: numeric `1` means 1%. When typing, `0.5%` means half a percent and the shorthand `0.5` means 50%; the app confirms that reading in a notice. Stored numbers are never reinterpreted. Fractional legacy files must declare `percentageUnit: "fraction"`.

## Scenarios And Recovery

Switching scenarios saves outgoing changes to its working draft. New initiatives remain in a shared portfolio catalog; deletion markers keep deleted initiatives, pillars, and workstreams from returning through another scenario. **Working plan** is the first scenario option. Deleting the active scenario returns to the working plan. A baseline is a frozen comparison plan used by Projection and Since last review.

Undo/redo covers plan data: structure, initiatives, goals, dates, toggles, scenarios, baseline, deletions, and brand settings. View preferences (filters, density, column widths, sort, layouts, Review panel, grouping) are not undo steps. Deletion Undo preserves newer unrelated edits.

Autosave validates the project with the same rules used to open files; a change that could not be reopened is not saved over the last good copy, and a warning explains why. Replacement imports and new projects keep up to five local recovery copies within a 2 MB budget; a project too large for a copy is reported. Browser storage holds about 5 MB per site: larger projects open and work, and the warning asks you to download them.

Project formats v1, v2, and v3 load; downloads use v3. Files saved by 1.6.7 open unchanged (a saved 1.6.7 file is part of the test suite). Unsupported, oversized, malformed, or inconsistent files are rejected and the current project is left untouched.

## Exports

**PowerPoint.** Choose **Full deck** or **Current view**. Options (next to the scope) can include the register appendix, apply the Initiatives filters, turn off Since last review (included by default whenever a baseline exists; no slide without one), and set an accent colour, font, and a logo chosen from this device (embedded in the project and deck; nothing is uploaded). Options are remembered per project. A filtered deck states its filter on every slide and does not compare the subset with the portfolio goal.

The full deck: title; one-page summary (two centered blocks above the same six-segment bar, scale, and key as the web tracker); bridge to goal; timing by pillar; projection; pillar contribution; pillar pages with status pills, a value column, realized fill, and an as-of line (up to ten rows per slide); since last review; decisions needed; optional register appendix. Bridge, projection, and pillar contribution are native charts that stay editable. Notes keep complete names, values, and context.

**PNG** draws the roadmap from current data on any tab, scaled to stay within image limits. **Present** shows the roadmap full screen. **Print / PDF** on the register uses landscape pages. File names follow `<project> — <view> — <as-of date>`.

## Privacy

No backend, analytics, project upload, external runtime script, or CDN. Content Security Policy blocks application network connections, objects, forms, and remote frames. Imports, scenarios, baselines, and preferences are validated before replacement. Exports are generated locally.

This does not protect against browser extensions, a compromised device, or sharing downloaded files. Hosting receives ordinary application-asset requests, not entered project data.

## Source And Build

Edit `src/app.html` (core app), `src/finance.js` (shared financial definitions, statuses, and formatting), `src/model.js` (validation, persistence safety, recovery), `src/workspace.js` and `src/workspace.css` (review, drilldown, bulk editing, paste rows), `src/register.js` and `src/register.css` (Initiative Register), or `src/exports.js` (PNG, PowerPoint, presentation). Do not manually edit generated `index.html`.

```sh
python3 tasks/build.py
python3 tasks/build.py --check
```

Users opening a release do not need a build tool.

## Verification

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium webkit firefox
npm install --prefix tasks/test-artifacts/tools --no-save axe-core@4.10.3
python3 tasks/verify_all.py
```

The gate runs the feature suite, core and audit regressions in Chromium, WebKit, and Firefox, consistency and feature contracts, workspace tests, axe accessibility scans, export and presentation-design checks, register checks, and release/rollback validation. The axe bundle is a test-only dependency, never part of the shipped app. Set `AXE_PATH` to use another local installation.

Test output (results JSON, downloaded decks, renders) is written to `tasks/test-artifacts/`, which is ignored by git; CI uploads it as a build artifact. The gate fails if running it changes any tracked file. Failures return nonzero. PowerPoint checks include dense fixtures, geometric bounds, chart parts, and package content types; visual renders are reviewed before release. Native PowerPoint repair-dialog behavior requires verification in Microsoft PowerPoint, not only XML inspection.

## Releases

See [release and rollback instructions](docs/releases.md). Packages contain only app assets, the vendored PowerPoint writer/license, version metadata, and checksums. Project data and test artifacts are excluded.

**Publishing today:** GitHub Pages for this repository is configured to serve the `main` branch directly (legacy branch source), so every merge to `main` publishes the whole repository, including `src/` and `tasks/`. The gated `.github/workflows/pages.yml` workflow is not the deployment path until the repository owner switches the Pages source to **GitHub Actions**. That switch is the recommended fix: the workflow then publishes only the verified package, and only when run manually.
