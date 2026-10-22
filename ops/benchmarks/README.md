# Workstream N — offline portrait render performance and risk gate

Run from the repository root on Linux with **local** `ffmpeg` and `ffprobe`
(including libx264, AAC, xfade and drawtext):

```bash
python3 ops/benchmarks/render_benchmark.py \
  --width 1080 --height 1920 --fps 24 --preset veryfast \
  --memory-limit-mib 2048 --report /tmp/retailgrowth-1080x1920.json
```

All inputs are locally generated original color cards and an original 440 Hz test
tone. No downloaded media, user files, cloud access, external APIs, proprietary
music or third-party copyright attestations are required or tested. Temporary
video is deleted after its probe result is read. The command invokes the same
`video-engine/render.py` used by the worker, so it includes media preflight,
FFmpeg encoding, MP4 stream probing and file finalization.

## Measurements and interpretation

- JSON contains FFmpeg/ffprobe version, executable SHA-256 and ELF x86_64
  identification, exposed codec/filter support, legal-review flags, source
  environment, preset, frame rate, encoded bytes, wall seconds, sampled peak
  **process-tree** RSS and sampled CPU seconds. Linux `/proc` reads every
  150 ms are **lower-bound estimates**, not enforceable memory caps. Dynamic
  dependencies are **not** assessed as safe-to-package by this script.
- The benchmark's synthetic asset generation time is **excluded** from render
  timing and reported separately. Cloud queue delay, image upload/download,
  Supabase/API calls, license review, cold starts, retries, output signing
  and network egress are not simulated. A pass is a **local/CI-only** signal,
  never an Azure Flex measurement or a production licensed-media test.
- Enforced configuration: host 1,200 seconds, DB lease 1,500 seconds,
  FFmpeg subprocess cap 780 seconds, 420 seconds reserved for all other worker
  phases and a 300-second lease margin after the host timeout. The code
  accepts a sampled memory limit only when explicitly supplied. Values must
  be revised together with Coordinator 3 if the deployment policy changes.
- GitHub CI runs an additional *1080x1920, 15 fps ultrafast* smoke
  profile to limit hosted runner minutes. This profile is **not** the
  production/default 24 fps veryfast profile above; do not extrapolate
  timings from one preset, host CPU or file type to another.
- An offline budget pass does **not** establish the worker's full 20-minute
  execution path or 25-minute lease behavior. Record a deployment approval
  blocker until same-profile on-Azure Flex CPU/memory/scratch and private
  media I/O are measured with separate owner approval.

## Illustrative compute cost sensitivity (not live Azure prices)

Supply **both** customer-verified rates and requested resource allocation:

```bash
python3 ops/benchmarks/render_benchmark.py --fps 15 --preset ultrafast \
  --allocated-vcpus 2 --allocated-memory-gib 2 \
  --vcpu-rate 0.00001 --memory-rate 0.000001 --renders 1000 \
  --report /tmp/retailgrowth-cost-sensitivity.json
```

Those example numbers are *arbitrary inputs solely to demonstrate the math*,
**not Azure rates or a quote**. The estimate is
`elapsed_seconds × (vCPUs × USD_per_vCPU_second + GiB × USD_per_GiB_second)`
times requested render count. Obtain current provider region/plan rates and
minimum billing conditions before decision; storage, queue, egress, AI, retries,
memory billing details, cold starts and orchestration overhead are excluded.

## Executable licensing and legal safety

- SHA256 and executable version are traceability data, **not proof of origin**.
  `--enable-nonfree` builds fail closed; `--enable-gpl` builds require
  separate GPL compliance review, and even LGPL builds need compliance,
  dependency and notice review. `libx264`/H.264 patent distribution
  conditions and font licenses must also be assessed.
- GitHub-hosted runner FFmpeg is **not** an approved redistributable
  Azure Linux x86_64 static binary; `scripts/deploy/check.sh` independently
  audits Azure packaging. Confirm static binary linking, platform/ABI,
  executable bits, notices, permitted distribution and legal signoff for
  the specific **packaged** SHA before approval. Neither this workstream
  nor its offline measurements authorize production video use.
- `video-engine/asset_preflight.py` enforces 25 MiB images, 50 MiB audio,
  image magic + decoder codec, ≤8,192 px/side, ≤24 MP, audio stream type/
  channels/rate/duration and a 15s ffprobe limit. It is defense in depth,
  not malware scanning, licensing verification or a substitute for the
  tenant-bound server-staged path/rights checks in `render.py`.

**Handoff:** Coordinator 3 owns shared docs, Azure runtime settings, FFmpeg
bundling and deployment decisions. Workstream N must not modify them or
claim performance measured on unprovisioned Azure.
