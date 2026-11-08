#!/usr/bin/env python3
"""Create deterministic rights-safe 15/30/60s Feature4 Diwali source package for render CI.

This imports the deliberately small synthetic media fixture used by the real
cross-feature tests; never downloads photos/music or claims true AI model motion.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "media"))
sys.path.insert(0, str(ROOT / "video-engine"))
from test_feature4_cross_feature import CreativeReelTests  # noqa: E402
from creative_contract import compile_creative_reel  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Authorized synthetic demo only; never real retail media")
    parser.add_argument("project", help="New empty private output directory")
    parser.add_argument("--seconds", type=int, default=30, choices=(15, 30, 60))
    parser.add_argument("--width", type=int, default=540, choices=(540, 1080))
    parser.add_argument("--with-narration", action="store_true", help="Add a test-only synthetic 863Hz narration channel")
    args = parser.parse_args()
    project = Path(args.project)
    if project.exists() and any(project.iterdir()):
        raise SystemExit("Fixture output directory must be empty")
    fixture = CreativeReelTests(methodName="test_diwali_30s_brand_logo_motion_poster_exact_offer")
    fixture.setUp()
    try:
        fixture.make_assets(with_video=True)
        fixture.request["output"]["width"] = args.width
        fixture.request["output"]["height"] = args.width * 16 // 9
        fixture.request["duration_seconds"] = args.seconds
        if args.seconds == 15:
            # Short-form HD stress fixture with all meaningful editorial roles:
            # opening, source-audio motion, product, exact approved offer, CTA.
            scenes = fixture.request["scenes"]
            sequence = ((scenes[0], 0, 2), (scenes[1], 2, 5),
                        (scenes[2], 7, 3), (scenes[3], 10, 3),
                        (scenes[5], 13, 2))
            fixture.request["scenes"] = []
            for order, (scene, start, length) in enumerate(sequence):
                trimmed = copy.deepcopy(scene)
                trimmed["order"] = order
                trimmed["start_time"] = start
                trimmed["duration"] = length
                fixture.request["scenes"].append(trimmed)
        if args.seconds == 60:
            # One full-minute stress timeline. The only source video is still an
            # original 8s synthetic fixture; no real fashion inference implied.
            duration_by_scene = (5, 7, 10, 14, 14, 10)
            start = 0
            for i, (scene, length) in enumerate(zip(fixture.request["scenes"], duration_by_scene)):
                scene["order"] = i
                scene["start_time"] = start
                scene["duration"] = length
                start += length
        # The synthetic soundtrack/SFX are original deterministic wave synthesis:
        # no third-party songs, sample packs or purported trending-music rights.
        import math
        import struct
        import wave
        with wave.open(str(fixture.assets/"original_demo_music.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            for i in range(args.seconds * 22050):
                t=i/22050
                note=(196,246.94,293.66,392)[int(t/2)%4]
                pulse=0.12 if t % .5 < .065 else 0.0
                sample=int(7000*(.20*math.sin(2*math.pi*note*t)+
                                  .08*math.sin(2*math.pi*note*2*t)+
                                  pulse*math.sin(2*math.pi*90*t))*min(1,t/.6)*min(1,(args.seconds-t)/1))
                w.writeframesraw(struct.pack("<h",max(-32768,min(32767,sample))))
        with wave.open(str(fixture.assets/"original_demo_sfx.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            for i in range(22050):
                t=i/22050
                pulse=int(11000*math.sin(2*math.pi*(210+300*t)*t)*math.exp(-7*t))
                w.writeframesraw(struct.pack("<h",pulse))
        fixture.add("original_demo_music", "original_demo_music.wav", "audio", "retailer")
        fixture.add("original_demo_sfx", "original_demo_sfx.wav", "audio", "retailer")
        fixture.request["music_asset_id"] = "original_demo_music"
        if args.with_narration:
            # A deliberately unmistakable SINUSOIDAL test marker, not human speech.
            # An actual encode/AAC spectral gate proves the F4 narration channel.
            with wave.open(str(fixture.assets/"original_demo_voice.wav"), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(22050)
                for i in range(args.seconds * 22050):
                    t = i / 22050
                    ramp = min(1, t / .2, (args.seconds-t) / .2)
                    sample = int(3800 * math.sin(2 * math.pi * 863 * t) * max(0, ramp))
                    w.writeframesraw(struct.pack("<h", sample))
            fixture.add("original_demo_voice", "original_demo_voice.wav", "audio", "retailer")
            fixture.request["voiceover_asset_id"] = "original_demo_voice"
            fixture.request["voiceover_source"] = "retailer"
            # The test-only sine wave is NOT spoken dialogue. These reviewed
            # timestamped words are just a visual marker for the encoded video.
            fixture.request["script"]["transcript"] = [
                {"start": 0.9, "duration": 0.9, "text": "SUBTITLE CHECK 873"}
            ]
        fixture.request["scenes"][3]["sfx_asset_id"] = "original_demo_sfx"
        output = compile_creative_reel(fixture.request, fixture.manifest, fixture.assets, project)
        print(json.dumps({"status": "COMPILED_SYNTHETIC_TEST_ONLY",
                          "duration_seconds": fixture.request["duration_seconds"],
                          "project": str(output), "scene_count": len(fixture.request["scenes"]),
                          "real_ai_motion": False, "commercial_media": False,
                          "real_voiceover": False, "synthetic_narration_test": args.with_narration,
                          "test_only_caption_proof": args.with_narration,
                          "spoken_word_qa_accepted": False,
                          "showcase_eligible": False}))
    finally:
        fixture.root_tmp.cleanup()


if __name__ == "__main__":
    main()
