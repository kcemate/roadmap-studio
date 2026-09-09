# Roadmap Studio 1.6 Audit Upgrade

## Contract

Objective: implement all thirteen accepted product-audit recommendations while preserving local-only operation, existing project compatibility, and the current executive visual hierarchy. Source baseline: b8497b1. Main route: repository implementation with Impeccable hardening and the existing PowerPoint workflow. No CSV import or audit log.

Rollback: retain baseline Git commit b8497b1 and a versioned local application package before implementation. Build from source fragments into index.html; no external runtime calls or new CDNs. The existing vendored PowerPoint runtime remains packaged.

## Plan

- [x] 1 Percentage canonicalization and round-trip invariants.
- [x] 2 Complete import validation, safe identifiers, atomic state replacement.
- [x] 3 Reconciled totals with explicit undated/excluded populations.
- [x] 4 Independent actual dollars/as-of and unweighted realized values.
- [x] 5 Saved scenario drafts and shared-catalog deletion semantics.
- [x] 6 Operation-specific undo, baseline recovery, and persistent input drafts.
- [x] 7 Strict financial/date validation and resilient incomplete timelines.
- [x] 8 Paginated PowerPoints and readable browser presentation navigation.
- [x] 9 Responsive metrics, long-name layout, keyboard and screen-reader access.
- [x] 10 Financial total drilldowns with inclusion/calculation context.
- [x] 11 Sorting, bulk edits, column presets, comparisons, and exceptions.
- [x] 12 Benefit type/value basis and linked exclusion explanations.
- [x] 13 Context-rich exports, visible version, reproducible release/rollback, automated gates.

## Verification

Add failing regression tests first. Run existing feature suite and new audit tests; use realistic dense/empty/undated/edge-value fixtures, malicious import canaries, and save/switch/delete round trips. Render PowerPoint and inspect key slides; test desktop/mobile/keyboard and supported browser engines. Never weaken a test to hide a regression; explicitly document changed financial semantics where an old assertion encodes the audited bug.

## Worker Contracts

### Presentation worker
- Owns src/exports.js and tasks/audit_export_tests.py only.
- Reads this plan, src/app.html, current export module, audit report and lessons.
- Implements pagination, readability, export scope/context/parity and browser presentation navigation.
- Preserve existing helper/function signatures where feasible. Read financial helpers from main; do not implement separate financial formulas.
- No network, production, Git, or deployment writes. Test against built application; coordinate hooks instead of editing main source.
- Return changed files, actual test output, generated deck/render evidence, and any integration hooks needed.

### Workspace worker
- Owns src/workspace.js, src/workspace.css and tasks/audit_workspace_tests.py only.
- Implements sorting/bulk edit/column presets, total drilldowns, scenario comparison and exception surfaces, mobile/accessibility finishing.
- Main calls initWorkspace(), enhanceGrid(), refreshWorkspace(), enhanceDrawer() and workspaceSortedItems(items). New functions use existing S, $, esc, itemValue, realizedItemValue, pushUndo/renderAll/scheduleSave and do not override them.
- Main owns input commit, financial model, persistence, scenario core, original markup. Request hooks rather than editing those files.
- No backend, CSV, audit log, CDN, deployment or Git actions. Use synthetic fixtures, genuine RED tests and screenshots.
- Return exact hooks/state fields plus verification.

### Release worker
- Owns .github/workflows/, tasks/release.py, tasks/verify_release.py and docs/releases.md only.
- Implements reproducible local release packaging with manifest/checksums, versioned archives, stable current path and rollback instructions, CI that fails on actual errors and runs existing/new suites.
- Main owns existing runner exit status, version constant and README. No remote setup/push or deployment; prepare the explicit publish gate and identify external prerequisites.
- No uploads of entered data. Include only index.html, vendor runtime and release metadata in site packages.

## Review

All thirteen implementation areas are complete in the local 1.6.0 build. The frozen-build gate passed: 120 existing checks, 34 core regressions in each of Chromium/WebKit/Firefox, 10 workspace tests, 7 export checks, and the accessibility sweep across 20 viewport/surface combinations. Reproducibility, checksum validation, and rollback passed. See tasks/audit-integration-results.json for actual output.

Rendered dense, long-name, executive, projection, and rollup slides were visually inspected. Dense workstreams continue across pages; rollup pages contain at most three pillars. Full truncated names remain in speaker notes, with measured Arial text and no shrink-to-fit instructions. Native Microsoft PowerPoint was not installed, so its repair dialog was not directly tested.

The versioned package is release/archives/roadmap-studio-1.6.0.zip. Pre-upgrade assets are preserved in release/archives/pre-audit-b8497b1.zip and the rollback branch. Public hosting activation and GitHub publishing remain separate approval gates; neither occurred during this implementation.
