#!/usr/bin/env python3
"""Create deterministic rights-safe 30s Feature4 Diwali source package for render CI.

This imports the deliberately small synthetic media fixture used by the real
cross-feature tests; never downloads photos/music or claims true AI model motion.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "media"))
sys.path.insert(0, str(ROOT / "video-engine"))
from test_feature4_cross_feature import CreativeReelTests  # noqa: E402
from creative_contract import compile_creative_reel  # noqa: E402


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python video-engine/demo_feature4_diwali.py /new/empty/project-dir")
    project = Path(sys.argv[1])
    if project.exists() and any(project.iterdir()):
        raise SystemExit("Fixture output directory must be empty")
    fixture = CreativeReelTests(methodName="test_diwali_30s_brand_logo_motion_poster_exact_offer")
    fixture.setUp()
    try:
        fixture.make_assets(with_video=True)
        output = compile_creative_reel(fixture.request, fixture.manifest, fixture.assets, project)
        print(json.dumps({"status": "COMPILED_SYNTHETIC_TEST_ONLY",
                          "duration_seconds": fixture.request["duration_seconds"],
                          "project": str(output), "scene_count": len(fixture.request["scenes"]),
                          "real_ai_motion": False, "commercial_media": False}))
    finally:
        fixture.root_tmp.cleanup()


if __name__ == "__main__":
    main()
