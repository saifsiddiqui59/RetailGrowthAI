#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CAMPAIGN="$ROOT/frontend/src/features/campaigns/fixtures/sample-campaign.json"
python3 -m unittest discover -s "$ROOT/tests/media" -p 'test_*.py' -v
python3 "$ROOT/video-engine/generate_test_assets.py" --campaign "$CAMPAIGN" --out-dir "$TMP/assets"
python3 "$ROOT/video-engine/render.py" \
  --campaign "$TMP/assets/campaign-with-ci-audio.json" \
  --manifest "$TMP/assets/manifest.json" --asset-root "$TMP/assets" \
  --day-index 1 --output "$TMP/reel.mp4" --width 1080 --height 1920 \
  --fps 15 --preset ultrafast --offer-text "20% off selected styles" \
  --allow-test-media
python3 "$ROOT/video-engine/probe.py" "$TMP/reel.mp4" --width 1080 --height 1920
python3 "$ROOT/tests/media/check_content.py" "$TMP/reel.mp4"
mkdir -p "$ROOT/ci-artifacts"
cp "$TMP/reel.mp4" "$ROOT/ci-artifacts/workstream-c-30s-reel.mp4"
# A second full-resolution offline render records CPU/RSS on the actual CI runner.
# 15fps/ultrafast is a fast smoke profile, NOT production's 24fps/veryfast.
python3 "$ROOT/ops/benchmarks/render_benchmark.py" \
  --width 1080 --height 1920 --fps 15 --preset ultrafast \
  --report "$ROOT/ci-artifacts/workstream-n-render-benchmark.json"
echo "PASS: 30s 1080x1920 H.264/AAC multi-image Reel, xfade, generated tone, overlays, rights"

# Feature #4 gates a real deterministic CPU producer run, not only HTML compilation.
# No tenant credentials or new cloud resources are required.
bash "$ROOT/video-engine/hyperframes/ci-smoke.sh"
