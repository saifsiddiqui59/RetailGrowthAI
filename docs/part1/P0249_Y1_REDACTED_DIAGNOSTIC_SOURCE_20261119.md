# Issue #249 — Y1 deployment/indexing read-only source recovery (2026-11-19)

Two unchanged original SHA blobs from existing unreviewed [#921](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/921), head `64ba7a53ae7942791185d98bbd08d8d71e642bb6`:
- `ops/p0249_y1_deploy_diagnostic_readonly.py` SHA `3456d2d0eb174959191434ecf86201b5c1e988ad`
- `tests/infra/test_p0249_y1_deploy_diagnostic_readonly.py` SHA `d6816f8cc124613a1f05ca471a0397192422bf73`

Existing current-main fail-closed `ops/p0249_y1_canary_guard.py` SHA `8a44ca7b9902db51fbf76f1c9f8a2695f30357a9` is untouched. Offline tests prove allowlisted non-secret deployment/build flags only, bounded sanitized status classification, and guard rejection before any calls. The diagnostic source may use Azure CLI ONLY if separately run in protected authenticated DEV with exact Y1/FC1 guard; this PR **does not add any workflow, dispatch, Azure permission, deployment, account read or network call**.

Original #921 stays OPEN for independent manual workflow/cloud permission review; neither this source addition nor fixture CI establishes Azure Y1 indexed Functions or fixes original Flex gateway 503. No host credentials, GPU, paid AI, Azure resource writes, PROD or WineShopPOS edits. Source acceptance requires exact-head 4/4 and separately fresh main 4/4.
