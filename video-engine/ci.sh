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

# Feature4 real-stock review candidate, only on this branch's PR CI.
# Fail if real Pexels media cannot be fetched; never fall back to the
# OWNER_REJECTED illustrated synthetic Reel and mislabel it as a showcase.
# No workflow mutation, paid resource, GPU, tenant credentials or production use.
if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" && "${GITHUB_HEAD_REF:-}" == "feat/feature4-professional-video-studio" ]]; then
  STOCK_PROJECT="$TMP/feature4-stock-project"
  STOCK_PROOF="$ROOT/ci-artifacts/feature4-stock-provenance.json"
  STOCK_MP4="$ROOT/ci-artifacts/feature4-stock-real-footage-15s.mp4"
  python3 "$ROOT/video-engine/feature4_stock_showcase.py" --download \
    --project "$STOCK_PROJECT" --provenance "$STOCK_PROOF"
  # Existing verified Node 22 & HyperFrames engine; no new rendering engine.
  timeout --signal=TERM --kill-after=10s 400s \
    node "$ROOT/video-engine/hyperframes/render.mjs" "$STOCK_PROJECT" "$STOCK_MP4"
  python3 - "$STOCK_MP4" <<'PY'
import json,subprocess,sys
info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams",
  "-show_format","-of","json",sys.argv[1]],text=True))
v=[s for s in info["streams"] if s.get("codec_type")=="video"]
a=[s for s in info["streams"] if s.get("codec_type")=="audio"]
assert len(v)==len(a)==1 and v[0]["codec_name"]=="h264" and a[0]["codec_name"]=="aac"
assert (int(v[0]["width"]),int(v[0]["height"]))==(1080,1920)
assert abs(float(info["format"]["duration"])-15)<.3
print("PASS: real Pexels-stock 15-second Full-HD cinematic concept; NOT approved product")
PY
  # Owner-authorized Feature3 garment photo proxies + Feature5 motion stock.
  GARMENT_PROJECT="$TMP/feature4-garment-30s-project"
  GARMENT_PROOF="$ROOT/ci-artifacts/feature4-garment-30s-provenance.json"
  GARMENT_MP4="$ROOT/ci-artifacts/feature4-stock-garment-30s.mp4"
  python3 "$ROOT/video-engine/feature4_garment_integration.py" --download \
    --project "$GARMENT_PROJECT" --provenance "$GARMENT_PROOF"
  timeout --signal=TERM --kill-after=10s 500s \
    node "$ROOT/video-engine/hyperframes/render.mjs" "$GARMENT_PROJECT" "$GARMENT_MP4"
  python3 - "$GARMENT_MP4" "$GARMENT_PROOF" <<'PY'
import json,subprocess,sys
d=json.loads(subprocess.check_output(["ffprobe","-v","error",
    "-show_streams","-show_format","-of","json",sys.argv[1]],text=True))
v=[s for s in d["streams"] if s.get("codec_type")=="video"]
a=[s for s in d["streams"] if s.get("codec_type")=="audio"]
assert len(v)==len(a)==1 and v[0]["codec_name"]=="h264" and a[0]["codec_name"]=="aac"
assert (int(v[0]["width"]),int(v[0]["height"]))==(1080,1920)
assert abs(float(d["format"]["duration"])-30)<.4
proof=json.load(open(sys.argv[2]))
assert len(proof["source_media"])==5 and not proof["commercial_release_eligible"]
assert not proof["model_garment_match_verified"] and not proof["showcase_eligible"]
assert proof["music_beat_source"].startswith("Measured offline PCM")
assert len(proof["measured_beat_timestamps"]) > 20
assert all(any(abs(c-b)<.17 for b in proof["measured_beat_timestamps"])
    for c in proof["synced_scene_starts"][1:])
print("PASS: 30s actual Pexels garment + stock-person Reel, NOT garment identity or production acceptance")
PY
  # F4-50: real stock editorial scene-time sidecars in short-retention PR QA.
  # Explicitly NOT spoken transcription or Feature2-approved speech captions.
  python3 - "$ROOT/video-engine" "$GARMENT_PROOF" "$ROOT/ci-artifacts" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from feature4_subtitles import export_private_subtitle_pair
p=json.loads(Path(sys.argv[2]).read_text())
assert p["duration_seconds"]==30 and p["scene_count"]==7
assert not p["actual_spoken_voiceover"] and not p["commercial_release_eligible"]
starts=p["synced_scene_starts"]
titles=["A NEW SEASON","THE GARMENT EDIT","STYLE IN MOTION","TEXTURE AND DETAIL",
        "THE FASHION STORY","CURATED STYLE","STOCK GARMENT CONCEPT - NOT A RETAILER AD"]
assert len(starts)==len(titles) and len(set(starts))==len(starts)
cues=[]
for i,(start,title) in enumerate(zip(starts,titles)):
    end=starts[i+1] if i+1<len(starts) else 30
    # A short editorial title within its existing scene; no fake spoken cues.
    cue_start=round(start+.2,3)
    span=min(1.5,round(end-cue_start-.1,3))
    assert .2<=span<=6
    cues.append({"start":cue_start,"duration":span,"text":title})
root=Path(sys.argv[3])
proof=export_private_subtitle_pair(cues,duration_seconds=30,
    srt_path=root/"feature4-stock-30s-editorial-titles.srt",
    vtt_path=root/"feature4-stock-30s-editorial-titles.vtt")
proof["caption_kind"]="EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO"
proof["commercial_release_eligible"]=False
(root/"feature4-stock-30s-editorial-titles-proof.json").write_text(
    json.dumps(proof,indent=2)+"\n",encoding="utf-8")
print("PASS: 30s Pexels editorial title sidecars SRT/VTT exactly follow real scene cuts; NOT spoken")
PY

  # F4-53: reviewer sees 12 REAL decoded Pexels frames, not only HTML.
  python3 "$ROOT/video-engine/feature4_review_contact_sheet.py" \
    --source "$GARMENT_MP4" --duration 30 \
    --output "$ROOT/ci-artifacts/feature4-stock-garment-review-contact-sheet.jpg"
  # F4-47: actual decoded Pexels actor movement; reject frozen footage.
  python3 "$ROOT/video-engine/feature4_encoded_motion_qa.py" \
    --source "$GARMENT_MP4" --duration 30 --moving-starts 0 10 20 \
    --report "$ROOT/ci-artifacts/feature4-stock-garment-moving-pixels-proof.json"
  # F4-43: audio-only loudness mastering; H264 packet hash must not change.
  GARMENT_MASTER="$ROOT/ci-artifacts/feature4-stock-garment-30s-mastered.mp4"
  GARMENT_MASTER_PROOF="$ROOT/ci-artifacts/feature4-stock-garment-master-proof.json"
  python3 "$ROOT/video-engine/feature4_audio_master.py" \
    --source "$GARMENT_MP4" --duration 30 \
    --output "$GARMENT_MASTER" --report "$GARMENT_MASTER_PROOF"
  python3 - "$GARMENT_MASTER_PROOF" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
assert p["status"]=="PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"
assert p["mastered_audio_mean_db"] > p["source_audio_mean_db"] + 2
assert not p["commercial_release_eligible"] and not p["signed_download_ready"]
print("PASS: real stock 30s AAC audio mastered with H264 video packet hash unchanged")
PY
  # CPU-only compressed reviewer proxy from the same verified Full-HD MP4.
  # Artifact contains no retailer/user media, just explicitly labeled stock QA.
  python3 "$ROOT/video-engine/feature4_private_preview.py" \
    --source "$GARMENT_MASTER" --duration 30 \
    --output "$ROOT/ci-artifacts/feature4-stock-garment-30s-small.mp4" \
    --report "$ROOT/ci-artifacts/feature4-stock-garment-30s-small-proof.json"


  # F4-51: append independent cross-feature QA ledger only for actual
  # public-stock test footage; do not copy customer media into CI artifacts.
  python3 "$ROOT/video-engine/feature4_quality_receipt.py" \
    --original "$GARMENT_MP4" --master "$GARMENT_MASTER" \
    --preview "$ROOT/ci-artifacts/feature4-stock-garment-30s-small.mp4" \
    --provenance "$GARMENT_PROOF" \
    --motion-proof "$ROOT/ci-artifacts/feature4-stock-garment-moving-pixels-proof.json" \
    --master-proof "$GARMENT_MASTER_PROOF" \
    --preview-proof "$ROOT/ci-artifacts/feature4-stock-garment-30s-small-proof.json" \
    --editorial-proof "$ROOT/ci-artifacts/feature4-stock-30s-editorial-titles-proof.json" \
    --output "$ROOT/ci-artifacts/feature4-cross-feature-qa-receipt.json"

fi
