# Feature 7 CPU-only development readiness — GPU remains OFF

This is a **source/development gate**, not a cloud GPU stop action, billed
resource inventory, a production release certificate, or authorization to
start an A100. No Azure or third-party GPU resource is started or stopped here.

## Source implemented without depending on Features 2/3/4/5

- `private_intake_cpu.mjs` stages a *trusted local worker input* under a
  private per-shop root with file-byte SHA256, MP4 `ftyp`, FFprobe H264/HEVC,
  audio/duration/size limits, no symlink traversal, no overwrite of existing
  assets and cleanup on invalid media. It calls an injected **current
  authenticated server intake authorization** callback. Only the
  coordinator can implement its real JWT/RLS/backend adapter. The emitted
  `PENDING_INDEPENDENT_REVIEW` / `NOT_REGISTERED_IN_SUPABASE` states are
  deliberate: staging a file is **not** customer rights or production
  registration. Do not expose its raw filesystem paths to a web browser.
- `cpu_readiness.mjs` rejects Feature7's GPU-enabled, remote-model and
  paid-inference switches, sets CPU/offline process settings and reports
  missing model/real hosted checks as **BLOCKED**. It explicitly sets
  `gpu_start_authorized:false` even when a local model directory exists.
  It does not disable GPU hardware or control billed Azure resources.
- Existing `offline_whisperx_cpu.mjs` can invoke a genuine locally
  provisioned WhisperX command only with preinstalled weights, aligner and
  licenses. Its CI process adapter uses a **fake executable**; the real
  speech-recognition model is **not installed, executed or benchmarked**.
  No model auto-download is allowed.
- `tests/media/test_feature7_private_intake.py` verifies real MP4/AAC
  staging, no-overwrite, no symlink, foreign/revoked/VIEWER/overquota and
  malformed media failure.
- `tests/media/test_feature7_cpu_readiness.py` verifies explicit GPU
  OFF / internet model disabled / paid inference rejected, and no false
  model-ready signal.
- `tests/media/test_feature7_cpu_e2e.py` performs a complete **offline
  fixture**: generate original H264/AAC video, private stage it as
  unapproved, separately *simulate* a reviewer-authorized rights registry
  and word-timed transcript, compute Feature7 review suggestions, adjust
  one source trim, explicitly confirm, persist an SQLite one-time approval
  claim, and generate exact Feature4 approved-edit envelope. The test DOES
  NOT execute Feature4's real renderer, a live signed-in user or actual
  speech recognition. Test-only fake membership or source rights must not
  be used in a deployed service.

## Run all Feature7 tests locally with GPU off

From the repo root with Node.js, Python 3, FFmpeg and ffprobe installed:

```bash
export FEATURE7_GPU_ENABLED=0
export FEATURE7_ALLOW_PAID_INFERENCE=0
export FEATURE7_NETWORK_MODELS=0
export FEATURE7_ENABLE_REMOTE_PROVIDER=0
node video-engine/feature7/cpu_readiness.mjs
python3 -m unittest discover -s tests/media -p 'test_feature7*.py' -v
```

Tests that download pinned public CC0 speech fixture do so only in GitHub
Actions or when explicitly enabled with `RETAIL_F7_CC0_WEB_TEST=1` and
delete it afterwards. CPU/readiness checks do not install model weights.

## Release gates, intentionally not marked complete

1. Current authenticated OWNER/EDITOR tenant MP4 registration/upload,
   per-shop quotas, actual private storage rights and signed playback.
2. Real approved WhisperX offline model + language/word quality benchmark;
   approved open-source software source alone does not prove model weight
   license suitability, or commercial customer's publicity consent.
3. Actual Feature4 editor mounting the reviewer, durable PostgreSQL
   human approval with optimistic revision/one-use outbox and latest
   media-rights rechecks (local SQLite is only a test journal).
4. Existing Feature4 renderer: final captions/owned B-roll/multi-cut audio
   preservation, final 1080x1920 download signed by the trusted backend.
5. Hosted DEV two-shop positive/foreign/revoked/expired checks using real
   signed-in users and approved retailer-owned footage.

The user explicitly requires **GPU OFF until Feature7 is ready**. Even
when these release gates pass, starting paid compute requires separate
explicit budget/authorization. Do not quietly enable GPU on green CI.

Canonical `docs/PROJECT_STATE.md`, `NEXT_TASK.md`, `DECISIONS.md` and
`WORK_LOG.md` are coordinator-owned per AGENTS.md. Feature7 logs in
`video-engine/feature7/HANDOFF.md` and PR #513 only until integration.
