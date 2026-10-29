# Feature3 private saved-design and generated-job browser scope fencing — 2026-10-29

## Actual source fix
`frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx` previously performed signed, tenant-scoped HTTP reads through `feature3Api` and checked some generated-image links, but persisted old draft/history/generated-job arrays and CAS ticket data while a shop/campaign/day or API provider changed. A delayed `listDesigns`, `listGeneratedJobs` or `saveDesign` could update browser state after a new scope mounted. The generated signed-link check also compared shop/provider without the **campaign/day** scope key.

The updated wrapper:
- Tags saved drafts, reopened designs, generated-job statuses, messages and busy state with the same validated `feature3ContextKey(shop,campaign,day)`. The rendered view shows **nothing from a different scope or replaced signed API session**, even before React's next effect cleanup; state includes API provider identity as well as shop/campaign/day.
- Uses per-request generations plus currently mounted shop/day/provider reference to discard stale history, job and download replies, including responses that arrive between render and effect cleanup.
- Resets the optimistic save CAS ticket and scoped pending flag on workspace/provider change, and checks provider identity synchronously before carrying a revision. A late save acknowledgement cannot update the new shop/day's design ID/revision; unknown POST acknowledgement is **not automatically retried**. Saving a current context still uses the existing `feature3Api.saveDesign` and server-side SQL CAS.
- Requires an actual saved DRAFT row's shop, campaign and day IDs to match current scope before reopening; every referenced private image must still be decoded in the current authenticated imageMap.
- Does **not** change database grants, invent commercial rights, generate media, activate GPU, or expand access to signed URLs.

`frontend/src/features/creative/feature3-workspace-scope.mjs` supplies simple pure client-side presentation/epoch checks; `tests/frontend/feature3-workspace-scope.test.mjs` verifies first-paint tenant/day denial, stale API/session and overlapping request generations, and validates the real component source compiles while keeping the no-retry/identity fences. The existing guarded private-link TTL remains unchanged; already minted 60s links still cannot be instantly revoked merely by client state.

## Release boundaries
Source-only, mocked frontend tests cannot validate actual signed cross-tenant DEV, real model/customer licences, approved model reuse, generated PNG quality or a mounted no-URL Azure route. All 31 hosted Supabase migrations remain unchanged. Require exact PR-head four CI jobs and fresh postmerge main CI; genuine live rights/source audits and cross-feature service spans remain separate approval gates. Never modify WineShopPOS or PROD.

Signed API providers must be replaced on auth-session replacement, not silently reused with mutable credentials. The component cannot detect an invisible session change in the same provider object. Cached 60-second links are hidden immediately on provider replacement, independent of effect cleanup.
