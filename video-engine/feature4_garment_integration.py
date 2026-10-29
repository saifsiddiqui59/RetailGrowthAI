#!/usr/bin/env python3
"""CPU-only Feature4 garment+stock-motion 30s test (NOT a retailer garment match)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.parse
import urllib.request
from asset_preflight import inspect_staged_image
from professional import compile_composition, VideoPlanError
from feature4_stock_showcase import (CLIPS, DEMO_SHOP, LICENSE_URL, StockShowcaseError,
    check_input, normalize_for_renderer, retrieve_stock)
from feature4_beat_edit import original_rhythmic_music, snap_scene_cuts, BeatEditError

GARMENTS = (
    ("garment01", "8306370", "Ron Lach",
     "https://www.pexels.com/photo/clothes-hanged-on-clothes-hanger-inside-a-boutique-8306370/"),
    ("garment02", "8387134", "Ron Lach",
     "https://www.pexels.com/photo/hanging-clothes-in-a-clothes-rack-inside-a-boutique-8387134/"),
)
# Two more official Pexels editorial photos for the FULL-MINUTE QA only.
# 30-second verified source/appearance remains byte-for-byte unchanged.
MINUTE_GARMENTS = (
    ("garment03", "4947543", "Maria Orlova",
     "https://www.pexels.com/photo/collection-of-female-clothes-on-rack-in-boutique-4947543/"),
    ("garment04", "4857762", "Rachel Claire",
     "https://www.pexels.com/photo/stylish-clothes-hanging-on-rack-in-fashion-boutique-4857762/"),
)
MAX_IMAGE_BYTES = 22_000_000
OUTRO = "STOCK GARMENT CONCEPT - NOT A RETAILER AD"


class ImageRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if u.scheme != "https" or u.hostname != "images.pexels.com":
            raise StockShowcaseError("Garment redirect outside approved host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def retrieve_garment(dest: Path, source_id: str):
    if source_id not in {rec[1] for rec in GARMENTS + MINUTE_GARMENTS}:
        raise StockShowcaseError("Garment ID not allowlisted")
    if dest.exists() or dest.is_symlink():
        raise StockShowcaseError("Refusing garment overwrite")
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = ("https://images.pexels.com/photos/" + source_id +
           "/pexels-photo-" + source_id + ".jpeg?auto=compress&cs=tinysrgb&w=1200")
    part = dest.with_suffix(".download")
    try:
        opener = urllib.request.build_opener(ImageRedirect)
        with opener.open(urllib.request.Request(url, headers={
                "User-Agent": "RetailGrowthAI-Feature4-LicensedMediaQA/1.0",
                "Accept": "image/jpeg"}), timeout=55) as stream, part.open("wb") as out:
            if (urllib.parse.urlsplit(stream.url).hostname != "images.pexels.com" or
                    stream.headers.get("Content-Type", "").split(";")[0].strip().lower() != "image/jpeg"):
                raise StockShowcaseError("Unexpected garment origin or mime type")
            size, magic = 0, b""
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                if not magic:
                    magic = chunk[:3]
                size += len(chunk)
                if size > MAX_IMAGE_BYTES:
                    raise StockShowcaseError("Oversize garment JPEG")
                out.write(chunk)
        if size < 15000 or magic != b"\xff\xd8\xff":
            raise StockShowcaseError("Garment not a JPEG")
        part.replace(dest)
        return {"source_url": url, "bytes": size}
    except (OSError, urllib.error.URLError, StockShowcaseError):
        part.unlink(missing_ok=True)
        raise


def checked_garment(path: Path):
    if (not path.is_file() or path.is_symlink() or path.suffix.lower() not in (".jpg", ".jpeg")
            or not 15000 <= path.stat().st_size <= MAX_IMAGE_BYTES):
        raise StockShowcaseError("Unsafe or missing garment photo")
    try:
        inspect_staged_image(path)
    except (ValueError, OSError) as exc:
        raise StockShowcaseError("Invalid garment image preflight") from exc


def make_garment_project(source_dir: Path, project_dir: Path, *, seconds: int = 30):
    if type(seconds) is not int or seconds not in (30, 60):
        raise StockShowcaseError("Only 30s or 60s stock editorial test duration allowed")
    source_dir = Path(source_dir).resolve(strict=True)
    if project_dir.exists() and any(project_dir.iterdir()):
        raise StockShowcaseError("Refusing garment composition overwrite")
    with tempfile.TemporaryDirectory(prefix="rgai-garment-private-") as temporary:
        stage = Path(temporary)
        manifest = {"shop_id": DEMO_SHOP, "assets": {}}
        evidence = []
        for aid, sid, creator, page, urls in CLIPS:
            original, norm = source_dir / (sid + ".mp4"), stage / (sid + ".mp4")
            measured = check_input(original)
            staged = normalize_for_renderer(original, norm)
            manifest["assets"][aid] = {"kind": "video", "path": norm.name,
                "rights": {"commercial_use": True, "license": "royalty_free",
                           "source": page, "evidence": "Pexels stock motion; no model endorsement"}}
            evidence.append({"source_feature": "feature5_stock_proxy", "asset_id": aid,
                "source_id": sid, "creator": creator, "page": page,
                "sha256_original": hashlib.sha256(original.read_bytes()).hexdigest(),
                "sha256_staged": hashlib.sha256(norm.read_bytes()).hexdigest(),
                "original_probe": measured, "stage_probe": staged, "ai_generated": False})
        active_garments = GARMENTS + MINUTE_GARMENTS if seconds == 60 else GARMENTS
        for aid, sid, creator, page in active_garments:
            original, dest = source_dir / (sid + ".jpg"), stage / (sid + ".jpg")
            checked_garment(original)
            dest.write_bytes(original.read_bytes())
            manifest["assets"][aid] = {"kind": "image", "path": dest.name,
                "rights": {"commercial_use": True, "license": "royalty_free",
                           "source": page, "evidence": "Independent stock garment photo; not worn by model"}}
            evidence.append({"source_feature": "feature3_garment_proxy", "asset_id": aid,
                "source_id": sid, "creator": creator, "page": page,
                "sha256_original": hashlib.sha256(original.read_bytes()).hexdigest(),
                "retailer_garment": False, "ai_generated": False})
        music = stage / ("original-" + str(seconds) + "s.wav")
        detected_beats = original_rhythmic_music(music, seconds=seconds)
        manifest["assets"]["test_music"] = {"kind": "audio", "path": music.name,
            "rights": {"commercial_use": True, "license": "owned",
                       "source": "Feature4 original deterministic wave synthesizer",
                       "evidence": "No third-party song or simulated licensed trending track"}}
        sequence = [
            (0, 5, "look01", "A NEW SEASON"),
            (5, 5, "garment01", "THE GARMENT EDIT"),
            (10, 5, "look02", "STYLE IN MOTION"),
            (15, 5, "garment02", "TEXTURE AND DETAIL"),
            (20, 5, "look03", "THE FASHION STORY"),
            (25, 3, "garment01", "CURATED STYLE"),
            (28, 2, None, OUTRO),
        ]
        if seconds == 60:
            # Twelve scenes are the renderer contract maximum. All 60 seconds
            # are real, staged stock reference assets; repeat footage is disclosed,
            # never represented as new Feature5-generated model motion.
            sequence = [
                (0, 5, "look01", "A NEW SEASON"),
                (5, 5, "garment01", "DETAILS WORTH NOTICING"),
                (10, 5, "look02", "THE EDIT IN MOTION"),
                (15, 5, "garment03", "FORM AND TEXTURE"),
                (20, 5, "look03", "LOOKS FOR EVERY DAY"),
                (25, 5, "garment01", "CURATED REFERENCE"),
                (30, 5, "look02", "MOVEMENT AND STYLE"),
                (35, 5, "garment04", "CLOTHING DETAILS"),
                (40, 5, "look01", "THE CITY EDIT"),
                (45, 5, "garment01", "FIND YOUR STYLE"),
                (50, 8, "garment03", "EDITORIAL FASHION STUDY"),
                (58, 2, None, OUTRO),
            ]
        # Auto-find actual PCM onsets; no invented fixed-grid positions.
        sequence = snap_scene_cuts(sequence, detected_beats, duration_seconds=seconds)
        scenes = []
        for idx, (start, dur, aid, headline) in enumerate(sequence):
            scene = {"start": start, "duration": dur, "headline": headline,
                     "transition": "cut" if idx == 0 else "fade",
                     "animation_preset": "subtle_zoom" if aid and aid.startswith("garment") else "fade"}
            if aid:
                scene["asset_id"] = aid
                if aid.startswith("look"):
                    scene["mute_source"] = True
            scenes.append(scene)
        plan = {"version": "rg_video_v2", "shop_id": DEMO_SHOP, "mode": "music_sync",
            "template": "cinematic", "duration_seconds": seconds,
            "output": {"width": 1080, "height": 1920, "fps": 24},
            "brand": {"name": "GARMENT / EDIT", "primary_color": "#C8AB82"},
            "beats": detected_beats, "scenes": scenes, "cta": OUTRO,
            "music_asset_id": "test_music"}
        compiled = compile_composition(plan, manifest, stage, project_dir)
        html = (compiled / "index.html").read_text(encoding="utf-8")
        expected_video = 3 if seconds == 30 else 5
        expected_photos = 3 if seconds == 30 else 6
        expected_final_id = 'id="scene6"' if seconds == 30 else 'id="scene11"'
        if (html.count('class="footage clip"') != expected_video or
                html.count('class="product-photo"') != expected_photos or
                expected_final_id not in html or 'id="cta"' in html or
                'src="https:' in html):
            raise StockShowcaseError("Compiled garment edit failed scene/rights assertions")
        return compiled, {
            "status": "OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY",
            "duration_seconds": seconds,
            "scene_count": len(scenes),
            "reused_stock_video_clips": seconds == 60,
            "source_media": evidence, "license_url": LICENSE_URL,
            "feature2": "Original synthesized rhythmic music and editorial test copy; no viral song/voice",
            "music_beat_source": "Measured offline PCM onset detector, not invented beat grid",
            "measured_beat_timestamps": detected_beats,
            "synced_scene_starts": [scene["start"] for scene in scenes],
            # Offline *editorial titles*, not aligned spoken words. Derived
            # from the actual beat-snapped rendered scene starts, not a fixed grid.
            "editorial_subtitle_kind": "EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO",
            "editorial_subtitle_cues": [
                {"start": round(float(scene["start"]), 3),
                 "duration": min(5.5, round(float(scene["duration"]), 3)),
                 "text": scene["headline"]} for scene in scenes
            ],
            "feature3": "Pexels garment PHOTO proxy; not tenant garment or virtual try-on",
            "feature5": "Pexels HUMAN motion proxy; not model-generated motion",
            "feature7": "Basic timed editing; advanced effects not accepted",
            "model_garment_match_verified": False,
            "retailer_product_identity_verified": False,
            "model_endorsement_claimed": False,
            "human_approved": False, "actual_spoken_voiceover": False,
            "showcase_eligible": False, "commercial_release_eligible": False,
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--seconds", type=int, choices=(30, 60), default=30)
    ap.add_argument("--provenance", required=True)
    mx = ap.add_mutually_exclusive_group(required=True)
    mx.add_argument("--download", action="store_true")
    mx.add_argument("--source-dir")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="rgai-stock-input-") as tmp:
        root = Path(tmp) if args.download else Path(args.source_dir)
        if args.download:
            for _, sid, _, _, urls in CLIPS:
                retrieve_stock(root / (sid + ".mp4"), urls)
            for _, sid, _, _ in (GARMENTS + MINUTE_GARMENTS if args.seconds == 60 else GARMENTS):
                retrieve_garment(root / (sid + ".jpg"), sid)
        proj, report = make_garment_project(root, Path(args.project), seconds=args.seconds)
        proof = Path(args.provenance)
        proof.parent.mkdir(parents=True, exist_ok=True)
        proof.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"project": str(proj), "status": report["status"],
            "sources": len(report["source_media"]), "provenance": str(proof)}))


if __name__ == "__main__":
    try:
        main()
    except (StockShowcaseError, VideoPlanError, BeatEditError, OSError, ValueError) as exc:
        print("FEATURE4 STOCK GARMENT BLOCKED: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
