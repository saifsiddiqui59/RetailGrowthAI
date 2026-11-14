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


# The scene's interior is sampled, not its transition edges. This is *not* a
# continuous no-black-frame certification: an intervening flash may be missed.
INTERIOR_SAMPLE_FRACTIONS=(.15,.30,.50,.70,.85)


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
    if _sha(source)!=source_sha:
        raise VisibilityProofError("Encoded Reel bytes changed while scene frames were decoded")
    return {"schema":"feature4_scene_visibility_v2",
            "status":"SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
            "source_sha256":source_sha,
            "sample_fractions":list(INTERIOR_SAMPLE_FRACTIONS),
            "seconds":seconds,"checked_scene_count":len(scenes),
            "checked_scenes":checked,"sustained_near_black_count":0,
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
