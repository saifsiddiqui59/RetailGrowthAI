#!/usr/bin/env python3
"""Actual local 5-second 1080x1920 H264/AAC silent TECHNICAL b-roll for Feature4.

Source is the original deterministic silhouette PNG, never licensed fashion
footage, real model, music, human speech, or authoritative retailer media.
No API keys, cloud calls, paid resources, external URLs or shop storage writes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

DIR=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True)
    p.add_argument("--render",action="store_true")
    a=p.parse_args()
    output=Path(a.output_dir).resolve()
    if not a.render:
        print(json.dumps({"mode":"PLAN_NO_MEDIA_WRITTEN","source":str(DIR/"generate-synthetic-matte.py"),
                          "target":"1080x1920 H264/AAC 24fps 5s","can_publish":False}))
        return
    ffmpeg=shutil.which("ffmpeg")
    ffprobe=shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Local ffmpeg AND ffprobe required")
    output.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(DIR/"generate-synthetic-matte.py"),
                    "--output-dir",str(output)],check=True,timeout=50,
                    capture_output=True)
    src=output/"feature2-synthetic-first-frame.png"
    dst=output/"feature4-synthetic-broll-5sec.mp4"
    if dst.exists():raise RuntimeError("Refusing to overwrite a previous original MP4")
    args=[ffmpeg,"-hide_banner","-loglevel","error","-n",
          "-loop","1","-framerate","24","-i",str(src),
          "-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=48000",
          "-t","5","-vf","format=yuv420p","-c:v","libx264",
          "-preset","ultrafast","-crf","27","-r","24",
          "-c:a","aac","-b:a","96k","-shortest",
          "-movflags","+faststart",str(dst)]
    subprocess.run(args,check=True,capture_output=True,timeout=90)
    probe=subprocess.run([ffprobe,"-v","error","-show_entries",
                          "stream=codec_name,width,height,r_frame_rate",
                          "-show_entries","format=duration",
                          "-of","json",str(dst)],check=True,capture_output=True,timeout=20)
    info=json.loads(probe.stdout)
    streams=info["streams"]
    video=next(s for s in streams if s.get("codec_name")=="h264")
    assert (video["width"],video["height"],video["r_frame_rate"])==(1080,1920,"24/1")
    assert any(s.get("codec_name")=="aac" for s in streams)
    assert abs(float(info["format"]["duration"])-5)<0.04
    receipt={
      "schema":"retailgrowth.offline-f4-5-technical-video.v1",
      "filename":dst.name,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
      "duration_seconds":5,"dimensions":[1080,1920],
      "video_codec":"h264","audio_codec":"aac",
      "music":"NONE_SILENT_AUDIO","first_frame_file":src.name,
      "rights":"ORIGINAL_LOCAL_GEOMETRIC_TEST_FIXTURE_ONLY",
      "approved_fashion_asset":False,
      "approved_retailer_or_person":False,
      "can_publish":False,
    }
    (output/"feature4-video-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
if __name__=="__main__":main()
