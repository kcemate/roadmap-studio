# Roadmap Studio Engineering

Read PRODUCT.md, tasks/lessons.md, and relevant source/tests before editing. Plan non-trivial work in tasks/todo.md, add failing regression tests first, and record actual verification before declaring completion.

## Source And Build

- src/app.html: core app markup, rendering, editing, persistence, and scenarios.
- src/finance.js: the single source for statuses, inclusion, undated and financial-initiative definitions, portfolio totals, the goal basis, and money/percent/date formatting. Every view and export derives its numbers here; do not add another roll-up.
- src/model.js: project validation (the loader's `checked*` rules, also used for input), save-time validation, deletion markers, drafts, and local recovery.
- src/workspace.js / workspace.css: review (exceptions, since last review, compare, recovery), drilldown, bulk editing, saved layouts, paste rows, responsive/accessibility extensions.
- src/register.js / register.css: Initiative Register, print layout, and the register PowerPoint appendix.
- src/exports.js: PNG, PowerPoint (slide masters, story deck, native charts, package repair), and presentation behavior.
- index.html is generated. Edit source, then run `python3 tasks/build.py`; never manually edit generated output.
- vendor/pptxgen.bundle.js is required in every deployable package. It loads on first export and is not modified; known writer defects are corrected after writing (see `repairChartWorkbooks` in exports.js).

## Verification

Run `python3 tasks/verify_all.py` (it runs `tasks/build.py --check`, the feature suite, every `tasks/audit_*_tests.py` suite, and release/rollback validation). Install test dependencies from `requirements-dev.txt` and axe-core as README describes. Tests read the committed build and never rebuild it; they write output only to `tasks/test-artifacts/` and must not change tracked files (the gate fails if they do). `roadmap_feature_tests.py --update-tracker` is the only way to rewrite the tracker CSV, and only from a real run.

For output changes, generate and visually inspect real PowerPoint renders; XML text presence alone is insufficient. Verify desktop/mobile and keyboard behavior. Tests must fail with nonzero exit status.

Do not weaken tests to hide defects. If an approved financial or UI rule changes, document the semantic change and replace an obsolete assertion with stronger coverage of the new contract.

## Data And Scope

No external project-data calls, CDN dependencies, backend, CSV file import, or audit log. Paste rows accepts tab-separated text from the clipboard only. Treat imports, pasted rows, baselines, scenarios, and saved preferences as untrusted. Preserve user data and existing work; files saved by earlier versions must keep opening (see tasks/fixtures/). Keep internal percentages in percentage points; never re-interpret numeric fractions during formatting or serialization. Recorded actuals are not confidence-weighted.

Keep rollout and rollback verifiable. Do not push, merge, deploy, change hosting, or access credentials without user authorization. Note that GitHub Pages currently serves `main` directly, so merging to `main` publishes. Build and test locally first; package only application assets, never project data or test artifacts.
