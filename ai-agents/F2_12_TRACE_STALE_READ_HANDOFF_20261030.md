# Feature #2 / F2-12 — private trace UI stale-read fence

Status: **IN PROGRESS**, source-only, not integrated DONE.

## Verified code scope
- `Feature2TracePanel.jsx` now invalidates any pending private trace read when shop, campaign, workflow, source SHA, enabled state, reader callback, or a newer read changes. Stale responses **and stale failures/finally blocks** cannot erase a newer result or reset its busy state.
- `voiceover-trace-request-gate.mjs` is a deterministic local concurrency helper, not a server authorization/HMAC validator. `feature2-private-trace-request-gate.test.mjs` checks cross-tenant/source/disable invalidation, overlapping reads and explicit reader cancellation.
- No hosted private trace API, genuine AI inference, customer media, paid service, GPU, PROD, WineShopPOS or main merge is claimed.

## Verification and coordinator action
- Targeted: `cd frontend && node --test ../tests/frontend/feature2-private-trace-request-gate.test.mjs ../tests/frontend/feature2-private-trace.test.mjs`.
- Production JSX compile: `cd frontend && node scripts/feature2-voiceover-compile.mjs`.
- Exact-head four-job CI and coordinator review required; do not claim green before observed.
- Stacked branch `feat/f2-12-trace-stale-request-fence-20261030` targets Feature2 draft branch PR #551. Coordinator integrates only after reviewed CI, then records F2-12 evidence in the central task manager and canonical docs.
- Remaining dependency: coordinator must provide a real tenant-private persisted trace writer/read API with HMAC verified on the server and signed JWT/RLS, then acceptance tests with two genuinely provisioned isolated DEV accounts. Existing test users are NOT_CREATED, and offline fixtures are not live evidence.
