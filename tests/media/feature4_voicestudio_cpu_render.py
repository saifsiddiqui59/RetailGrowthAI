#!/usr/bin/env python3
"""CPU-only F4 narration acceptance: approved synthetic WAV -> HyperFrames -> AAC MP4.

This uses the existing compiler and renderer; it does not synthesize speech or
claim that synthetic fixture approval represents hosted tenant authorization.
"""
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "video-engine"), str(ROOT / "tests" / "media")]
from creative_contract import compile_creative_reel
from test_feature4_narration import NarrationMediaTests

def main():
    fixture = NarrationMediaTests().fixture()
    try:
        # The shared narration fixture defaults to the 540x960 preview preset.
        # Exercise the approved final-export preset before asserting Full HD.
        fixture.request["output"].update({"width": 1080, "height": 1920, "fps": 24})
        fixture.request["script"]["transcript"] = [
            {"start": 0.5, "duration": 2.5, "text": "Approved synthetic caption"},
            {"start": 14.0, "duration": 2.0, "text": "Original fixture narration"},
        ]
        with tempfile.TemporaryDirectory(prefix="f4-voice-cpu-") as temp:
            project = compile_creative_reel(
                fixture.request, fixture.manifest, fixture.assets,
                Path(temp) / "project")
            page = (Path(project) / "index.html").read_text(encoding="utf-8")
            assert page.count('id="approved-voiceover"') == 1, "Narration track missing or duplicated"
            assert page.count('class="clip spoken-caption"') == 2, "Approved caption cues missing"
            assert 'data-track-index="5" data-volume="0.12"' in page, "Music not ducked"
            output = Path(temp) / "reel.mp4"
            subprocess.run(
                ["node", str(ROOT / "video-engine" / "hyperframes" / "render.mjs"),
                 str(project), str(output)],
                check=True, timeout=420)
            info = json.loads(subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_streams", "-show_format",
                 "-of", "json", str(output)], text=True, timeout=30))
            streams = info["streams"]
            video = [s for s in streams if s.get("codec_type") == "video"]
            audio = [s for s in streams if s.get("codec_type") == "audio"]
            assert len(video) == len(audio) == 1, "Expected one video and one audio track"
            assert video[0]["codec_name"] == "h264" and audio[0]["codec_name"] == "aac"
            assert (int(video[0]["width"]), int(video[0]["height"])) == (1080, 1920), "Reel is not vertical Full HD"
            assert video[0].get("pix_fmt") == "yuv420p", "Reel pixel format is not broadly playable"
            assert video[0].get("r_frame_rate") == "24/1", "Reel frame rate drifted from approved 24 fps"
            assert abs(float(audio[0].get("duration", info["format"]["duration"])) - 30) < 0.3, "AAC track duration mismatches Reel"
            assert abs(float(info["format"]["duration"]) - 30) < 0.3
            assert output.stat().st_size > 10000
            # Decode actual AAC, not merely inspect an audio-stream header.
            # Synthetic 350 Hz narration + 196 Hz music must produce nonzero
            # PCM. This does not assert transcript/speech alignment.
            pcm = subprocess.check_output(
                ["ffmpeg", "-nostdin", "-v", "error", "-i", str(output),
                 "-map", "0:a:0", "-t", "1", "-ac", "1", "-ar", "8000",
                 "-f", "s16le", "-acodec", "pcm_s16le", "-"],
                timeout=45)
            assert len(pcm) >= 8000 * 2, "Encoded narration is truncated"
            samples = struct.unpack("<" + "h" * (len(pcm) // 2), pcm)
            rms = math.sqrt(sum(x * x for x in samples) / len(samples))
            assert rms > 100, "Encoded narration/music unexpectedly silent"
            # Verify the original narration tone is actually present in decoded
            # AAC, rather than passing because the music bed alone is audible.
            # The synthetic fixture uses 350 Hz narration and 196 Hz music.
            # Integer-Hz, one-second windows make this a deterministic DFT bin.
            def tone_magnitude(samples, frequency):
                n = len(samples)
                return abs(sum(
                    sample * complex(
                        math.cos(-2 * math.pi * frequency * i / 8000),
                        math.sin(-2 * math.pi * frequency * i / 8000))
                    for i, sample in enumerate(samples)
                )) / n

            narration_level = tone_magnitude(samples, 350)
            bed_level = tone_magnitude(samples, 196)
            assert narration_level > 100, "Approved 350 Hz narration missing from AAC"
            assert bed_level > 5, "Licensed 196 Hz music bed missing from AAC"
            assert narration_level > bed_level, "Music bed is not ducked below narration"
            # Confirm audio survives into the second half of the Reel; a first-
            # second-only PCM probe would miss truncated narration or a mixer
            # that silently drops the approved voiceover after the opening.
            late_pcm = subprocess.check_output(
                ["ffmpeg", "-nostdin", "-v", "error", "-ss", "20",
                 "-i", str(output), "-map", "0:a:0", "-t", "1",
                 "-ac", "1", "-ar", "8000", "-f", "s16le",
                 "-acodec", "pcm_s16le", "-"], timeout=45)
            assert len(late_pcm) >= 8000 * 2, "Late narration audio is truncated"
            late_samples = struct.unpack("<" + "h" * (len(late_pcm) // 2), late_pcm)
            late_rms = math.sqrt(sum(x * x for x in late_samples) / len(late_samples))
            assert late_rms > 100, "Encoded narration/music silent at 20 seconds"
            late_narration = tone_magnitude(late_samples, 350)
            late_bed = tone_magnitude(late_samples, 196)
            assert late_narration > 100, "Approved narration disappeared before 20 seconds"
            assert late_bed > 5, "Music bed disappeared before 20 seconds"
            assert late_narration > late_bed, "Late music masks approved narration"
            # End-of-reel verification catches an AAC muxer that truncates the
            # approved track after the mid-reel probe, despite valid duration
            # metadata. Use the same synthetic frequency separation at 29s.
            tail_pcm = subprocess.check_output(
                ["ffmpeg", "-nostdin", "-v", "error", "-ss", "29",
                 "-i", str(output), "-map", "0:a:0", "-t", "0.8",
                 "-ac", "1", "-ar", "8000", "-f", "s16le",
                 "-acodec", "pcm_s16le", "-"], timeout=45)
            assert len(tail_pcm) >= 6000 * 2, "Final AAC narration is truncated"
            tail_samples = struct.unpack("<" + "h" * (len(tail_pcm) // 2), tail_pcm)
            assert tone_magnitude(tail_samples, 350) > 100, "Approved narration missing at Reel end"
            assert tone_magnitude(tail_samples, 196) > 5, "Music bed missing at Reel end"
            assert tone_magnitude(tail_samples, 350) > tone_magnitude(tail_samples, 196), "End music masks narration"
            # Decode the actual encoded portrait frames at the beginning and
            # near the end. Container metadata alone cannot prove that the
            # video track is decodable for the full approved narration span.
            for second in (1, 15, 29):
                frame = subprocess.check_output(
                    ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(second),
                     "-i", str(output), "-map", "0:v:0", "-frames:v", "1",
                     "-vf", "scale=32:56,format=gray", "-f", "rawvideo", "-"],
                    timeout=45)
                assert len(frame) == 32 * 56, (
                    f"Missing or undecodable portrait video frame at {second}s")
                assert max(frame) - min(frame) >= 5, (
                    f"Near-uniform encoded video frame at {second}s")
            print("PASS: original approved synthetic PCM narration + music/captions encoded by existing HyperFrames CPU renderer")
    finally:
        fixture.root_tmp.cleanup()

if __name__ == "__main__":
    main()
