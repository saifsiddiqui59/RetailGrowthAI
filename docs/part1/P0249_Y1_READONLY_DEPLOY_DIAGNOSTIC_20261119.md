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

## 2026-11-20 — strict index provenance and duplicate-setting safety (source only)

The diagnostics now classifies `EXACT_TWO` or `EXACT_FIVE` only from
uniform bare known function names or exact `rgai-dev-y1-p0249-d4e5ddbd/<function>`
names. A different site's prefix, nested path, mixed bare/prefixed output,
unknown/duplicate names or malformed strings cannot be treated as accepted
Y1 indexing just because the last path segment matches. The parser never
prints unrecognized names. Duplicate expected app-setting keys (including
case aliases) and missing/malformed setting names fail closed; unknown
configuration keys remain ignored and their values never leave the process.
No extra Azure queries or writes are added. Offline negative regressions
cover the above and the existing manual-only protected workflow remains
unchanged. Green source CI, independent shared diagnostic review and actual
protected DEV read-only execution are distinct gates; no five-GET live
deployment or signed two-shop acceptance is claimed.

## 2026-11-20 — owner-delegated failed-release readout and next safe check

Original five-route trial #44618073780 passed resource identity, five/rollback ZIP validation and JWT transport checks but **failed** indexing (only 2, not 5, on 12 checks). Independent restore verified the original 2 routes and 20/20 health responses.

Protected read-only diagnostic #44621448507 verified original Flex unaffected and Y1 still EXACT_TWO. SCM_DO_BUILD_DURING_DEPLOYMENT is true; ENABLE_ORYX_BUILD is absent; WEBSITE_RUN_FROM_PACKAGE is present with an **unclassified value**. No entries appeared in the deployment-history API and the permitted log-category checks revealed no specific startup or build error. Empty history does not prove ZIP upload failed.

The next read-only diagnostic emits only a fixed value class for WEBSITE_RUN_FROM_PACKAGE (ABSENT / DISABLED / LOCAL_PACKAGE / EXTERNAL_HTTPS_URL / UNRECOGNIZED), and a fixed mixed-versus-aligned build flag class. It never prints package URLs, SAS tokens, account names, raw deployment logs, or secret values. Microsoft guidance for Linux Consumption remote build requires SCM_DO_BUILD_DURING_DEPLOYMENT=true, ENABLE_ORYX_BUILD=true and no active run-from-package; external package URL is a separate mode. A mixed configuration is a **hypothesis**, not proof of the root cause or permission for another deployment or app-setting change.

No second ZIP deploy, GPU/paid inference, PROD, SQL, customer Auth, original Flex, WineShopPOS or frontend cutover.
