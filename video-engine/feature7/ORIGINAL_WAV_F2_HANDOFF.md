# Feature7 → Feature2 original-WAV transcription handoff (29 Oct 2026)

**Draft producer PR:** [#513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513).
**Consumer PR:** [Feature2 #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551).
This is a Feature7-owned source implementation, **not** a deployed shared API or proof of real model weights.

## Gap closed in source

Feature2's `ai-agents/src/ai_agents/feature2_voice_quality.py::review_signed_audio_transcript` explicitly rejects a Feature7 MP4 transcript for synthesized voice-over. It requires original `audio/wav`, exact WAV SHA256, shop/campaign/plan/asset/job fields, original duration, the unchanged `feature7_asr_evidence_v1` HMAC format, exact normalized word digest, real local CPU decoder claims and a separately **trusted** current source/job read twice. Feature2 `feature2_local_voice_workflow.review_registered_kokoro_audio` requires an authoritative *persisted* F7 job with `origin='trusted_feature7_original_audio_worker'` and `revoked_at=null`.

The new `video-engine/feature7/original_wav_cpu.mjs` exports:

- `inspectOriginalPrivatePCM16Wav({root,relative_path,expected_sha256})`: parse original RIFF/WAVE mono PCM16, 16–48 kHz, 0.2–65 seconds, at most 20 MB; verify original SHA and size, prohibit symlinks/path traversal. Actual bytes are inspected rather than invented metadata. This returns the private original WAV data **only to the trusted worker**.
- `transcribeFeature2OriginalWavCPU(...)`: requires server-held HMAC secret, externally verified CURRENT tenant/editor/job rights and revision through `read_current_audio`; all registered original-WAV SHA/duration/creative/lease fields must match; stages the exact WAV privately; uses **existing genuine Faster-Whisper upstream CPU inference** `faster_whisper_cpu.py` (preinstalled model weights, offline CPU INT8); checks exact word timestamps and actual source hash again; re-reads rights/revision and persists an immutable job using trusted `save_verified_job`. Without real checkpoint or confirmed persistence it returns no receipt.
- `feature7_signed_faster_whisper_asr_v1` **additive original-WAV shape**: `source_media_kind:'audio/wav'`, `shop_id`, `campaign_id`, `creative_plan_sha256`, `asset_id`, `job_id`, `source_sha256`, `original_media_sha256`, `source_duration_seconds`, `model_id:'faster_whisper_small_cpu_int8'`, real `model_revision`, `model_bin_sha256`, `transcription_status:'real_local_cpu_decoder_output'`, source-bound `transcript_sha256`, `words:[{word,startMs,endMs}]`, `evidence` HMAC, `local_cpu_inference_invoked:true`, `no_remote_model_calls:true`, `approved:false`, `renderable:false`, `customer_publishable:false`. Confidence is **absent** because no true calibrated probability was established.
- Persisted job record for Feature2 consumption includes `job_id`, `shop_id`, `campaign_id`, `audio_asset_id`, `source_media_kind:'audio/wav'`, `original_audio_sha256`, `origin:'trusted_feature7_original_audio_worker'`, `revoked_at:null` and exact original `receipt`.

The old MP4 `faster_whisper_cpu.mjs` and `feature7_asr_evidence_v1` remain unchanged. **No shared contract, F2 code, Supabase RPC, JS root package, or Feature4 renderer is changed by this worker.** The trusted callbacks are backend-only; do NOT export as browser calls or trust an `issued_by` field as real auth.

## Tests and limitations

`tests/media/test_feature7_original_wav_cpu.py` uses real PCM16 WAV bytes, tests SHA/RIFF/mono/frames, private source and double current-rights check, HMAC compatibility with the exact Feature2 Python canonical payload and signed transcript words, denial for revoked/foreign/expired-job/stale creative/duplicate or changed source, symlink/path traversal, invalid audio/provider and failed persistence. Successful test run uses **clearly marked TEST-ONLY fake CLI output** to assert the **protocol** and makes no claim that a model actually recognized speech. Production always executes the upstream-model Python driver path.

Still genuinely blocked: authorized operator provisioning of exact MIT candidate `Systran/faster-whisper-small` local model weights + model-file SHA manifest, pinned Faster-Whisper dependencies; real CPU/WER benchmark on independently transcribed and rights-released human/Indian-accent speech, word-timing listening acceptance, hosted authenticated audio registration and durable PostgreSQL job/outbox implementation, two-tenant DEV acceptance, Feature4 final renderer and approved audio. No model download, GPU, paid inference, cloud deployment, public original WAV or WineShopPOS modification.

Feature2 should consume the persisted original-WAV F7 result after independently re-reading its own original audio and trusted F7 job; it must not treat worker signature or review status as human approval.
