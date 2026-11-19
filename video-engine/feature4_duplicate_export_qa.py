#!/usr/bin/env python3
"""CPU-only encoded duplicate proof for one original, owner-rejected 30s fixture.

Uses the *same* JS Timeline Studio duplicate -> trusted v2 compiler ->
HyperFrames encoded media as the existing split/reorder render. Compares
two duplicated real-video interior samples at equal relative time, checks
temporal change and scene separation. This cannot certify exact original
motion frame identity, art direction, commercial media rights or human QA.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

from feature4_edited_export_qa import (
    EditorExportProofError, _source_fingerprint, _luma_delta,
)
from feature4_private_preview import PreviewExportError, inspect_mp4


class DuplicateExportProofError(EditorExportProofError):
    pass


def _center_frame(source: Path, sec: float) -> bytes:
    """Inspect center video pixels; avoid fixed lower-third glass and UI text."""
    try:
        result = subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file",
            "-ss", str(sec), "-i", str(source), "-map", "0:v:0",
            "-vf", "crop=iw*0.6:ih*0.42:iw*0.2:ih*0.16,scale=72:96,format=gray",
            "-frames:v", "1", "-f", "rawvideo", "-"
        ], check=True, capture_output=True, timeout=35)
    except (OSError, subprocess.SubprocessError) as exc:
        raise DuplicateExportProofError("Cannot decode duplicate preview video frame") from exc
    if len(result.stdout) != 72 * 96:
        raise DuplicateExportProofError("Truncated duplicate scene video frame")
    return result.stdout


def verify_mock_duplicate_output(source: Path, *, expected_sha256: str) -> dict:
    """Verify synthetic VIDEO duplicate 10..15 -> 15..20 encoded output.

    A one-video/two-asset duplicate must preserve 0s source inpoint twice,
    produce matching *moving* center pixels at offset 1.5 and 3.5, and retain
    distinct 0..10 product and 20..30 offer scenes. Thresholds here apply
    only to the frozen private synthetic fixture, never arbitrary footage.
    """
    if type(expected_sha256) is not str or re.fullmatch(
        r"[0-9a-f]{64}", expected_sha256
    ) is None:
        raise DuplicateExportProofError("Trusted final render SHA256 required")
    source = Path(source)
    try:
        fingerprint = _source_fingerprint(source)
    except EditorExportProofError as exc:
        raise DuplicateExportProofError("Unsafe encoded duplicate MP4 source") from exc
    if fingerprint[0] != expected_sha256:
        raise DuplicateExportProofError("Encoded duplicate source SHA differs from render")
    try:
        metadata = inspect_mp4(source, max_size=80 * 1024 * 1024)
    except PreviewExportError as exc:
        raise DuplicateExportProofError("Expected private H264/AAC encoded output") from exc
    if ((metadata["width"], metadata["height"]) != (540, 960)
            or abs(metadata["seconds"] - 30) > .45):
        raise DuplicateExportProofError("Expected verified 30s 540p duplicate export")

    # Two SOURCE-INPOINT-0 clips are present at timeline [10,15) and [15,20).
    # Compare equal relative positions, and require the underlying video to
    # change within each clip; a repeated still cannot pass as motion.
    times = (2.0, 11.5, 13.5, 16.5, 18.5, 24.0)
    photo, first_early, first_late, copy_early, copy_late, offer = [
        _center_frame(source, sec) for sec in times
    ]
    try:
        unchanged = _source_fingerprint(source) == fingerprint
    except EditorExportProofError as exc:
        raise DuplicateExportProofError("Encoded duplicate MP4 changed during QA") from exc
    if not unchanged:
        raise DuplicateExportProofError("Encoded duplicate MP4 changed during QA")
    early_pair = _luma_delta(first_early, copy_early)
    late_pair = _luma_delta(first_late, copy_late)
    temporal = min(_luma_delta(first_early, first_late),
                   _luma_delta(copy_early, copy_late))
    scene_distance = min(
        _luma_delta(first_early, photo), _luma_delta(first_early, offer),
        _luma_delta(copy_early, photo), _luma_delta(copy_early, offer),
        _luma_delta(photo, offer),
    )
    # Only original generated asset: JPEG/codec differences and scene-index
    # overlays can cause slight disagreement even when source timestamps
    # match. This does NOT prove frame-exact media-source inpoints.
    if not (early_pair <= 3.5 and late_pair <= 3.5
            and temporal >= .5 and scene_distance >= 8):
        raise DuplicateExportProofError(
            "Encoded duplicate clip frames, actual motion or scene distinction regressed")
    return {
        "schema": "feature4_duplicate_encoded_mock_parity_v1",
        "status": "ENCODED_DUPLICATE_MOCK_TECHNICALLY_VERIFIED",
        "source_sha256": fingerprint[0],
        "profile": "30s/540x960/H264/AAC",
        "editor_operation": "duplicate",
        "video_scene_starts_seconds": [10, 15],
        "source_video_inpoints_seconds": [0, 0],
        "sample_times_seconds": list(times),
        "first_duplicate_luma_delta": round(early_pair, 3),
        "second_duplicate_luma_delta": round(late_pair, 3),
        "minimum_video_temporal_luma_delta": round(temporal, 3),
        "minimum_video_vs_photo_luma_delta": round(scene_distance, 3),
        "exact_source_frame_verified": False,
        "human_visual_approval": False,
        "commercial_release_eligible": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    report = Path(args.report)
    if (report.exists() or report.is_symlink()
            or report.suffix.lower() != ".json"
            or not report.parent.is_dir() or report.parent.is_symlink()):
        raise DuplicateExportProofError("Expected new private JSON duplicate report")
    result = verify_mock_duplicate_output(
        Path(args.source), expected_sha256=args.expected_sha256)
    with report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "commercial_release_eligible": False}))


if __name__ == "__main__":
    main()
