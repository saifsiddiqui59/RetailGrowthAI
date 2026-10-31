"""Feature7 Pexels Full HD *stock demonstration* export using existing AutoBroll.

NOT a new user-facing editor, production Feature4 renderer, licensed customer
garment, signed tenant download, human approval, model inference or paid GPU.
Reuses already-adapted upstream MIT AutoBroll caption plan and FFmpeg's
existing editing filters to produce a REAL 1080x1920 H.264/AAC stock sample.
Source Pexels files remain untouched and result is private until published
through the authenticated coordinator-owned F4 approval/download workflow.

CLI:
 python3 video-engine/feature7/pexels_fullhd_export.py \
   --video /trusted/stock_8581174.mp4 \
   --photo /trusted/stock_5490963.jpg --output /private/demo1080.mp4
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

REPO_ROOT=Path(__file__).resolve().parents[2]
WIDTH=1080
HEIGHT=1920
FPS=30
VIDEO_SECONDS=9
PHOTO_SECONDS=6.5
FADE_SECONDS=.5
EXPECTED_SECONDS=15


class PexelsFullHdError(ValueError):
    pass


def _check_source(source: Path, *, extension: str, maximum_bytes: int):
    if not source.is_absolute() or source.suffix.lower()!=extension:
        raise PexelsFullHdError("Explicit absolute Pexels source path required")
    s=source.lstat()
    if not stat.S_ISREG(s.st_mode) or stat.S_ISLNK(s.st_mode) or not 4096<s.st_size<=maximum_bytes:
        raise PexelsFullHdError("Invalid, linked or oversized Pexels media")
    with source.open("rb") as source_file:
        head=source_file.read(16)
    if extension==".mp4" and head[4:8]!=b"ftyp":
        raise PexelsFullHdError("Actual MP4 signature required")
    if extension==".jpg" and head[:3]!=b"\xff\xd8\xff":
        raise PexelsFullHdError("Actual JPEG signature required")
    digest=hashlib.sha256()
    with source.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exec(command, *, timeout=240):
    try:
        finished=subprocess.run(command,capture_output=True,text=True,
                                timeout=timeout,check=False)
    except subprocess.TimeoutExpired as e:
        raise PexelsFullHdError("Bounded CPU render timed out") from e
    if finished.returncode:
        raise PexelsFullHdError(
            "FFmpeg/AutoBroll test command failed: "+finished.stderr[-2800:])
    return finished.stdout


def _probe(file: Path):
    return json.loads(_exec([
        "ffprobe","-v","error","-show_streams","-show_format",
        "-of","json",str(file)],timeout=30))


def _generate_existing_autobroll_captions():
    # This is the licensed AutoBroll algorithm already vendored as
    # autobroll_semantics.mjs. Do not implement caption word grouping twice.
    script="""
    import {buildPexelsOfflineEditFixture}
      from './video-engine/feature7/pexels_autobroll_fixture.mjs';
    process.stdout.write(JSON.stringify(buildPexelsOfflineEditFixture()));
    """
    try:
        proc=subprocess.run(["node","--input-type=module","-e",script],
          cwd=REPO_ROOT,check=True,text=True,capture_output=True,timeout=15)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
        raise PexelsFullHdError("Existing MIT AutoBroll plan unavailable") from e
    data=json.loads(proc.stdout)
    pages=data["marketing_overlay_pages"]
    if data["voice_transcription_claimed"] or data["real_user_approval"] or not pages:
        raise PexelsFullHdError("Unreviewed stock test cannot claim genuine ASR or approval")
    phrase=" ".join(w["text"] for w in pages[0]["words"])
    if not phrase or len(phrase)>80:
        raise PexelsFullHdError("Invalid AutoBroll display text")
    return phrase


def _filter_textfile(path):
    # Paths are machine-created in an isolated temp dir. Escape the FFmpeg
    # filtergraph delimiters rather than allow external arbitrary text/path.
    return str(path).replace("\\","\\\\").replace(":","\\:").replace("'","\\'").replace(",","\\,")


def render_pexels_fullhd(*, video: Path, photo: Path,
                         output: Path, timeout_seconds: int=240):
    """Real 1080p stock export with private file guard and exact media probe.

    The AAC track is intentionally silent when stock has no verified approved
    soundtrack. We will not create false speech or reuse unlicensed music.
    """
    if not all(shutil.which(x) for x in ("node","ffmpeg","ffprobe")):
        raise PexelsFullHdError("Requires Node, FFmpeg/libx264/drawtext, ffprobe")
    video=Path(video)
    photo=Path(photo)
    output=Path(output)
    if not output.is_absolute() or output.suffix.lower()!=".mp4":
        raise PexelsFullHdError("Explicit absolute destination .mp4 required")
    if output.exists() or output.is_symlink():
        raise PexelsFullHdError("Never overwrite an existing customer video")
    if output.resolve()==video.resolve() or output.resolve()==photo.resolve():
        raise PexelsFullHdError("Never overwrite source media")
    vhash=_check_source(video,extension=".mp4",maximum_bytes=100*1024*1024)
    ihash=_check_source(photo,extension=".jpg",maximum_bytes=24*1024*1024)
    input_probe=_probe(video)
    if not any(z.get("codec_type")=="video" for z in input_probe["streams"]):
        raise PexelsFullHdError("Missing real video source")
    if float(input_probe["format"]["duration"])<VIDEO_SECONDS:
        raise PexelsFullHdError("Real footage is too short for selected sample")
    photo_probe=_probe(photo)
    if not any(z.get("codec_type")=="video" for z in photo_probe["streams"]):
        raise PexelsFullHdError("Missing real Pexels photograph")
    caption=_generate_existing_autobroll_captions()
    output.parent.mkdir(parents=True,exist_ok=True)
    temp_output=output.with_name("."+output.stem+".f7working.mp4")
    if temp_output.exists() or temp_output.is_symlink():
        raise PexelsFullHdError("Unsafe previous partial output; refuse overwrite")
    try:
        with tempfile.TemporaryDirectory(prefix="f7-fullhd-") as dirname:
            work=Path(dirname)
            first=work/"caption.txt"
            second=work/"broll-caption.txt"
            brand=work/"brand.txt"
            first.write_text(caption,encoding="utf-8")
            second.write_text("DISCOVER YOUR STYLE",encoding="utf-8")
            brand.write_text("FASHION EDIT  /  STOCK DEMO",encoding="utf-8")
            caption_ref=_filter_textfile(first)
            second_ref=_filter_textfile(second)
            brand_ref=_filter_textfile(brand)
            # Both video and photo are genuine Pexels pixels. The still has a
            # restrained 4.5-second movement from 1.00x to ~1.045x.
            # Uses existing FFmpeg fps/scale/crop/zoompan/xfade/drawtext,
            # not a new proprietary video editor.
            text_style=(
               "fontcolor=white:fontsize=64:"
               "borderw=2:bordercolor=black@0.3:"
               "x=(w-text_w)/2:y=1660")
            brand_style=(
               "fontcolor=white:fontsize=31:"
               "borderw=1:bordercolor=black@0.35:"
               "x=(w-text_w)/2:y=1515")
            graph=(
              "[0:v]trim=duration=9,setpts=PTS-STARTPTS,"
              "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,"
              "crop=1080:1920,setsar=1,settb=AVTB,"
              "eq=contrast=1.035:saturation=1.06,"
              "format=yuv420p,"
              "drawbox=x=0:y=1450:w=iw:h=470:color=black@0.28:t=fill,"
              f"drawtext=textfile={brand_ref}:{brand_style},"
              f"drawtext=textfile={caption_ref}:{text_style}:"
              "enable='between(t,0.6,8.9)'[v0];"
              "[1:v]scale=1134:2016:force_original_aspect_ratio=increase,"
              "crop=1134:2016,setsar=1,"
              "zoompan=z='min(zoom+0.00033,1.05)':"
              "x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
              "d=1:s=1080x1920:fps=30,"
              "trim=duration=6.5,setpts=PTS-STARTPTS,settb=AVTB,"
              "format=yuv420p,"
              "drawbox=x=0:y=1450:w=iw:h=470:color=black@0.28:t=fill,"
              f"drawtext=textfile={brand_ref}:{brand_style},"
              f"drawtext=textfile={second_ref}:{text_style}[v1];"
              "[v0][v1]xfade=transition=fade:duration=0.5:offset=8.5,"
              "format=yuv420p[v]"
            )
            command=[
              "ffmpeg","-hide_banner","-loglevel","error","-nostdin",
              "-threads","2","-filter_threads","2",
              "-i",str(video),
              "-loop","1","-framerate","30","-t",str(PHOTO_SECONDS),
              "-i",str(photo),
              "-f","lavfi","-i",
              "anullsrc=channel_layout=stereo:sample_rate=48000",
              "-filter_complex",graph,
              "-map","[v]","-map","2:a:0",
              "-c:v","libx264","-preset","veryfast","-crf","20",
              "-profile:v","high","-level:v","4.2",
              "-pix_fmt","yuv420p","-r","30","-g","60",
              "-c:a","aac","-b:a","128k","-ar","48000","-ac","2",
              "-movflags","+faststart","-t",str(EXPECTED_SECONDS),
              "-y",str(temp_output)
            ]
            _exec(command,timeout=timeout_seconds)
            result=_probe(temp_output)
            v=[z for z in result["streams"] if z["codec_type"]=="video"]
            a=[z for z in result["streams"] if z["codec_type"]=="audio"]
            if len(v)!=1 or len(a)!=1 or \
                v[0]["codec_name"]!="h264" or a[0]["codec_name"]!="aac" or \
                (v[0]["width"],v[0]["height"])!=(WIDTH,HEIGHT) or \
                v[0].get("pix_fmt")!="yuv420p" or \
                v[0].get("r_frame_rate")!="30/1" or \
                int(a[0].get("sample_rate",0))!=48000 or \
                not 14.7<float(result["format"]["duration"])<15.3:
                raise PexelsFullHdError("Actual output failed Full HD social export spec")
            if _check_source(video,extension=".mp4",
                             maximum_bytes=100*1024*1024)!=vhash or \
                _check_source(photo,extension=".jpg",
                              maximum_bytes=24*1024*1024)!=ihash:
                raise PexelsFullHdError("Source bytes changed during video export")
            os.chmod(temp_output,0o600)
            os.replace(temp_output,output)
            return {
                "output":str(output),"bytes":output.stat().st_size,
                "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                "width":WIDTH,"height":HEIGHT,"fps":FPS,
                "duration_seconds":float(result["format"]["duration"]),
                "video_codec":"h264","audio_codec":"aac",
                "sample_rate_hz":48000,
                "stock_source_video_sha256":vhash,
                "stock_source_photo_sha256":ihash,
                "marketing_text":"AUTOBROLL_SOURCE_PLAN_ONLY",
                "soundtrack":"SILENT_AAC_PLACEHOLDER_NO_LICENSED_MUSIC",
                "gpu_started":False,"paid_model_calls":0,
                "customer_rights_approved":False,
                "customer_final_download_ready":False,
                "review_required":True
            }
    finally:
        temp_output.unlink(missing_ok=True)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description="CPU-only licensed Pexels Full HD test export")
    cli.add_argument("--video",type=Path,required=True)
    cli.add_argument("--photo",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    options=cli.parse_args()
    receipt=render_pexels_fullhd(video=options.video,photo=options.photo,
                                 output=options.output)
    print(json.dumps(receipt,indent=2))
