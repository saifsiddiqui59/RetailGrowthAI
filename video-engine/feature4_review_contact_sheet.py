#!/usr/bin/env python3
"""Private stock-video reviewer contact sheet: actual encoded frames, not a mock.

This source-only helper is not a media grant, object-storage publisher, human
quality judgment, garment identifier or commercial-use authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageDraw
from feature4_private_preview import inspect_mp4, PreviewExportError

class ContactSheetError(ValueError):
    pass

WIDTH,HEIGHT=180,320
COLUMNS=3
FRAME_COUNT=12

def _sha(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()

TOP=64
CELL_H=346

def _frame(source, at):
    try:
        data=subprocess.run([
            "ffmpeg","-nostdin","-v","error","-protocol_whitelist","file",
            "-ss",f"{at:.3f}","-i",str(source),"-map","0:v:0",
            "-vf",f"scale={WIDTH}:{HEIGHT}:flags=bicubic,setsar=1",
            "-frames:v","1","-pix_fmt","rgb24","-f","rawvideo","pipe:1",
        ],check=True,capture_output=True,timeout=35).stdout
    except (OSError,subprocess.SubprocessError) as exc:
        raise ContactSheetError("Could not extract verified encoded video frame") from exc
    if len(data)!=WIDTH*HEIGHT*3:
        raise ContactSheetError("FFmpeg frame data truncated or invalid")
    return Image.frombytes("RGB",(WIDTH,HEIGHT),data)

def render_contact_sheet(source: Path, output: Path, *, seconds: int):
    if type(seconds) is not int or seconds not in (15,30,60):
        raise ContactSheetError("Expected bounded verified 15/30/60-second video")
    source,output=Path(source),Path(output)
    if output.suffix.lower() not in (".jpg",".jpeg") or output.is_symlink() or output.exists():
        raise ContactSheetError("Contact sheet must have a fresh local JPEG destination")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ContactSheetError("Contact sheet must remain in a pre-existing private directory")
    try:
        media=inspect_mp4(source,max_size=80*1024*1024)
    except PreviewExportError as exc:
        raise ContactSheetError("Source not validated H264/AAC portrait MP4") from exc
    if abs(media["seconds"]-seconds)>.45:
        raise ContactSheetError("Source duration mismatch")
    source_sha=_sha(source)
    canvas=Image.new("RGB",(WIDTH*COLUMNS,TOP+CELL_H*4),(16,21,28))
    draw=ImageDraw.Draw(canvas)
    draw.text((10,12),"F4 STOCK QA / NOT A RETAILER AD",fill=(250,211,145))
    draw.text((10,35),f"ENCODED FRAMES  |  {seconds}s  |  NO PRODUCT MATCH CLAIM",fill=(200,205,210))
    frames=[]
    fingerprints=[]
    possible_repeats=[]
    for i in range(FRAME_COUNT):
        at=round((i+.5)*seconds/FRAME_COUNT,3)
        image=_frame(source,at)
        x=(i%COLUMNS)*WIDTH
        y=TOP+(i//COLUMNS)*CELL_H
        canvas.paste(image,(x,y))
        draw.text((x+6,y+323),f"{at:05.2f}s / STOCK",fill=(236,236,236))
        # Compare source picture content, not the overlaid timestamp/banner.
        # Wide separation avoids false positives within an intended shot.
        signature=image.crop((0,0,WIDTH,250)).convert("L").resize((24,32)).tobytes()
        for old_time,old_signature in fingerprints:
            if at-old_time < seconds/3:
                continue
            difference=sum(abs(a-b) for a,b in zip(signature,old_signature))/len(signature)
            if difference < 4.0:
                possible_repeats.append({"earlier_seconds":old_time,
                                         "later_seconds":at,
                                         "mean_luma_delta":round(difference,2)})
        fingerprints.append((at,signature))
        frames.append(at)
    if _sha(source)!=source_sha:
        raise ContactSheetError("Encoded Reel changed while contact-sheet frames were decoded")
    temp=None
    try:
        with tempfile.NamedTemporaryFile(prefix=".f4-review-",suffix=".jpg",
                                         dir=str(output.parent),delete=False) as tmp:
            temp=Path(tmp.name)
        canvas.save(temp,format="JPEG",quality=85,optimize=True)
        # No overwrite, even if another reviewer writer won a race.
        os.link(temp,output)
        temp.unlink()
        temp=None
    except (OSError,ValueError) as exc:
        raise ContactSheetError("Could not securely write private reviewer JPEG") from exc
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    if _sha(source)!=source_sha:
        output.unlink(missing_ok=True)  # This invocation created the fresh hard-link.
        raise ContactSheetError("Encoded Reel changed during private contact-sheet export")
    sha=_sha(output)
    return {"status":"ENCODED_REVIEW_CONTACT_SHEET_NOT_APPROVAL",
            "source_sha256":source_sha,
            "contact_sheet_sha256":sha,"duration_seconds":seconds,
            "frames_seconds":frames,"frame_count":FRAME_COUNT,
            "possible_repeated_shot_pairs":possible_repeats[:20],
            "repetition_warning":bool(possible_repeats),
            "visual_diversity_accepted":False,
            "commercial_release_eligible":False,
            "owner_visual_approval":False,"garment_identity_verified":False}

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True)
    ap.add_argument("--duration",required=True,type=int,choices=(15,30,60))
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    proof=render_contact_sheet(Path(args.source),Path(args.output),seconds=args.duration)
    print(proof)
