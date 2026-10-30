# Feature3 F3-13 — Private generated-history state envelope (source-only)

## Scope and defect

The existing `validateFeature3GeneratedHistory` strictly projected individual job rows, but `scopedFeature3GeneratedHistory` spread the *surrounding state object* into its result. An accidental extra signed URL, private object key, approval flag, or arbitrary provider metadata could therefore escape the intended private status-only view despite valid job rows.

## Proposed source fix

The scoped selector now requires own shop/jobs fields, permits only `shopId`, `jobs`, `message` and `busy`, validates message length/type and boolean busy, then returns a fresh frozen allowlisted object. Unexpected fields or malformed values fail closed to empty jobs/message. The existing row validator and signed tenant restrictions remain unchanged.

Added deterministic Node regression in `tests/frontend/feature3-generated-history.test.mjs` covering valid current-shop history, unexpected signed URL/object path/approval/provider fields, invalid message/busy, and minimal state compatibility.

## Evidence / status

- Central original task: **F3-13**, cross-tenant, rights and ambiguous-ACK regressions. This change covers **only browser state-envelope leakage**, not full F3-13 acceptance.
- Branch: `feat/feature3-f3-13-history-envelope-20261030` from main `a75f9df62451dbc701633782a9baf1b16e32c8c8`.
- Source is a review proposal, not integrated DONE. Verify exact-head four-job CI and fresh main four-job CI after coordinator merge; do not mark task-progress DONE until acceptance.
- Independent coordinator integration wave PR #811 is still under review. This change intentionally avoids its modified files; coordinator must reconcile against the latest main before merge.
- No GPU, provider inference, hosted SQL, queue ACK, Azure deployment, PROD or WineShopPOS operations. No media fixture is approved production output.

## Remaining acceptance

Coordinator review, PR exact-head 4/4 and fresh postmerge main 4/4; genuine hosted signed-role and rights-revocation E2E remain blocked on approved DEV service/role setup, current legal source evidence and mounted private route. No live output claims.
