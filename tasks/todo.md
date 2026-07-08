- [x] Inspect the current README and GitHub branch/PR state.
- [x] Replace stale README content with the latest Roadmap Studio feature set.
- [x] Remove obsolete ExcelJS/Excel import-export references from repo-facing docs.
- [x] Call out local-only/no-egress behavior, save/open JSON, PowerPoint, PNG, projection, and stacked chart features.
- [x] Run the full test suite and README sanity checks.
- [ ] Commit and push the documentation update to GitHub.

## Planned Spec

- The GitHub landing page should describe what Roadmap Studio does today, not the older Excel-focused version.
- The README should be suitable for a recruiter/reviewer: concise product summary, feature list, privacy/security posture, export capabilities, testing status, and local run instructions.
- Avoid adding screenshots or generated assets unless needed; keep this docs-only pass focused and low-risk.

## Review

- Replaced stale Excel-focused README content with a current Roadmap Studio overview.
- Documented the latest Structure, Initiatives, Roadmap, Projected Savings, Stacked Bar Chart, PNG, save/open, and PowerPoint export features.
- Added repo-facing privacy/security notes covering local-only storage, no backend, no external runtime scripts, local PowerPoint vendor bundle, and browser CSP/no-egress posture.
- Confirmed the README no longer claims Excel import/export support.
- Final validation before commit: `python3 tasks/roadmap_feature_tests.py` returned 87 passed, 0 failed, 0 untested; `git diff --check` passed.
