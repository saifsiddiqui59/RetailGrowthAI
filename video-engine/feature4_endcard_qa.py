#!/usr/bin/env python3
"""Feature4 real encoded 60s *stock* outro edit regression, never ad approval.

Detect whether the actual decoded ~57.5s frame genuinely differs from the
preceding clothing-rack shot. This is a visual change heuristic only: it does
not recognize lettering, guarantee legibility, clear model rights or authorize
any tenant. Run on the PRIVATE original render before audio mastering.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

from feature4_private_preview import inspect_mp4, PreviewExportError


class EndcardProofError(ValueError):
    pass


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pixels(path, at):
    try:
        process = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-protocol_whitelist", "file", "-ss", f"{at:.3f}", "-i",
             str(path), "-map", "0:v:0", "-frames:v", "1", "-vf",
             "scale=120:212,format=gray", "-f", "rawvideo", "-"],
            check=True, capture_output=True, timeout=40)
    except (OSError, subprocess.SubprocessError) as exc:
        raise EndcardProofError("Encoded endcard frame cannot be decoded") from exc
    if len(process.stdout) != 120 * 212:
        raise EndcardProofError("Encoded endcard frame has invalid pixel length")
    return process.stdout


def _difference(left, right):
    return round(sum(abs(a-b) for a, b in zip(left, right)) / len(left), 3)


def verify_stock_endcard(source: Path, provenance: Path):
    """Bounded three decoded-frame check for the exact private 60s stock QA.

    Refuses a continued garment-rack shot at 57.5s; does not pretend to
    identify text or measure every video frame. Last 5s must be a separate
    reviewed technical-only scene, never a retailer promotion.
    """
    source, provenance = Path(source), Path(provenance)
    if (source.is_symlink() or not source.is_file()
            or source.suffix.lower() != ".mp4"
            or provenance.is_symlink() or not provenance.is_file()
            or provenance.suffix.lower() != ".json"
            or provenance.stat().st_size > 250_000):
        raise EndcardProofError("Unsafe private original or provenance input")
    try:
        record = json.loads(provenance.read_text(encoding="utf-8"))
        media = inspect_mp4(source, max_size=80*1024*1024)
    except (ValueError, OSError, UnicodeDecodeError, PreviewExportError) as exc:
        raise EndcardProofError("Invalid encoded source or private QA provenance") from exc
    if not isinstance(record, dict):
        raise EndcardProofError("Provenance must be a trusted object")
    scenes = record.get("scene_windows")
    cues = record.get("editorial_subtitle_cues")
    if (record.get("status") != "OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY"
            or record.get("duration_seconds") != 60
            or record.get("commercial_release_eligible") is not False
            or record.get("human_approved") is not False
            or record.get("actual_spoken_voiceover") is not False
            or not isinstance(scenes, list) or len(scenes) != 12
            or not isinstance(cues, list) or len(cues) != 12
            or record.get("editorial_subtitle_kind") != "EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO"
            or not isinstance(scenes[-1], dict)
            or not isinstance(scenes[-2], dict)
            or type(scenes[-1].get("start")) not in (int, float)
            or type(scenes[-1].get("duration")) not in (int, float)
            or type(scenes[-2].get("start")) not in (int, float)
            or type(scenes[-2].get("duration")) not in (int, float)
            or not isinstance(cues[-1], dict)
            or type(cues[-1].get("start")) not in (int, float)
            or not math.isfinite(cues[-1]["start"])
            or not math.isfinite(scenes[-1]["start"])
            or not math.isfinite(scenes[-1]["duration"])
            or not 54.5 <= scenes[-1]["start"] <= 55.5
            or scenes[-1]["duration"] < 4.5
            or abs(scenes[-1]["start"] + scenes[-1]["duration"] - 60) > .003
            or abs(scenes[-2]["start"] + scenes[-2]["duration"]-scenes[-1]["start"]) > .003
            or cues[-1].get("text") != "STOCK GARMENT CONCEPT - NOT A RETAILER AD"
            or abs(cues[-1].get("start", -100)-scenes[-1]["start"]) > .003):
        raise EndcardProofError("The 60s stock outro must be a distinct 55-60s disclaimer")
    if (abs(media["seconds"] - 60) > .45
            or (media["width"], media["height"]) not in ((540, 960), (1080, 1920))):
        raise EndcardProofError("Unexpected encoded source profile")
    source_sha = _sha(source)
    before = _pixels(source, 53.0)
    middle = _pixels(source, 57.5)
    tail = _pixels(source, 59.3)
    if _sha(source) != source_sha:
        raise EndcardProofError("Source video mutated during endcard pixel verification")
    visual_change = _difference(before, middle)
    endcard_stability = _difference(middle, tail)
    # Full-screen card must no longer look like the previously repeated rack.
    # This is a regression threshold for the stock fixture, not aesthetic QA.
    if visual_change < 25:
        raise EndcardProofError("Encoded 55s endcard resembles held garment-rack shot")
    if endcard_stability > 22:
        raise EndcardProofError("Encoded 55s endcard unexpectedly changes after reveal")
    return {
        "schema": "feature4_stock_endcard_pixel_v1",
        "status": "ENCODED_OUTRO_VISUALLY_CHANGED_NOT_TEXT_APPROVAL",
        "source_sha256": source_sha, "duration_seconds": 60,
        "outro_start_seconds": scenes[-1]["start"],
        "pre_outro_sample_seconds": 53.0,
        "outro_sample_seconds": 57.5,
        "outro_tail_sample_seconds": 59.3,
        "scene_delta_mean_luma": visual_change,
        "outro_stability_delta_mean_luma": endcard_stability,
        "commercial_release_eligible": False, "human_visual_approval": False,
        "retailer_garment_verified": False, "text_legibility_verified": False,
        "spoken_caption_sync_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    destination = Path(args.report)
    if (destination.exists() or destination.is_symlink()
            or destination.suffix.lower() != ".json"
            or destination.parent.is_symlink() or not destination.parent.is_dir()):
        raise EndcardProofError("Private endcard report must be a fresh JSON file")
    report = verify_stock_endcard(Path(args.source), Path(args.provenance))
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"],
                      "scene_delta": report["scene_delta_mean_luma"],
                      "owner_approved": False}))


if __name__ == "__main__":
    main()
