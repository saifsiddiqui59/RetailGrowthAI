# Feature #2 F2-27 — private sentence-retake post-write fence

Scope: one source-only, GPU-OFF security regression for existing F2-27. This is layered on the existing Feature #2 PR #551 branch; it does not reopen source-complete tasks or edit coordinator-owned files.

- `ai-agents/src/ai_agents/feature2_sentence_retake.py`: after the trusted pending-private writer returns, independently recheck the current editor role and exact authoritative creative plan. Reject writer receipts that claim publishable/approved output or skip fresh Feature #7 transcription.
- `ai-agents/tests/test_feature2_sentence_retake.py`: offline deterministic callback tests for post-write role revocation, changed plan, forged approved receipt, skipped ASR and a still-unapproved successful synthetic path. The test stubs trusted Kokoro metadata and does **not** execute inference, demonstrate audio quality or register production media.
- Ambiguous storage writes are **not retried**. An actual backend still needs transactional commit-time tenant/RLS authorization, durable one-shot reservation, orphan cleanup and signed original-WAV registration.
- No cloud, Supabase SQL, paid AI, GPU, PROD, WineShopPOS or user-facing samples.

Task: `F2-27`, **IN PROGRESS** until reviewed integration, exact-head four-job CI, real signed backend and fresh postmerge main CI. Do not mark integrated DONE from this source PR.

Coordinator proposed status receipt (not an authoritative shared registry write): `F2-27` remains `IN PROGRESS`; evidence is this PR, its head SHA and any verified CI result. Existing `coordination/task_progress.json` remains coordinator-owned.

Cross-feature dependencies: Feature #7 must provide a genuine tenant-signed new original-WAV transcript and human listening evidence; Feature #4 must assemble a reviewed corrected scene; coordinator must implement current-role/plan-fenced private transaction and approval API. Acceptance requires each producer's signed source/asset SHA, current tenant authorization, explicit human review and approved integration.
