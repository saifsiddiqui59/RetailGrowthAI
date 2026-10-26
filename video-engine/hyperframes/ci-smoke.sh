#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
PROJECT="$TEMP/diwali-composition"
OUTPUT="$ROOT/ci-artifacts/feature4-30s-hyperframes-synthetic.mp4"
mkdir -p "$ROOT/ci-artifacts"
python3 "$ROOT/video-engine/demo_feature4_diwali.py" "$PROJECT"
timeout --signal=TERM --kill-after=10s 180s npm install --prefix "$ROOT/video-engine/hyperframes" --no-audit --no-fund
if [ -x "$ROOT/video-engine/hyperframes/node_modules/.bin/puppeteer" ]; then
  timeout --signal=TERM --kill-after=10s 140s "$ROOT/video-engine/hyperframes/node_modules/.bin/puppeteer" browsers install chrome-headless-shell
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
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
# Capture resolved dependency lock for review; later pin it to repo and use npm ci.
cp "$ROOT/video-engine/hyperframes/package-lock.json" "$ROOT/ci-artifacts/feature4-review-package-lock.json"

# Acceptance-stage output contract: exercise real 1080x1920 frames, not just
# 540p upscaling or an HTML plan. The main 30-second mode is required.
# All materials are original synthetic fixtures, NEVER customer media.
PROJECT_HD="$TEMP/diwali-1080p"
OUTPUT_HD="$ROOT/ci-artifacts/feature4-30s-1080p-hyperframes-synthetic.mp4"
python3 "$ROOT/video-engine/demo_feature4_diwali.py" "$PROJECT_HD" --seconds 30 --width 1080
if (( NODE_MAJOR >= 22 )); then
  timeout --signal=TERM --kill-after=10s 420s node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT_HD" "$OUTPUT_HD"
else
  timeout --signal=TERM --kill-after=10s 420s npm exec --yes --package=node@22 -- node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT_HD" "$OUTPUT_HD"
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
python3 "$ROOT/video-engine/hyperframes/check_feature4_output.py" "$ROOT/ci-artifacts" --fullres

# Explicit full-minute qualification (full 1080p, CPU, no GPU/provider charges).
# Once the first source benchmark is recorded, keep this as an opt-in gate to
# avoid paying a 60s full-resolution encode on every unrelated branch change.
if [[ "${FEATURE4_FULL_MINUTE_CI:-1}" == "1" ]]; then
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
