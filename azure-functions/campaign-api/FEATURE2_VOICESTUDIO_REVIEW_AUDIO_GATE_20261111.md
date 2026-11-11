# Feature2 private VoiceStudio original: current-retailer review gate (2026-11-11)

**Security-boundary source, staged for independent review; not deployed.**

The producer saves TWO private PCM WAV objects per one-shot original request: unpadded `original.wav` for a retailer to **listen and review**, and full-reel `render.wav` for the separately approved Feature4 video. Neither is a public link.

`VoiceStudioPrivateStorage.read_verified_original` was added in parent PR #936; this new `feature2_voicestudio_review_audio.read_current_voiceover_for_review` service method enforces the *existing* `SupabaseJWTVerifier` and `TenantStore.member(write=True)` before touching private bytes. It calls the four-RPC SQL client's authoritative `read_private_receipt` for the currently approved shop/campaign/original-key job. It requires `NEEDS_REVIEW`, source-private, rights-confirmed, no publish approval and a valid original SHA, then fetches only the `{shop}/voicestudio/{campaign}/{request}/original.wav` object from private Supabase Storage using server credentials, independently checks SHA again, then repeats current receipt and JWT/RLS membership after I/O. Any cross-shop, viewer, unknown receipt, revoked consent, mismatched digest, expired JWT or failed storage read denies without disclosing data or the secret.

This is **a service method, not an HTTP route**. A future independently reviewed root route must map denied/unauthenticated outcomes to sanitized HTTP statuses, apply `Cache-Control: no-store`, never log WAV/JWT/body, and choose stable content type `audio/wav`. It must NOT expose `render.wav` to a `NEEDS_REVIEW` human; Feature4 can consume it only after a different current `APPROVED_FOR_EDITING` source/tenant/rights check.

Current SQL RPC itself is still a REVIEW-ONLY proposal in PR #923, and the protected Feature2 source/route is staged in #920/#925. No live authenticated two-shop request, licensed model, human reviewer action or physical preview has occurred. Safe production integration requires independently reviewed SQL schema, actual verified DEV identities, human plan approval and licensed model. Any downstream HTML audio control must use only a short-lived *authenticated* same-shop response, not the Supabase service key, a public bucket or a permanent signed link.

No paid model, GPU, Azure/PROD mutation or WineShopPOS change.
