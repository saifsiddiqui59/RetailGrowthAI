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

**Next coding action:** Add an opt-in server-only PostgREST adapter that binds the original-key RPC and read/registration receipts (with zero browser keys), and tests two-shop denial and lost ACK. Then review its SQL proposal and deploy DEV only with permission. Do not retry uncertain provider/writer/job receipt. Retain default VoiceStudio model weights OFF: upstream OmniVoice is CC-BY-NC, upstream app AGPL-3.0, separate licensing clearance mandatory.

Owner task IDs F2-19 and F2-20 stay IN PROGRESS; no WineShopPOS, GPU, paid model, DEV/PROD deployment or protected review bypass.
