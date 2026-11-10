# Feature2 F2-19/F2-20 — VoiceStudio verified original-key private media registration

## Executed source scope (2026-11-11)
A real compositional worker *function* `run_verified_private_voice_job` now calls the existing:

1. `create_private_voiceover` (merged in PR #905): current reviewed script/editor, original-key SQL claim callback, upstream VoiceStudio API, SHA-proven 15/30/60s Feature4 WAV, post-provider script and membership rechecks;
2. `VoiceStudioPrivateStorage` (merged in PR #909): actual private Supabase Storage POST of two no-upsert WAV objects, then GET readback and SHA256 comparison of both objects;
3. trusted `register_verified_private_pair` callback **only after** byte-verified private readback, including exact shop/campaign/request/plan job and no-publish rights;
4. independent trusted `read_private_receipt` after registration to return only private `NEEDS_REVIEW` asset metadata. No public URL or rights/approval escalation.

`ai-agents/tests/test_feature2_voicestudio_registration.py` exercises the real two Python modules and an in-memory fake private Supabase HTTP backend in one deterministic path, including foreign shop, unapproved script, duplicate original ID, corrupted readback, partial second-object write, ambiguous SQL registration and approval revocation. No model downloaded, payment made or actual voice inferred. The API sender is fake; CI green is NOT hosted acceptance.

## Still not delivered
**Real SQL `claim_once` and `register_verified_private_pair` are injected *authoritative interfaces*, not implemented backed by Supabase here.** A SQL migration/privileged RPC must guarantee original-key dedupe and atomic job+asset CAS against CURRENT JWT/RLS membership/rights/lease. Source-only review of Feature2 parent #551/#848 SQL proposal is needed to reconcile its existing job/plan/asset tables; no unreviewed schema or HTTP deployment is authorized. Signed private playback, actual CPU model inference with a commercially licensed exact revision, and Feature4/7 consumer acceptance also remain unverified.

**Additional implementation in this PR:** `azure-functions/campaign-api/feature2_voicestudio_sql.py` now supplies a strict 4-RPC, service-only PostgREST client (`plan`, `claim`, `register`, `receipt`) with bounded JSON/origin checks and a verified signed actor supplied by the backend, never the browser. `tests/ai/test_feature2_voicestudio_sql.py` covers foreign claims, malicious responses, role/review states and private hashes. `ai-agents/tests/test_feature2_voicestudio_sql_registration_e2e.py` composes the REAL Python adapters end-to-end with synthetic SQL/Storage/VoiceStudio transports. **Next:** independently review the matching SQL schema proposed by PR #923, implement human-approved plan authoring and proper JWT entry route, deploy DEV only after review, then run signed two-shop tests. No SQL RPC is actually deployed by this PR. Do not retry uncertain provider/writer/job receipt. Retain default VoiceStudio model weights OFF: upstream OmniVoice is CC-BY-NC, upstream app AGPL-3.0, separate licensing clearance mandatory.

Owner task IDs F2-19 and F2-20 stay IN PROGRESS; no WineShopPOS, GPU, paid model, DEV/PROD deployment or protected review bypass.
