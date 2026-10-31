#!/usr/bin/env python3
"""Feature #4 real-footage concept. This is NOT proof of retailer garment identity.

Downloads only specific Pexels videos on explicit --download; never sources
media from a browser-provided URL or authorizes tenant media. Used ONLY for
separate consent-free stock editing QA, not a retailer product endorsement.
The authoritative Feature4 compiler/render pipeline remains unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import wave

from professional import compile_composition, VideoPlanError

DEMO_SHOP="11111111-1111-4111-8111-111111111111"
LICENSE_URL="https://www.pexels.com/license/"
# Provenance verified against the public Pexels pages on 2026-10-28.
# HD first; last source's official download redirects to UHD if HD unavailable.
CLIPS=(
    ("look01", "8151871", "RDNE Stock project",
     "https://www.pexels.com/video/a-fashionable-woman-modeling-while-walking-8151871/",
     ("https://videos.pexels.com/video-files/8151871/8151871-hd_1920_1080_30fps.mp4",)),
    ("look02", "8249911", "RDNE Stock project",
     "https://www.pexels.com/video/woman-walking-while-looks-at-camera-8249911/",
     ("https://videos.pexels.com/video-files/8249911/8249911-hd_1920_1080_25fps.mp4",)),
    ("look03", "7626927", "Mikhail Nilov",
     "https://www.pexels.com/video/woman-wearing-black-dress-7626927/",
     ("https://videos.pexels.com/video-files/7626927/7626927-hd_1080_1920_25fps.mp4",)),
)
MAX_MEDIA_BYTES=155_000_000

class StockShowcaseError(ValueError):
    pass

class TrustedHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u=urllib.parse.urlsplit(newurl)
        if u.scheme!="https" or u.hostname!="videos.pexels.com":
            raise StockShowcaseError("Stock download redirected outside verified Pexels video host")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def retrieve_stock(destination:Path, urls):
    """Only fetch fixed allowlisted URLs; bounded size; atomic output."""
    destination.parent.mkdir(parents=True,exist_ok=True)
    opener=urllib.request.build_opener(TrustedHostRedirect)
    error=None
    for source_url in urls:
        u=urllib.parse.urlsplit(source_url)
        if u.scheme!="https" or u.hostname!="videos.pexels.com":
            raise StockShowcaseError("Unapproved stock URL")
        partial=destination.with_suffix(".download")
        try:
            with opener.open(urllib.request.Request(source_url,headers={
                "User-Agent":"RetailGrowthAI-Feature4-StockEditingQA/1.0",
                "Accept":"video/mp4,*/*;q=0.8",
            }),timeout=55) as response, partial.open("wb") as output:
                if urllib.parse.urlsplit(response.url).hostname!="videos.pexels.com":
                    raise StockShowcaseError("Stock media origin changed")
                if response.headers.get("Content-Type","").split(";")[0].strip().lower() not in ("video/mp4","application/octet-stream","binary/octet-stream"):
                    raise StockShowcaseError("Stock response was not an MP4")
                size=0
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk: break
                    size+=len(chunk)
                    if size>MAX_MEDIA_BYTES: raise StockShowcaseError("Stock media size cap exceeded")
                    output.write(chunk)
            if size<50_000: raise StockShowcaseError("Downloaded stock clip too small")
            partial.replace(destination)
            return {"download_url":source_url,"sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),"size_bytes":size}
        except (OSError,urllib.error.URLError,StockShowcaseError) as exc:
            error=exc
            partial.unlink(missing_ok=True)
    raise StockShowcaseError("Verified Pexels stock video could not be downloaded: "+type(error).__name__)

def check_input(source:Path):
    if not source.is_file() or source.is_symlink() or source.suffix.lower()!=".mp4" or not 50_000<=source.stat().st_size<=MAX_MEDIA_BYTES:
        raise StockShowcaseError("Stock clip missing, unsafe or oversized")
    try:
        d=json.loads(subprocess.check_output(["ffprobe","-v","error","-protocol_whitelist","file",
             "-show_streams","-show_format","-of","json",str(source)],text=True,timeout=25))
        v=[s for s in d["streams"] if s.get("codec_type")=="video"]
        seconds=float(d["format"]["duration"])
        if len(v)!=1 or v[0].get("codec_name") not in ("h264","hevc","vp9","mpeg4") or seconds<5.05 or seconds>180:
            raise StockShowcaseError("Stock clip codec or length unsuitable")
        return {"seconds":round(seconds,3),"width":int(v[0]["width"]),"height":int(v[0]["height"])}
    except (OSError,KeyError,ValueError,subprocess.SubprocessError) as exc:
        if isinstance(exc,StockShowcaseError): raise
        raise StockShowcaseError("Stock media failed FFprobe verification") from exc

def original_music(path:Path,seconds=15):
    """Original generated low-volume ambient synth, not licensed third-party music or TTS."""
    rate=22050
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        from array import array
        result=array("h")
        for i in range(seconds*rate):
            t=i/rate
            # Quiet warm chord progression, soft bass and rhythmic transient.
            chord=((174.61,220,261.63),(196,246.94,293.66),(164.81,220,261.63))[int(t//5)%3]
            envelope=min(1,t/.6,max(0,(seconds-t)/.7))
            chord_wave=sum(math.sin(2*math.pi*f*t) for f in chord)/3
            bass=math.sin(2*math.pi*chord[0]/2*t)
            kick=math.sin(2*math.pi*(70+35*(t%1))*t)*math.exp(-25*(t%1))
            value=int(11500*envelope*(.31*chord_wave+.19*bass+.18*kick))
            result.append(max(-32768,min(32767,value)))
        wav.writeframes(result.tobytes())

def normalize_for_renderer(source:Path,destination:Path,width=1080,height=1920):
    """Remove sparse GOP seeking risks and make a short, exact, private 9:16 clip.

    Preserves the original source untouched. No interpolation, identity edit,
    third-party plugin, color style transfer or source-audio carrythrough.
    """
    if not 100<=width<=1080 or not 160<=height<=1920:
        raise StockShowcaseError("Unsafe normalized portrait resolution")
    check_input(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise StockShowcaseError("Refusing to replace a staged source file")
    # Re-encode only the first 5.25s used by the fixed 5s edit; 24fps / 1s GOP.
    # Background source tracks are deliberately muted in reviewed concept plan.
    cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-i",str(source),"-map","0:v:0","-an","-sn","-dn",
         "-t","5.25","-vf",f"fps=24,scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1",
         "-c:v","libx264","-preset","veryfast","-crf","21",
         "-g","24","-keyint_min","24","-sc_threshold","0",
         "-pix_fmt","yuv420p","-movflags","+faststart","-map_metadata","-1",
         "-threads","2",str(destination)]
    try:
        subprocess.run(cmd,check=True,capture_output=True,timeout=110)
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        destination.unlink(missing_ok=True)
        raise StockShowcaseError("Could not stage fixed-GOP portrait source") from exc
    info=check_input(destination)
    if (info["width"],info["height"])!=(width,height) or not 5.15<=info["seconds"]<=5.35:
        raise StockShowcaseError("Normalized source duration/resolution mismatch")
    return info


def make_project(source_dir:Path,project_dir:Path,allow_staged_test=False):
    """Compile immutable, re-encoded Pexels clips using the same trusted renderer."""
    if project_dir.exists() and any(project_dir.iterdir()):
        raise StockShowcaseError("Refusing to overwrite non-empty project")
    source_dir=Path(source_dir).resolve(strict=True)
    # No writes to third-party originals or owner/user-upload media.
    with tempfile.TemporaryDirectory(prefix="feature4-private-normalized-") as work:
        stage=Path(work)
        sources={}
        for asset_id,id,creator,url,urls in CLIPS:
            original=source_dir/(id+".mp4")
            measured=check_input(original)
            normalized=stage/(id+".mp4")
            normalized_info=normalize_for_renderer(original,normalized)
            sources[asset_id]=(original,normalized,id,creator,url,measured,normalized_info)
        music=stage/"original-concept-bed.wav"
        original_music(music)
        manifest={"shop_id":DEMO_SHOP,"assets":{}}
        for aid,(original,normalized,id,creator,url,measured,normalized_info) in sources.items():
            manifest["assets"][aid]={"kind":"video","path":normalized.name,"rights":{
                "commercial_use":True,"license":"royalty_free",
                "source":url,
                "evidence":"Pexels License; stock footage only, no model endorsement; source ID "+id}}
        manifest["assets"]["original_music"]={"kind":"audio","path":music.name,
            "rights":{"commercial_use":True,"license":"owned",
                      "source":"RetailGrowthAI original wave-synthesized demo soundtrack",
                      "evidence":"Original deterministic composition; no third-party music"}}
        plan={"version":"rg_video_v2","shop_id":DEMO_SHOP,"mode":"media",
              "template":"cinematic","duration_seconds":15,
              "output":{"width":1080,"height":1920,"fps":24},
              "brand":{"name":"FASHION EDIT","primary_color":"#C8AB82"},
              "scenes":[
                  {"start":0,"duration":5,"asset_id":"look01",
                   "headline":"THE FASHION EDIT","transition":"cut","animation_preset":"fade","mute_source":True},
                  {"start":5,"duration":5,"asset_id":"look02",
                   "headline":"STYLE IN MOTION","transition":"fade","animation_preset":"subtle_zoom","mute_source":True},
                  {"start":10,"duration":3,"asset_id":"look03",
                   "headline":"A NEW PERSPECTIVE","transition":"slide","animation_preset":"fade","mute_source":True},
                  {"start":13,"duration":2,
                   "headline":"STOCK FASHION EDIT - NOT A RETAILER AD",
                   "transition":"fade","animation_preset":"fade"},
              ],
              "cta":"STOCK FASHION EDIT - NOT A RETAILER AD",
              "music_asset_id":"original_music"}
        compiled=compile_composition(plan,manifest,stage,project_dir)
        page=(compiled/"index.html").read_text(encoding="utf-8")
        if (page.count('class="footage clip"')!=3 or
                "THE FASHION EDIT" not in page or
                "STOCK FASHION EDIT - NOT A RETAILER AD" not in page or
                'id="scene3"' not in page or 'id="cta"' in page):
            raise StockShowcaseError("Stock render diverged from approved face-safe concept endcard")
        provenance={"status":"STOCK_CONCEPT_TECHNICAL_DEMO_ONLY",
                    "approval":"PENDING_HUMAN_REVIEW",
                    "showcase_eligible":False,"commercial_release_eligible":False,
                    "photoreal_human_shown":"actual stock videos; no AI-generation claim",
                    "retailer_garment_identity_verified":False,
                    "model_endorsement_claimed":False,"real_spoken_voiceover":False,
                    "source_license":LICENSE_URL,
                    "normalization":"24fps H264 1s keyframes / 1080x1920 center crop; audio muted",
                    "source_media":[{"source_id":id,"creator":creator,"page_url":url,
                        "downloaded_asset_sha256":hashlib.sha256(original.read_bytes()).hexdigest(),
                        "render_stage_sha256":hashlib.sha256(normalized.read_bytes()).hexdigest(),
                        "measured_source":measured,"measured_stage":normalized_info}
                        for original,normalized,id,creator,url,measured,normalized_info in sources.values()],
                    "music":"Original local wave synthesizer, not licensed commercial music"}
        return compiled,provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True,help="Empty project dir")
    parser.add_argument("--source-dir",help="Existing locally staged Pexels MP4s")
    parser.add_argument("--download",action="store_true",help="Fetch only the three Pexels stock IDs")
    parser.add_argument("--provenance",required=True,help="JSON evidence destination")
    args=parser.parse_args()
    if not args.download and not args.source_dir: parser.error("Specify --source-dir or --download")
    if args.download and args.source_dir: parser.error("Choose one staging mode")
    with tempfile.TemporaryDirectory(prefix="feature4-stock-") as temp:
        stage=Path(temp) if args.download else Path(args.source_dir)
        if args.download:
            for aid,id,creator,url,urls in CLIPS:
                retrieve_stock(stage/(id+".mp4"),urls)
        project,report=make_project(stage,Path(args.project))
        dest=Path(args.provenance)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"project":str(project),"status":report["status"],
                          "sources":len(report["source_media"]),
                          "showcase_eligible":False,"provenance":str(dest)}))

if __name__=="__main__":
    try:main()
    except (StockShowcaseError,VideoPlanError,OSError,ValueError) as exc:
        print("FEATURE4 STOCK DEMO BLOCKED: "+str(exc),file=sys.stderr)
        raise SystemExit(2)
