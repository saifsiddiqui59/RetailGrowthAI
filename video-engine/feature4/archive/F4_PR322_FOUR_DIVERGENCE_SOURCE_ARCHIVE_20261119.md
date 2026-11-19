# Feature4 historical parent #322 current-main reconciliation (2026-11-19)

- Original draft: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322
- Original pinned head: `b9525a9ea3d5e5aee351edf89a3c011c2314ed2e`
- Compared against `main` commit/tree `36ae62c9e300aa22170aa1c97b088af4603155bc`
- **184/188 original changed-file Git blob SHAs are EXACTLY identical to current main**.
- **4/188 differ** intentionally; all original per-file GitHub patch hunks for those four are preserved below verbatim. Original unchanged 184 files need no archive because their content is already in main and Git history.
- This preserves code provenance only. **DO NOT claim F4-01–F4-31 commercially complete, publishable, signed DEV verified, licensed source media, visual QA, 24/30fps consumer release or tenant-rights acceptance** from parent retirement.
- Current-main safety takes precedence: never wholesale merge stale conflicted #322 to overwrite modern narration-duration checks or replace deterministic CI with Pexels network downloads. Continue verified gaps in new small current-main F4 PRs with current approvals.

## Four differing original files and newer-main rationale

- `tests/media/test_asset_preflight.py` — original blob `d879d6b44169d60b55f8df0d6cfc3b3b9285838b`; current-main blob `d8cee50d275dcf272f8286c0ae5f20d0c8b4812f`. Old test demanded duration in shared music preflight; latest main deliberately moved approved narration-duration enforcement into professional.py with separate ffprobe check.
- `video-engine/asset_preflight.py` — original blob `aa23885d9b7aa1dff0347592070a5cb2f5a21e9c`; current-main blob `399397ff8a8ff64a0d2f1ae3e481404209fa103b`. Old generic audio preflight required duration; current version leaves unknown duration to the stricter professional narration check and returns only codec/rate/size metadata.
- `video-engine/ci.sh` — original blob `9d7c48c6e1598554ecf90eea75d326ab3f7a134f`; current-main blob `1f02f6fa93596d702421b29f7e84126c7ae04878`. Original branch included PR-only remote Pexels media downloads and long showcase/third-party asset checks; latest main retains deterministic offline CI and separately reviewed manual extended F4 CPU workflow (#977). Never restore unlicensed or network-heavy PR CI wholesale.
- `video-engine/professional.py` — original blob `048869948ee3544ac2b30261c1aef57a68d15310`; current-main blob `5ff1a0c7b29479c3d166afa0f51375e8a4d0181e`. Latest main adds checked_narration_duration ffprobe guard to reject uncertain or unbounded staged narration, rather than relying on historic shared preflight duration field.

## Exact four original GitHub PR file patches

### tests/media/test_asset_preflight.py

~~~~diff
@@ -73,6 +73,16 @@ def test_unparseable_audio_duration_denied(self):
             with self.assertRaisesRegex(AssetPreflightError, "Invalid audio"):
                 inspect_staged_audio(audio)
 
+    def test_missing_audio_duration_denied_before_render(self):
+        audio = self.root / "unknown.wav"
+        audio.write_bytes(b"placeholder")
+        with patch("asset_preflight._probe", return_value={"streams": [
+            {"codec_type": "audio", "codec_name": "pcm_s16le",
+             "sample_rate": "44100", "channels": 2}
+        ], "format": {}}):
+            with self.assertRaisesRegex(AssetPreflightError, "length limit"):
+                inspect_staged_audio(audio)
+
     def test_probe_timeout_fail_closed(self):
         image = self.root / "image.png"
         image.write_bytes(b"\x89PNG\r\n\x1a\n")
~~~~

### video-engine/asset_preflight.py

~~~~diff
@@ -95,9 +95,9 @@ def inspect_staged_audio(path):
         raise AssetPreflightError("Invalid audio stream metadata") from exc
     if not 0 < rate <= 192000 or not 0 < channels <= 8:
         raise AssetPreflightError("Audio channel/sample-rate limit failed")
-    if duration is not None and (not math.isfinite(duration) or not 0 < duration <= 3600):
+    if duration is None or not math.isfinite(duration) or not 0 < duration <= 3600:
         raise AssetPreflightError("Music length limit failed")
-    return {"bytes": size, "sample_rate": rate, "channels": channels}
+    return {"bytes": size, "sample_rate": rate, "channels": channels, "duration_seconds": duration}
 
 
 def preflight_assets(images, music):
~~~~

### video-engine/ci.sh

~~~~diff
@@ -22,3 +22,137 @@ python3 "$ROOT/ops/benchmarks/render_benchmark.py" \
   --width 1080 --height 1920 --fps 15 --preset ultrafast \
   --report "$ROOT/ci-artifacts/workstream-n-render-benchmark.json"
 echo "PASS: 30s 1080x1920 H.264/AAC multi-image Reel, xfade, generated tone, overlays, rights"
+
+# Feature #4 gates a real deterministic CPU producer run, not only HTML compilation.
+# No tenant credentials or new cloud resources are required.
+bash "$ROOT/video-engine/hyperframes/ci-smoke.sh"
+# Exercise actual approved synthetic WAV + music + timed captions through the
+# existing F4 compiler and HyperFrames CPU encoder (no TTS, GPU or cloud).
+python3 "$ROOT/tests/media/feature4_voicestudio_cpu_render.py"
+
+# Feature4 real-stock review candidate, only on this branch's PR CI.
+# Fail if real Pexels media cannot be fetched; never fall back to the
+# OWNER_REJECTED illustrated synthetic Reel and mislabel it as a showcase.
+# No workflow mutation, paid resource, GPU, tenant credentials or production use.
+if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" && "${GITHUB_HEAD_REF:-}" == "feat/feature4-professional-video-studio" ]]; then
+  STOCK_PROJECT="$TMP/feature4-stock-project"
+  STOCK_PROOF="$ROOT/ci-artifacts/feature4-stock-provenance.json"
+  STOCK_MP4="$ROOT/ci-artifacts/feature4-stock-real-footage-15s.mp4"
+  python3 "$ROOT/video-engine/feature4_stock_showcase.py" --download \
+    --project "$STOCK_PROJECT" --provenance "$STOCK_PROOF"
+  # Existing verified Node 22 & HyperFrames engine; no new rendering engine.
+  timeout --signal=TERM --kill-after=10s 400s \
+    node "$ROOT/video-engine/hyperframes/render.mjs" "$STOCK_PROJECT" "$STOCK_MP4"
+  python3 - "$STOCK_MP4" <<'PY'
+import json,subprocess,sys
+info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams",
+  "-show_format","-of","json",sys.argv[1]],text=True))
+v=[s for s in info["streams"] if s.get("codec_type")=="video"]
+a=[s for s in info["streams"] if s.get("codec_type")=="audio"]
+assert len(v)==len(a)==1 and v[0]["codec_name"]=="h264" and a[0]["codec_name"]=="aac"
+assert (int(v[0]["width"]),int(v[0]["height"]))==(1080,1920)
+assert abs(float(info["format"]["duration"])-15)<.3
+print("PASS: real Pexels-stock 15-second Full-HD cinematic concept; NOT approved product")
+PY
+  # Owner-authorized Feature3 garment photo proxies + Feature5 motion stock.
+  GARMENT_PROJECT="$TMP/feature4-garment-30s-project"
+  GARMENT_PROOF="$ROOT/ci-artifacts/feature4-garment-30s-provenance.json"
+  GARMENT_MP4="$ROOT/ci-artifacts/feature4-stock-garment-30s.mp4"
+  python3 "$ROOT/video-engine/feature4_garment_integration.py" --download \
+    --project "$GARMENT_PROJECT" --provenance "$GARMENT_PROOF"
+  timeout --signal=TERM --kill-after=10s 500s \
+    node "$ROOT/video-engine/hyperframes/render.mjs" "$GARMENT_PROJECT" "$GARMENT_MP4"
+  python3 - "$GARMENT_MP4" "$GARMENT_PROOF" <<'PY'
+import json,subprocess,sys
+d=json.loads(subprocess.check_output(["ffprobe","-v","error",
+    "-show_streams","-show_format","-of","json",sys.argv[1]],text=True))
+v=[s for s in d["streams"] if s.get("codec_type")=="video"]
+a=[s for s in d["streams"] if s.get("codec_type")=="audio"]
+assert len(v)==len(a)==1 and v[0]["codec_name"]=="h264" and a[0]["codec_name"]=="aac"
+assert (int(v[0]["width"]),int(v[0]["height"]))==(1080,1920)
+assert abs(float(d["format"]["duration"])-30)<.4
+proof=json.load(open(sys.argv[2]))
+assert len(proof["source_media"])==5 and not proof["commercial_release_eligible"]
+assert not proof["model_garment_match_verified"] and not proof["showcase_eligible"]
+assert proof["music_beat_source"].startswith("Measured offline PCM")
+assert len(proof["measured_beat_timestamps"]) > 20
+assert all(any(abs(c-b)<.17 for b in proof["measured_beat_timestamps"])
+    for c in proof["synced_scene_starts"][1:])
+print("PASS: 30s actual Pexels garment + stock-person Reel, NOT garment identity or production acceptance")
+PY
+  # F4-50: real stock editorial scene-time sidecars in short-retention PR QA.
+  # Explicitly NOT spoken transcription or Feature2-approved speech captions.
+  python3 - "$ROOT/video-engine" "$GARMENT_PROOF" "$ROOT/ci-artifacts" <<'PY'
+import json,sys
+from pathlib import Path
+sys.path.insert(0,sys.argv[1])
+from feature4_subtitles import export_private_subtitle_pair
+p=json.loads(Path(sys.argv[2]).read_text())
+assert p["duration_seconds"]==30 and p["scene_count"]==7
+assert not p["actual_spoken_voiceover"] and not p["commercial_release_eligible"]
+starts=p["synced_scene_starts"]
+titles=["A NEW SEASON","THE GARMENT EDIT","STYLE IN MOTION","TEXTURE AND DETAIL",
+        "THE FASHION STORY","CURATED STYLE","STOCK GARMENT CONCEPT - NOT A RETAILER AD"]
+assert len(starts)==len(titles) and len(set(starts))==len(starts)
+cues=[]
+for i,(start,title) in enumerate(zip(starts,titles)):
+    end=starts[i+1] if i+1<len(starts) else 30
+    # A short editorial title within its existing scene; no fake spoken cues.
+    cue_start=round(start+.2,3)
+    span=min(1.5,round(end-cue_start-.1,3))
+    assert .2<=span<=6
+    cues.append({"start":cue_start,"duration":span,"text":title})
+root=Path(sys.argv[3])
+proof=export_private_subtitle_pair(cues,duration_seconds=30,
+    srt_path=root/"feature4-stock-30s-editorial-titles.srt",
+    vtt_path=root/"feature4-stock-30s-editorial-titles.vtt")
+proof["caption_kind"]="EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO"
+proof["commercial_release_eligible"]=False
+(root/"feature4-stock-30s-editorial-titles-proof.json").write_text(
+    json.dumps(proof,indent=2)+"\n",encoding="utf-8")
+print("PASS: 30s Pexels editorial title sidecars SRT/VTT exactly follow real scene cuts; NOT spoken")
+PY
+
+  # F4-53: reviewer sees 12 REAL decoded Pexels frames, not only HTML.
+  python3 "$ROOT/video-engine/feature4_review_contact_sheet.py" \
+    --source "$GARMENT_MP4" --duration 30 \
+    --output "$ROOT/ci-artifacts/feature4-stock-garment-review-contact-sheet.jpg"
+  # F4-47: actual decoded Pexels actor movement; reject frozen footage.
+  python3 "$ROOT/video-engine/feature4_encoded_motion_qa.py" \
+    --source "$GARMENT_MP4" --duration 30 --moving-starts 0 10 20 \
+    --report "$ROOT/ci-artifacts/feature4-stock-garment-moving-pixels-proof.json"
+  # F4-43: audio-only loudness mastering; H264 packet hash must not change.
+  GARMENT_MASTER="$ROOT/ci-artifacts/feature4-stock-garment-30s-mastered.mp4"
+  GARMENT_MASTER_PROOF="$ROOT/ci-artifacts/feature4-stock-garment-master-proof.json"
+  python3 "$ROOT/video-engine/feature4_audio_master.py" \
+    --source "$GARMENT_MP4" --duration 30 \
+    --output "$GARMENT_MASTER" --report "$GARMENT_MASTER_PROOF"
+  python3 - "$GARMENT_MASTER_PROOF" <<'PY'
+import json,sys
+p=json.load(open(sys.argv[1]))
+assert p["status"]=="PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"
+assert p["mastered_audio_mean_db"] > p["source_audio_mean_db"] + 2
+assert not p["commercial_release_eligible"] and not p["signed_download_ready"]
+print("PASS: real stock 30s AAC audio mastered with H264 video packet hash unchanged")
+PY
+  # CPU-only compressed reviewer proxy from the same verified Full-HD MP4.
+  # Artifact contains no retailer/user media, just explicitly labeled stock QA.
+  python3 "$ROOT/video-engine/feature4_private_preview.py" \
+    --source "$GARMENT_MASTER" --duration 30 \
+    --output "$ROOT/ci-artifacts/feature4-stock-garment-30s-small.mp4" \
+    --report "$ROOT/ci-artifacts/feature4-stock-garment-30s-small-proof.json"
+
+
+  # F4-51: append independent cross-feature QA ledger only for actual
+  # public-stock test footage; do not copy customer media into CI artifacts.
+  python3 "$ROOT/video-engine/feature4_quality_receipt.py" \
+    --original "$GARMENT_MP4" --master "$GARMENT_MASTER" \
+    --preview "$ROOT/ci-artifacts/feature4-stock-garment-30s-small.mp4" \
+    --provenance "$GARMENT_PROOF" \
+    --motion-proof "$ROOT/ci-artifacts/feature4-stock-garment-moving-pixels-proof.json" \
+    --master-proof "$GARMENT_MASTER_PROOF" \
+    --preview-proof "$ROOT/ci-artifacts/feature4-stock-garment-30s-small-proof.json" \
+    --editorial-proof "$ROOT/ci-artifacts/feature4-stock-30s-editorial-titles-proof.json" \
+    --output "$ROOT/ci-artifacts/feature4-cross-feature-qa-receipt.json"
+
+fi
~~~~

### video-engine/professional.py

~~~~diff
@@ -0,0 +1,625 @@
+#!/usr/bin/env python3
+"""Feature #4: trusted, media-authorized HyperFrames composition compiler.
+
+This is a backend-only compiler. The caller MUST have already checked JWT,
+active shop membership, quota, approval and private-media ownership in the DB.
+The manifest MUST be generated by that trusted backend, never accepted as an
+attested rights declaration from an untrusted browser.
+"""
+import argparse
+import html
+import json
+import math
+import re
+import shutil
+import subprocess
+import sys
+import wave
+from pathlib import Path
+
+from asset_preflight import inspect_staged_audio, inspect_staged_image
+from feature4_caption_track import checked_caption_cues
+from render import checked_path, validate_rights
+
+VERSION = "rg_video_v2"
+MODES = {"text", "image", "poster", "media", "music_sync"}
+TEMPLATES = {"streetwear", "cinematic", "festival"}
+# Fixed renderer-authorized vocabulary shared with editor validation.
+SUPPORTED_ANIMATIONS = frozenset({"subtle_zoom", "fade", "slide", "pop", "glow"})
+SUPPORTED_TRANSITIONS = frozenset({"fade", "slide", "cut"})
+# Four strictly bounded, server-reviewed channel gains. No arbitrary filters.
+AUDIO_GAIN_LIMITS = {
+    "source": (0.2, 1.0), "music": (0.0, 1.0),
+    "voiceover": (0.2, 1.0), "sfx": (0.0, 0.5),
+}
+
+
+def checked_audio_mix(value, *, has_music, has_voice, has_source, has_sfx):
+    """Deny unknown, inactive, unbounded or unapproved gain controls."""
+    if value is None:
+        return {}
+    if type(value) is not dict or set(value) - set(AUDIO_GAIN_LIMITS):
+        raise VideoPlanError("Unknown or unapproved audio mix controls")
+    available = {"source": has_source, "music": has_music,
+                 "voiceover": has_voice, "sfx": has_sfx}
+    levels = {}
+    for name, raw in value.items():
+        low, high = AUDIO_GAIN_LIMITS[name]
+        if (available[name] is not True or type(raw) not in (int, float)
+                or not math.isfinite(raw) or not low <= raw <= high
+                or abs(raw * 100 - round(raw * 100)) > 1e-7):
+            raise VideoPlanError("Audio mix requires present approved track and bounded 0.01 gain")
+        levels[name] = round(float(raw), 2)
+    return levels
+
+
+def _gain_text(gain):
+    return f"{gain:.2f}".rstrip("0").rstrip(".")
+
+UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,36}$")
+ASSET_ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
+IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
+VIDEOS = {".mp4", ".mov", ".m4v"}
+AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
+MAX_BYTES_VIDEO = 250 * 1024 * 1024
+STYLES = {
+    "streetwear": ("#0a0a0c", "#f6f000", "#ffffff", "STREET / EDITION"),
+    "cinematic": ("#141922", "#d2b38a", "#f7f1e7", "THE COLLECTION"),
+    "festival": ("#351130", "#ffb947", "#fff7eb", "CELEBRATE IN STYLE"),
+}
+
+
+class VideoPlanError(ValueError):
+    pass
+
+
+def fields(value, allowed, required, label):
+    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
+        raise VideoPlanError(f"{label}: missing or unsupported fields")
+
+
+def number(value, label, low, high):
+    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
+        raise VideoPlanError(f"{label}: finite number required")
+    if not low <= value <= high:
+        raise VideoPlanError(f"{label}: out of range")
+    return float(value)
+
+
+def clean_text(value, label, limit=140, optional=False):
+    if optional and value is None:
+        return ""
+    if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
+        raise VideoPlanError(f"{label}: invalid text length")
+    if any(ord(c) < 32 or ord(c) == 127 for c in value):
+        raise VideoPlanError(f"{label}: control character")
+    return html.escape(value.strip(), quote=True)
+
+
+def checked_video(path):
+    if path.stat().st_size > MAX_BYTES_VIDEO or path.stat().st_size <= 0:
+        raise VideoPlanError("Video byte-size limit exceeded")
+    try:
+        p = subprocess.run(
+            ["ffprobe", "-v", "error", "-protocol_whitelist", "file", "-show_format",
+             "-show_streams", "-of", "json", str(path)], capture_output=True,
+            text=True, check=True, timeout=18,
+        )
+        data = json.loads(p.stdout)
+        streams = data.get("streams", [])
+        video = [s for s in streams if s.get("codec_type") == "video"]
+        audio = [s for s in streams if s.get("codec_type") == "audio"]
+        if len(video) != 1 or len(audio) > 1 or len(streams) != len(video) + len(audio):
+            raise VideoPlanError("Unsupported source video streams")
+        v = video[0]
+        w, h = int(v.get("width", 0)), int(v.get("height", 0))
+        dur = float(data.get("format", {}).get("duration", 0))
+        if w < 100 or h < 100 or w > 4096 or h > 4096 or w*h > 12_000_000:
+            raise VideoPlanError("Source video resolution out of bounds")
+        if not math.isfinite(dur) or not 0 < dur <= 180:
+            raise VideoPlanError("Source video duration out of bounds")
+        if v.get("codec_name") not in {"h264", "hevc", "vp9", "av1", "mpeg4"}:
+            raise VideoPlanError("Unsupported source video codec")
+        if audio and audio[0].get("codec_name") not in {"aac", "mp3", "pcm_s16le", "opus"}:
+            raise VideoPlanError("Unsupported source audio codec")
+        return dur, bool(audio)
+    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError,
+            KeyError, TypeError, OverflowError) as exc:
+        raise VideoPlanError("Invalid or unprobeable staged source video") from exc
+
+
+def validate(plan, manifest, asset_root, allow_test_media=False):
+    fields(plan, {"version", "shop_id", "mode", "template", "duration_seconds", "output",
+                  "scenes", "cta", "music_asset_id", "voiceover_asset_id", "audio_mix", "caption_cues", "beats", "brand", "logo_asset_id"},
+           {"version", "shop_id", "mode", "template", "duration_seconds", "output", "scenes", "cta"}, "plan")
+    fields(manifest, {"shop_id", "assets"}, {"shop_id", "assets"}, "manifest")
+    if plan["version"] != VERSION or plan["shop_id"] != manifest["shop_id"] or not UUID.fullmatch(str(plan["shop_id"])):
+        raise VideoPlanError("Version or authenticated shop_id mismatch")
+    if plan["mode"] not in MODES or plan["template"] not in TEMPLATES:
+        raise VideoPlanError("Unknown creation mode/template")
+    duration = plan["duration_seconds"]
+    if type(duration) is not int or duration not in (15, 30, 60):
+        raise VideoPlanError("Duration must be 15, 30, or 60 whole seconds")
+    fields(plan["output"], {"width", "height", "fps"}, {"width", "height", "fps"}, "output")
+    out = plan["output"]
+    if (out["width"], out["height"]) not in ((540, 960), (1080, 1920)) or out["fps"] not in (24, 30):
+        raise VideoPlanError("Only portrait 540p/1080p, 24/30 FPS is supported")
+    clean_text(plan["cta"], "approved CTA", 110)
+    if plan.get("caption_cues") is not None:
+        if plan.get("voiceover_asset_id") is None:
+            raise VideoPlanError("Timed subtitles need approved voiceover")
+        try:
+            checked_caption_cues(plan["caption_cues"],duration)
+        except ValueError as exc:
+            raise VideoPlanError("Invalid approved timed subtitle: "+str(exc)) from exc
+    brand = plan.get("brand")
+    if brand is not None:
+        fields(brand, {"name", "primary_color", "secondary_color"},
+               {"name", "primary_color"}, "approved brand kit")
+        clean_text(brand["name"], "shop name", 85)
+        for color in ("primary_color", "secondary_color"):
+            if color in brand and (not isinstance(brand[color], str)
+                                   or not re.fullmatch(r"#[0-9a-fA-F]{6}", brand[color])):
+                raise VideoPlanError("Brand colors must be six-digit hex")
+    scenes = plan["scenes"]
+    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 12:
+        raise VideoPlanError("Expected 1-12 bounded scenes")
+    assets = manifest["assets"]
+    if not isinstance(assets, dict):
+        raise VideoPlanError("Missing trusted media map")
+    ordered = {}
+    previous_end = 0.0
+    source_audio = False
+    for i, scene in enumerate(scenes):
+        fields(scene, {"start", "duration", "asset_id", "headline", "offer", "trim_start", "mute_source",
+                       "poster_overlay_asset_id", "animation_preset", "transition", "sfx_asset_id"},
+               {"start", "duration", "headline"}, f"scene {i}")
+        start = number(scene["start"], "scene start", 0, 60)
+        length = number(scene["duration"], "scene duration", 0.5, 60)
+        if abs(start - previous_end) > 0.001 or start + length > duration + 0.001:
+            raise VideoPlanError("Scenes must be contiguous and bounded")
+        previous_end = start + length
+        clean_text(scene["headline"], "approved headline", 110)
+        if "offer" in scene:
+            clean_text(scene["offer"], "approved offer", 70)
+        if scene.get("animation_preset", "subtle_zoom") not in SUPPORTED_ANIMATIONS:
+            raise VideoPlanError("Unknown approved animation preset")
+        if scene.get("transition", "fade") not in SUPPORTED_TRANSITIONS:
+            raise VideoPlanError("Unknown reviewed transition")
+        sfx_id = scene.get("sfx_asset_id")
+        if sfx_id is not None:
+            if (not isinstance(sfx_id, str) or not ASSET_ID.fullmatch(sfx_id)
+                    or sfx_id not in assets):
+                raise VideoPlanError("Unknown approved sound effect")
+            sfx = assets[sfx_id]
+            fields(sfx, {"kind", "path", "rights"}, {"kind", "path", "rights"}, "sound effect entry")
+            if sfx["kind"] != "audio":
+                raise VideoPlanError("Sound effect must be audio")
+            validate_rights(sfx["rights"], sfx_id, allow_test_media)
+            sfx_path = checked_path(asset_root, sfx["path"], sfx_id, AUDIO)
+            inspect_staged_audio(sfx_path)
+            ordered[sfx_id] = (sfx_path, "audio")
+        overlay_id = scene.get("poster_overlay_asset_id")
+        if overlay_id is not None:
+            if (not isinstance(overlay_id, str) or not ASSET_ID.fullmatch(overlay_id)
+                    or overlay_id not in assets or overlay_id == scene.get("asset_id")):
+                raise VideoPlanError("Unknown approved poster overlay")
+            poster = assets[overlay_id]
+            fields(poster, {"kind", "path", "rights"}, {"kind", "path", "rights"}, "poster entry")
+            if poster["kind"] != "poster":
+                raise VideoPlanError("Poster overlay must be a reviewed poster")
+            validate_rights(poster["rights"], overlay_id, allow_test_media)
+            overlay_path = checked_path(asset_root, poster["path"], overlay_id, IMAGES)
+            inspect_staged_image(overlay_path)
+            ordered[overlay_id] = (overlay_path, "poster")
+        if "mute_source" in scene and type(scene["mute_source"]) is not bool:
+            raise VideoPlanError("mute_source must be boolean")
+        aid = scene.get("asset_id")
+        if aid is None:
+            if plan["mode"] != "text" and not plan.get("brand"):
+                raise VideoPlanError("Media mode text-only scenes require approved brand identity")
+            if "trim_start" in scene or "mute_source" in scene:
+                raise VideoPlanError("Cannot trim or mute a text-only scene")
+            continue
+        if not isinstance(aid, str) or not ASSET_ID.fullmatch(aid) or aid not in assets:
+            raise VideoPlanError("Unknown server-authorized asset ID")
+        entry = assets[aid]
+        fields(entry, {"kind", "path", "rights"}, {"kind", "path", "rights"}, "media entry")
+        validate_rights(entry["rights"], aid, allow_test_media)
+        kind = entry["kind"]
+        if kind not in ({"image", "poster", "video"} if plan["mode"] in {"media", "music_sync", "text"}
+                        else {"image", "poster"}):
+            raise VideoPlanError("Asset kind forbidden for this mode")
+        path = checked_path(asset_root, entry["path"], aid, IMAGES if kind in {"image", "poster"} else VIDEOS)
+        if kind in {"image", "poster"}:
+            inspect_staged_image(path)
+            if "trim_start" in scene or "mute_source" in scene:
+                raise VideoPlanError("Cannot trim or mute an image")
+        else:
+            vduration, has_audio = checked_video(path)
+            offset = number(scene.get("trim_start", 0), "trim_start", 0, 180)
+            if offset + length > vduration + .06:
+                raise VideoPlanError("Video trim exceeds source duration")
+            source_audio = source_audio or (has_audio and not scene.get("mute_source", False))
+        ordered[aid] = (path, kind)
+    if abs(previous_end - duration) > .001:
+        raise VideoPlanError("Scenes must fill total duration")
+    logo_id = plan.get("logo_asset_id")
+    if logo_id is not None:
+        if not isinstance(logo_id, str) or not ASSET_ID.fullmatch(logo_id) or logo_id not in assets:
+            raise VideoPlanError("Unknown verified store logo")
+        logo = assets[logo_id]
+        fields(logo, {"kind", "path", "rights"}, {"kind", "path", "rights"}, "logo entry")
+        if logo["kind"] != "logo":
+            raise VideoPlanError("Brand logo must have logo kind")
+        validate_rights(logo["rights"], logo_id, allow_test_media)
+        logo_path = checked_path(asset_root, logo["path"], logo_id, IMAGES)
+        inspect_staged_image(logo_path)
+        ordered[logo_id] = (logo_path, "logo")
+    music_id = plan.get("music_asset_id")
+    if music_id is not None:
+        if not isinstance(music_id, str) or not ASSET_ID.fullmatch(music_id) or music_id not in assets:
+            raise VideoPlanError("Unknown authorized music ID")
+        entry = assets[music_id]
+        fields(entry, {"kind", "path", "rights"}, {"kind", "path", "rights"}, "music entry")
+        if entry["kind"] != "audio":
+            raise VideoPlanError("Music asset must be audio")
+        validate_rights(entry["rights"], music_id, allow_test_media)
+        path = checked_path(asset_root, entry["path"], music_id, AUDIO)
+        inspect_staged_audio(path)
+        ordered[music_id] = (path, "audio")
+    voice_id = plan.get("voiceover_asset_id")
+    if voice_id is not None:
+        if not isinstance(voice_id, str) or not ASSET_ID.fullmatch(voice_id) or voice_id not in assets:
+            raise VideoPlanError("Missing authorized narration")
+        voice = assets[voice_id]
+        fields(voice, {"kind", "path", "rights"}, {"kind", "path", "rights"}, "narration entry")
+        if voice["kind"] != "audio":
+            raise VideoPlanError("Narration media must be audio")
+        validate_rights(voice["rights"], voice_id, allow_test_media)
+        voice_path = checked_path(asset_root, voice["path"], voice_id, AUDIO)
+        info = inspect_staged_audio(voice_path)
+        if info["duration_seconds"] is None or info["duration_seconds"] + .06 < duration:
+            raise VideoPlanError("Approved narration is shorter than the Reel")
+        ordered[voice_id] = (voice_path, "audio")
+    beats = plan.get("beats", [])
+    if not isinstance(beats, list) or len(beats) > 300:
+        raise VideoPlanError("Invalid beat-grid size")
+    prev = -1.0
+    for beat in beats:
+        b = number(beat, "beat", 0, duration)
+        if b <= prev:
+            raise VideoPlanError("Beats must be strictly ascending")
+        prev = b
+    checked_audio_mix(
+        plan.get("audio_mix"), has_music=music_id is not None,
+        has_voice=voice_id is not None, has_source=source_audio,
+        has_sfx=any(s.get("sfx_asset_id") is not None for s in scenes),
+    )
+    if plan["mode"] == "music_sync":
+        if music_id is None or len(beats) < 2:
+            raise VideoPlanError("Beat-sync requires rights-cleared music and beat timestamps")
+        if any(min(abs(scene["start"] - beat) for beat in beats) > .17
+               for scene in scenes[1:]):
+            raise VideoPlanError("Beat-sync scene boundaries must align with provided beat-grid")
+    return ordered, source_audio
+
+
+def silent_wav(path, duration):
+    with wave.open(str(path), "wb") as stream:
+        stream.setnchannels(2)
+        stream.setsampwidth(2)
+        stream.setframerate(44100)
+        for _ in range(duration):
+            stream.writeframes(b"\x00\x00\x00\x00" * 44100)
+
+
+def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media=False):
+    """Return authorized local project directory; no rendering or cloud side effects."""
+    ordered, source_audio = validate(plan, manifest, asset_root, allow_test_media)
+    workspace = Path(output_dir).resolve()
+    if workspace.exists() and any(workspace.iterdir()):
+        raise VideoPlanError("Composition destination must be empty to prevent stale media")
+    workspace.mkdir(parents=True, exist_ok=True)
+    media = workspace / "assets"
+    media.mkdir()
+    names = {}
+    for i, (asset_id, (path, _kind)) in enumerate(ordered.items()):
+        name = f"asset{i:02d}{path.suffix.lower()}"
+        shutil.copyfile(path, media / name)
+        names[asset_id] = "assets/" + name
+    if plan.get("music_asset_id") is None:
+        silent_wav(media / "silence.wav", plan["duration_seconds"])
+        soundtrack = "assets/silence.wav"
+    else:
+        soundtrack = names[plan["music_asset_id"]]
+    duration = plan["duration_seconds"]
+    width, height = plan["output"]["width"], plan["output"]["height"]
+    bg, accent, fg, kicker = STYLES[plan["template"]]
+    brand = plan.get("brand") or {}
+    if brand.get("primary_color"):
+        accent = brand["primary_color"]
+    k = html.escape(kicker)
+    mix = checked_audio_mix(
+        plan.get("audio_mix"), has_music=plan.get("music_asset_id") is not None,
+        has_voice=plan.get("voiceover_asset_id") is not None, has_source=source_audio,
+        has_sfx=any(s.get("sfx_asset_id") is not None for s in plan["scenes"]),
+    )
+    components = []
+    for i, scene in enumerate(plan["scenes"]):
+        start, length = scene["start"], scene["duration"]
+        aid = scene.get("asset_id")
+        media_markup = ""
+        # The separate footage track must carry the same reviewed transition as
+        # its scene overlay; otherwise only the text fades/slides in the MP4.
+        transition = scene.get("transition", "fade")
+        if aid:
+            _path, kind = ordered[aid]
+            src = names[aid]
+            if kind == "video":
+                mute = " muted" if scene.get("mute_source", False) else ""
+                trim = scene.get("trim_start", 0)
+                original_audio = " data-has-audio=\"true\"" if not scene.get("mute_source", False) else ""
+                media_markup = (
+                    f'<video class="footage clip" id="video{i}" data-transition="{transition}" src="{src}" '
+                    f'data-start="{start}" data-duration="{length}" data-media-start="{trim}" '
+                    f'data-track-index="0" data-volume="{_gain_text(mix.get("source", 1.0))}" style="--span:{length}s" '
+                    f'playsinline{original_audio}{mute}></video>'
+                )
+            else:
+                media_markup = f'<img class="product-photo" src="{src}" alt="" decoding="sync">'
+        poster_markup = ""
+        if scene.get("poster_overlay_asset_id"):
+            poster_src = names[scene["poster_overlay_asset_id"]]
+            poster_markup = f'<img class="poster-overlay" src="{poster_src}" alt="">'
+        headline = clean_text(scene["headline"], "headline")
+        # Bound headline typography for the narrow 9:16 canvas; preserve all approved text.
+        title_length = len(scene["headline"].strip())
+        title_font = max(24, width // (10 if title_length <= 32 else 15 if title_length <= 70 else 20))
+        offer = clean_text(scene.get("offer"), "offer", optional=True)
+        offer_markup = f'<p class="offer">{offer}</p>' if offer else ""
+        if scene.get("sfx_asset_id"):
+            src = names[scene["sfx_asset_id"]]
+            components.append(
+                f'<audio id="sfx{i}" src="{src}" data-start="{start}" '
+                f'data-duration="{min(2, length)}" data-track-index="6" data-volume="{_gain_text(mix.get("sfx", .25))}"></audio>'
+            )
+        animation = scene.get("animation_preset", "subtle_zoom")
+        transition = scene.get("transition", "fade")
+        leading_video = media_markup if aid and ordered[aid][1] == "video" else ""
+        video_layer = " has-video" if leading_video else ""
+        scene_image = media_markup if aid and ordered[aid][1] != "video" else ""
+        # Promote intro logo to a root-level timed image. Nested images in
+        # a timed scene were missing from the actual Chromium render.
+        is_poster = bool(aid and ordered[aid][1] == "poster")
+        poster_layer = " has-poster" if is_poster else ""
+        # Application-selected editorial scene roles. Never derive CSS from user text.
+        role = ("intro" if i == 0 and not aid else
+                "outro" if i == len(plan["scenes"]) - 1 else
+                "sale" if offer else "motion" if leading_video else
+                "poster" if is_poster else "product")
+        components.append(
+            f'{leading_video}<section id="scene{i}" class="clip scene s{i%3}{video_layer}{poster_layer} role-{role} anim-{animation} trans-{transition}" '
+            f'data-start="{start}" data-duration="{length}" data-track-index="1" '
+            f'style="--span:{length}s">'
+            f'<div class="halo"></div><div class="editorial-rule"></div>' 
+            f'<div class="photo-wrap">{scene_image}</div>{poster_markup}'
+            f'<div class="glass"><p class="kicker">{k} / {i+1:02d}</p>'
+            f'<h1 style="font-size:{title_font}px">{headline}</h1>{offer_markup}</div>'
+            f'<p class="index">RG · {i+1:02d} / {len(plan["scenes"]):02d}</p></section>'
+        )
+    # The only JavaScript is HyperFrames' own runtime. No client HTML, JS, URL or CSS enters this file.
+    css = f"""
+*{{box-sizing:border-box}}
+html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:{bg};font-family:Arial,'Helvetica Neue',sans-serif}}
+#main{{position:relative;width:{width}px;height:{height}px;overflow:hidden;background:linear-gradient(128deg,{bg},#0b0d15 60%,{bg})}}
+.scene{{position:absolute;inset:0;overflow:hidden;color:{fg};
+  background:radial-gradient(ellipse 85% 65% at 65% 28%,{accent}20,transparent 78%),
+  linear-gradient(152deg,{bg},#10111d 83%)}}
+.scene.has-video{{background:linear-gradient(0deg,#0b0b13a8,transparent 26%,transparent 80%,#0b0b130f)}}
+.scene.trans-fade{{animation:editorialFade var(--span) linear both}}
+.scene.trans-slide{{animation:editorialSlide var(--span) ease-in-out both}}
+.scene.trans-cut{{animation:none}}
+.halo{{position:absolute;width:110%;height:58%;left:12%;top:6%;border-radius:50%;background:{accent};opacity:.09;filter:blur({width//8}px);pointer-events:none}}
+.editorial-rule{{position:absolute;top:13%;left:7%;width:20%;height:1px;background:{accent};opacity:.8}}
+.photo-wrap{{position:absolute;top:10%;height:72%;width:100%;left:0;display:grid;place-items:center;overflow:hidden}}
+.product-photo{{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 24px 48px #0009);animation:editorialDrift var(--span) ease-in-out both}}
+.footage{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}}
+.footage[data-transition="fade"]{{animation:editorialFade var(--span) linear both}}
+.footage[data-transition="slide"]{{animation:editorialSlide var(--span) ease-in-out both}}
+.footage[data-transition="cut"]{{animation:none}}
+.poster-overlay{{position:absolute;right:4%;top:15%;height:32%;max-width:45%;object-fit:contain;filter:drop-shadow(0 10px 28px #000a);animation:posterReveal var(--span) ease-out both}}
+.glass{{position:absolute;left:6%;right:6%;bottom:8%;padding:4.5% 5%;min-height:17%;
+  background:linear-gradient(105deg,#090912ed,#171625ba);border-top:1px solid {accent}83;
+  box-shadow:0 17px 42px #0007;animation:copyLift var(--span) ease-in-out both}}
+.kicker{{font-size:{max(12,width//43)}px;letter-spacing:.27em;font-weight:700;color:{accent};margin:0 0 4%;text-transform:uppercase}}
+h1{{font-weight:800;font-size:{width//12}px;line-height:1.06;letter-spacing:-.015em;text-transform:uppercase;margin:0;overflow-wrap:anywhere}}
+.offer{{font-weight:900;font-size:{width//8}px;letter-spacing:-.055em;color:{accent};line-height:1;margin:4% 0 0}}
+.index{{position:absolute;bottom:2%;right:6%;font-size:{max(11,width//48)}px;letter-spacing:.22em;font-weight:700;opacity:.58}}
+.spoken-caption{{position:absolute;left:7%;right:7%;bottom:35%;z-index:12;
+ display:flex;justify-content:center;text-align:center;pointer-events:none}}
+.spoken-caption span{{display:inline-block;max-width:100%;padding:2.2% 4%;
+ color:#fff;background:#090a13e8;border-radius:{max(7,width//100)}px;
+ font-size:{max(22,width//19)}px;line-height:1.2;font-weight:800;
+ text-shadow:0 1px 3px #000;overflow-wrap:anywhere;
+ animation:subtitlePop .18s ease-out both}}
+@keyframes subtitlePop{{from{{opacity:0;transform:translateY(10%)}}to{{opacity:1;transform:translateY(0)}}}}
+.s2 .glass{{border-top-color:{fg}66}}
+.hero-logo{{position:absolute;top:20%;left:28%;width:44%;height:32%;z-index:5;object-fit:contain;
+ filter:drop-shadow(0 15px 42px #0008)}}
+/* A distinct editorial composition for each semantic scene; no user HTML. */
+.role-intro{{background:radial-gradient(ellipse 64% 49% at 50% 35%,{accent}29,transparent 78%),linear-gradient(160deg,{bg},#0c0b13)}}
+.role-intro .editorial-rule{{left:39%;width:22%;top:16%}}
+.role-intro .glass{{left:7%;right:7%;bottom:10%;text-align:center;background:none;border:0;box-shadow:none;min-height:13%;padding:2%}}
+.role-intro h1{{font-family:Georgia,'Times New Roman',serif;font-size:{width//11}px!important;
+  font-weight:500;letter-spacing:-.025em;line-height:1.06;text-transform:none}}
+.role-intro .kicker{{letter-spacing:.4em}}
+.role-motion .glass{{left:0;right:0;bottom:0;min-height:28%;border:0;padding:9% 8% 12%;
+ background:linear-gradient(0deg,#080a14f2,#10111aa8 66%,transparent);box-shadow:none}}
+.role-motion h1{{font-family:Georgia,'Times New Roman',serif;font-size:{width//11}px!important;
+  font-weight:500;letter-spacing:-.02em;text-transform:none}}
+.role-motion .editorial-rule{{top:16%;left:8%;width:16%}}
+.role-product .photo-wrap{{top:6%;height:66%;left:7%;width:86%}}
+.role-product .glass{{bottom:7%;left:10%;right:10%;background:#11131ae6;border-left:2px solid {accent};border-top:0}}
+.role-product h1{{font-family:Georgia,'Times New Roman',serif;font-weight:500;text-transform:none;
+  font-size:{width//12}px!important}}
+.role-sale .photo-wrap{{top:7%;height:69%;left:-6%;width:78%;filter:brightness(.84)}}
+.role-sale .poster-overlay{{right:3%;top:11%;max-width:35%;height:26%}}
+.role-sale .glass{{left:5%;right:5%;bottom:6%;min-height:29%;padding:4.5%;
+  background:linear-gradient(112deg,#160b25f0,#35122fe0);border:1px solid {accent}70}}
+.role-sale h1{{font-family:Georgia,'Times New Roman',serif;font-weight:500;font-size:{width//14}px!important;
+  text-transform:none}}
+.role-sale .offer{{font-size:{width//6}px;font-weight:900;text-shadow:0 0 22px {accent}60}}
+.role-poster .photo-wrap{{top:6%;height:73%}}
+.role-outro{{background:radial-gradient(ellipse at 50% 30%,{accent}28,transparent 75%),#11111b}}
+.role-outro .photo-wrap{{top:4%;left:12%;width:76%;height:67%}}
+.role-outro .product-photo{{object-fit:contain;animation:outroReveal var(--span) ease-out both}}
+.role-outro .glass{{bottom:7%;left:7%;right:7%;padding:3.5%;min-height:16%;
+  border-top:2px solid {accent};background:#0b0c16f0;text-align:center}}
+.role-outro .glass h1{{font-family:Georgia,'Times New Roman',serif;text-transform:none;
+  font-weight:500;font-size:{width//12}px!important}}
+.role-outro .kicker{{margin:0 0 2%}}
+.role-outro .editorial-rule{{display:none}}
+/* Effect presets animate the reviewed text layer; scene transitions and
+   footage-track transition animations remain independent. */
+.anim-subtle_zoom .glass{{animation:presetSubtleZoom var(--span) ease-in-out both}}
+.anim-fade .glass{{animation:presetFade var(--span) ease both}}
+.anim-slide .glass{{animation:presetSlide var(--span) cubic-bezier(.2,.7,.2,1) both}}
+.anim-pop .glass{{animation:promoPop var(--span) ease-in-out both}}
+.anim-glow .glass{{animation:presetGlow var(--span) ease-in-out both}}
+.anim-glow .offer{{text-shadow:0 0 15px {accent},0 0 30px {accent}75}}
+.anim-slide .photo-wrap{{animation:editorialDrift var(--span) ease both}}
+@keyframes presetSubtleZoom{{0%{{opacity:.72;transform:scale(.975)}}30%{{opacity:1}}100%{{opacity:1;transform:scale(1.03)}}}}
+@keyframes presetFade{{0%{{opacity:0}}20%{{opacity:1}}100%{{opacity:1}}}}
+@keyframes presetSlide{{0%{{opacity:0;transform:translate3d(-10%,0,0)}}25%{{opacity:1;transform:translate3d(0,0,0)}}100%{{opacity:1;transform:translate3d(0,0,0)}}}}
+@keyframes presetGlow{{0%{{opacity:.85;filter:brightness(.82)}}55%{{opacity:1;filter:brightness(1.22)}}100%{{opacity:1;filter:brightness(1)}}}}
+@keyframes editorialFade{{0%{{opacity:0}}7%{{opacity:1}}96%{{opacity:1}}100%{{opacity:.98}}}}
+@keyframes editorialSlide{{0%{{opacity:0;transform:translate3d(7%,0,0)}}14%{{opacity:1;transform:translate3d(0,0,0)}}100%{{opacity:1;transform:translate3d(0,0,0)}}}}
+@keyframes editorialDrift{{0%{{transform:scale(1.025) translate3d(-1%,1%,0)}}100%{{transform:scale(1.12) translate3d(1%,-1%,0)}}}}
+@keyframes copyLift{{0%{{opacity:0;transform:translateY(9%)}}15%{{opacity:1;transform:translateY(0)}}92%{{opacity:1}}100%{{opacity:.95}}}}
+@keyframes posterReveal{{0%{{opacity:0;transform:scale(.88) rotate(3deg)}}18%{{opacity:1;transform:scale(1) rotate(0deg)}}100%{{opacity:1}}}}
+@keyframes outroReveal{{0%{{opacity:0;transform:scale(.94)}}16%{{opacity:1;transform:scale(1)}}100%{{opacity:1}}}}
+@keyframes promoPop{{0%{{transform:scale(.91);opacity:0}}15%{{transform:scale(1);opacity:1}}95%{{opacity:1}}100%{{opacity:1}}}}
+"""
+
+    if plan.get("logo_asset_id"):
+        # This is a timed overlay on the root; the logo source is a trusted, staged asset.
+        logo_src = names[plan["logo_asset_id"]]
+        # A centered hero logo is suitable for a text-only branded intro.
+        # On image/video-led openings it conceals the product/model and breaks
+        # fashion composition. Preserve the small top-right brand mark below.
+        if not plan["scenes"][0].get("asset_id"):
+            intro_seconds = min(3, plan["scenes"][0]["duration"])
+            components.append(
+                f'<img id="intro-logo" class="clip hero-logo" src="{logo_src}" alt="" '
+                f'data-start="0" data-duration="{intro_seconds}" data-track-index="2">'
+            )
+        components.append(
+            f'<img id="brand-logo" class="clip" src="{logo_src}" alt="" '
+            f'data-start="0" data-duration="{duration}" data-track-index="4" '
+            f'style="position:absolute;top:3%;right:5%;width:16%;height:10%;object-fit:contain;z-index:8">'
+        )
+    if brand.get("name"):
+        shop_name = clean_text(brand["name"], "shop name", 85)
+        components.append(
+            f'<div id="brand-name" class="clip" data-start="0" data-duration="{duration}" '
+            f'data-track-index="4" style="position:absolute;left:5%;top:3%;z-index:8;'
+            f'font-size:{width//22}px;font-weight:900;color:{fg};text-shadow:0 1px 9px #000;'
+            f'max-width:70%;overflow-wrap:anywhere">{shop_name}</div>'
+        )
+    # The final CTA remains sourced from approved input and is displayed throughout the last scene.
+    cta = clean_text(plan["cta"], "CTA", 110)
+    last = plan["scenes"][-1]
+    cta_start = max(0, duration - min(3, last["duration"]))
+    if last["headline"].strip().casefold() != plan["cta"].strip().casefold():
+        components.append(
+            f'<div id="cta" class="clip" data-start="{cta_start}" data-duration="{duration-cta_start}" '
+            f'data-track-index="3" style="position:absolute;top:16%;left:12%;right:12%;z-index:9;'
+            f'background:{accent};color:{bg};padding:2%;text-align:center;font-size:{width//22}px;'
+            f'font-weight:900;border-radius:12px">{cta}</div>'
+        )
+    # Source of truth is the Feature2-reviewed transcript, never browser HTML.
+    for index,cue in enumerate(plan.get("caption_cues") or []):
+        safe=clean_text(cue["text"],"approved timed subtitle",90)
+        components.append(
+            f'<div id="spoken-caption{index}" class="clip spoken-caption" '
+            f'data-start="{cue["start"]}" data-duration="{cue["duration"]}" '
+            f'data-track-index="8"><span>{safe}</span></div>'
+        )
+    # Narration is a full-length approved audio source, not 2-second SFX.
+    # Fix gain in the trusted renderer until an advanced audio-mix contract exists.
+    if plan.get("voiceover_asset_id") is not None:
+        src = names[plan["voiceover_asset_id"]]
+        components.append(
+            f'<audio id="approved-voiceover" src="{src}" data-start="0" '
+            f'data-duration="{duration}" data-track-index="7" data-volume="{_gain_text(mix.get("voiceover", 1.0))}" '
+            f'data-fade-in="0.10" data-fade-out="0.16"></audio>'
+        )
+    # Duck ONLY the licensed bed beneath clips retaining their original sound.
+    # This is deterministic scene-level gain, not transcription/VAD/AI speech QA.
+    # Keep the original single-track path for music-free and silent-video Reels.
+    if (source_audio or plan.get("voiceover_asset_id") is not None) and plan.get("music_asset_id") is not None:
+        for i, scene in enumerate(plan["scenes"]):
+            aid = scene.get("asset_id")
+            is_source_sound = bool(aid and ordered[aid][1] == "video"
+                                   and not scene.get("mute_source", False))
+            music_gain = mix.get("music", .55)
+            gain = _gain_text(min(music_gain, .12) if
+                              (is_source_sound or plan.get("voiceover_asset_id") is not None)
+                              else music_gain)
+            start, length = scene["start"], scene["duration"]
+            fade = min(0.12, length / 6)
+            components.append(
+                f'<audio id="soundtrack{i}" src="{soundtrack}" data-start="{start}" '
+                f'data-duration="{length}" data-media-start="{start}" '
+                f'data-track-index="5" data-volume="{gain}" '
+                f'data-fade-in="{fade}" data-fade-out="{fade}"></audio>'
+            )
+    else:
+        music_gain = mix.get("music", .55)
+        gain = _gain_text(min(music_gain, .15) if
+                          (source_audio or plan.get("voiceover_asset_id") is not None)
+                          else music_gain)
+        components.append(
+            f'<audio id="soundtrack" src="{soundtrack}" data-start="0" '
+            f'data-duration="{duration}" data-track-index="5" data-volume="{gain}" '
+            f'data-fade-in="0.35" data-fade-out="1.0"></audio>'
+        )
+    page = (
+        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
+        f'<meta name="viewport" content="width={width},height={height}">'
+        f'<style>{css}</style></head><body>'
+        f'<div id="main" data-composition-id="main" data-no-timeline data-start="0" '
+        f'data-duration="{duration}" data-width="{width}" data-height="{height}" '
+        f'data-fps="{plan["output"]["fps"]}">'
+        + "".join(components) + '</div></body></html>'
+    )
+    (workspace / "index.html").write_text(page, encoding="utf-8")
+    (workspace / "render-config.json").write_text(json.dumps(
+        {"fps": plan["output"]["fps"], "width": width, "height": height,
+         "quality": "standard", "format": "mp4",
+         "duration_seconds": duration, "template": plan["template"], "mode": plan["mode"],
+         "renderer": "hyperframes", "contract_version": VERSION}, indent=2) + "\n")
+    return workspace
+
+
+def main():
+    parser = argparse.ArgumentParser(description="Feature4 trusted HyperFrames composition compiler (no cloud calls)")
+    parser.add_argument("--plan", required=True)
+    parser.add_argument("--manifest", required=True)
+    parser.add_argument("--asset-root", required=True)
+    parser.add_argument("--output-dir", required=True)
+    parser.add_argument("--allow-synthetic-test", action="store_true", help="Offline CI ONLY; never backend production")
+    args = parser.parse_args()
+    try:
+        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
+        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
+        target = compile_composition(plan, manifest, args.asset_root, args.output_dir, args.allow_synthetic_test)
+        print(json.dumps({"result": "COMPILED", "path": str(target), "version": VERSION}))
+    except (VideoPlanError, OSError, ValueError, KeyError) as exc:
+        print(f"COMPOSITION REJECTED: {exc}", file=sys.stderr)
+        raise SystemExit(2)
+
+
+if __name__ == "__main__":
+    main()
~~~~

