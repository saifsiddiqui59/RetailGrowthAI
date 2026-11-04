# Feature #2 durable run checkpoint — 2026-10-30 (F2-30)

- Task: **F2-30** voice/locale route negative validation, source improvement committed; not integrated DONE.
- PR: **#833**, draft, stacked on #551; branch `feat/feature2-f2-30-unhashable-voice-selector-20261030`.
- Pre-checkpoint source/test head: `5ef4cd9fe886b3b8c3c66614cc609d2a76f50948`.
- Files: `ai-agents/src/ai_agents/feature2_azure_speech.py`, `ai-agents/tests/test_feature2_azure_speech.py`.
- Change: type-check voice ID, locale and speed before dict membership/lookup to deny malformed/unhashable fields with `SpeechRejected` and no reservation/provider egress. Seven offline negative fixtures.
- Tests: not executed in this run; exact-head CI not yet verified. No Azure Speech provider call or live credentials used.
- Independent parallel F2-02 work: draft PR **#832**, stacked on #801; its checkpoint is in `docs/feature2/RUN_CHECKPOINT.md` on that PR branch. Do not confuse these separate branch heads or assume they are integrated.
- Blocker: coordinator integration of parent PR #551, exact-head 4/4 and postmerge main CI; no automatic merge.
- NEXT: verify CI for PRs #832 and #833; if pending, inspect **F2-08** source-only blind-review history checks and add a distinct regression only if missing. Check registry, ownership and PRs before any edits.
