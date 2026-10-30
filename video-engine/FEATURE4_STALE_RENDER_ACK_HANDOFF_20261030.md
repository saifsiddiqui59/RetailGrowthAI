# Feature4 F4-10 — stale render acknowledgement browser fence (2026-10-30)

**Source/Playwright IN PROGRESS, not hosted tenant validation.** Feature4-owned branch `feat/feature4-stale-render-response-fence-20261030` is stacked on F4-02 draft PR #841 with all earlier reviewed code intact.

## Bug
`VideoStudio.jsx` previously awaited `onRender(structuredClone(draft))`, then updated React `submitted`, `error`, and `busy` unconditionally. If a user switched from Shop A to Shop B or edited the active Reel while the network request was pending, a late ACK or error could mutate the *new* context. In particular, `submitted=true` could reveal Shop B's old `renderStatus=SUCCEEDED` signed preview without a current Shop B render; late errors could also clear the in-flight state of a newer request.

## Scoped source fix
- Add a local monotonically increasing request epoch, an immediate in-flight guard, and a render-time live `shopId`/approved creative-direction identity reference. Only the still-active request from the unchanged context may set `submitted`, error, or clear busy on completion.
- Invalidate epochs and unlock the local form when shop changes, an approved creative plan replaces a draft, a user edit/retrim/new draft changes it, or the component unmounts. The old remote job may continue; the fix **does not send cancellation, retry, charge, cross-tenant access, or approval calls**. Backend ledger and JWT verification are unaffected and still mandatory. Starting another job hides the previous output while awaiting server acknowledgement.
- Four new Playwright tests mount the *real* React Video Studio and Timeline Studio in a disposable fake-shop harness with deferred synthetic `onRender`: late Shop A success must not reveal a synthetic old Shop B signed video; Shop A rejection must not overwrite Shop B active render's busy/error; editing while a request is pending invalidates its ACK, but a fresh edited draft can submit. No real private links, signed media, network API or production uploads are consumed.
- This avoids a browser trust/race bug but **does not prove secure server authorization or JWT/token expiry**. The test provides no commercial media/rights or hosted worker acceptance.

## Remaining gates
Exact-head 4/4 GitHub Actions, coordinator-reviewed parent integration/main 4/4, real DEV shop sign-in/switch, stale expiring private signed URLs, reviewer check of actual rendered 15/30/60 outputs, and #249 Azure 503/#650 Functions package reconciliation. F4-10 remains IN PROGRESS, 0/31 accepted integrated DONE. No GPU, charged AI, PROD, WineShopPOS or public video sample.

## Follow-up source fix on same draft
An approved direction can change to an invalid/revoked object and then back to `null` without the shop changing; merely comparing the callback's original and final `creativeDirection` reference would falsely accept a pre-revocation ACK. The approval/rights review effect now **always invalidates the render epoch on any direction change**, including removal; current shop edit controls recover without waiting for a stale remote response. Fourth Playwright race test toggles approval away and back while the old ACK is pending, verifies the previous result stays hidden and only a fresh render submit may reveal the current signed fixture. Source code remains frontend-only, no remote cancel/charge. 
