# Roadmap Studio 1.6.6

A local-first app for turning strategic pillars, workstreams, and initiatives into an executive roadmap and a defensible financial story.

Open `index.html` in a browser. No server or account is required. Keep the adjacent `vendor/` folder: it contains the offline PowerPoint writer. Use **Download** for a portable `.roadmap.json` project file; browser autosave is not a substitute for a backup.

## What's New

- Initiative Register: every initiative, grouped by pillar and Active/Proposed, with full names, financial values, realization, timing, and owner. Print / PDF creates a landscape report using the browser's local Save as PDF; register PowerPoints are available alone or as an opt-in full-deck appendix.

- Active replaces Approved in initiative controls, summaries, comparisons, and PowerPoint. Legacy project classifications and financial totals are preserved.

- Optional, editable Stretch goal beneath Portfolio goal, saved with each plan. Executive web and PowerPoint views show both targets and identified/realized progress against each, with no automatic multiplier.
- Row-selection checkboxes and numbers stay vertically centered with initiative fields, including taller rows.
- Correct, round-trip-safe percentages and strict financial/date validation.
- Atomic, bounded project imports with safe identifiers and consistent references.
- Reconciled portfolio totals, including explicit unscheduled and excluded value.
- Recorded actual dollars and an as-of date, independent of forecast confidence.
- Per-scenario working drafts, intentional deletion semantics, comprehensive undo, and local recovery.
- Persisted unfinished grid/drawer edits, protected across reloads.
- Recurring/one-time benefits, annual/lifetime inputs, recognition rules, optional implementation costs, and linked exclusions.
- Sortable initiatives, filtered bulk edits, custom column layouts, and reporting-date controls.
- Clickable financial totals with contributing initiatives and calculation context.
- A compact Review workspace for exceptions, scenario comparisons, and recovery.
- Responsive metrics, labeled controls, modal focus handling, and measured timeline labels.
- Paginated PowerPoints, explicit export scope, report context, and readable presentation scrolling.
- Visible version, reproducible offline releases, rollback tooling, and automated verification gates.

## Views

**Structure** manages pillars and workstreams. **Initiatives** holds names, timing, approval, status, owners, financial type/value, realization, confidence, and inclusion in totals. The detail drawer contains actuals, benefit economics, recognition, exclusion links, and dated realization phases.

**Roadmap** groups work by pillar or owner, supports collapsing groups and drag-based timing, and keeps full details available from each bar. Not Started remains black; Savings and Avoidance retain their financial color distinction.

**Executive Summary** shows identified opportunity and realized actuals against the goal. **Portfolio Rollup** shows aggregate Active and Proposed lanes per pillar. **Projected Savings** shows planned Savings and combined trajectories, with confidence, actuals, target, and baseline context. **Stacked Bar Chart** compares pillar contributions for Savings only and combined value.

**Review**, accessible from Initiatives, contains exceptions, scenario comparison, and local recovery. Financial drilldowns show contributors and calculation rules.

## Financial Definitions

| Concept | Definition |
| --- | --- |
| Portfolio value | Included lifetime Savings plus Avoidance; unscheduled work remains in the portfolio. |
| Annual recurring input | Converted to full dated duration using calendar-year proration. Requires complete dates. |
| One-time value | Full entered benefit, not an annual run-rate. |
| Planned recognition | Linear across the range, full value at completion, or full value upfront. Milestones recognize on their date. Undated work cannot be projected. |
| Recorded actuals | Explicit dollars through the reporting date; never confidence-discounted or added on top of opportunity. |
| Legacy realization | Without explicit actual dollars, dated cumulative phases take precedence over a single percentage. |
| Expected value | Planned value multiplied by confidence; recorded actuals are unchanged. |
| Net benefit | Lifetime planned value minus optional total implementation cost. Gross headlines are not silently netted. |
| Excluded work | Visible on the roadmap but excluded from financial totals; a credited initiative and reason explain why. |

Stored percentages are percentage points: numeric `1` means 1%. Explicit `0.5%` means half a percent. Existing direct-entry shorthand `0.5` means 50% only when parsing new text; stored numbers are never reinterpreted. Fractional legacy files must explicitly declare `percentageUnit: "fraction"`.

## Scenarios And Recovery

Switching scenarios saves outgoing changes to its working draft. New initiatives remain in a shared portfolio catalog; deletion markers prevent another scenario resurrecting deleted work. A baseline is a frozen comparison plan. Download separate files when independent portfolio membership is needed.

Undo/redo restores configuration as well as initiative data. Deletion Undo preserves newer unrelated edits. Replacement imports/new projects retain up to five size-bounded recovery copies. Invalid imports leave the current project untouched. Autosave failure shows a persistent warning with a download action.

Project formats v1, v2, and v3 pass through validation; downloads use v3. Unsupported, oversized, malformed, or inconsistent files are rejected. Keep the original when import fails. Browser storage belongs to the current browser/profile/origin and can be cleared.

## Exports

Choose **Full deck** or **Current view**. The full PowerPoint tells the story in this order: Executive Summary, Portfolio Rollup, Projected Savings, Pillar Contribution, then detailed roadmap pages. Reports identify project, scenario, reporting date, baseline, and confidence basis; notes retain the version and grouping context.

The 1.6.1 export uses two centered executive metric blocks, balanced two-pillar rollup pages, continuous projection lines with direct labels, and separate dollar/share contribution columns. A distant target stays visible above the projection without flattening the chart. Both contribution bars represent 100%, with consistent pillar order and colors.

Dense roadmaps continue across slides at up to four initiatives per page instead of shrinking labels. Short bars use numbered references to a readable initiative column. Unscheduled work is identified, while complete names and financial details remain in slide notes. Savings is green and Avoidance is blue; approval lanes use labeled neutral colors, and composition colors identify pillars rather than financial types. PNG export and browser presentation remain local; oversized presentation views scroll at readable size.

## Privacy

No backend, analytics, project upload, external runtime script, or CDN. Content Security Policy blocks application network connections, objects, forms, and remote frames. Imports, scenarios, baselines, and preferences are validated before replacement. Exports are generated locally.

This does not protect against browser extensions, a compromised device, or sharing downloaded files. Hosting receives ordinary application-asset requests, not entered project data.

## Source And Build

Edit `src/app.html` (core app), `src/model.js` (validation/finance/recovery), `src/workspace.js` and `src/workspace.css` (review/editing), or `src/exports.js` (exports/presentation). Do not manually edit generated `index.html`.

```sh
python3 tasks/build.py
python3 tasks/build.py --check
```

Users opening a release do not need a build tool.

## Verification

```sh
python3 -m pip install playwright==1.58.0 Pillow==12.1.1 PyMuPDF==1.27.2.2
python3 -m playwright install chromium webkit firefox
npm install --prefix /tmp/roadmap-audit-tools --no-save axe-core@4.10.3
python3 tasks/verify_all.py
```

The gate runs the existing feature suite, core regressions in Chromium/WebKit/Firefox, workspace tests, axe accessibility scans, export and presentation-design checks, and release/rollback validation. The axe bundle is a test-only dependency, never part of the shipped app. Set \`AXE_PATH\` to use another local installation.

Tracker/result files and \`tasks/audit-integration-results.json\` record actual output. Failures return nonzero. PowerPoint checks include dense fixtures and geometric bounds; visual renders are reviewed before release. Native PowerPoint repair-dialog behavior requires verification in Microsoft PowerPoint, not only XML inspection.

## Releases

See [release and rollback instructions](docs/releases.md). Packages contain only app assets, the vendored PowerPoint writer/license, version metadata, and checksums. Project data and test artifacts are excluded.

The manual GitHub Pages workflow prepares a stable public address. Enabling and publishing that site is a separate approval step; local packaging or pushing code does not automatically deploy it.
