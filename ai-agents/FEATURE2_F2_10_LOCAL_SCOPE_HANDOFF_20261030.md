# Feature #2 F2-10 — in-flight local voice UI revocation fence (2026-10-30)

**Status:** IN PROGRESS / source-only, original task `F2-10` (38-task tracker); no integrated DONE claim. Dedicated branch based on unified draft #551, disjoint from existing file-upload replacement PR #759.

## Change
- LocalVoicePanel now invalidates all pending private voice, status, quality, revision, sentence retake and playback responses if the signed UI enablement changes, the voice/language/speed changes, the reviewed source changes, or a trusted callback is replaced/revoked.
- Disabled signed UI scope clears stale private audio/status/review state. It never silently retries an uncertain speech request.
- Extracted a deterministic pure scope comparison helper and added Node regression tests for role revocation, shop/campaign/plan/source changes, voice changes and callback identity replacement.
- No model inference, GPU, paid API, deployment, PROD, SQL, rights approval or WineShopPOS change. These tests use synthetic function identities, not real authenticated users or audio.

## Verification and blockers
- Targeted: `node --test tests/frontend/feature2-local-voice-scope.test.mjs`; component compilation: `node --test tests/frontend/feature2-voiceover-component.test.mjs`. CI execution/results must be inspected; this handoff does not claim passing tests.
- Parent PR #551 remains draft and coordinator-owned ISSUE-650 Azure package constraint is unresolved; do not merge with failing protected checks. Coordinator must review this source PR, integrate on main and verify fresh 4/4 CI before updating `coordination/task_progress.json`.
- **Dependency:** F2-CREATIVE-SOURCE (coordinator) — current accepted F2 Creative Studio signed mount and source contracts on main; acceptance: exact-head 4/4 and postmerge main 4/4.
- **Dependency:** F2-19 (coordinator + F2) — actual tenant JWT/RLS protected speech callback and durable job readback; acceptance: real DEV authenticated current editor and role revocation checks with two isolated shop owners, no secret exposure.
- **Dependency:** ISSUE-249 (Azure reliability lead) — signed DEV gateway 503 fix; acceptance: live protected speech/readback E2E without 503.
- A client-side fence is defense-in-depth only, never an authorization grant. Real hosted verification remains blocked.
