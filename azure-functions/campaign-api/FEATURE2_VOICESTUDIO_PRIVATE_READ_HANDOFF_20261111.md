# Feature2 VoiceStudio private WAV read contract (2026-11-11)

This Feature2-owned change adds **real, bounded, SHA256-verified private WAV byte readers** to the existing server-side Supabase Storage adapter at `azure-functions/campaign-api/feature2_voicestudio_storage.py`.

- `read_verified_original(shop_id,campaign_id,request_id,sha)`: exact original VoiceStudio PCM, for a **separately authenticated human reviewer** only.
- `read_verified_render(shop_id,campaign_id,request_id,sha)`: exact padded Feature4 PCM, for the independently authorized Feature4 renderer only.
- Both derive immutable object paths solely from canonical v4 shop/campaign/request IDs, fetch from existing private `retailgrowth-media` bucket with backend-only API key, reject redirects/status changes, cap binary bytes to 8MiB, require valid PCM WAV and compare actual SHA against current trusted SQL evidence. No signed/public URLs or credentials are returned to callers. Existing `verify_pair` now uses the same read code but returns only verified byte counts.

**No public endpoint is created.** These are server-only byte transport primitives and **do not** perform user authentication, editor membership, review authorization or rights grants. They must only be called *after and before* an independent current user/JWT/RLS rights and SQL original-key receipt check. The new synthetic tests prove correct object selection, no path injection, fail-closed readback, bounded profile and no automatic retry.

Integration next: server-only authenticated `NEEDS_REVIEW` audio preview with current editor membership and original-key receipt; Feature4 current `APPROVED_FOR_EDITING` rights check before calling render reader; then true audio/video, reviewed captions and two-shop DEV E2E after an approved commercial model. Root HTTP registration and SQL schema still require independent security review in PRs #920/#923/#925.

Source-only, model OFF, no GPU/paid provider, hosted DEV/PROD or WineShopPOS change. F2-19/F2-20 not fully accepted.
