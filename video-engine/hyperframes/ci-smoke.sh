#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
PROJECT="$TEMP/diwali-composition"
OUTPUT="$ROOT/ci-artifacts/feature4-30s-hyperframes-synthetic.mp4"
mkdir -p "$ROOT/ci-artifacts"
python3 "$ROOT/video-engine/demo_feature4_diwali.py" "$PROJECT"
# Validate the exact committed v3 dependency lock BEFORE npm executes any
# installation scripts. No network-driven package resolution or lock rewrites.
python3 "$ROOT/video-engine/hyperframes/lock_guard.py" --lock "$ROOT/video-engine/hyperframes/package-lock.json" --report "$ROOT/ci-artifacts/feature4-npm-dependency-audit.json"
timeout --signal=TERM --kill-after=10s 180s npm ci --prefix "$ROOT/video-engine/hyperframes" --no-audit --no-fund
if [ -x "$ROOT/video-engine/hyperframes/node_modules/.bin/puppeteer" ]; then
  timeout --signal=TERM --kill-after=10s 140s "$ROOT/video-engine/hyperframes/node_modules/.bin/puppeteer" browsers install chrome-headless-shell
fi
# Run offline package/browser readiness checks before the full CPU render.
# The older-node npm-exec fallback is unqualified and remains a DEV blocker.
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if (( NODE_MAJOR >= 22 )); then
  python3 "$ROOT/video-engine/hyperframes/qualify_runtime.py" --report "$ROOT/ci-artifacts/feature4-runtime-preflight.json"
else
  echo "Feature4 source runtime preflight deferred: runner Node <22, fallback npm exec used" >&2
fi
if (( NODE_MAJOR >= 22 )); then
  timeout --signal=TERM --kill-after=10s 480s node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT" "$OUTPUT"
else
  timeout --signal=TERM --kill-after=10s 480s npm exec --yes --package=node@22 -- node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT" "$OUTPUT"
fi
python3 - "$OUTPUT" <<'PY'
import json,subprocess,sys
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',sys.argv[1]],text=True))
v=[s for s in info['streams'] if s.get('codec_type')=='video']
a=[s for s in info['streams'] if s.get('codec_type')=='audio']
assert len(v)==1 and v[0]['codec_name']=='h264'
assert (v[0]['width'],v[0]['height'])==(540,960)
assert len(a)==1 and a[0]['codec_name']=='aac'
assert abs(float(info['format']['duration'])-30)<.25
print('PASS: actual HyperFrames 30s synthetic Diwali MP4 H264/AAC')
PY
for sec in 1 6 13 18 24 28; do
 ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$sec" -i "$OUTPUT" -frames:v 1 "$ROOT/ci-artifacts/feature4-frame-$sec.jpg"
done

# Quantify scene diversity and prove original 480Hz fixture-track remains in AAC mix.
python3 "$ROOT/video-engine/hyperframes/check_feature4_output.py" "$ROOT/ci-artifacts"
# Preserve the exact committed SHA-pinned lock in the CI evidence artifact.
cp "$ROOT/video-engine/hyperframes/package-lock.json" "$ROOT/ci-artifacts/feature4-review-package-lock.json"

# Acceptance-stage output contract: exercise real 1080x1920 frames, not just
# 540p upscaling or an HTML plan. The main 30-second mode is required.
# All materials are original synthetic fixtures, NEVER customer media.
PROJECT_HD="$TEMP/diwali-1080p"
OUTPUT_HD="$ROOT/ci-artifacts/feature4-30s-1080p-hyperframes-synthetic.mp4"
# Exercise actual AAC narration track in the high-resolution render instead
# of merely verifying the source HTML (synthetic 863Hz tone, NOT a human voice).
python3 "$ROOT/video-engine/demo_feature4_diwali.py" "$PROJECT_HD" --seconds 30 --width 1080 --with-narration
if (( NODE_MAJOR >= 22 )); then
  timeout --signal=TERM --kill-after=10s 440s python3 "$ROOT/video-engine/hyperframes/benchmark_render.py" "$PROJECT_HD" "$OUTPUT_HD" "$ROOT/ci-artifacts/feature4-1080p-cpu-benchmark.json" --timeout 420
else
  timeout --signal=TERM --kill-after=10s 440s python3 "$ROOT/video-engine/hyperframes/benchmark_render.py" "$PROJECT_HD" "$OUTPUT_HD" "$ROOT/ci-artifacts/feature4-1080p-cpu-benchmark.json" --timeout 420 --use-npm-node22
fi
python3 - "$OUTPUT_HD" <<'PY'
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path("video-engine").resolve()))
from render_adapter import verify_mp4
proof=verify_mp4(sys.argv[1],duration=30,width=1080,height=1920,fps=24)
info=json.loads(subprocess.check_output(
    ["ffprobe","-v","error","-show_streams","-of","json",sys.argv[1]],text=True))
v=next(s for s in info["streams"] if s.get("codec_type")=="video")
assert v.get("pix_fmt")=="yuv420p", v.get("pix_fmt")
assert int(v.get("nb_frames",720)) in range(718,723),v.get("nb_frames")
print("PASS: actual 1080x1920/24fps/30s HyperFrames encode",proof)
PY
for sec in 1 6 13 18 28; do
 ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$sec" -i "$OUTPUT_HD" -frames:v 1 "$ROOT/ci-artifacts/feature4-fullres-frame-$sec.jpg"
done
# Check a synthetic caption is VISIBLY burned into the encoded 1080p MP4.
# All three frames are within the same 0..3s intro shot to avoid a fake pass
# from unrelated scene cuts. No speech/text semantic quality is claimed.
for t in 0.6 1.2 2.2; do
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$t" -i "$OUTPUT_HD" -frames:v 1 "$ROOT/ci-artifacts/feature4-caption-frame-$t.png"
done
python3 "$ROOT/video-engine/hyperframes/check_feature4_output.py" "$ROOT/ci-artifacts" --fullres

# Explicit full-minute qualification (full 1080p, CPU, no GPU/provider charges).
# TRUE editable-timeline export parity: run upstream Timeline Studio JS commands,
# authorize the resulting 30s draft in trusted Python, stage only original
# mock media, then render an actual second MP4 with the same HyperFrames engine.
# Lower-res 540x960 avoids a second costly Full-HD encoding. No GPU/AI call.
EDITED_PROJECT="$TEMP/edited-30s-composition"
EDITED_MP4="$ROOT/ci-artifacts/feature4-30s-540p-actual-editor-mock.mp4"
python3 "$ROOT/video-engine/demo_feature4_edited_reel.py" "$EDITED_PROJECT" --width 540
if [[ "$NODE_MAJOR" -ge 22 ]]; then
  timeout --signal=TERM --kill-after=10s 420s node "$ROOT/video-engine/hyperframes/render.mjs" "$EDITED_PROJECT" "$EDITED_MP4"
else
  timeout --signal=TERM --kill-after=10s 420s npm exec --yes --package=node@22 -- node "$ROOT/video-engine/hyperframes/render.mjs" "$EDITED_PROJECT" "$EDITED_MP4"
fi
python3 - "$ROOT/video-engine" "$EDITED_MP4" <<'PY'
import sys
sys.path.insert(0,sys.argv[1])
from render_adapter import verify_mp4
proof=verify_mp4(sys.argv[2],duration=30,width=540,height=960,fps=24)
print("PASS: actual edited JS->trusted Python->HyperFrames MP4",proof)
PY
for sec in 2 15 26; do
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$sec" -i "$EDITED_MP4" -frames:v 1 "$ROOT/ci-artifacts/feature4-editor-frame-$sec.jpg"
done
# F4-MVP-30: verify ACTUAL encoded editor scene order/trim replay and SHA,
# not just the 30s H264/AAC container. Original synthetic media only.
python3 "$ROOT/video-engine/feature4_edited_export_qa.py" \
  --source "$EDITED_MP4" \
  --report "$ROOT/ci-artifacts/feature4-30s-editor-encoded-parity.json"

# F4-04: duplicate is a DIFFERENT real editor action from split/reorder.
# Reuse the same approved mock-only fixture and actual HyperFrames engine,
# physically encode a second 30s 540p video and prove two 5s video scenes
# restart the same source in-point. Never release synthetic footage to users.
DUPLICATE_PROJECT="$TEMP/duplicate-30s-composition"
DUPLICATE_MP4="$ROOT/ci-artifacts/feature4-30s-540p-actual-duplicate-mock.mp4"
python3 "$ROOT/video-engine/demo_feature4_edited_reel.py" \
  "$DUPLICATE_PROJECT" --width 540 --operation duplicate
if (( NODE_MAJOR >= 22 )); then
  timeout --signal=TERM --kill-after=10s 420s node \
    "$ROOT/video-engine/hyperframes/render.mjs" "$DUPLICATE_PROJECT" "$DUPLICATE_MP4"
else
  timeout --signal=TERM --kill-after=10s 420s npm exec --yes \
    --package=node@22 -- node "$ROOT/video-engine/hyperframes/render.mjs" \
    "$DUPLICATE_PROJECT" "$DUPLICATE_MP4"
fi
python3 "$ROOT/video-engine/feature4_edited_export_qa.py" \
  --source "$DUPLICATE_MP4" --operation duplicate \
  --report "$ROOT/ci-artifacts/feature4-30s-duplicate-encoded-parity.json"

# Once the first source benchmark is recorded, keep this as an opt-in gate to
# avoid paying a 60s full-resolution encode on every unrelated branch change.
if [[ "${FEATURE4_FULL_MINUTE_CI:-0}" == "1" ]]; then
  PROJECT_60="$TEMP/diwali-60s-1080p"
  OUTPUT_60="$ROOT/ci-artifacts/feature4-60s-1080p-hyperframes-synthetic.mp4"
  python3 "$ROOT/video-engine/demo_feature4_diwali.py" "$PROJECT_60" --seconds 60 --width 1080
  if (( NODE_MAJOR >= 22 )); then
    timeout --signal=TERM --kill-after=10s 480s node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT_60" "$OUTPUT_60"
  else
    timeout --signal=TERM --kill-after=10s 480s npm exec --yes --package=node@22 -- node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT_60" "$OUTPUT_60"
  fi
  python3 - "$OUTPUT_60" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path("video-engine").resolve()))
from render_adapter import verify_mp4
proof=verify_mp4(sys.argv[1],duration=60,width=1080,height=1920,fps=24)
print("PASS: real 60s/1080p/24fps HyperFrames full-minute H264/AAC",proof)
PY
  for sec in 1 9 18 29 42 55; do
    ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$sec" -i "$OUTPUT_60" -frames:v 1 "$ROOT/ci-artifacts/feature4-minute-frame-$sec.jpg"
  done
fi
