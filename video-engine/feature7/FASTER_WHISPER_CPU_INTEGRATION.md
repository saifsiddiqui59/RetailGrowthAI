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
