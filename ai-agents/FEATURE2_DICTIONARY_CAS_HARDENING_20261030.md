# Feature #2 / F2-10: reviewed Kokoro spelling correction hardening

Date 2026-10-30. **CODE IMPLEMENTED, TASK STILL IN PROGRESS** until real JWT/RLS, rights and protected CI acceptance.

Changes in existing module `feature2_pronunciation_dictionary.py`: valid canonical same-shop UUID v4 required; reviewed `word` must be exactly one matchable source token (a multiword spelling cannot match the existing one-token substitution regex); `spoken_as` may be a bounded phonetic phrase, but no untrusted markup, hidden spaces or control characters. This prevents silent reports of "approved" replacements that cannot be applied.

Signed editor and exact source preferences are checked before the DB CAS. The returned receipt must match shop, word, spoken hint and exactly the next integer revision, and cannot claim paid inference, publishing, automated retry or verified audio quality. The current editor is rechecked **after** CAS before a successful approval is returned; source-only callbacks do NOT implement transactional rollback, which the trusted server/DB must independently ensure. The private read projector also rejects unsigned/unmatchable correction records and forged publish/retry flags, preserves the reviewed original script, and never labels the changed text as proof of correct audio.

Added targeted offline negative tests for revocation after save, invalid UUID, multiword source, hidden/markup spelling, forged paid/publish/phoneme results, and one positive multiword phonetic hint. No real Kokoro model, OpenPronounce or Feature7 ASR inference, human pronunciation decision, hosted private write, or rights release was performed. Coordinator: reconcile current F2 parent #551 with new source branch, maintain the protected ZIP 120-member invariant under issue #650, resolve Azure DEV #249 separately, verify exact-head all four CI checks and fresh postmerge main four checks, then test real signed editor and F4/F7 retake handoff.

GPU OFF, all paid models OFF, no new deployment, PROD or WineShopPOS modification.
