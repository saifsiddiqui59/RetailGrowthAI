# Feature #3 — Wave B reconciled integration proposal (2026-10-30)

**STAGED SOURCE ONLY; not merged, not production, GPU OFF.** This review branch starts at the Wave A candidate head `c32bf8756d8fb2fa88627ca4177f2317d30f6d00` (PR #811), then composes nine remaining independent F3 work PRs. It must be reviewed/merged by the coordinator *after* Wave A, with full combined branch and postmerge main four-job CI. The underlying PRs remain individually reviewable.

## Exact source inputs
#693 model current approved-use array, #744 second provider GPU-OFF status after private rights planning, #768 Blob URL replacement revocation failure, #709 provider/tenant scoped generated image history, #778 worker private original final lease fence, #790 approved poster context/signed copy, #791 scoped workspace provider busy state, #798 FLUX snapshot import input key duplicate denial and #802 model video-reference grant checking.

33 touched paths total (including scoped handoff/test files). **Six overlapping source files were reconciled against Wave A** rather than overwritten:
- `feature3_gpu_job_plan.py` and `test_feature3_gpu_job_plan.py`: retain Wave A lease/rights revision checks and append #693 exact approved-use list guard/tests.
- `feature3_gpuoff_queue_intake.py`: preserve Wave A `require_gpu_off()` used by Azure peek (including empty queues), add #744 *second* authoritative GPU-OFF check before final receipt; #744 isolated tests.
- `feature3-generated-blob-scope.mjs` and its test: retain Wave A image decode `discardFailed`, add #768 fresh-URL/exception-safe replacement logic and tests.
- `Feature3GeneratedHistory.jsx`: retain Wave A decoded-image `onError` revocation, add #709 backend API/binary-client identity scoping for history and previews.
All six compositions were made by verified context-matched hunks. Five additional independent PRs were imported as their exact original Git blobs without changing shared contracts or WineShopPOS.

## Coordinator acceptance
1. Validate PR #811 exact-head four-job CI green and feature rights review before main integration.
2. Validate **this stacked PR exact-head four-job CI**; verify old and new security regressions together, and do not treat individual PR green as combined acceptance. Repair actual failures without dropping tests.
3. Coordinator alone merges Wave A to `main`, verifies fresh main four-job CI, rebases or retargets Wave B to new `main`, verifies its newest exact head and then merges Wave B. Verify fresh postmerge main four-job CI again; update canonical state, ledger and task progress after accepted integration. Do not claim 33/33 or provider/licensed output completion.
4. The branch contains *no* hosted mutations or durable model/queue side effects by construction. Tests use disposable SQL, mock browser and CPU fixture media only. New PRs that arise after the snapshot need separate scoped review.

## Hosted release blockers remain
#471/#325 signed private no-URL Azure endpoint/current rights; #249 Azure 503; #627 genuine signed Testing Chat worker spans; F3-LICENSED-MEDIA independently licensed/approved original outfit/model; F5-GPU-AUTHORIZATION/PART3-WAN22-CONTRACT paid-provider/lease approval. Real VTON, image fidelity and invoice acceptance still blocked. All GPU/paid inference off; no production, hosted SQL, Azure queue, customer license approval or WineShopPOS change.

## Wave B addendum — existing Feature3 PR #812
- Integrated source-only F3-10/F3-13 proposal #812 (exact original PR head `73a195a940171dcd591a80cfd572555c01ec597b`, individual CI #41053717105 4/4) in **this same branch**, rather than opening a third integration train. Imported its standalone three handoff files, its private model Blob cleanup guard, and combined stricter generated-history allowlist with existing #709 signed API identity scoping.
- Reconciliation note: #812's original state selector only allowed `shopId,jobs,message,busy` and would reject legitimate #709 state carrying a private `api` identity. Revised selector permits `api` solely as an internal equality fence, **never exposes `api` in the returned frozen four-field snapshot**, and fails closed on extra URLs/metadata/approval flags, malformed busy/message and foreign API/shop. Updated original and additional negative fixture tests accordingly. This is **source-only** and does not certify hosted auth.
- The original #812 DEV Auth read-only handoff reports test accounts not provisioned; **no test login credentials, account creations or real sign-in verified in this wave**. All hosted F3-21 acceptance stays blocked.
- Wave B now includes ten additional source PRs above A, with 4 relevant overlap paths reconciled for this addendum. Updated cumulative exact-head four-job CI and coordinator review mandatory; previous 4/4 head is historic after this patch. No new task is DONE from source-only changes.

## Wave B source-only follow-up — private file/worker late rights fence
- Additional F3-02/F3-13 regression hardens `poster-engine/feature3_worker_input_handoff.py`, the existing F3→F4/F5 in-process bytes/file handoff. A genuine tenant-approved grant or garment revision may change **during the final worker lease callback** or temporary file write; a true lease response alone must not expose stale private images. An independent current `prepare_fashion_references` proof now runs after the terminal lease check for both in-memory and temporary-path delivery, and the disposable file directory is cleaned if rights or product revisions changed.
- Deterministic isolated media tests deny model/garment rights revoked during terminal lease and garment revision changed during final staged-file lease; asserting no staged path is yielded and temp files are removed. Synthetic authorizers/fixtures and real local image bytes only; not hosted RLS or paid inference. No external consumer contract or provider behavior changed.
- Coordinator review and NEW combined exact-head 4/4 CI required. Earlier #813 head and CI are historical after this new source commit. **0/33 hosted DONE** unchanged; GPU OFF and no PROD/WineShopPOS.

## 2026-10-30 — F3-11/F3-13 private model review session isolation and JWT gate
- The disabled-by-default Feature3SignedModelWorkflow editor had unscoped local React state: prior shop/API state could retain private source PNG selection, model/media IDs, rights confirmation, review checkboxes, notes and revisions across signed tenant/session changes. It now remounts the whole editor for shop + signed provider identity (and enabled/disabled transitions), while comparing original shop/provider/permission after each async network step.
- A source upload that completes after a shop/session change cannot launch the separate non-idempotent registration POST, and stale review/revoke responses cannot update the replacement UI. The backend still verifies real JWT roles and rights; the browser cannot grant licensing/approval.
- The signed model workflow POST client now rejects control/whitespace/non-ASCII JWT text before fetch, disallows ambient credentials and referrers, preserves no-redirect and no-retry behavior. Offline fixture tests assert isolation and no malformed-token send; NOT live signed DEV testing or commercial licensing evidence.
- Scoped tasks F3-09/F3-11/F3-13 remain source partial, **0/33 fully hosted DONE**. Coordinator review and new exact-head/full postmerge CI required. GPU OFF, no hosted DB/PROD/WineShopPOS changes.

- Final stale async fence: renderer-local monotonically increasing scope revision prevents an old signed tenant A operation from resuming after an A→B→A switch with the same shop/provider IDs. Both non-idempotent upload and review flows now suppress out-of-scope `finally` state updates. The revision is local UI state only, not SQL rights approval.

## 2026-10-30 — F3-08/F3-21 revalidate signed JWT at final private PNG delivery
- `Feature3RevocablePNGReader` now rechecks the signed JWT after the final live tenant/rights check, immediately before returning private PNG bytes. If the JWT expires, is revoked or verifies to another actor mid-stream, the request fails closed even if earlier membership and rights snapshots passed. JWT verifier exceptions are opaque rather than exposing internal credentials/URLs.
- Added four deterministic offline real-PNG/synthetic-JWT regression cases: expired JWT during binary transport, changed actor after transport, token revoked during final rights verification, and sanitized failed initial verification. Current RLS/storage proof remains in place; no fake JWT indicates actual DEV authentication.
- F3-08/F3-21 source-only hardening, NOT a live Azure Functions route, real signed DEV E2E, accepted commercial media or 33-package DONE. Coordinator must review exact-head 4/4 CI, merge, retest fresh main and separately approve the mounted route and current-role/expired-token DEV negatives. GPU/paid services OFF; no hosted SQL, Azure queue, PROD or WineShopPOS writes.

- First exact-head CI #41059611652 caught one **legitimate expected-call-count regression** in the existing composed HTTP contract: success now invokes `verify_user_jwt` twice, not once. Adjusted that baseline expectation and added a composed `Feature3PrivateBinaryHTTP` test proving an expired JWT during the last rights read returns an opaque **404 with zero PNG bytes**. This is not a retry of unsafe cloud operations; source-only fix then fresh exact-head CI required.
