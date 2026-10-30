# Feature #7 — durable scheduled-run checkpoint

Updated: 2026-10-30. This checkpoint is **source-only** and does not change the coordinator task registry.

- **Task:** F7-G (negative input validation), scoped to offline caption projection.
- **Parent:** draft PR #513 (`feat/feature7-uploaded-footage-semantics-20261028`).
- **This change:** stacked draft PR #825 (`feat/feature7-caption-projection-validation-20261030`).
- **Code/test commit before checkpoint:** `e07ee3f6d4c836f7d37f5e129018d0e7e7b3fac7`.
- **Changed code:** `video-engine/feature7/transcript_adapter.mjs`: validate every cue/word, including outside the trim, before filtering; cap cue/word counts and time bounds; reject malformed inputs.
- **Added test:** `tests/media/test_feature7_caption_projection.py`: clipping correctness, off-window invalid cues, invalid word intervals and resource limits.
- **Verification:** GitHub source commits and PR created. Local Python/Node tests **not run in this execution**; exact-head GitHub Actions **pending inspection**. Do not mark F7-G fully tested, PR-ready or integrated.
- **Acceptance still missing:** passing targeted tests, exact-head CI, coordinator review and merge; hosted DEV and real media QA remain separate.
- **Next task:** F7-F: inspect existing Feature4 F4-15 source handoff, add one independent contract-negative regression if needed; if blocked or already covered, select next independent F7-G/F7-AA negative test after rereading the task registry.
- **Safety:** no paid inference, GPU, cloud, production, real customer media or WineShopPOS changes. Test fixtures are not production media.
- **Ownership:** Feature7 only; coordinator updates shared status and integrates main.

The next scheduled execution should inspect PR #825 head/CI, correct any failing test, and then select the next eligible task without repeating this patch.
