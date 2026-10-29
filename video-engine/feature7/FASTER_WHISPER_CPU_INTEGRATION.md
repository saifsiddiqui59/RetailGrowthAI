# Feature #7 — Real Faster-Whisper CPU speech-to-text

## Actual upstream implementation used

Source: https://github.com/SYSTRAN/faster-whisper (MIT).
Pinned PyPI package: faster-whisper==1.2.1, wheel SHA256:
79a66ad50688c0b794dd501dc340a736992a6342f7f95e5811be60b5224a26a7

Approved model *candidate*: Systran/faster-whisper-small, MIT model card,
multilingual, pinned revision 536b0662742c02347bc0e980a01041f333bce120.
https://huggingface.co/Systran/faster-whisper-small/tree/536b0662742c02347bc0e980a01041f333bce120

Actual faster_whisper_cpu.py imports the real upstream WhisperModel and
calls constructor with local absolute model dir, device="cpu",
compute_type="int8", cpu_threads=2, local_files_only=True. It then calls
transcribe(task="transcribe", word_timestamps=True, vad_filter=False,
condition_on_previous_text=False). The lazy output is consumed to execute
the model; no handcrafted STT neural network is used.

Installer for a *dedicated, separately provisioned offline CPU worker*
(operator-reviewed; NOT a CI dependency):

~~~sh
uv venv /opt/retailgrowth-asr-env
uv pip install --python /opt/retailgrowth-asr-env/bin/python "faster-whisper==1.2.1"
~~~

Obtain the pinned model on a permitted provisioning machine (not in customer
jobs), review licenses/dependencies, compute the real SHA256 of the downloaded
files and copy into a network-isolated CPU worker. Required operator manifest:

~~~json
{
  "version":"feature7_faster_whisper_model_manifest_v1",
  "model_project":"Systran/faster-whisper-small",
  "model_revision":"536b0662742c02347bc0e980a01041f333bce120",
  "commercial_rights_reviewed":true,
  "files":{
    "config.json":"REPLACE_WITH_VERIFIED_SHA256",
    "model.bin":"REPLACE_WITH_VERIFIED_SHA256",
    "tokenizer.json":"REPLACE_WITH_VERIFIED_SHA256"
  }
}
~~~

Never run with placeholder hashes or assume an operator boolean automatically
certifies licensing. The worker validates each actual local model file hash
both before and after inference. Missing weights, symlinks, corrupted files,
invalid/empty word timestamps or a disallowed locale fail closed. Model
downloads and remote inference are disabled inside worker jobs.

## Existing Feature #7 private-media trust boundary

faster_whisper_cpu.mjs calls this real Python driver only from trusted server:
- Current authenticated tenant membership/video rights (backend must supply).
- Existing exact private H.264/AAC MP4 hash/codec/tenant preflight.
- Original WAV extraction with actual FFmpeg, bounded size and timeout.
- Actual local CTranslate2 word-level decoding, with zero fabricated words.
- Source SHA256 reverified after long-running inference; temp speech deleted.
- Existing HMAC transcript evidence scoped to shop, asset, job and source hash.

Result version: feature7_signed_faster_whisper_asr_v1.
Output contains model revision, model.bin digest, language, actual word timings
and source-bound transcript digest. It always has approved:false and
renderable:false. HMAC is service evidence, NOT a human approval or customer
authentication.

Feature #2 owns Kokoro/Azure text-to-speech and may consume this shared STT
output for automated speech quality review. Feature #4 owns final rendering,
audio mixing, captions and user-facing publishing. No shared interface, auth
route, Supabase migration or Feature #2/#4-owned code was changed here.

## Acceptance and accuracy testing

faster_whisper_benchmark.py executes the real model on SHA-verified local WAV
and a separately provided human reference file, then computes Levenshtein WER,
including proper Hindi/Marathi combining-mark tokenization. A provisional
20% WER target is reported, but a single file does NOT certify Indian accents,
brand names, phoneme naturalness or word-timing quality.

The ordinary CI suite uses actual FFmpeg for MP4 checks, exercises the actual
upstream model API *adapter* with a TEST-ONLY fake model object, checks model
SHA and no-network policies, and confirms missing weights fail closed. Tests
DO NOT download or execute actual Faster-Whisper weights in regular CI.

**Real checkpoint inference and word-error benchmark are NOT YET VERIFIED.**
Need locally provisioned immutable commercially reviewed model weights and
multiple rights-cleared human reference recordings; verify real CPU RAM and
latency before live rollout. Also need coordinator JWT/RLS private upload,
signed playback, durable human review/outbox, Feature #4 renderer and hosted
DEV two-tenant end-to-end testing.

No GPU, paid inference, WineShopPOS, Azure DEV/PROD or password was touched.

## 2026-10-29 — Feature7 NON-GPU independent continuation, nine-track QA (source only)

- **Track 1 — Feature2 exact original WAV consumer**: added `tests/media/test_feature7_feature2_live_consumer_contract.py`, which imports the REAL `ai_agents.feature2_voice_quality.review_signed_audio_transcript` when coordinator integrates Feature2 #551. Until that source exists in the *same checkout*, it **skips rather than fabricating a consumer**. Existing F7 original-WAV signed HMAC/stored-job tests remain green from previous exact-head CI; hosted Postgres/UX wiring remains coordinator-owned.
- **Track 2 — original WAV parsing**: tightened `original_wav_cpu.mjs` to reject duplicate/extended fmt, audio before fmt, chunks after data, trailing RIFF garbage, unknown chunks, excessive ancillary chunks and malformed headers while preserving signed exact PCM16 identity. Added real Python-generated PCM WAV adversarial Node tests in `tests/media/test_feature7_offline_input_hardening.py`.
- **Track 3 — local job recovery**: existing `review_journal.py` and `review_dispatch_journal.py` already implement/test SQLite CAS, two independent connection claims, revoked approvals, timeout and retry/dead-letter fencing. Verified as *preexisting implemented source* rather than duplicating or calling hosted DB complete. Durable Postgres remains coordinator-owned.
- **Track 4 — transcript safety**: `transcript_adapter.mjs` rejects control and bidi formatting injection, malformed Unicode surrogates, and >80-codepoint words while allowing Devanagari combining characters and repeated speech words. New `test_feature7_offline_input_hardening.py` checks Hindi, punctuation, invalid word clocks, overlap and missing timestamps without pretending these words were actually ASR-generated.
- **Track 5 — Feature3 technical footage**: `test_feature7_feature3_actual_demo.py` only consumes the ACTUAL separate Feature3 Actions #40831572603 9s 1080x1920 technical MP4 when operator provides both pinned file and its independently checked SHA256. Otherwise **skip**; don't counterfeit a VTON garment or represent a synthetic avatar as a real shop owner. Feature3 source scripts are not on this older F7 draft branch, and real customer footage remains unavailable.
- **Track 6 — reviewer UX**: `reviewer_panel.mjs` blocks duplicate scene-approval and caption correction requests until editable inputs change or rejected Promise/callback is handled. `test_feature7_reviewer.py` / `test_feature7_caption_corrections.py` now assert one forward request, continued `approved:false`, and disabled one-shot controls rather than incorrectly expecting buttons remain enabled after submission. Live mounting stays Feature4-owned.
- **Track 7 — original media quality**: added `test_feature7_aac_caption_clock_quality.py`; it encodes ACTUAL local H264/AAC FFmpeg media, checks source-trim word-boundary timing, gap exclusions, and proves the original MP4 SHA256 unchanged. This is source/offline QA, not final F4 renderer acceptance; existing genuine CC0 voice caption tests preserved.
- **Track 8 — genuine CPU instrumentation**: `faster_whisper_cpu.py` records actual elapsed decode time, real-time factor and process peak RSS (when OS exposes resource), reporting **null** on Windows rather than inventing RAM. Added `cpu_stt_benchmark_report.py` + `test_feature7_cpu_stt_benchmark_report.py`; cost is computed only from explicit operator hourly price and measured CPU seconds; concurrency/quality/cost beyond inference are explicitly UNVERIFIED. No model weights installed during ordinary CI.
- **Track 9 — consolidated evidence**: all new tests are discoverable by existing `video-engine/ci.sh`; Feature7 HANDOFF/TASKS and CPU model guide updated. Shared docs/PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG remain coordinator-owned after merge, per `AGENTS.md`/PARALLEL_WORK. Branch PR #513 remains draft.

**Unresolved external tasks (no GPU strictly required):** actual license-reviewed model files/real CPU spoken-word inference, multi-speaker India-accent WER/word-timing and measured RAM; original uploaded customer footage/rights; Feature2 Kokoro real generated original WAV and source merge; coordinator Supabase JWT/RLS private upload and signed playback, durable Postgres approval/job/outbox; Feature4 mounted review UI, multi-cut/B-roll/captions/voice/music finished Reel; hosted DEV two-tenant end-to-end with genuine user approval. No GPU, paid provider, PROD, WineShopPOS changes. Do not claim the conditional source tests are executed in normal PR CI.

## 2026-10-29 — Verified-input SHA evidence and fully offline CPU checkpoint readiness (independent continuation)

- Verified Feature2 PR #551 remains draft at current `4fd35c77abefb0794d25f63ca35de68023a67937`, F7 PR #513 remains draft, and Feature3's actual public technical 9-second MP4 Actions artifact ID `12879355229` exists on run `40831572603` (this source was NOT fetched into the current CI checkout).
- Fixed concrete broken benchmark provenance: `cpu_stt_benchmark_report.py` required `verified_input_sha256` but `faster_whisper_cpu.py` never emitted it. The real model worker now hashes the actual staged original private WAV before inference, rehashes after inference and refuses source mutations; emits `verified_input_sha256` and existing measured actual CPU RSS/wall time. Both F7 video and original WAV subprocess adapters independently rehash/verify this audio SHA before accepting/signing a transcript. The original WAV adapter propagates verified hash and measured RSS; original MP4 source SHA remains separately bound by its existing signed original-media check.
- Security tests `test_feature7_faster_whisper_cpu.py` and `test_feature7_original_wav_cpu.py` assert real original WAV byte hash, source mutation during the model subprocess denied, and F2-compatible signed original WAV packet. These are API/protocol/anti-tamper tests with TEST-ONLY mock model; no pretrained model inference or speech WER was executed.
- `faster_whisper_preflight.py` is a no-network/no-inference operator check. It rejects missing local model/checkpoint SHA, wrong Faster-Whisper version (requires 1.2.1), missing CTranslate2, unsupported CPU `int8` or GPU/paid/network policy. Returns `model_weights_actual_inference_executed:false` and `human_reference_wer_passed:false`; does not claim independent commercial-license verification. `test_feature7_faster_whisper_preflight.py` uses explicitly fake weights to test rejection/contract only.
- `faster_whisper_inventory.py` inventories an ACTUAL operator-staged `Systran/faster-whisper-small` local model, writes SHA256 manifest to a new private 0600 file but deliberately sets `commercial_rights_reviewed:false`; separately audited model/dependency licensing, supplier rights and relevant legal approval are required before an operator may set it true. `test_feature7_faster_whisper_inventory.py` rejects unknown/empty/unexpected/symlinked files. The readiness test refuses all draft manifests as release ready. Neither script downloads weights.
- Runbook: provision approved local model and pinned `faster-whisper==1.2.1`/CTranslate2 CPU dependencies out-of-band on a no-egress worker. Use `python video-engine/feature7/faster_whisper_inventory.py --model-dir /private/models/faster-whisper-small --output-file /private/model-inventory.json` to generate **draft** SHA inventory. After *real* legal/checkpoint review and human-signed approval, operator prepares separate immutable approved manifest and executes `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' FEATURE7_GPU_ENABLED=0 FEATURE7_ALLOW_PAID_INFERENCE=0 FEATURE7_NETWORK_MODELS=0 python video-engine/feature7/faster_whisper_preflight.py --model-dir /private/models/faster-whisper-small --model-manifest /private/approved-manifest.json`. Do not post model weights, customer audio, manifest grants or private URLs to PR logs. Only then use actual `faster_whisper_benchmark.py` with SHA-bound, independently human-transcribed speech; no human WER or model CPU RAM measurement has yet been made.
- The F3 test `tests/media/test_feature7_feature3_actual_demo.py` still conditionally skips until the real Actions artifact is securely staged. The F2 exact Python consumer conditional test still requires a coordinator combined source checkout and is skipped on this standalone feature PR. Live Supabase rights/job callbacks and Feature4 render are external owners.
- No change to WineShopPOS, no paid/GPU inference, no PROD/DEV deployment, no global CI workflow/shared `docs/**` edits. Re-verify exact head 4/4 CI and media-test logs before reporting passed. PR #513 remains draft for coordinator.
