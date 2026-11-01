# Feature #3 — F3-10 / F3-13 private generated Blob revocation retry

## Defect and owned scope
The pre-existing browser generated PNG preview `clear()` erased the only owned object URL before calling `URL.revokeObjectURL`. If that operation threw, the private URL was hidden from React (correct) but lost from the cleanup ledger (incorrect), so later cleanup could not retry. The failed replacement path could also drop the newly issued URL when its attempted revocation threw.

## Source-only change
- Retain failed-to-revoke, **locally issued** object URLs in a private `pendingRevoke` Set, never in a renderable state.
- Retry pending cleanup on explicit `clear()` or `selectScope()`; remove each entry after successful revoke.
- Clear visible preview and job **before** touching the revoke API, and clear tenant association before a scope switch, so failures remain fail-closed.
- Never accept an old live or pending URL as a fresh replacement; no remote URL or API/Storage path is used.
- Source/tests: `feature3-generated-blob-scope.mjs`; `tests/frontend/feature3-generated-blob-scope.test.mjs`. Original package IDs F3-10 (Blob lifecycle) and F3-13 (negative/revocation regressions).

## Evidence and required gates
Targeted Node command: `node --test tests/frontend/feature3-generated-blob-scope.test.mjs`. The GitHub connector cannot execute local Node; evaluate exact final-head four-job CI and results before review. No new cloud deployment, GPU, paid inference, hosted SQL, actual commercial rights, signed multi-tenant DEV tests, preview assets, or PROD/WineShopPOS changes. Independent reviewer required for sensitive private-media lifecycle code; no source-only CI is 33-package hosted DONE.

Current blockers remain: Feature3 signed PNG route #471/#325, licensed media F3-LICENSED-MEDIA, Azure reliability #249 and source/rights-approved real hosted tests. No new acceptance event.

## 2026-11-01 continuation — bounded private URL allocation under revoke outage
- Additional F3-10/F3-13 regression: while a browser keeps rejecting `URL.revokeObjectURL` for a hidden previously issued URL, repeated clicks on Preview must not allocate an unbounded series of fresh private Blob URLs. Earlier pending-revoke logic retained URLs for later retry, but `install()` allocated a new URL **before** attempting pending cleanup on every call.
- `install()` now first retries any existing hidden `pendingRevoke` ledger and denies new allocation until all old locally issued URLs have been revoked. A failed initial replacement still releases the new URL (or tracks it for retry) and never renders either URL. Test repeats 20 denied Preview attempts with **zero** additional object URL allocations, then verifies recovery, current-shop display and exact one-time cleanup.
- This remains source-only, within the existing PR #859 and original task IDs F3-10/F3-13. CI must pass on the **new exact head** after this change; earlier PR green is stale. Independent private-media review, current-main integration and fresh postmerge 4/4 are still required; no hosted media or production acceptance.
