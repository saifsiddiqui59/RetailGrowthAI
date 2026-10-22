#!/usr/bin/env python3
"""Generate original synthetic color cards and a tone, never stock/media downloads."""
import argparse
import json
import subprocess
from pathlib import Path

SYNTH_AUDIO_ID = "synthetic_ci_audio_001"


def run(command):
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)


def generate(campaign_file, directory):
    campaign = json.loads(Path(campaign_file).read_text(encoding="utf-8"))
    day = campaign["days"][0]
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    assets = {}
    colors = ["#b73565", "#177a98", "#d49c27", "#8357b1", "#4a944a"]
    for i, segment in enumerate(day["instagram"]["reel"]["storyboard"]):
        asset_id = segment["asset_id"]
        filename = f"card{i+1}.jpg"
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", f"color=c={colors[i % len(colors)]}:s=360x640",
             "-frames:v", "1", "-q:v", "3", "-update", "1", str(directory / filename)])
        assets[asset_id] = {
            "kind": "image", "path": filename,
            "rights": {"license": "synthetic_test", "source": "video-engine/generate_test_assets.py",
                       "commercial_use": True,
                       "evidence": "Original generated flat color card, no third-party media"},
        }
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=3",
         "-c:a", "pcm_s16le", str(directory / "test-tone.wav")])
    assets[SYNTH_AUDIO_ID] = {
        "kind": "audio", "path": "test-tone.wav",
        "rights": {"license": "synthetic_test", "source": "video-engine/generate_test_assets.py",
                   "commercial_use": True,
                   "evidence": "Original generated sine-wave TEST TONE, NOT production music"},
    }
    # Copy fixture; only the temp copy carries a synthetic audio asset ID.
    day["instagram"]["reel"]["music_asset_id"] = SYNTH_AUDIO_ID
    temp_campaign = directory / "campaign-with-ci-audio.json"
    temp_campaign.write_text(json.dumps(campaign, indent=2), encoding="utf-8")
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({"shop_id": campaign["shop_id"], "assets": assets}, indent=2),
                        encoding="utf-8")
    return temp_campaign, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    campaign, manifest = generate(args.campaign, args.out_dir)
    print(json.dumps({"campaign": str(campaign), "manifest": str(manifest)}))


if __name__ == "__main__":
    main()
