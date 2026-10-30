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


def tone_amplitude(mp4, t, hz=480, sample_rate=8000, window_seconds=1.0):
    # Windowed PCM checks use actual AAC-decoded bytes, never HTML declarations.
    if not 0.10 <= window_seconds <= 1.0:
        raise ValueError("Unsupported bounded AAC inspection window")
    data = subprocess.check_output(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(t), "-i", str(mp4),
         "-t", str(window_seconds), "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "-"],
        timeout=25,
    )
    samples = array.array("h")
    samples.frombytes(data)
    if sys.byteorder != "little":
        samples.byteswap()
    if len(samples) < int(sample_rate * window_seconds * .5):
        raise AssertionError("No usable decoded audio segment")
    re_part = im_part = 0.0
    for i, val in enumerate(samples):
        angle = 2*math.pi*hz*i/sample_rate
        re_part += val * math.cos(angle)
        im_part -= val * math.sin(angle)
    return math.hypot(re_part, im_part) / len(samples)



def soundtrack_bed_magnitude(mp4, t):
    """Synthetic soundtrack plays 293.66Hz at both 5s and 12s in this test."""
    return tone_amplitude(mp4,t,hz=293.66)


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
    # Audibly duck the APPROVED bed only during source-audio scenes.
    music_during_source=soundtrack_bed_magnitude(clip,5)
    music_after_source=soundtrack_bed_magnitude(clip,12)
    if not (music_after_source > 45 and
            music_after_source > 2.2 * max(1, music_during_source)):
        raise AssertionError("Approved soundtrack was not ducked during source clip")
    if not (with_motion >= 30 and with_motion > 8 * max(1,without_motion)):
        raise AssertionError("Feature #5 fixture source audio lost in the composition mix")
    return {"intro_logo_luma_stddev": round(hero_luma, 2),
            "scene_delta": [round(n,2) for n in changes],
            "source_tone_amplitude": round(with_motion,2),
            "nonclip_tone_amplitude": round(without_motion,2),
            "bed_ducked_source_amplitude": round(music_during_source, 2),
            "bed_nonvoice_amplitude": round(music_after_source, 2)}


def check_fullres_artifact(media_dir):
    """Gate actual 1080p scene diversity; never equate synthetic visuals with fashion realism."""
    root = Path(media_dir)
    expected = (1, 6, 13, 18, 28)
    pictures = []
    for time in expected:
        p = root / f"feature4-fullres-frame-{time}.jpg"
        with Image.open(p) as image:
            picture = image.convert("RGB")
        if picture.size != (1080, 1920):
            raise AssertionError(f"Incorrect full-resolution screenshot at {time}s")
        variation = ImageStat.Stat(picture.convert("L")).stddev[0]
        if variation < 12:
            raise AssertionError(f"1080p scene at {time}s visually blank ({variation:.1f})")
        pictures.append(picture.resize((270, 480)))
    scene_changes = [
        ImageStat.Stat(ImageChops.difference(a, b).convert("L")).mean[0]
        for a, b in zip(pictures, pictures[1:])
    ]
    if sum(d > 8 for d in scene_changes) < 3:
        raise AssertionError(f"1080p scenes not distinguishable: {scene_changes}")
    # Distinct fixed 863Hz fixture tone must survive the actual HyperFrames
    # mix → AAC encode → MP4 demux → PCM decode. This does NOT test speech.
    encoded_mp4 = root / "feature4-30s-1080p-hyperframes-synthetic.mp4"
    narr_mid = tone_amplitude(encoded_mp4, 13, hz=863)
    narr_end = tone_amplitude(encoded_mp4, 27, hz=863)
    if not (narr_mid > 55 and narr_end > 55):
        raise AssertionError("Approved synthetic narration track missing in final AAC")
    # F4-07: inspect actual encoded AAC near the start and end of the Reel,
    # not merely the renderer's data-fade-* attributes. The fixture's own
    # deterministic 0.2s envelope contributes to these measurements, so this
    # checks the combined exported envelope, NOT renderer-only automation.
    narr_fade_in = tone_amplitude(encoded_mp4, 0, hz=863, window_seconds=.12)
    narr_fade_out = tone_amplitude(encoded_mp4, 29.88, hz=863, window_seconds=.12)
    if not (narr_mid > 1.7 * max(1, narr_fade_in, narr_fade_out)):
        raise AssertionError("Encoded synthetic narration did not preserve audible start/end fades")
    # Synthetic subtitle is visible at t=1.2s and absent at t=0.6/2.2s.
    # Compare the same first-scene, fixed region to detect true time-gated
    # pixels in the FINAL decoded MP4, without OCR or claiming spoken QA.
    before = Image.open(root / "feature4-caption-frame-0.6.png").convert("RGB")
    during = Image.open(root / "feature4-caption-frame-1.2.png").convert("RGB")
    after = Image.open(root / "feature4-caption-frame-2.2.png").convert("RGB")
    if any(frame.size != (1080, 1920) for frame in (before, during, after)):
        raise AssertionError("Incorrect decoded caption proof frame size")
    caption_region = (180, 1060, 900, 1360)
    def frame_delta(a, b):
        return ImageStat.Stat(ImageChops.difference(
            a.crop(caption_region), b.crop(caption_region)).convert("L")).mean[0]
    visible_delta = frame_delta(before, during)
    baseline_delta = frame_delta(before, after)
    if not (visible_delta > 4.0 and visible_delta > 2.5 * max(1.0, baseline_delta)):
        raise AssertionError(
            f"Timed subtitle not visible in encoded 1080p MP4: "
            f"caption_delta={visible_delta:.2f}, same_scene_baseline={baseline_delta:.2f}"
        )
    return {"synthetic_caption_encoded_pixel_delta": round(visible_delta, 2),
            "same_scene_caption_off_delta": round(baseline_delta, 2),
            "caption_semantic_alignment_accepted": False,
            "synthetic_narration_mid_amplitude": round(narr_mid, 2),
            "synthetic_narration_end_amplitude": round(narr_end, 2),
            "synthetic_narration_fade_in_amplitude": round(narr_fade_in, 2),
            "synthetic_narration_fade_out_amplitude": round(narr_fade_out, 2),
            "encoded_aac_envelope_checked_not_spoken_quality": True,
            "spoken_word_qa_accepted": False,
            "resolution": "1080x1920", "frames_sampled": len(pictures),
            "scene_deltas": [round(x, 2) for x in scene_changes],
            "commercial_fashion_realism_accepted": False}


if __name__=="__main__":
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--fullres"):
        raise SystemExit("usage: python check_feature4_output.py <ci-artifacts-folder> [--fullres]")
    if len(sys.argv) == 3:
        print("PASS: actual 1080p visual diversity only", check_fullres_artifact(sys.argv[1]))
    else:
        print("PASS: real HyperFrames frame diversity + synthetic source audio", check_artifact(sys.argv[1]))
