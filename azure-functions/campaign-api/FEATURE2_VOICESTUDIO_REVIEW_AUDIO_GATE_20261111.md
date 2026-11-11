# Feature2 private VoiceStudio original: current-retailer review gate (2026-11-11)

**Security-boundary source, staged for independent review; not deployed.**

The producer saves TWO private PCM WAV objects per one-shot original request: unpadded `original.wav` for a retailer to **listen and review**, and full-reel `render.wav` for the separately approved Feature4 video. Neither is a public link.

`VoiceStudioPrivateStorage.read_verified_original` was added in parent PR #936; this new `feature2_voicestudio_review_audio.read_current_voiceover_for_review` service method enforces the *existing* `SupabaseJWTVerifier` and `TenantStore.member(write=True)` before touching private bytes. It calls the four-RPC SQL client's authoritative `read_private_receipt` for the currently approved shop/campaign/original-key job. It requires `NEEDS_REVIEW`, source-private, rights-confirmed, no publish approval and a valid original SHA, then fetches only the `{shop}/voicestudio/{campaign}/{request}/original.wav` object from private Supabase Storage using server credentials, independently checks SHA again, then repeats current receipt and JWT/RLS membership after I/O. Any cross-shop, viewer, unknown receipt, revoked consent, mismatched digest, expired JWT or failed storage read denies without disclosing data or the secret.

This is **a service method, not an HTTP route**. A future independently reviewed root route must map denied/unauthenticated outcomes to sanitized HTTP statuses, apply `Cache-Control: no-store`, never log WAV/JWT/body, and choose stable content type `audio/wav`. It must NOT expose `render.wav` to a `NEEDS_REVIEW` human; Feature4 can consume it only after a different current `APPROVED_FOR_EDITING` source/tenant/rights check.

Current SQL RPC itself is still a REVIEW-ONLY proposal in PR #923, and the protected Feature2 source/route is staged in #920/#925. No live authenticated two-shop request, licensed model, human reviewer action or physical preview has occurred. Safe production integration requires independently reviewed SQL schema, actual verified DEV identities, human plan approval and licensed model. Any downstream HTML audio control must use only a short-lived *authenticated* same-shop response, not the Supabase service key, a public bucket or a permanent signed link.

No paid model, GPU, Azure/PROD mutation or WineShopPOS change.

## 2026-11-11 next code action — exact branch checkpoint
- Commit `99e87276195bf8d124ddf83c08f4d9ce84722ab9` repaired a critical escaped-newline source bug: `_wav(content)` had been part of a Python comment, so malformed digest-matching WAV payloads were not independently rejected. The validator now executes before post-read SQL/JWT/membership checks. Existing synthetic negative tests `test_digest_matching_non_wav_denied_even_with_swapped_storage_reader` and `test_digest_matching_wav_with_hidden_trailing_bytes_denied` exercise this behavior.
- NEXT CODE ACTION: run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py` on this exact branch; inspect the latest exact-head four-job Part 1 CI for the new commit and repair failures within F2-owned paths. Then verify #937 independent security review and reconcile latest main without bypassing protected #920/#923/#925. Do not merge until independently approved and exact-head 4/4, followed by fresh main 4/4.
- Local pytest and exact-head CI **not verified** at this checkpoint; no deployment or paid model execution.


## 2026-11-11 continuation checkpoint — JWT identity and approved-plan rotation
- Source test commit `563a2c39d914dc59bc54b3591a1fd03243eaee56`: two additional synthetic denial tests cover a JWT subject changing after private WAV read and an approved plan SHA changing between SQL receipt reads. Both must deny bytes before any downstream handoff.
- NEXT CODE ACTION: run `python -m pytest -q tests/ai/test_feature2_voicestudio_review_audio.py` at the **current** #937 head, repair any owned test failures, and inspect exact-head four-job Actions. Reconcile with latest main only after checking changed paths and concurrent workers. Independent review of #937 and protected #920/#923/#925 remains required; do not merge or deploy without it.
- Tests and exact-head CI for this new commit are not yet verified. No model inference or hosted resources were used.
