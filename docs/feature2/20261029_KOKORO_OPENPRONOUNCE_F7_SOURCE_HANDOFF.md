# Feature2 original GitHub speech-code reuse and integration handoff — 29 Oct 2026

**Real upstream imports, no fake audio assertion.** Branch `feat/feature2-unified-offline-source-20261028`, draft PR #551. Source-only independent work completed: actual MIT `thewh1teagle/kokoro-onnx` API `Kokoro.create` as **default free CPU generator**, actual MIT `Halleck45/OpenPronounce` API `compare_audio_with_text` as optional lazy phoneme reviewer. Repo checked immutable upstream source commits and MIT LICENSEs; original unchanged Kokoro `examples/save.py` and OpenPronounce `__init__.py` included as traceable upstream references. These are actual upstream libraries, not an assistant-recreated neural inference engine. Pinned code/weights and original source attribution: `ai-agents/oss/kokoro-onnx/` and `ai-agents/oss/OpenPronounce/`.

## Implemented independent source

- `feature2_kokoro_local.py`: imports upstream `kokoro_onnx.Kokoro`, validates **actual original** pinned `model-files-v1.1` ONNX INT8 114119327 bytes SHA256 `ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c`, voice pack 28214398 bytes SHA256 `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`; does CPU-only 24kHz PCM16 local inference into original SHA-proven WAV; validates real samples and bounds concurrent sessions; no network-per-request downloads. If weights/library unavailable, **fails closed**.
- `feature2_voice_quality.py`: original WAV duration, clipping, RMS, >12s silence evidence; consumes only versioned Feature7 Faster-Whisper word timestamps, same tenant/creative plan/original audio SHA, no fake missing time; differentiates STT mismatch from OpenPronounce phoneme concerns; optional `run_openpronounce_lazy` invokes real OpenPronounce only when offline gTTS-free reference/checkpoint preloaded (English heuristic with false positives). **Feature7 owns actual Faster-Whisper implementation; F2 imports versioned output only**.
- `feature2_pronunciation_dictionary.py`: same-shop editor-reviewed correction spelling with atomic revision callback; no client-forged approval or inference-confidence claims; one bounded local revised source (not original approved text overwrite).
- `feature2_local_voice_workflow.py`: tenant current signed owner/editor, immutable source twice, once-only local job claim, original private audio registration, non-publishable `retailgrowth.feature2-to-feature4-original-voice.v1` payload and honest F7/review flags, **no automatic Azure fallback**.
- Existing Feature2 `VoiceoverSelector.jsx` now shows **Free local Kokoro first**, original UK/US English actual voice IDs, and **Azure Speech explicitly premium** (en-IN, hi-IN, mr-IN where regional speech service is available). It is still **NOT mounted on the live dashboard or backed by a real signed production route**.
- Existing Azure Speech adapter remains pay-authorized, server-only and OFF until approved, with exact pricing/cost ledger; F4 alone mixes narration/music, lip sync/caption alignment and renders real private Reel.

## Working *real* CPU demonstration execution command (requires actual original bytes)

On a controlled offline worker with Python 3.13, ffmpeg/ffprobe, 1–2 GB free RAM or more (actual peak NOT measured), and `kokoro-onnx==0.6.1` installed from isolated `ai-agents/oss/kokoro-onnx/requirements-optional.txt` (plus NumPy/ONNX runtime transitive deps), first use original GitHub release `model-files-v1.1` to download the exact two pinned files **once** into an operator-owned, read-only private cache; do not download in request path. `verify_cache` checks the source SHA256 and size before executing:

```bash
uv run --project ai-agents --with kokoro-onnx==0.6.1 --with soundfile \
  python ai-agents/test-fixtures/retailer-voice/run-real-kokoro-cpu.py --plan
# After operator has obtained SHA-verified model weights (not supplied by CI):
RETAIL_FEATURE2_KOKORO_CPU_ENABLED=true \
uv run --project ai-agents --with kokoro-onnx==0.6.1 --with soundfile \
  python ai-agents/test-fixtures/retailer-voice/run-real-kokoro-cpu.py --run \
  --model-dir /private/rgai-kokoro-models --output-dir /private/rgai-kokoro-demo \
  --example diwali --voice af_heart --mp3
```

A successful **real** run (not yet obtained here) writes original speech `kokoro-cpu-original.wav`, optional MP3, original SHA receipt, CPU inference time and FFprobe codec proof. Supported fictional tests: Diwali boutique, fashion boutique, weekend restaurant. Audio quality, ASR transcript accuracy, peak RSS/CPU concurrency, phoneme correctness, Hindi support and live storage remain **UNVERIFIED** until actual bytes/checkpoints/Feature7 and authorized readers are provided. Current assistant runtime cannot download the 114 MB ONNX/28 MB voice weights or install ONNX runtime (container DNS disabled); therefore **NO authentic Kokoro-generated sample WAV or before/after acoustic evidence is claimed**. All tests only verify integration logic or synthetic WAV byte handling.

## Licensing / practical limits

- Kokoro ONNX inference MIT, upstream revision `3596b26764286a7de9d90c363e988d50578918e5`. Kokoro-82M weights on HF `hexgrad/Kokoro-82M` Apache-2.0. ONNX release's GitHub REST authoritative SHA256 digest pinned from original release assets. Do not assume voice styles/phonemizer GPL dependency notices or downloaded audio sampling rights are cleared for SaaS without separate operator review. This v1 English model only supports en-us/en-gb as used here, not hi-IN/mr-IN or Indian English native. English pronunciation of Indian proper names requires review.
- OpenPronounce `0.3.0` MIT revision `74bc17ea406e6f057f15eea0e70951e1931af868`; Wav2Vec2 language/phone models are **independent checkpoints**, large, need model rights and origin audits; gTTS default would call network, **blocked**. Score is a heuristic; not commercial certification. No model weights downloaded or human-rated comparison done.
- Faster-Whisper `SYSTRAN/faster-whisper` is Feature7-owned, not duplicated; coordinator and Feature7 must agree exact output before relying on consumer proposal `retailgrowth.feature7-stt-words.v1`.
- Azure Speech premium fallback requires explicitly approved TTS and cost receipt, no silent invocation if local fails.
- Produced original model bytes remain private to renderer worker, not passed to UI/log, with a tenant-bound immutable SHA and rights review before F4 audio mixing.

## Still pending / other-team dependencies

Actual 114 MB+28 MB original model files plus optional CPU runtime installation and real audio proof; phoneme model checkpoints and license/CPU memory benchmark; actual STT model inference in F7 and word-timestamp signing; local correction trial on **real spoken** wrong word and human listening; signed F2 HTTP routes, Supabase private audio/SHA registration, billing/voice cache, reviewer approval and browser preview; F4 final real video mixing; Azure issue #249 503. Repo main/production hosting is not changed; only coordinator merges draft #551, updates canonical docs and cross-feature contracts. No WineShopPOS, cloud or paid calls.

## One sentence pronunciation retake source now available

`feature2_sentence_retake.local_sentence_retake` uses immutable original F2 script sentence boundaries (<=13), the same original voice/lang/speed, an active same-shop editor, approved per-shop dictionary entries, exact source plan, initial audio SHA, a **durable once-only sentence retake reservation** and verified original private new WAV before returning a non-publishable `retailgrowth.feature2-sentence-retake.v1` reference. The output explicitly requires a **fresh Feature7 transcript and manual re-listening**. Feature4 must assemble the retake into the final sentence/scene track, preserve original timing, and re-check private lease/rights. There is **no unbounded retry loop or automatic Azure fallback**; any source rejection keeps the original unreleased. The spelling-only example `kurti`→`kur-tee` is **not proven** to sound better without actual Kokoro WAV, F7 and human approval. Tests: `test_feature2_sentence_retake.py` (mock-only).
