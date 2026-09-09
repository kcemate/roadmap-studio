# Roadmap Studio Engineering

Read PRODUCT.md, tasks/lessons.md, and relevant source/tests before editing. Plan non-trivial work in tasks/todo.md, add failing regression tests first, and record actual verification before declaring completion.

## Source And Build

- src/app.html: core app markup, financial helpers, rendering, editing, persistence, and scenarios.
- src/model.js: project validation, shared financial definitions, draft/recovery support.
- src/workspace.js / workspace.css: review, drilldown, bulk editing, saved layouts, responsive/accessibility extensions.
- src/exports.js: PNG, PowerPoint, and presentation behavior.
- index.html is generated. Edit source, then run `python3 tasks/build.py`; never manually edit generated output.
- vendor/pptxgen.bundle.js is required in every deployable package.

## Verification

Run `python3 tasks/build.py --check`, `python3 tasks/roadmap_feature_tests.py`, and all `tasks/audit_*_tests.py` suites. For output changes, generate and visually inspect real PowerPoint renders; XML text presence alone is insufficient. Verify desktop/mobile and keyboard behavior. Tests must fail with nonzero exit status. Update result/tracker data only from real runs.

Do not weaken tests to hide defects. If an approved financial or UI rule changes, document the semantic change and replace an obsolete assertion with stronger coverage of the new contract.

## Data And Scope

No external project-data calls, CDN dependencies, backend, CSV import, or audit log. Treat imports, baselines, scenarios, and saved preferences as untrusted. Preserve user data and existing work. Keep internal percentages in percentage points; never re-interpret numeric fractions during formatting or serialization. Recorded actuals are not confidence-weighted.

Keep rollout and rollback verifiable. Do not push, merge, deploy, change hosting, or access credentials without user authorization. Build and test locally first; package only application assets, never project data or test artifacts.
