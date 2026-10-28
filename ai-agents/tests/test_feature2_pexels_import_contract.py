"""Official Pexels SDK import plan executes without key, downloads or paid calls."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1] / "test-fixtures" / "clothing-shop-pexels"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node unavailable")
def test_official_pexels_sdk_import_plan_is_usable_for_other_features():
    script = ROOT / "import-official-pexels.mjs"
    syntax = subprocess.run(["node", "--check", str(script)], capture_output=True,
                            text=True, timeout=20)
    assert syntax.returncode == 0, syntax.stderr
    run = subprocess.run(["node", str(script), "--plan"], capture_output=True,
                         text=True, timeout=20)
    assert run.returncode == 0, run.stderr
    plan = json.loads(run.stdout)
    assert plan["kind"] == "DISCOVERY_PLAN_NOT_MEDIA"
    assert len(plan["items"]) == 4
    assert {row["media_type"] for row in plan["items"]} == {"IMAGE", "VIDEO"}
    assert plan["can_publish"] is False
    assert plan["original_media_downloaded"] is False
