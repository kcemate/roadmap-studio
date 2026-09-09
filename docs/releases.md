# Roadmap Studio Releases

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

Roadmap Studio releases are offline packages. They contain exactly the generated
`index.html`, the vendored PowerPoint runtime and its license, `release.json`, and
`SHA256SUMS`. Project files, test artifacts, source files, tasks, browser storage,
credentials, and other user-entered data are never packaged.

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
python3 tasks/verify_release.py release/archives/roadmap-studio-1.6.6.zip
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

`.github/workflows/ci.yml` runs `tasks/verify_all.py`: generated-source checks,
the existing browser suite, core regressions in Chromium/WebKit/Firefox, workspace,
axe accessibility, exports, presentation-design regressions, and release reproducibility/rollback. Every command
uses its real exit status, so a failed gate fails the job. The integration report
also verifies that the application did not change during testing.

## GitHub Pages approval gate

`.github/workflows/pages.yml` is manual only. An authorized repository operator
must open **Actions > Publish stable GitHub Pages release > Run workflow** and type
`publish`. The workflow reruns every release gate, packages only `release/current`,
and deploys it to the stable public URL:

`https://<repository-owner>.github.io/<repository-name>/`

External approval is still required to enable GitHub Pages with **GitHub Actions**
as its source, configure any required `github-pages` environment reviewers, merge
the workflow to the publishing branch, and manually trigger it. The workflow uses
GitHub's short-lived Pages identity token; it defines no application secret and
does not upload Roadmap Studio project data. No deployment occurs merely because
code is pushed or a pull request is opened.
