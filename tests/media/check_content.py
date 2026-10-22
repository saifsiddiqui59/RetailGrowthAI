#!/usr/bin/env python3
"""Verify different scene colors, crossfade frames, and audible synthetic CI tone."""
import struct
import subprocess
import sys


def sample_rgb(filename, second):
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
           "-ss", str(second), "-i", filename, "-frames:v", "1",
           "-vf", "crop=100:100:(iw-100)/2:(ih-100)/2,scale=1:1,format=rgb24",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    result = subprocess.check_output(cmd, timeout=30)
    if len(result) != 3:
        raise AssertionError("Unable to sample center scene color")
    return result


def check(filename):
    scenes = [sample_rgb(filename, sec) for sec in (3, 15, 27)]
    if len(set(scenes)) != 3:
        raise AssertionError(f"Multi-image content missing: {scenes}")
    fade = sample_rgb(filename, 10.25)
    if fade in scenes:
        raise AssertionError("Expected distinct blended frame at first transition")
    raw = subprocess.check_output(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
         "-ss", "2", "-i", filename, "-t", "0.2", "-map", "0:a:0",
         "-ac", "1", "-ar", "8000", "-c:a", "pcm_s16le", "-f", "s16le", "-"],
        timeout=30,
    )
    if not raw or max(abs(s[0]) for s in struct.iter_unpack("<h", raw)) < 100:
        raise AssertionError("Expected audible audio samples")
    print(f"PASS: distinct scene colors, blended transition and non-silent licensed-test tone; center RGB={scenes}")


if __name__ == "__main__":
    check(sys.argv[1])
