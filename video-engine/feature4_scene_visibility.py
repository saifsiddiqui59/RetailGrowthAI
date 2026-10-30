#!/usr/bin/env python3
"""Sample actual encoded scene pixels for sustained empty/black scene defects.

Technical Full-HD / mobile H264-AAC QA only. Cannot determine editorial taste,
product identity, copyright, human anatomy, consent, or unexpected overlays.
Media paths/timecodes come from trusted immutable render provenance, never HTTP.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess

from feature4_private_preview import inspect_mp4, PreviewExportError


class VisibilityProofError(ValueError):
    pass


def _pixel_frame(path, at):
    try:
        result=subprocess.run(
            ["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-protocol_whitelist","file","-ss",f"{at:.3f}","-i",str(path),
             "-map","0:v:0","-frames:v","1",
             "-vf","scale=60:100,format=gray","-f","rawvideo","-"],
            check=True,capture_output=True,timeout=35)
    except (OSError,subprocess.SubprocessError) as exc:
        raise VisibilityProofError("Actual video scene sample cannot be decoded") from exc
    if len(result.stdout)!=6000:
        raise VisibilityProofError("Decoded scene grayscale pixels incomplete")
    values=result.stdout
    return {"time_seconds":round(at,3),
            "mean_luma":round(sum(values)/len(values),2),
            "near_black_fraction":round(sum(v<=12 for v in values)/len(values),4)}


def _sha(path:Path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as media:
        for chunk in iter(lambda:media.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


# Independent full-file decoder detects sustained black holds between sample
# probes without claiming that every sub-second blank frame is impossible.
INTERIOR_SAMPLE_FRACTIONS=(.15,.30,.50,.70,.85)
BLACK_HOLD_MIN_SECONDS=.65
_BLACK_HOLD_RX=re.compile(
    r"black_start:(\\d+(?:\\.\\d+)?)\\s+black_end:(\\d+(?:\\.\\d+)?)"
    r"\\s+black_duration:(\\d+(?:\\.\\d+)?)"
)


def _continuous_black_holds(source, *, seconds):
    """Scan all decoded video frames for >=.65s near-uniform black holds."""
    try:
        run=subprocess.run([
            "ffmpeg","-nostdin","-hide_banner","-loglevel","info",
            "-protocol_whitelist","file","-i",str(source),
            "-map","0:v:0",
            "-vf","blackdetect=d=0.65:pix_th=0.05:pic_th=0.98",
            "-an","-f","null","-",
        ],capture_output=True,text=True,check=True,timeout=160)
    except (OSError,subprocess.SubprocessError) as exc:
        raise VisibilityProofError("Continuous actual encoded black-frame scan failed") from exc
    matches=list(_BLACK_HOLD_RX.finditer(run.stderr))
    if run.stderr.count("black_start:")!=len(matches):
        raise VisibilityProofError("Incomplete black-frame scan evidence")
    holds=[]
    for match in matches:
        start,end,span=map(float,match.groups())
        if (not all(math.isfinite(x) for x in (start,end,span))
                or start<0 or end<=start or end>seconds+.5
                or abs(end-start-span)>.08 or span<BLACK_HOLD_MIN_SECONDS-.09):
            raise VisibilityProofError("Inconsistent continuous black-frame event")
        holds.append((round(start,3),round(end,3),round(span,3)))
    return holds


def verify_scene_visibility(source:Path,*,seconds:int,scenes):
    """Reject sampled near-black frames *inside* every trusted scene window.

    Two 30/70-percent samples could miss a fully black center interval. Five
    interior samples catch that regression; intentional full-black interludes
    must be explicitly edited out before this stock quality acceptance. A
    sampled pass never certifies all frames or human/editorial acceptance.
    """
    if type(seconds) is not int or seconds not in (15,30,60):
        raise VisibilityProofError("Unsupported fixed Reel duration")
    if type(scenes) is not list or not 2<=len(scenes)<=12:
        raise VisibilityProofError("Trusted fixed scene segments required")
    elapsed=0.0
    for scene in scenes:
        if type(scene) is not dict or set(scene)!={"start","duration"}:
            raise VisibilityProofError("Unreviewed scene timing fields")
        start=scene["start"]
        span=scene["duration"]
        if (type(start) not in (int,float) or type(span) not in (int,float)
                or not math.isfinite(start) or not math.isfinite(span)
                or span<.5 or abs(start-elapsed)>.002
                or start<0 or span>seconds):
            raise VisibilityProofError("Noncontiguous or unsupported trusted scene")
        elapsed=round(start+span,3)
    if abs(elapsed-seconds)>.003:
        raise VisibilityProofError("Visual QA requires the complete expected Reel timeline")
    try:
        record=inspect_mp4(Path(source),max_size=80*1024*1024)
    except PreviewExportError as exc:
        raise VisibilityProofError("Visual QA requires valid encoded H264/AAC media") from exc
    if (abs(record["seconds"]-seconds)>.45
            or (record["width"],record["height"]) not in ((540,960),(1080,1920))):
        raise VisibilityProofError("Visual QA source profile differs from approved Reel")
    source_sha=_sha(source)
    checked=[]
    for scene in scenes:
        start,span=scene["start"],scene["duration"]
        # Exact interior fractions are checked again by the final receipt.
        samples=[_pixel_frame(source,start+fraction*span)
                 for fraction in INTERIOR_SAMPLE_FRACTIONS]
        blank=any(x["near_black_fraction"]>=.985 and x["mean_luma"]<=14
                  for x in samples)
        checked.append({"scene_start":start,"duration":span,
                        "samples":samples,"sustained_near_black":blank})
        if blank:
            raise VisibilityProofError(f"Encoded scene at {start}s has a nearly entirely blank/black sample")
    holds=_continuous_black_holds(source,seconds=seconds)
    if _sha(source)!=source_sha:
        raise VisibilityProofError("Encoded Reel bytes changed while scene frames were decoded")
    if holds:
        raise VisibilityProofError("Encoded Reel contains a sustained continuous black hold")
    return {"schema":"feature4_scene_visibility_v3",
            "status":"SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
            "source_sha256":source_sha,
            "sample_fractions":list(INTERIOR_SAMPLE_FRACTIONS),
            "seconds":seconds,"checked_scene_count":len(scenes),
            "checked_scenes":checked,"sustained_near_black_count":0,
            "continuous_full_reel_black_scan":True,
            "continuous_black_hold_threshold_seconds":BLACK_HOLD_MIN_SECONDS,
            "continuous_long_black_holds_count":0,
            "sub_threshold_blank_frames_certified_absent":False,
            "short_blank_frames_excluded_by_sampling":False,
            "unexpected_overlay_absence_verified":False,
            "commercial_release_eligible":False,
            "garment_identity_verified":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True)
    ap.add_argument("--duration",required=True,type=int,choices=(15,30,60))
    ap.add_argument("--provenance",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    source,prov,report=Path(args.source),Path(args.provenance),Path(args.report)
    if (prov.is_symlink() or not prov.is_file() or prov.stat().st_size>250000
            or report.is_symlink() or report.exists() or not report.parent.is_dir()):
        raise VisibilityProofError("Source provenance/report must be a private fresh file")
    p=json.loads(prov.read_text(encoding="utf-8"))
    if (not isinstance(p,dict) or p.get("duration_seconds")!=args.duration
            or p.get("status")!="OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY"
            or p.get("commercial_release_eligible") is not False
            or not isinstance(p.get("scene_windows"),list)):
        raise VisibilityProofError("Expected immutable technical-only scene provenance")
    result=verify_scene_visibility(source,seconds=args.duration,scenes=p["scene_windows"])
    report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"count":result["checked_scene_count"]}))


if __name__=="__main__":
    main()
