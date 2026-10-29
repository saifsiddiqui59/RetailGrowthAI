# Feature #2 / task #27 — exact one-shot sentence-retake receipt

2026-10-29. **IN PROGRESS**; source-only continuation of unified draft PR #551; no inference/GPU/live deployment.

## Source change
- Existing `feature2_sentence_retake.local_sentence_retake` now echoes the immutable reserved `job_key` in pending metadata and requires its **trusted backend private-store** receipt to match job key, shop, campaign, plan SHA, original audio SHA, new private WAV SHA, voice, locale, speed and pending review state. Rejects receipt claims of publishing, commercial approval or Azure fallback.
- It checks current editor and exact source plan again **after** the private writer callback, so an already-revoked result cannot be reported successful. This does **not** roll back an already-written object. A real coordinator atomic writer must transactionally fence rights/lease/plan and clean up partial writes.
- Existing React `verifyLocalSentenceRetakeReceipt` checks exact original request job_key/voice/locale/speed, one reserved attempt and null word timestamps, rather than accepting a cross-job reused receipt.
- Synthetic PCM and injected test doubles cover good pending receipts, 12 altered writer fields, in-flight revocation and changed plan; Node tests reject cross-job replay, different voice/locale/speed, multiple reserved attempts and fabricated word timing. These are not real Kokoro inference/verified pronunciation.

## Acceptance / coordinator dependency
Task #27 remains IN PROGRESS. Existing upstream signed editor, approved pronunciation dictionary, genuine offline Kokoro licensed weight/inference, F7 real signed transcript, F4 approved audio assembly, real transactional private store, issue #650 protected Functions ZIP packaging and #249 DEV HTTP reliability are **not** delivered by this PR. Coordinator must ratify the backend receipt contract, test durable claim/lease and side-effect rollback with true signed DEV users and integrate reviewed work into main only after exact-head and postmerge 4/4 CI. No paid API, public URL, commercial use, GPU, PROD or WineShopPOS.
