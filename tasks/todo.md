- [x] Move realized totals underneath their Savings and Avoidance parent totals.
- [x] Keep the existing realized savings and realized avoidance calculations unchanged.
- [x] Update roadmap header regression coverage for the grouped layout.
- [x] Run full validation.
- [x] Publish a new here.now site.

## Review

- Roadmap header now groups `Savings` with `Realized` underneath and `Avoidance` with `Realized` underneath.
- Removed the narrow roadmap header constraint and allowed the legend to wrap cleanly.
- Visual check saved at `tasks/test-artifacts/roadmap-header-stacked-wide.png`.
- Full Playwright behavior suite: 66 passed, 0 failed, 0 untested.
- Published and verified: https://ancient-hazel-k3jv.here.now/
