#!/usr/bin/env bash
# Feature4 separate CPU full-minute validation. Never a publishing/marketing route.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /absolute/new-private-output-directory" >&2; exit 2
fi
OUTPUT="$1"
if [[ -z "$OUTPUT" || "$OUTPUT" != /* || -e "$OUTPUT" || -L "$OUTPUT" ]]; then
  echo "Usage: $0 /absolute/new-private-output-directory" >&2; exit 2
fi
case "$OUTPUT" in
  /|/tmp|/mnt|/home|/root|/var|/etc|/dev|/proc|/sys)
    echo "Unsafe system directory" >&2; exit 2;;
esac
mkdir -m 700 -- "$OUTPUT"
WORK="$(mktemp -d)"
trap 'rm -rf -- "$WORK"' EXIT
PROJECT="$WORK/garment-minute"
PROOF="$OUTPUT/feature4-stock-60s-provenance.json"
VIDEO="$OUTPUT/feature4-stock-garment-60s.mp4"
MASTER="$OUTPUT/feature4-stock-garment-60s-mastered.mp4"
SMALL="$OUTPUT/feature4-stock-garment-60s-small.mp4"
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
node -e 'if(Number(process.versions.node.split(".")[0])<22) process.exit(2)'
python3 "$ROOT/video-engine/feature4_garment_integration.py" --download \
  --seconds 60 --project "$PROJECT" --provenance "$PROOF"
timeout --signal=TERM --kill-after=12s 750s \
  node "$ROOT/video-engine/hyperframes/render.mjs" "$PROJECT" "$VIDEO"
python3 - "$VIDEO" "$PROOF" <<'PY'
import json,subprocess,sys
from pathlib import Path
info=json.loads(subprocess.check_output(["ffprobe","-v","error",
  "-show_streams","-show_format","-of","json",sys.argv[1]],text=True))
v=[s for s in info["streams"] if s.get("codec_type")=="video"]
a=[s for s in info["streams"] if s.get("codec_type")=="audio"]
p=json.loads(Path(sys.argv[2]).read_text())
assert len(v)==len(a)==1 and v[0]["codec_name"]=="h264" and a[0]["codec_name"]=="aac"
assert (int(v[0]["width"]),int(v[0]["height"]))==(1080,1920)
assert abs(float(info["format"]["duration"])-60)<.35
assert p["duration_seconds"]==60 and p["scene_count"]==12
assert p["reused_stock_video_clips"] and not p["commercial_release_eligible"]
assert not p["model_garment_match_verified"]
print("PASS: real stock 60-second Full-HD render, not approved retailer identity")
PY
python3 "$ROOT/video-engine/feature4_encoded_motion_qa.py" \
  --source "$VIDEO" --duration 60 --moving-starts 0 10 20 30 40 \
  --report "$OUTPUT/feature4-60s-motion-qa.json"
python3 "$ROOT/video-engine/feature4_audio_master.py" \
  --source "$VIDEO" --duration 60 --output "$MASTER" \
  --report "$OUTPUT/feature4-60s-audio-proof.json"
python3 "$ROOT/video-engine/feature4_private_preview.py" \
  --source "$MASTER" --duration 60 --output "$SMALL" \
  --report "$OUTPUT/feature4-60s-preview-proof.json"

# Encode the actual beat-aligned editorial QA titles onto a NEW 540p
# reviewer MP4. These are not transcribed/approved human speech.
python3 - "$ROOT/video-engine" "$PROOF" "$SMALL" "$OUTPUT" <<'PY'
import json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from feature4_subtitles import export_private_subtitle_pair
from feature4_subtitle_burnin import burn_reviewed_subtitles
record=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if (record.get("editorial_subtitle_kind")!="EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO"
        or record.get("duration_seconds")!=60
        or record.get("actual_spoken_voiceover") is not False):
    raise ValueError("Refuse to invent spoken-subtitle approval for stock demo")
out=Path(sys.argv[4])
cues=record["editorial_subtitle_cues"]
srt=out/"feature4-stock-minute-editorial.srt"
vtt=out/"feature4-stock-minute-editorial.vtt"
export_private_subtitle_pair(cues,duration_seconds=60,srt_path=srt,vtt_path=vtt)
proof=burn_reviewed_subtitles(Path(sys.argv[3]),srt,
                             out/"feature4-stock-minute-captioned-review.mp4",
                             cues=cues,expected_seconds=60)
report=out/"feature4-stock-minute-captioned-proof.json"
fd=os.open(report,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,"w",encoding="utf-8") as file:
    json.dump(proof,file,indent=2)
    file.write("\n")
print("PASS: actual FFmpeg subtitle burn-in",proof["cue_count"],
      "beat-snapped editorial cue intervals; NOT speech alignment")
PY

# Decode actual frames from the native 60s MP4 and retain repeated-shot warning.
python3 - "$ROOT/video-engine" "$VIDEO" "$OUTPUT" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from feature4_review_contact_sheet import render_contact_sheet
output=Path(sys.argv[3])
proof=render_contact_sheet(Path(sys.argv[2]),
                           output/"feature4-60s-review-contact-sheet.jpg", seconds=60)
(output/"feature4-60s-contact-sheet-qa.json").write_text(
    json.dumps(proof,indent=2)+"\n",encoding="utf-8")
print("Review contact-sheet frame count:",proof["frame_count"],
      "repetition-warning:",proof["repetition_warning"])
PY
python3 "$ROOT/video-engine/feature4_minute_quality_receipt.py" \
  --original "$VIDEO" --master "$MASTER" --preview "$SMALL" \
  --provenance "$PROOF" --motion "$OUTPUT/feature4-60s-motion-qa.json" \
  --master-proof "$OUTPUT/feature4-60s-audio-proof.json" \
  --preview-proof "$OUTPUT/feature4-60s-preview-proof.json" \
  --contact-image "$OUTPUT/feature4-60s-review-contact-sheet.jpg" \
  --contact-proof "$OUTPUT/feature4-60s-contact-sheet-qa.json" \
  --captioned "$OUTPUT/feature4-stock-minute-captioned-review.mp4" \
  --caption-srt "$OUTPUT/feature4-stock-minute-editorial.srt" \
  --caption-vtt "$OUTPUT/feature4-stock-minute-editorial.vtt" \
  --caption-proof "$OUTPUT/feature4-stock-minute-captioned-proof.json" \
  --output "$OUTPUT/feature4-60s-cross-feature-qa-receipt.json"
echo "PASS 60s stock editor technical source/render/preview only; no customer/owner approval"
