# Feature #2 — signed private voice, audit and editor source gateway handoff

Checkpoint date: **2026-11-09**. Feature lead: F2. **SOURCE COMPONENTS ONLY, NOT HOSTED OR MAIN INTEGRATED.** Original 38-task state remains 9/17/12 and 0/38 integrated DONE.

## Concrete code paths

- `azure-functions/campaign-api/feature2_store.py`: `Feature2PrivateVoiceStore` (F2-19/20), `Feature2PrivateAuditStore` (F2-08/12), `Feature2PrivateReviewedDraftStore` (F2-03/31). Current owner/editor JWT membership + PostgREST RLS reads, canonical UUID and original SHA, bounded event/revision histories; no service role for browser reads. Revocation, source integrity, immutable chain and independent evidence remain required for actual hosted acceptance.
- `azure-functions/campaign-api/feature2_adapter.py`: `Feature2PrivateVoiceGateway`, `Feature2PrivateAuditGateway`, `Feature2PrivateReviewedDraftGateway`. All compose existing verified source validators through operator-injected trust dependencies, never fake a missing signer/worker.
- `azure-functions/campaign-api/function_app.py`: GET-only status and private binary WAV paths behind `RETAIL_FEATURE2_PRIVATE_VOICE_READ` default OFF. Protected deployed ZIP does **not** yet include required original validator modules; even enabling flag cannot yield a verified live read without reviewed package changes (503 fail closed). Status: F2-19/20 IN_PROGRESS.
- `frontend/src/features/voiceover/feature2-private-http.mjs` and `LocalVoicePanel.jsx`: GET-only session-scoped job status and SHA-verified private WAV streaming (20 MB hard cap), SHA+plan-hash from source, redirect disabled, no retries, no automatic playback. F2-10/26 IN_PROGRESS until signed Creative Studio mount.
- `ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql`, `feature2_private_audit_REVIEW_ONLY.sql`, `feature2_private_prompt_review_REVIEW_ONLY.sql`: proposed SQL **not applied**. RLS and protected signing/admin table design require independent review before migrations.

## Code and test evidence

| Batch | Commit | Exact-head CI |
|---|---|---|
| Signed voice RLS + original WAV | `71f9733b` | [4/4 #42283898465](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42283898465) |
| Fail-closed GET routes | `bfb6e66a` | [4/4 #42284871646](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284871646) |
| Original WAV browser client | `090d67d8` | [4/4 #42285862962](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42285862962) |
| F2-08/12 private signed HMAC audit | `bb7b53db` | [4/4 #42571554660](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42571554660) |
| F2-03/31 signed prompt revision + guarded CAS | `6461acc0` | [4/4 #42572366036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42572366036) |

Code tests used synthetic users and mocked private RLS/Storage/transaction backends. Human review HMACs are **test-only**, NOT real signed reviewers. The verified keys need independent signer lifecycle approval, and any SQL RLS raw attestation visibility needs security review. Do not grant browser publishing, rights, motion, monetary or job-worker permissions from these source readers.

## Next integration prerequisites

Independent security review of parent #551 and child #848 touched protected paths, actual packaged runtime Node22/Python dependencies and explicit RLS migrations, current signed two-shop DEV test-account evidence, real atomic budget/editor/source RPC CAS with auditable idempotency, private WAV bucket authorization and F7 signed original audio consumer, followed by Feature4/Creative Studio mount. No GPU or paid AI, PROD, hosted DB writes or WineShopPOS change are authorized.
