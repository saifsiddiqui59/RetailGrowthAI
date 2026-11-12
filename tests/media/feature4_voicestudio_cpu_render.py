#!/usr/bin/env python3
"""CPU-only F4 narration acceptance: approved synthetic WAV -> HyperFrames -> AAC MP4.

This uses the existing compiler and renderer; it does not synthesize speech or
claim that synthetic fixture approval represents hosted tenant authorization.
"""
import json
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
        fixture.request["script"]["transcript"] = [
            {"start": 0.5, "duration": 2.5, "text": "Approved synthetic caption"},
            {"start": 14.0, "duration": 2.0, "text": "Original fixture narration"},
        ]
        with tempfile.TemporaryDirectory(prefix="f4-voice-cpu-") as temp:
            project = compile_creative_reel(
                fixture.request, fixture.manifest, fixture.assets,
                Path(temp) / "project")
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
            assert abs(float(info["format"]["duration"]) - 30) < 0.3
            assert output.stat().st_size > 10000
            print("PASS: original approved synthetic PCM narration + music/captions encoded by existing HyperFrames CPU renderer")
    finally:
        fixture.root_tmp.cleanup()

if __name__ == "__main__":
    main()
