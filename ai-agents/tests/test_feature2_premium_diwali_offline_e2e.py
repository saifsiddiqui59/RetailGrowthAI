"""End-to-end OFFLINE Feature2 test using actual vendored upstream MIT director.

The scenario is an original synthetic premium Diwali kurti brand, 20% test
offer and private *mock* first frame. It does not call a real provider or
generate images, audio or video. Keeps GPU off until genuine F2 readiness.
"""
from pathlib import Path
import json
import shutil
import subprocess

import pytest


def test_premium_fashion_creative_director_end_to_end_without_paid_gpu():
    node = shutil.which("node")
    assert node, "Node22 runtime needed to run real pinned upstream JS tests"
    root = Path(__file__).resolve().parents[1] / "creative-director"
    result = subprocess.run(
        [node, str(root / "tests" / "test-diwali-offline-e2e.js")],
        cwd=root,
        text=True, capture_output=True, check=False, timeout=45,
    )
    assert result.returncode == 0, result.stdout[-9000:] + "\n" + result.stderr[-9000:]
    plans = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    assert [x["reel_duration_seconds"] for x in plans] == [15, 30, 60]
    assert [x["motion_shots"] for x in plans] == [3, 6, 12]
    assert all(x["offline_preview"] == "PASS" and x["gpu"] == "OFF"
               and x["paid_inference"] == 0 and x["production_ready"] is False
               for x in plans)
    assert "no media rendered" in result.stdout
