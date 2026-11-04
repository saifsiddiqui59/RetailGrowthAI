# Feature #3 F3-09 / F3-13 — Private workspace reads without hosted dependencies

## Verified defect
The existing Feature3SecureDraftWorkspace already uses a React busy flag and
per-endpoint request nonces. React busy state is asynchronous: rapid second
clicks (two draft history GETs, two GPU history GETs, or two signed-download
requests) can all start before the render disables controls. A history refresh
and a private download can also overlap. These are **unnecessary authenticated
reads**, not evidence of cross-tenant authorization.

## Owned source fix
A synchronous, component-local, exact-identity private read gate now serializes
three GET kinds: draft history, generated job statuses, and signed download
receipt. It denies a simultaneous second read **before the API call**, and
releases only its own token after a response. Shop/day/JWT API rotation cancels
the old token; a late response is ignored and cannot unlock the replacement.
Draft restore and non-idempotent save also refuse to overlap with a private
GET. Existing write CAS, server RLS, JWT and image-rights checks are unchanged.
No new endpoint, provider, paid model, GPU, storage URL or cloud mutation.

## Offline test evidence and acceptance
Dynamic Node regression tests cover the two-click race, cross-kind exclusion,
scope/API identity, cancelled late receipt, and stale-finally isolation.
Source/JSX contract tests check all three UI paths and save/reopen guards.
Use `node --test tests/frontend/feature3-workspace-scope.test.mjs` and verify
mandatory exact-final-head Part 1 CI 4/4 before any merge. This work is
**F3-09/F3-13 source-only**, not evidence of a real signed DEV session or
a full hosted Creative Studio workflow. Existing #858/#860 and private media
PRs must not be overwritten. No protected review/rights approval bypass.

## Next action
Independently review actual component behavior with a mocked Playwright
browser fixture if available; maintain open original task IDs, then safe
feature-owned main integration with fresh main CI and separately reviewed docs.
Real authenticated DEV, rights, mounted binary route and Azure #249 remain
production acceptance gates, but **do not block these offline tests**.


## 2026-11-04 — Mock browser scenario (same PR)
Added a real Chromium Playwright scenario to existing `frontend/e2e/campaign-journey.spec.mjs`
using isolated mocked Supabase/Auth and campaign API responses (not actual DEV
identities). It walks persisted campaign -> opt-in CPU Studio -> editable text
poster -> undo/redo -> downloaded day-bound JSON -> same-day reopen -> forged
foreign-day JSON denial. Asserts no GPU/render/upload/signed-link side effects,
and that a signed backend save remains disabled without a v2 API. GitHub
frontend CI runs the existing browser tests. Not a hosted rights/RLS PASS.
