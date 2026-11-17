# Feature #2 — retailer-copy Unicode claim hardening (2026-10-30)

- Original task: **F2-02** in the pinned 38-task tracker.
- Ownership: Feature #2. Stacked draft PR **#707** onto existing Feature #2 integration draft **#551**. No merge or deployment.
- Scope: offline source review in `ai-agents/src/ai_agents/feature2_creative_quality.py` and negative tests in `ai-agents/tests/test_feature2_editorial_basis.py`.
- Detect NFKC/fullwidth commercial percentage, currency, free-shipping and material claims that ASCII-only matching missed. Continue requiring exact *original* approved offer wording rather than silently normalizing it into a new approval.
- Reject unsafe invisible/bidi/word-break control characters; preserve valid Indic ZWJ/ZWNJ. Verify that signed percentage offer records agree with the numeric claim and carry a nonempty bounded SKU scope.
- Offline test cases cover forged/mismatched percent-off, empty SKU scope, Unicode-disguised discounts/prices/claims, invisible controls, and legitimate Hindi joiners. **Tests are not real model or live retailer evidence.**
- Source task status: **IN_PROGRESS**; no integrated DONE credit. Actual CI must be read from the exact PR head. Do not mark this as passed merely because tests were added.
- Required coordinator follow-up: review stacked PR #707 and choose the unified #551 integration path; resolve protected **COORD-PACKAGE-650** (owner: shared coordinator/Azure packager; acceptance: all four protected ZIP limit preflight tests pass without weakening limits); verify four-job exact-head CI and fresh postmerge main CI.
- Additional live gates: current tenant JWT/RLS, signed approved offers/SKUs, editor review, and Azure #249 reliability. Fixtures never authorize publication, paid inference, or customer claims.
- No GPU, paid model, PROD, hosted SQL, or WineShopPOS changes.

## Additional independent F2-04 source hardening

The same reviewed bounded private RSS snapshot and relevance scorer now reject invisible word-break and bidi controls inside source headlines. Tests exercise both the direct verified trend-row path and original signed RSS2 XML parsing path; legitimate Marathi relevance remains unchanged. This is **source-only IN_PROGRESS**, not a verified live trend, signed hosted feed fetch, or integrated task completion. The trusted private source, licensing and allowlist readers remain coordinator-owned.
