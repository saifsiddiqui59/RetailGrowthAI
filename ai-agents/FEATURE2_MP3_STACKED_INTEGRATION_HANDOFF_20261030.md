# Feature2 private MP3 stacked source integration — 2026-10-30

**Integration branch ONLY, not main/hosted DONE**. Source is copied from stacked [PR #704](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/704) at verified `4403b147cd24cd734dcdaf8dd60885b5d1309b18` onto the verified Feature #2 eight-PR batch [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) head `8dbb1bae15525c3aea44e9454bdd692c6785f1f0`.

This scoped integration imports exactly two existing Feature2 source/test paths:
- `ai-agents/src/ai_agents/feature2_voiceover_upload.py` — original MP3 source and PCM16 derived WAV remain distinct SHA/asset IDs; 2 private objects atomically registered; rights/voice quality remain PENDING; editor and authoritative plan checked again after storage; offline FFmpeg decoder bounded to operator binary.
- `ai-agents/tests/test_feature2_voiceover_upload.py` — actual licensed local FFmpeg test conditional on host binary and deterministic no-FFmpeg negative/positive fallback. Asserts malformed RIFF, duplicate streams, wrong rights and mismatched registered pair.
The two original audit/handoff records for MP3 rights and RIFF boundaries are preserved verbatim from PR #704. Existing consolidated #848 branches and their voice-quality/tests are untouched.

**Important excluded scope:** PR #704 contains earlier stacked F2 editorial Unicode and private blind A/B audit changes in `feature2_creative_quality.py`, `test_feature2_creative_quality.py`, `test_feature2_editorial_basis.py` and distinct source handoffs. Those remain on their source PR for later source reconciliation. This integration does NOT claim #704 entirely merged.

Coordinator acceptance: verify 4 exact-head PR CI jobs, reconcile latest parent #848 head then #551 and source PR #704 remaining audit diffs, preserve #650 ZIP 120-entry security invariant and unblock #249. The trusted actual private store must enforce transaction-level JWT/RLS and rollback; source mock callbacks are not durable signed storage. Real original commercial/media rights and human spoken approval must be verified independently. No paid AI, GPU, PROD or WineShopPOS; **0/38 verified integrated DONE** until approved main merge and fresh main four jobs.
