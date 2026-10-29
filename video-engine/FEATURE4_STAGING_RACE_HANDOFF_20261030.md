# Feature #4 F4-15 — private staging lease/rights race handoff (2026-10-30)

Status: **IN PROGRESS — SOURCE IMPLEMENTED, CI/INTEGRATION UNVERIFIED**. Task registry: `F4-15`, 31-task tracker. Parent Feature4 draft PR #322; this change is isolated and does not modify the shared task registry or canonical coordinator documents.

## Source delta
- `video-engine/feature4_worker_handoff.py`: revalidate the coordinator-supplied authoritative rights check and current claim token after loading the DB-approved bundle, before private media staging; revalidate both after every private asset download before proceeding to another asset or invoking CPU rendering.
- Return `STALE` without calling renderer, upload, finalize, or worker failure when a lease/authorization is lost during staging. The temporary directory still cleans up via context manager. This is **not** a hosted queue/claim/cleanup implementation.
- `tests/media/test_feature4_worker_handoff.py`: deterministic offline negative tests for lease loss during bundle read and lease/rights revocation during private download, asserting no render, publish, completion, or duplicate failure.

## Acceptance and remaining gates
- Run `python -m unittest discover -s tests/media -p 'test_feature4_worker_handoff.py'` on the exact branch head, then inspect the four GitHub Actions jobs on the PR merge ref. This document does **not** assert that either test suite has passed yet.
- Coordinator owns `F4-22` (protected Functions ZIP member guard, Issue #650) and `F4-23` (reconcile parent #322, review/merge, fresh 4/4 main CI). Parent #322 was previously blocked on a Python package ZIP >120 entries guard. Never weaken that gate in Feature4 code.
- Coordinator owns `F4-25` atomic lease/outbox/quota and `F4-27` hosted cancellation/poison/orphan cleanup. Required output: approved atomic claim/finalize RPCs and hosted cancellation tests; acceptance: stale claims never charge twice or publish, and orphan private objects are reconciled.
- Real signed-in two-shop DEV E2E (`F4-30`), rights-verified retailer footage, actual human visual review (`F4-31`) remain unverified. Offline fixtures do not represent approved customer media.
- No GPU, paid AI, hosted SQL, PROD, shared workflow, WineShopPOS, or external approvals touched.

Next Feature4 worker should select another independent source task while this draft is under review; never mark `F4-15` integrated DONE until approved merge and fresh 4/4 postmerge main CI.
