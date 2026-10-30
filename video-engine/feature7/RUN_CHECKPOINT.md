# Feature #7 — durable coding checkpoint

Updated 2026-10-30 (scheduled continuation). **Source-only**, no coordinator-integrated DONE.

## Current work: F7-G / F7-F review receipt negative boundary

- Parent: draft PR #513, `feat/feature7-uploaded-footage-semantics-20261028`.
- This run: draft stacked PR #840, `feat/feature7-review-receipt-time-bound-20261030`.
- Code/test HEAD before checkpoint: `23856baf97a66f4d763610d2fd72ea8b3f421172`.
- Changed `video-engine/feature7/review_fence.mjs`: reject approval receipt issue times that overflow JavaScript safe-integer expiry arithmetic; deny signed handoff receipts with noninteger/zero-TTL/fractional timestamps.
- Changed `tests/media/test_feature7_review_fence.py`: offline boundary tests at MAX_SAFE_INTEGER - 600000 and rejection of bad issue times, plus test-only correctly HMAC-signed malformed receipt payloads. Fixtures are synthetic and signing key is test-only.
- **Verification:** GitHub commits and draft PR #840 created. Exact-head PR-triggered workflow query for `23856baf97a66f4d763610d2fd72ea8b3f421172` returned **no runs** at inspection. Local tests NOT RUN: this runtime cannot resolve github.com to clone source. Do not mark tested, PR-ready, or integrated.
- **Required targeted test:** `python3 -m unittest discover -s tests/media -p 'test_feature7_review_fence.py' -v`; then exact-head four-job CI and coordinator review.
- **Current blocker:** CI not observed on stacked PR head. Owner: Feature7 worker/CI coordinator. Required output: green targeted tests and four-job exact-head CI, followed by coordinator-approved integration; no bypass.
- **Next task:** F7-F: independently verify Feature4 F4-15 edit envelope against current PR #322 source and add a contract regression only if not already covered. Otherwise continue F7-G/F7-AA with a nonduplicated negative test. Recheck PR #825 and #736 overlap before choosing caption work.
- Previous checkpoint: PR #825 (`feat/feature7-caption-projection-validation-20261030`) still open and unverified. Its change overlaps earlier PR #736; do not duplicate or treat either as integrated.
- **Restrictions:** GPU OFF, no paid inference, no cloud/PROD/SQL, no real customer media, no WineShopPOS. Coordinator alone owns canonical task registry and main merge.

Next scheduled run must read this file, inspect exact PR #840 head/CI, and either fix actual failures or move to the next eligible independent owned task without recreating this patch.
