#!/usr/bin/env python3
"""Measure motion in an already rendered and locally verified stock test MP4.

This is a technical regression gate for *moving pixels* only: it cannot infer
identity, garment fidelity, consent, reviewer approval or commercial quality.
Never derive motion samples from untrusted user/browser timestamp inputs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

from feature4_private_preview import inspect_mp4, PreviewExportError


class MotionProofError(ValueError):
    pass


def _frame(path: Path, sec: float):
    try:
        data = subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error",
             "-protocol_whitelist", "file",
             "-ss", str(sec), "-i", str(path),
             "-map", "0:v:0", "-vf", "scale=90:160,format=gray",
             "-frames:v", "1", "-f", "rawvideo", "-"],
            capture_output=True, check=True, timeout=35).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise MotionProofError("Could not decode requested local video frame") from exc
    if len(data) != 90 * 160:
        raise MotionProofError("Encoded footage frame not fully decoded")
    return data


def verify_moving_scenes(mp4: Path, *, seconds: int, scene_starts,
                         sample_offset=.8, separation=.7, threshold=5.0):
    """Measure mean absolute luma differences of reviewed moving scene windows.

    The caller (reviewer/CI) provides fixed expected moving-scene start times.
    It must NOT auto-trust browser clip tags or arbitrary timestamps.
    """
    if type(seconds) is not int or seconds not in (15, 30, 60):
        raise MotionProofError("Only verified Reel duration allowed")
    if (type(scene_starts) not in (tuple,list) or
            not 1 <= len(scene_starts) <= 10 or
            any(type(s) not in (int,float) or not math.isfinite(s)
                for s in scene_starts)):
        raise MotionProofError("Expected explicit trusted moving scene timecodes")
    if (scene_starts != sorted(set(scene_starts)) or
            any(s < 0 or s + sample_offset + separation >= seconds - .2
                for s in scene_starts)):
        raise MotionProofError("Invalid or repeated moving-scene ranges")
    if (type(sample_offset) not in (int,float) or not .5 <= sample_offset <= 1.2
            or type(separation) not in (int,float) or not .3 <= separation <= .9
            or type(threshold) not in (int,float) or not 3 <= threshold <= 18):
        raise MotionProofError("Unsafe motion verification configuration")
    try:
        source = inspect_mp4(Path(mp4), max_size=80*1024*1024)
    except PreviewExportError as exc:
        raise MotionProofError("Rendered MP4 failed trusted codec/input preflight") from exc
    if abs(source["seconds"]-seconds) > .45:
        raise MotionProofError("Encoded video duration not as expected")
    measured = []
    for start in scene_starts:
        a=_frame(Path(mp4),round(start+sample_offset,3))
        b=_frame(Path(mp4),round(start+sample_offset+separation,3))
        average=sum(abs(x-y) for x,y in zip(a,b))/len(a)
        measured.append({"expected_scene_start":start,"luma_difference":round(average,2)})
        if average < threshold:
            raise MotionProofError(
                f"Expected moving scene near {start}s is frozen or insufficiently distinct")
    return {
        "status":"MOVING_PIXELS_VERIFIED_NOT_CONTENT_APPROVAL",
        "duration_seconds":seconds,
        "source_sha256":hashlib.sha256(Path(mp4).read_bytes()).hexdigest(),
        "threshold_luma_difference":threshold,
        "checked_moving_scenes":measured,
        "garment_fidelity_verified":False,
        "human_model_identity_verified":False,
        "spoken_caption_semantics_verified":False,
        "commercial_release_eligible":False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True)
    ap.add_argument("--duration",type=int,choices=(15,30,60),required=True)
    ap.add_argument("--moving-starts",type=float,nargs="+",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    result=verify_moving_scenes(Path(args.source), seconds=args.duration,
                                scene_starts=args.moving_starts)
    path=Path(args.report)
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise MotionProofError("Expected new private QA report")
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
                      "motion_luma":result["checked_moving_scenes"]}))


if __name__=="__main__":
    main()
