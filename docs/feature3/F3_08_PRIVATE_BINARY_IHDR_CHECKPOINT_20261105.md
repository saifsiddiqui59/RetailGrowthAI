# Feature3 F3-08 source checkpoint — 2026-11-05

- Original task: **F3-08**, IN_PROGRESS; private PNG HTTP adapter already existed on main. This change hardens only the byte boundary, not a mounted authenticated Azure route.
- PR: #876, branch `feat/feature3-f3-08-png-ihdr-boundary-20261105`.
- Source: `azure-functions/campaign-api/feature3_private_binary_http.py` now rejects malformed IHDR dimensions, excessive pixel area, invalid color/depth combinations, nonstandard compression/filter/interlace and reserved chunk bits.
- Tests: `tests/api/test_feature3_private_binary_ihdr.py` uses synthetic PNG and forged but internally consistent SHA/CRC receipts, including positive roundtrip and denial cases.
- Baseline main `837943de3507c3021b16b4f54e2044f2e9418266`, Part1 main run #41964154857: four jobs success.
- New branch tests and exact-final-head CI: **not yet verified**; do not count source DONE. Requires independent affected-lead/security review before merge, and fresh main 4/4 afterward.
- Owner-accepted DEV_CODE_DONE baseline remains **4/33** (F3-01, F3-02, F3-03, F3-13); hosted **0/33**. No new accepted task completion from this PR.
- Next code action: wire the existing `Feature3PrivateBinaryHTTP` through a real JWT/RLS-backed revocable reader into the Azure Functions binary response route behind a default-OFF feature flag; add signed-role denial tests with disposable identities or isolated mocks. Do not connect the existing JSON signed-link route as a substitute.
- No GPU, provider, hosted SQL, PROD, cloud or WineShopPOS mutation.
