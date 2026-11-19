# Feature #2 / F2-31 — private editorial approval recheck (2026-10-30)

Status: **IN PROGRESS — source-only**, not integrated DONE.

## Change
- In `handoff-approval.js`, the trusted server-side approval adapter now re-reads the authenticated, tenant-bound editorial record after its initial reviewer-membership check, then checks membership again immediately before signing.
- It denies a changed/revoked original creative plan or motion SHA, media rights, retailer claims, independent human review, reviewer identity, shop/campaign, or active OWNER/EDITOR membership.
- No browser-provided approval, new publishing permission, paid model dispatch, GPU inference, cloud mutation, PROD edit or WineShopPOS access.
- The source-level HMAC receipt remains editorial-only. This additional read fence **does not** provide atomicity against a race after the final read. The coordinator must use a durable RLS transaction/CAS and a fresh recheck at the consuming Feature4 boundary.

## Verification
- Regression test `ai-agents/creative-director/tests/test-handoff-approval.js` covers revoked rights/claims/human decision, changed plan and motion digests, changed reviewer, third-read membership revocation and final read exceptions.
- Targeted command: `node ai-agents/creative-director/tests/test-handoff-approval.js`.
- Exact-head four-job CI is required; do not report PASS until the actual run is verified. Existing parent Feature2 PR #551 at `f38bf815cad7d77b7cadd9aa8bff55759e86947c` had 3/4 passing with four coordinator-owned ZIP member limit tests failing (issue #650); do not bypass those protected tests.

## Integration handoff
- Stacked feature-owned branch: `feat/f2-31-editorial-review-revocation-fence-20261030`.
- Target: existing Feature2 draft branch `feat/feature2-unified-offline-source-20261028`, PR #551; coordinator owns merging this stack and subsequently PR #551 into `main`.
- Task ID: `F2-31`. Proposed coordinator event: keep `IN PROGRESS`, `integrated_done=false`; attach branch/PR SHA, exact-head test evidence and coordinator acceptance only after review and fresh main 4/4.
- External blockers: F2-31 live signed reviewer JWT/RLS and persisted atomic CAS (coordinator); ISSUE-650 package 120-member CI gate (coordinator); genuine independently approved rights/retailer copy (coordinator/human reviewer).
