# Feature #2 — Kokoro voice / Feature #7 source continuation (29 Oct 2026)

Scope: Feature2-owned source on `feat/feature2-unified-offline-source-20261028`,
draft PR #551. **NOT** a hosted deployment, genuine speech-generation success,
Feature4 approval or customer-facing launch. Coordinator owns canonical docs,
shared APIs, .github/workflows, the frontend route and main merge.

## Verified engineering changes in this continuation

- `feature2_voice_quality.py (signed-audio adapter)` is a *strict, fail-closed* consumer of
  Feature7's existing `feature7_signed_faster_whisper_asr_v1` HMAC envelope.
  It verifies the exact F7 MAC domain/canonical fields, 10-minute lifetime,
  30-second skew, original SHA-256, tenant, campaign/creative, private asset ID,
  word digest, source WAV duration and original word timings. It does **not**
  run recognition, sign an F7 response or infer missing probabilities.
- **Non-interchangeable contracts discovered:** PR #513's actual
  `video-engine/feature7/faster_whisper_cpu.mjs` takes approved MP4 with audio,
  signs the original **MP4** `source_sha256` and returns millisecond words.
  This does **not** verify a Kokoro-generated original private WAV. The new
  F2 consumer explicitly requires `source_media_kind='audio/wav'`,
  `campaign_id`, `creative_plan_sha256` and the exact original WAV
  SHA. Until Feature7 provides an **independent server-only WAV audio adapter**
  and signed evidence of that source, it will reject all existing video-only
  receipts. No MP4 hash or arbitrary `worker_verified:true` JSON counts as
  accepted narration speech.
- `feature2_local_voice_workflow.py` no longer promotes an injected
  `f7_transcript` before the original WAV is registered: stage one private
  asset first, then run and sign F7 recognition against that asset, then
  review separately, then request independent human approval. Job/tenant
  revocation checks and explicit paid-Azure opt-in remain unchanged.
- `feature2_voice_quality.py` bounds word end to independently proven WAV
  duration when provided; zero-duration words are invalid. Where Feature7
  supplies no token confidence, `null` remains unknown rather than a
  fabricated 0.8 or 1.0. ASR text differences remain *suspicions*, not
  proven phoneme mistakes. Original RMS, clipped fraction, longest quiet
  interval and WAV SHA analysis remain source-backed.
- `voiceover-private-playback.mjs` and existing
  `LocalVoicePanel.jsx`/`VoiceoverSelector.jsx` allow a **callback-driven**
  private original WAV preview. The reader is required to enforce real
  authenticated same-shop authorization; the browser additionally verifies
  exact shop/campaign/asset/original SHA-256 before creating a temporary local
  `blob:` audio URL, revoking old URLs on cleanup. It never receives Azure
  keys or makes private audio public. The live shared app/router remains
  unchanged and the component is still disabled until backend wiring.
- `run-real-kokoro-cpu.py` still invokes **real** upstream pinned
  Kokoro ONNX on approved cached original weights, not a sine wave. Real
  runs now record elapsed and process CPU time, Kokoro realtime factor,
  Linux maximum process RSS including model loads, worker concurrency=1,
  FFprobe WAV (and optional MP3), exact WAV/MP3 SHA and optional
  **operator-supplied** hourly-price estimate. These measurements **do not
  exist yet**; script fields are instrumentation, not measured results.
  Pricing excludes Azure/storage idle and licensing review. No hypothetical
  rate is inserted.

## Evidence, acceptance and constraints

- Current assistant container has Python 3.13 and FFmpeg/FFprobe, but **no**
  `kokoro_onnx`/ONNX Runtime and cannot resolve GitHub (DNS error on official
  asset HEAD and raw GitHub download). No original 114,119,327-byte ONNX /
  28,214,398-byte voices cache could be fetched here. The official
  hashes are in `ai-agents/oss/kokoro-onnx/pinned-sources.json`.
  No actual playable Kokoro narration, benchmark numbers, real human speech,
  before/after pronunciation audio, or phoneme verified comparison was made.
- Running normal CI verifies *fake or synthetic fixtures only*. The F7 HMAC
  tests deliberately create synthetic receipts, never model inference. The
  pre-existing Kokoro tests use a **sine test-double** labeled TEST_ONLY;
  synthetic audio is NOT presented as a TTS deliverable.
- Correct genuine run on an operator-approved offline CPU worker:
  `RETAIL_FEATURE2_KOKORO_CPU_ENABLED=true uv run --project ai-agents --with kokoro-onnx==0.6.1 --with soundfile python ai-agents/test-fixtures/retailer-voice/run-real-kokoro-cpu.py --run --model-dir /private/rgai-kokoro-models --output-dir /private/rgai-kokoro-demo --example diwali --voice af_heart --mp3`
  Optionally pass `--worker-hourly-usd` with the verified billed rate
  to estimate measured compute (not full service cost).
- **Never** upload privately generated customer audio or customer scripts to
  public GitHub artifacts or expose signed download URLs. Original model
  download is one-time operator provisioning, not per-user inference.
  Human-listen, rights and pronunciation review remain mandatory.
- Other blockers: Feature7 ASR CPU weights + signed *original-WAV* input,
  Feature7 word timings/independent confidence, approved offline OpenPronounce
  checkpoints, current signed F2 HTTP source/private WAV storage callbacks,
  production cache/usage/once-only token claims, authorized private browser
  endpoint, F1 route and F4 final rendering, Azure issue #249 ingress 503.
  Azure Speech is a **separately approved paid provider only**.
- Feature4 PR #322 must receive only a **private registered approved**
  narration asset and trusted signed metadata: shop/campaign, immutable
  source script SHA, original WAV SHA/duration, actual provider/voice/version,
  F7-sourced timing if available, quality issues, dictionary changes, human
  signoff and music-ducking recommendation. Feature4 alone owns final music
  mixing/captions/FFmpeg final export. An F2 source-only handoff is not
  permission to render/publish.
- No shared docs, routes, .github workflows, Supabase/hosted DEV, PROD, GPU,
  paid model calls, WineShopPOS or main branch changed.

## Next independent actions

1. Finish exact-head four-job CI on PR #551 and fix owned regressions.
2. Have Feature7 acknowledge original-WAV ASR input + signed versioned
   matching audio SHA/asset/campaign/creative/word timing (its existing
   MP4 handler MUST remain intact).
3. After an approved CPU runner has the official hash-verified weights,
   execute actual Kokoro and independently listen to the WAV. Repeat for
   approved corrected script and compare through genuine F7/phoneme review.
4. Coordinator wires signed tenant/job/private-audio HTTP callbacks,
   Feature1 route and Feature4 editor, then runs live DEV negative E2E
   with same-shop and foreign-shop users; do not assert completed before proof.

## Additional UI source-only review controls

- The existing local voice panel now offers an **editable proposed script** separately
  from the immutable approved source. Changes are submitted only to an injected
  signed editor-review callback as `NEEDS_REVIEW`, never directly used for
  synthesis or authorization. The source creative plan and signed script SHA
  remain authoritative until a distinct approved revision arrives.
- A shop pronunciation suggestion form similarly submits a proposed
  word/spoken-as pair for human editor review; it cannot auto-approve dictionary
  changes, regenerate in a loop or call Azure Speech. The UI remains disabled
  until current backend-authenticated callbacks are supplied and the coordinator
  mounts the existing selector into the actual customer route.

## Operator-only one-time pinned model acquisition

The repo now includes `ai-agents/test-fixtures/retailer-voice/provision-pinned-kokoro-models.sh` for a separately authorized Linux/WSL/CI CPU provisioning host with outbound GitHub access. Run with `bash .../provision-pinned-kokoro-models.sh /absolute/private/cache`. It uses the official `thewh1teagle/kokoro-onnx` release `model-files-v1.1`, checks **exact SHA-256 and byte length** for both original files, uses private 0600 storage, reuses already verified cache on subsequent executions, never overwrites a mismatching cached original, and does not start a network request in the actual customer TTS inference path. The provisioning script was **not executed successfully** in this environment (DNS inaccessible), and is not a proof of inference. After independent operator licensing/CPU wheel approval, invoke the existing real-Kokoro runner; never publish customer sample recordings as CI artifacts.
