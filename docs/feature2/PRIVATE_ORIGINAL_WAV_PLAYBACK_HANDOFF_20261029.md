# Feature #2 — current tenant private original WAV playback boundary (2026-10-29)

**Status:** secure source adapter and synthetic WAV negative tests implemented. This does **not** mean Supabase DEV media registration, a deployed API, current licensed customer WAV access, or public publishing.

## Feature #2-owned source

Existing `ai-agents/src/ai_agents/feature2_local_voice_workflow.py::read_registered_private_original_wav` now requires trusted, server-implemented `authorize_current_editor`, `read_current_plan`, `read_registered_private_asset` and `read_private_blob` callbacks, plus exact current shop, campaign, creative plan and original WAV SHA.

The backend adapter verifies:

- Source plan is the existing reviewed Creative Director plan, and its original script SHA matches the private media registration.
- Original asset identity is a UUID registered with the **same** shop/campaign, exact plan SHA and immutable source WAV hash; provider is Kokoro, MIME is original WAV, `private:true`, no publish authorization, valid pending-rights state, no revocation and a trusted local inference evidence flag.
- Current OWNER/EDITOR authorization passes **before private blob access**, then again **after** original PCM16 WAV has been validated for strict headers, dimensions, duration and actual original SHA.
- The registered media metadata is re-read after the byte read and must be unchanged. A source rights revocation, changed shop, plan or file after read fails closed.

The trusted backend reader returns only authenticated **raw original WAV bytes to the current authorized editor**, as `retailgrowth.feature2-private-original-wav-read.v1`. The transport MUST use TLS, no-store/private response headers and same-origin signed JWT scope, **not a public bucket or independently reusable browser storage key**. The returned object is compatible with current `frontend/src/features/voiceover/voiceover-private-playback.mjs` that separately hashes bytes with browser crypto before creating an object URL, then revokes that object URL on source/tenant change.

It must **never** appear in the private stage trace, provider logs, job status, marketing export, support screenshots or public CDN. The receipt sets `can_publish:false`, `can_dispatch_motion:false`, `commercial_rights_not_certified:true` and `human_listen_required:true` explicitly.

## Coordinator-owned integration

1. Implement actual same-shop JWT/RLS and current OWNER/EDITOR checks **inside** the deployed Azure/Functions API, including after Blob reads. An untrusted request cannot provide server callbacks, private blob path, tenant grants or object store privileges.
2. Register original WAV media and its checksum in an immutable private media table/storage object with rights and revocation policy; enforce current commercial licensing and source retention. Do not equate sound produced by a model with licensed background music or a customer-provided microphone voice.
3. Call this adapter from the authenticated endpoint supplied to `VoiceoverSelector` as `onFetchLocalAudio`, returning the exact byte array and original SHA. Do not expose a long-lived SAS URL or shared storage object.
4. Test cross-tenant, revoked editor, revoked original media, changed SHA or duration, stale plan, wrong source mime and duplicate path; see offline `ai-agents/tests/test_feature2_local_voice_workflow.py`. Human audio review, commercial provenance and actual speech sound must be independently approved.
5. Coordinator still owns [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) for the protected ZIP package limit and exact-head 4/4 release tests.

This source adapter is **task #20 implementation in progress**, not real customer playback, signed URL issuance or complete hosted storage integration. No PROD, paid API, GPU, new database migration or WineShopPOS changes.
