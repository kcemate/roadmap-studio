- [x] Remove ExcelJS and Excel import/export surfaces.
- [x] Preserve JSON project save/open workflow.
- [x] Add no-egress CSP and security regression coverage.
- [x] Add browser-local PowerPoint export with one slide per pillar.
- [x] Run full validation.

## Review

- Removed the external ExcelJS CDN script.
- Removed Excel import and Excel export controls/code.
- Kept JSON project save/open and PNG export.
- Added a meta CSP with `connect-src 'none'` and no external origins.
- Added security tracker/test coverage as `SECURITY-001` and `SECURITY-002`.
- Added a local vendored PowerPoint writer in `vendor/pptxgen.bundle.js`.
- Added a `PowerPoint` export button that creates one readable slide per pillar.
- Added tracker/test coverage as `EXPORT-004`.
- Rendered the generated PPTX through headless Office and visually checked the first slide.
- Full Playwright behavior suite: 65 passed, 0 failed, 0 untested.
