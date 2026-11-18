# Feature #3 — development-code completion vs. hosted verification (2026-11-05)

## Owner decision: demo assets and test identities must not block DEV code

**Scope: development, not commercial launch.** Use self-generated/synthetic PNG/JPEG/MP4 samples, controlled demo content, and isolated non-privileged test shops. Test accounts should be actual isolated DEV accounts when legitimately provisioned and available; otherwise use clearly labelled mock JWT/rights/database callbacks and defer signed hosted tests. A synthetic approval callback is TEST DATA, not independent commercial authorization. **Do not require acquiring company permissions, customer photographs or a paid GPU to implement and test the source.**

Keep tenant/RLS/least-privilege/lease/asset-byte validation in application code. Do not grant real rights to third-party media, bypass signed-user security in hosted routes, publish demo likenesses, or imply rights-cleared production images. For an eventual public/commercial release, assess licensing and actual upload permissions separately. Avoid downloading/distributing unverified third-party originals; use generated or controlled test fixtures.

**Development-code acceptance:** A specific original task may be labelled `DEV_CODE_DONE` when its defined offline implementation is present in accepted `main`, has deterministic positive/negative regression coverage and fresh four-job postmerge main CI. Record exact evidence and distinguish unimplemented integration code from hosted verification. Do **not** append a canonical `DONE` / `verified_hosted` event to `coordination/task_progress.json` based on mocks. If a concrete missing source implementation is discovered, reopen the corresponding dev task. Host/release test readiness is tracked separately and never blocks the next independent source task.

## Verified GitHub development-code baseline

At the time of this checkpoint, `main` = `b1509e24557530ce99e412d10213139893f30df3`; fresh postmerge Part 1 [CI #41903466197](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41903466197) passed four of four jobs (Supabase isolated auth/RLS, Python, frontend, FFmpeg).

| Original task | DEV code | Concrete integrated evidence | Deferred *hosted* checks |
|---|---|---|---|
| **F3-01** — prior source PR integration | **DEV_CODE_DONE** (previously accepted) | Existing `coordination/task_progress.json` event, merged #813 and main CI #41131088666 | Does not certify an end-to-end product |
| **F3-02** — private worker input readers/materialization | **DEV_CODE_DONE** for offline worker input handoff | `poster-engine/feature3_worker_inputs_v1.py`, `feature3_worker_input_handoff.py`, real Pillow synthetic-pixel tests `tests/media/test_feature3_worker_inputs.py` and `test_feature3_worker_input_handoff.py`; merged [PR #862](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/862) | Actual hosted worker binding, real durable lease callback and user-upload rights |
| **F3-03** — registered private source byte/rights verifier | **DEV_CODE_DONE** for offline proof adapter and denial tests | `azure-functions/campaign-api/feature3_private_source_proof.py`, `tests/api/test_feature3_private_source_proof.py`; merged [PR #865](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/865) | Service-owned real approval authority, signed hosted output and independent production security/rights verification |
| **F3-13** — tenant/rights/uncertain-ACK regression baseline | **DEV_CODE_DONE** for current offline negative regression suite | `tests/media/test_feature3_worker_input_handoff.py` and `test_feature3_worker_inputs.py` contain foreign-shop/revocation/lease-denial cases; `tests/api/test_feature3_gpu_queue_publisher.py` covers unknown claim, failed send and ambiguous SQL ACK with no unsafe retry; merged [PR #866](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/866). [PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872) extends browser stale-callback regressions | Two genuinely signed real DEV shops, mounted live endpoints, queue/worker failures, independent tenant/security review |

**Revised DEV-only task snapshot:** 4/33 have an accepted development-code milestone (F3-01/02/03/13), 8/33 remain source-in-progress (F3-05 through F3-12), 21/33 remain blocked/dependent under the *older mixed-scope baseline*. These are not measures of hosted or commercial readiness. **Hosted acceptance remains 0/33** by the previous release rubric. The development completion labelling here does not assert full original task acceptance under the older hosted rubric, and the shared registry stays unchanged until separately reviewed.

The source PRs above were integrated by owner-authorized merges, and their GitHub history does **not** establish independent sensitive-code reviews. A 4/4 CI pass never substitutes for an independent rights/security approval where actually needed for release. This review gap does **not** stop safe demo-only coding.

## Immediate execution instructions (also reflected in hourly Feature #3 sprint)

1. F3-02/F3-03/F3-13 DEV source work is finished for the cited baseline; don't rebuild it solely to obtain commercial media or hosted logins. Reopen only when an identifiable implementation defect/new contract requirement is found.
2. Move source development to F3-08's unmounted authenticated private binary route and F3-09's Studio save/reopen/review wiring, using test-only media. F3-05/06/07/10/11/12 can advance independently with disposable/mocked verification.
3. Prefer two isolated DEV shops/accounts for real deny tests if safe credentials already exist. If not, use synthetic two-shop fixtures and record real hosted testing as deferred, **not** a failed coding task.
4. Record commits/PRs, actual tests, final-head CI and fresh main CI before any further DEV_CODE_DONE label. Preserve the original 33 IDs. Do not auto-enable paid inference/GPU, mutate hosted SQL, deploy PROD, modify WineShopPOS or bypass approvals.

**Canonical docs:** `docs/PROJECT_STATE.md`, `NEXT_TASK.md`, `DECISIONS.md`, `WORK_LOG.md` and the original 33-package ledger have overlapping open review PRs #873/#874. Reconcile those reviewable shared records rather than overwriting them or creating contradictory hosted DONE events. This feature-owned development status note does not alter those canonical files.
