"""Feature2 pinned MIT Creative Director regression gate (offline CPU, no providers).

This runs the ORIGINAL Node assertions extracted from #551 on every mandatory
Python CI pass; otherwise isolated ai-agents/creative-director/tests would not
run in the root Part1 workflow. No model weights, network or Azure required.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

DIRECTOR = Path(__file__).resolve().parents[2] / "ai-agents" / "creative-director"
TESTS = (
    "tests/test-director.js",
    "tests/test-caption-preview.js",
    "tests/test-consumer-compat.js",
    "tests/test-diwali-offline-e2e.js",
    "tests/test-feature3-demo-interoperability.js",
    "tests/test-feature4-feature5-fixture.js",
    "tests/test-handoff-approval.js",
    "tests/test-unified-output.js",
    "upstream/scripts/test-explainer-cues.js",
    "upstream/scripts/test-explainer-plan.js",
    "upstream/scripts/test-explainer-scene.js",
)


@pytest.mark.parametrize("relative_path", TESTS)
def test_pinned_creative_director_original_node_assertions(relative_path: str) -> None:
    node = shutil.which("node")
    assert node is not None, "Node must be installed for the pinned MIT source gate"
    path = DIRECTOR / relative_path
    assert path.is_file(), f"Missing Creative Director test: {relative_path}"
    output = subprocess.run(
        [node, str(path)],
        cwd=DIRECTOR,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        env={"PATH": __import__("os").environ.get("PATH", "")},
    )
    assert output.returncode == 0, (
        f"{relative_path} failed with exit {output.returncode}\n"
        f"STDOUT:\n{output.stdout[-3000:]}\nSTDERR:\n{output.stderr[-3000:]}"
    )
