#!/usr/bin/env python3
"""Validate actually encoded MP4 streams, format, and exact 30s timeline."""
import argparse
import json
import subprocess
from pathlib import Path


def verify_reel(path, width=1080, height=1920):
    path = Path(path)
    data = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    ))
    video = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if len(video) != 1 or len(audio) != 1:
        raise ValueError("Expected exactly one video and one audio stream")
    v, a = video[0], audio[0]
    if (v.get("codec_name") != "h264" or a.get("codec_name") != "aac"
            or v.get("width") != width or v.get("height") != height
            or v.get("pix_fmt") != "yuv420p"):
        raise ValueError("Wrong resolution, pixel format or H.264/AAC codecs")
    duration = float(data["format"]["duration"])
    if abs(duration - 30.0) > 0.12:
        raise ValueError(f"Wrong MP4 duration: {duration}")
    for stream in (v, a):
        if "duration" in stream and abs(float(stream["duration"]) - 30.0) > 0.15:
            raise ValueError(f"Incorrect {stream['codec_type']} stream duration")
    return {"duration_seconds": duration, "width": width, "height": height,
            "video_codec": v["codec_name"], "audio_codec": a["codec_name"],
            "video_pix_fmt": v["pix_fmt"], "size_bytes": path.stat().st_size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    args = parser.parse_args()
    print(json.dumps(verify_reel(args.path, args.width, args.height), indent=2))


if __name__ == "__main__":
    main()
