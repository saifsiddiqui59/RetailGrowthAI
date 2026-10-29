"""Actual pinned MIT director generates F4/F5 input packets with no GPU or grants."""
from pathlib import Path
import json
import shutil
import subprocess
import pytest
ROOT=Path(__file__).resolve().parents[1]/"creative-director"
@pytest.mark.parametrize("seconds", [15,30,60])
def test_actual_source_export_for_f4_f5(seconds):
    node=shutil.which("node")
    assert node
    run=subprocess.run([node,str(ROOT/"export-feature4-feature5-fixture.js"),str(seconds)],
                       capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stderr[-1800:]
    o=json.loads(run.stdout)
    assert len(o["feature4"]["timeline"])==seconds//5
    assert len(o["feature5"]["clip_requests"])==seconds//5
    assert o["feature5"]["can_run_paid_motion"] is False
    assert o["review"]["can_publish"] is False
    assert o["source_media"]["approved_feature3_frame_present"] is False
    assert all(x["first_frame_sha256"] is None for x in o["feature5"]["clip_requests"])
def test_actual_node_safety_checks():
    node=shutil.which("node")
    assert node
    p=subprocess.run([node,str(ROOT/"tests"/"test-feature4-feature5-fixture.js")],
                     capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr[-1800:]
    assert "export PASS" in p.stdout
