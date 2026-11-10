# Feature #2 — F7 signed original-WAV WER + manual comparison handoff (2026-10-29)

**State:** Implemented source-only deterministic word-error-rate calculation and signed-review guard. Neither real Faster-Whisper WAV inference nor human listening has taken place.

## What is implemented

Existing `ai-agents/src/ai_agents/feature2_voice_quality.py` now exposes `compare_signed_feature7_word_error_rate`. It first invokes existing `review_signed_audio_transcript`, which verifies Feature #7's original-WAV HMAC evidence (matching shop, campaign, plan, current audio SHA, job, model revision, bounded word timestamps and a trusted authoritative source callback). It does not accept a browser transcript, a public video/media URL or client-supplied `worker_verified=true` as signed proof.

The new scorer uses bounded 600×600 dynamic-programming **word-level Levenshtein** edit distance, rather than the approximate `SequenceMatcher` mismatch groups used for human review hints. It records substitutions, deletions, insertions, total edits, reference word count and WER = edits/reference words. WER **can be more than 1.0** if a hypothesis inserts extra words. Indic/Devanagari grapheme tokenization is preserved by the existing `_words` helper, but language-specific pronunciation is not validated by text WER.

The optional `human_transcript` is rejected without `verify_signed_human_transcript(shop,campaign,asset,plan,wav_sha,job,utf8_human_sha)`. The trusted backend must attest the independent human's current review of the *same original audio*, verify present-day role and signed fact/version, and recheck before returning results. Human transcripts are never copied to a frontend log; only aggregate word-error counts, identity hashes and a boolean attestation indicator are exposed.

## Interpreting result

`retailgrowth.feature2-verified-word-error-review.v1` includes:

- `feature7_asr_word_error`: reference script vs signed F7 transcript WER
- `human_transcript_vs_script_error`: reference script vs independently attested human transcript WER, or **null** if none
- `feature7_asr_vs_human_error`: signed F7 vs human transcript WER, or **null** if none
- `real_worker_execution_independently_observed: false`, `pronunciation_verified: false`, `can_publish: false`: no quality, acoustic, commercial or actual-model attestation inferred from source-only tests

The source test `ai-agents/tests/test_feature2_feature7_signed_audio.py` uses **synthetic HMAC data**. It covers missing/substituted/inserted words, Marathi/Hindi graphemes, changed WAV digest, expired/forged F7 receipts, unauthenticated human evidence, role revocation and unauthorized source. Those tests validate contract/security/metrics only.

## Still required to finish fixed task #17

1. Coordinate with F7 owner [PR #513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513): deploy real pinned CPU Faster-Whisper, ingest a *registered private original WAV* and check actual signed original F7 receipt, not fake decoder fixture output.
2. Implement the authenticated source/current-editor and **independent human transcript review** callbacks using coordinator-reviewed RLS, immutable receipts and job/source lease fencing; do not store raw scripts/transcripts in client trace logs.
3. Have humans listen to actual original audio and compare WER with a recorded independent transcript, including manually checked Indian retail brand words. A low WER does not prove pronunciation/accent success; the original private audio and licensed source must be reapproved.
4. Keep publication/media selection/retakes blocked until Feature4/editor accepts rights, fresh transcription and explicit approval.
5. Re-run full 4-job merged-head CI; coordinator issue [#650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) (protected Functions ZIP size) remains a separate integration blocker.

This does not alter shared coordinator interfaces, WineShopPOS, PROD, provider secrets, or model deployments.
