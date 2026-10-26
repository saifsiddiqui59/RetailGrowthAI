#!/usr/bin/env python3
"""Offline visual diversity and synthetic source-audio preservation gates.

These low-level checks supplement, not replace, human visual and speech QA.
The deterministic 480Hz source-clip tone comes from our own test fixture.
"""
import array
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

FRAME_TIMES = (1, 6, 13, 18, 24, 28)


def tone_amplitude(mp4, t, hz=480, sample_rate=8000):
    data = subprocess.check_output(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(t), "-i", str(mp4),
         "-t", "1", "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "-"],
        timeout=25,
    )
    samples = array.array("h")
    samples.frombytes(data)
    if sys.byteorder != "little":
        samples.byteswap()
    if len(samples) < sample_rate // 2:
        raise AssertionError("No usable decoded audio segment")
    re_part = im_part = 0.0
    for i, val in enumerate(samples):
        angle = 2*math.pi*hz*i/sample_rate
        re_part += val * math.cos(angle)
        im_part -= val * math.sin(angle)
    return math.hypot(re_part, im_part) / len(samples)


def check_artifact(media_dir):
    root = Path(media_dir)
    clip = root/"feature4-30s-hyperframes-synthetic.mp4"
    if not clip.is_file():
        raise AssertionError("Missing REAL HyperFrames MP4")
    frames=[]
    for t in FRAME_TIMES:
        p=root/f"feature4-frame-{t}.jpg"
        im=Image.open(p).convert("RGB")
        if im.size != (540,960):
            raise AssertionError("Wrong preview frame size")
        if ImageStat.Stat(im.convert("L")).stddev[0] < 15:
            raise AssertionError(f"Frame {t}s is blank or visually near-uniform")
        frames.append(im)
    # Catch invisible hero logo in the real six-scene synthetic video.
    intro_region = frames[0].crop((155, 170, 385, 540)).convert("L")
    hero_luma = ImageStat.Stat(intro_region).stddev[0]
    if hero_luma < 14:
        raise AssertionError(
            f"Opening brand hero is invisible or near-uniform ({hero_luma:.1f})"
        )
    changes=[
        ImageStat.Stat(ImageChops.difference(a,b).convert("L")).mean[0]
        for a,b in zip(frames,frames[1:])
    ]
    if sum(d > 9 for d in changes) < 4:
        raise AssertionError("Scene changes missing or near-identical")
    with_motion=tone_amplitude(clip,5)
    without_motion=tone_amplitude(clip,12)
    if not (with_motion >= 30 and with_motion > 8 * max(1,without_motion)):
        raise AssertionError("Feature #5 fixture source audio lost in the composition mix")
    return {"intro_logo_luma_stddev": round(hero_luma, 2),
            "scene_delta": [round(n,2) for n in changes],
            "source_tone_amplitude": round(with_motion,2),
            "nonclip_tone_amplitude": round(without_motion,2)}


if __name__=="__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python check_feature4_output.py <ci-artifacts-folder>")
    print("PASS: real HyperFrames frame diversity + synthetic source audio", check_artifact(sys.argv[1]))
