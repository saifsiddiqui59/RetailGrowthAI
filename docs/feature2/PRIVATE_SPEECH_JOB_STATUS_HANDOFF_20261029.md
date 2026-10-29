# Feature #2 — authenticated private speech job-status readback (2026-10-29)

**Source-only contract. Not a deployed HTTP API or live Azure/Kokoro worker.**

## Feature #2-owned implementation

- `frontend/src/features/voiceover/voiceover-model.mjs::makePrivateVoiceJobStatusRequest`: read-only query with the **original** client-generated once-only UUID request key, exact current shop/campaign/approved creative plan SHA and explicit provider `kokoro-onnx`. Cannot create another job, spend money or retry.
- `voiceover-model.mjs::verifyPrivateVoiceJobStatus`: checks the signed-in shop's returned identity, source SHA, exact original request key, private provider and bounded status `RESERVED | RUNNING | AWAITING_HUMAN_REVIEW | FAILED | DENIED | BLOCKED`. All results require `private:true`, `can_publish:false`, `paid_api_calls:0`, `automatically_retried:false` and `azure_fallback_used:false`. Only `AWAITING_HUMAN_REVIEW` can carry registered original audio asset UUID + WAV SHA. This is UI validation of trusted backend data, **not cryptographic verification of JWT or database rights**.
- `frontend/src/features/voiceover/LocalVoicePanel.jsx`: stores the submitted request key before the call; on uncertain network/server failure it **does not** issue a new UUID. Generation buttons remain disabled until a protected status query completes, or until a different approved tenant/plan/script is selected. Shows the original request reference and one explicit status-check button, **no automatic polling or retries**. If a signed terminal `FAILED / DENIED / BLOCKED` receipt is returned, a **new deliberate user action** can create a fresh request. Completed audio remains pending human listening, original rights and F7 transcription.
- The coordinator mounts `VoiceoverSelector` with optional `onFetchPrivateLocalJobStatus`, which forwards to the existing `LocalVoicePanel`; it must be supplied only by a trusted authenticated/RLS-backed API.
- `tests/frontend/feature2-local-voiceover.test.mjs` covers all authorized states, invalid/replayed job keys, changed tenant/script, paid fallback, fabricated success or publication, unauthenticated/stale private WAV and review status escalation.

## Coordinator-owned integration requirements

1. Authenticate the **current** owner/editor JWT on each job lookup. Query a durable tenant-private job record indexed uniquely by `(shop_id,campaign_id,request_key)`; verify exact original plan, reservation digest, current RLS membership, worker lease and rights. A browser UUID by itself never authorizes access.
2. Return one status record with schema `retailgrowth.feature2-private-voice-job-status.v1`, current shop/campaign/plan SHA, request key, provider, state, `terminal`, the mandatory deny/rights flags and nullable original WAV SHA/asset UUID as described. Never expose private WAV bytes, signed URLs, raw transcripts, bearer/JWT, provider keys, media grants or service HMACs.
3. Enforce the same budget/idempotency/fencing transaction described in [CPU reservation handoff](LOCAL_CPU_RESERVATION_HANDOFF_20261029.md). A timeout/503 must not trigger re-synthesis or a different request key. A final server status is authoritative, and a client may only submit a new job after deliberate action. An unknown backend result remains **UNKNOWN** and blocked.
4. Connect actual signed status to the existing private object-store original WAV rights and F7 signed transcript endpoints. A terminal status never grants commercial rights.
5. Verify real two-tenant and revoked-editor negative cases in disposable DB and signed-in DEV browser. Do not claim hosted E2E before approved rollout and coordinator packaging [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) pass.

This is **task #19 source implementation**, with task #21 quota binding preparation. It does not modify coordinator-owned shared APIs, Supabase migrations, Azure resources, PROD or WineShopPOS.
