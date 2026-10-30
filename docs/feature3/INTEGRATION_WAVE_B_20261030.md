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
