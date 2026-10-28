"""Execute actual pinned MIT upstream tests and the Feature2 adaptation (no network/AI)."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1] / "creative-director"


@pytest.mark.parametrize("script", [
    "upstream/scripts/test-explainer-plan.js",
    "upstream/scripts/test-explainer-cues.js",
    "upstream/scripts/test-explainer-scene.js",
    "tests/test-director.js",
])
def test_creative_director_node_source(script):
    node = shutil.which("node")
    assert node, "Node 20+ is required to run vendored upstream creative director tests"
    result = subprocess.run(
        [node, str(ROOT / script)],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=75,
        check=False,
    )
    assert result.returncode == 0, script + ":\n" + result.stdout[-12000:]
