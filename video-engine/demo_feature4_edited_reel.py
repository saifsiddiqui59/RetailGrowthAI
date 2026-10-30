#!/usr/bin/env python3
"""Mock-only 30-second FULL EDITOR -> trusted compiler -> real HyperFrames package.

Reuses the actual pinned MIT Timeline Studio JS edit commands via existing
edited_draft() helper; all test images and 'AI motion' are synthesized locally.
Never contacts a provider or downloads retailer/media, never claims real Wan.
OWNER REJECTED this illustrated output as a fashion Reel. CI regression ONLY.
Do NOT present it as a showcase, reference ad, customer demo, or release proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "media"))
sys.path.insert(0, str(ROOT / "video-engine"))
from test_feature4_cross_feature import CreativeReelTests  # noqa: E402
from test_feature4_editor_to_render_contract import edited_draft, duplicated_draft  # noqa: E402
from test_feature4_intent_compiler import pair  # noqa: E402
from feature4_intent_compiler import compile_approved_storyboard  # noqa: E402
from creative_contract import compile_creative_reel  # noqa: E402


def _run_ffmpeg(*args):
    subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)],
        capture_output=True, text=True, check=True, timeout=90,
    )


# An owner's explicit quality rejection is not reversed by codec/CI success.
# Technical regression artifacts stay available internally for deterministic QA.
OWNER_VISUAL_VERDICT = {
    "visual_quality_status": "OWNER_REJECTED",
    "showcase_eligible": False,
    "commercial_release_eligible": False,
    "fixture_purpose": "INTERNAL_CODEC_AND_EDITOR_REGRESSION_ONLY",
}


def make_edited_project(destination: Path, *, width: int = 540, operation: str = "split_reorder") -> dict:
    if width not in (540, 1080):
        raise ValueError("Only reviewed private portrait dimensions supported")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Refusing to replace an existing project/media directory")
    if operation not in ("split_reorder", "duplicate"):
        raise ValueError("Unsupported editor operation")
    original, trusted = pair()
    draft = edited_draft() if operation == "split_reorder" else duplicated_draft()
    source_scene = 0 if operation == "split_reorder" else 1
    if draft["scenes"][source_scene].get("sfx_asset_id") != "musicowned":
        raise ValueError("Expected approved source-audio edit fixture")
    if operation == "duplicate":
        if (len(draft["scenes"]) != 4 or
                [scene["duration"] for scene in draft["scenes"]] != [10, 5, 5, 10] or
                any(draft["scenes"][i].get("trim_start", 0) != 0 for i in (1, 2)) or
                "sfx_asset_id" in draft["scenes"][2]):
            raise ValueError("Untrusted duplicate did not preserve restart/SFX contract")
    draft["output"].update(width=width, height=width * 16 // 9)
    bundle = compile_approved_storyboard(draft, trusted)
    fixture = CreativeReelTests(methodName="test_diwali_30s_brand_logo_motion_poster_exact_offer")
    fixture.setUp()
    try:
        fixture.make_assets(with_video=True)
        # The existing source fixture has exactly 8 seconds of original drawn
        # motion. Extend explicitly to 10 seconds with a repeat for split
        # source in-points 0 and 4. It is NOT AI-generated/real human footage.
        extended = fixture.assets / "mock-only-10s-motion.mp4"
        _run_ffmpeg("-stream_loop", "1", "-i", fixture.assets / "fixture_clip.mp4",
                    "-t", "10", "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", extended)
        music = fixture.assets / "mock-only-owned-music.mp3"
        _run_ffmpeg("-f", "lavfi", "-i",
                    "sine=frequency=196:sample_rate=22050:duration=30",
                    "-c:a", "libmp3lame", "-b:a", "96k", music)
        generated = {
            "photokurti": fixture.assets / "product.png",
            "saleposter": fixture.assets / "sale.png",
            "motionwalk": extended,
            "musicowned": music,
            "storelogo": fixture.assets / "logo.png",
        }
        # A real worker would download exactly these immutable object_ids
        # after DB/JWT/RLS grants. This fixture never uses Internet storage.
        for asset_id, row in bundle["manifest"]["assets"].items():
            shutil.copyfile(generated[asset_id], fixture.assets / row["path"])
        compiled = compile_creative_reel(
            bundle["request"], bundle["manifest"], fixture.assets, destination
        )
        page = (compiled / "index.html").read_text(encoding="utf8")
        # Hard fail if the editor's real SFX/clip source trims or exact offer
        # would be dropped by the renderer. Matches real generated HTML.
        # Split/reorder plays at source inpoints 0 and 4; duplication must
        # restart the same source twice from inpoint 0. The final encoded
        # duplicate parity check independently samples the actual pixels.
        inpoints_ok = (('data-media-start="4"' in page and
                        'data-media-start="0"' in page)
                       if operation == "split_reorder" else
                       'data-media-start="4"' not in page and
                       page.count('data-media-start="0"') >= 2)
        if (page.count('class="footage clip"') != 2 or
                page.count('id="sfx') != 1 or
                not inpoints_ok or
                '20% OFF' not in page or 'Visit Our Store' not in page or
                (operation == "split_reorder" and 'id="intro-logo"' in page) or
                'id="brand-logo"' not in page or
                "90% OFF" in page):
            raise AssertionError("Actual edited HyperFrames composition diverged from approved timeline")
        audit = bundle["lineage"]
        if audit["fallback_events"] or audit["rendered_as"] != "AUTHORIZED_ASSEMBLY":
            raise AssertionError("Fixture cannot disguise premium motion fallback")
        return {
            "status": "EDITED_MOCK_ONLY_NOT_REAL_AI_MEDIA",
            "project": str(compiled), "seconds": 30, "width": width,
            "scenes": len(draft["scenes"]), "asset_ids": sorted(generated),
            "video_clip_count": 2, "approved_sfx_count": 1,
            "source_video_inpoints_seconds": [0, 4] if operation == "split_reorder" else [0, 0],
            "editor_operation": operation,
            "approved_offer": "20% OFF", "real_ai_motion": False,
            "commercial_fashion_realism_accepted": False,
            **OWNER_VISUAL_VERDICT,
        }
    finally:
        fixture.root_tmp.cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--width", type=int, default=540, choices=(540, 1080))
    parser.add_argument("--operation", choices=("split_reorder", "duplicate"),
                        default="split_reorder")
    args = parser.parse_args()
    print(json.dumps(make_edited_project(Path(args.project), width=args.width, operation=args.operation)))


if __name__ == "__main__":
    main()
