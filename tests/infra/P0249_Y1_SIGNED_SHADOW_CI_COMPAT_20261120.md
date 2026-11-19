# Issue #249 — postmerge signed-shadow test compatibility (2026-11-19)

- Context: PR #1018 replaced module-level tenant PostgREST URL opening with an origin-pinned, redirect-denying opener. PR #968's synthetic signed two-shop tests still patched the old module-level `tenant_store.urlopen` function.
- Observed live main #edfcd593 after #968: Actions #44591535212 Python failed 11 assertions with false 503 results while 1,991 tests passed. Root cause is test transport mismatch, not a reason to weaken JWT, current shop membership, tenant row checks, or redirect rejection.
- Fix: patch only `tenant_store._NO_REDIRECT_OPENER.open` with the existing strict synthetic PostgREST fixture; real signed JWT verification, tenant membership checks, route restrictions and negative cases remain executed.
- Verify the original 11 signed two-shop assertions, original #1018 redirect/origin negative tests, complete Python job and all four mandatory Part1 jobs on the exact PR head; then fresh main CI before marking accepted.
- Source/fixture only; no deployed Azure Y1 change, hosted SQL/Auth, feature approval, model/GPU spend, PROD or WineShopPOS modification. Original Issue #249 **remains open**.
