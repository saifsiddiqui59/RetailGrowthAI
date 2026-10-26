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
