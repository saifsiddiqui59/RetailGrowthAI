"""PR322 consumer support is checked, NEVER presumed. No GPU call."""
from pathlib import Path
import shutil
import subprocess


def test_current_feature4_motion_consumer_is_explicitly_blocked():
    root = Path(__file__).resolve().parents[1] / "creative-director"
    node = shutil.which("node")
    assert node, "Run actual source tests on Node-equipped CI runner"
    res = subprocess.run([node, str(root / "tests" / "test-consumer-compat.js")],
                         cwd=root, text=True, capture_output=True,
                         check=False, timeout=25)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "no paid dispatch" in res.stdout
