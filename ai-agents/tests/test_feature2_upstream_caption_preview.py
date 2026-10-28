"""Feature2 reuses the REAL vendored MIT Kuble director caption source offline."""
from pathlib import Path
import json
import shutil
import subprocess


def test_pinned_kuble_source_is_called_for_all_retail_reel_captions():
    node = shutil.which("node")
    assert node, "Pinned MIT Open Creative Director code requires Node in source CI"
    root = Path(__file__).resolve().parents[1] / "creative-director"
    proc = subprocess.run(
        [node, str(root / "tests/test-caption-preview.js")],
        cwd=root, capture_output=True, text=True, timeout=30, check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    rows = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
    assert [x["duration"] for x in rows] == [15, 30, 60]
    assert all(x["lines"] >= 1 and x["wordCount"] >= 1
               and x["upstream"] == "Kuble-Lab"
               and x["state"] == "PREVIEW" and x["gpu"] == "OFF"
               for x in rows)
    assert "upstream" in proc.stdout.lower()
