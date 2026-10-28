"""Run the Feature5 121-frame REAL CPU media smoke in the existing FFmpeg CI job.

The Python contract job may lack ffmpeg and thus conditionally skip this test;
video-engine/ci.sh owns guaranteed FFmpeg setup and discovers tests/media.
Tests use a locally fabricated still image and no Wan/GPU/provider requests.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "ai"))
from test_feature5_f3_to_wan_cpu_e2e import WanFeature3OfflineE2ETests

# unittest discovers the imported TestCase and executes all four cases
# with ffmpeg/Pillow supplied by existing CI. DO NOT skip renderer checks.
