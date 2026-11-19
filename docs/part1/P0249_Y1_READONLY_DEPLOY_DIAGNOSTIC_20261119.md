# Issue #249 — recovered safe Y1 deployment/indexing diagnostic

**Source-only; NOT dispatched or hosted accepted.** This latest-main diagnostic
updates the old conflicted PR #921 without copying its obsolete historical
report into shared canonical docs or enabling cloud operations on push.

## Safety / scope
- A manual-only `workflow_dispatch` on `main` with the explicit
  `YES-Y1-READONLY-BUILD` option and protected `dev` environment is
  required. No `push` or `pull_request` trigger; no settings or deployment
  write. Azure OIDC is read-only and ends with logout.
- `ops/p0249_y1_deploy_diagnostic_readonly.py` verifies existing original
  Flex and isolated Y1 resource identities before reading targeted settings,
  deployment summaries, redacted Kudu status-category booleans, and indexed
  function names. It prints ONLY allowlisted setting-presence/true/false
  classifications and `EXACT_TWO`, `EXACT_FIVE`, `OTHER_UNVERIFIED`
  or `INVALID` index status; never prints secret values, unexpected route
  names, raw Kudu logs or resource identifiers.
- Previously this diagnostic investigated 0 indexed functions following a
  ZIP HTTP202. That incident state is **historical**. Later hosted canary
  #42964811296 verified two isolated Y1 GETs. This diagnostic has NOT been
  dispatched against current Y1 and cannot prove any five-route deploy.
- Tests require exact-route classification and fail if source accidentally
  restores automatic cloud sessions. The source is on a reviewable PR;
  shared workflow changes still require independent affected-lead review.

## Release relationship
- Active source chain #968 → #995 → #1025 is **unmerged** and has a protected
  manual-only five-GET deployment/rollback workflow. Current original Flex
  #249 markerless 503 issue is OPEN.
- This diagnostic contains **no release or rollback command** and can be
  reviewed separately. Do not interpret `EXACT_FIVE` as signed two-shop RLS,
  original API POST/PATCH/private media parity, or frontend cutover.
- No Azure/AppSettings/Auth/Supabase SQL writes, GPU, paid model, PROD or
  WineShopPOS changes were made in preparing this source.
