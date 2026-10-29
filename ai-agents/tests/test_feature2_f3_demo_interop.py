"""Run original-feature3 byte pin checker with no network or user account."""
import subprocess
import shutil
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]/"creative-director"
@pytest.mark.skipif(shutil.which("node") is None,reason="Node not installed")
def test_f2_f3_pinned_demo_handoff_negative_and_integrity_checks():
    v=subprocess.run([shutil.which("node"),str(ROOT/"tests"/"test-feature3-demo-interoperability.js")],
        capture_output=True,text=True,timeout=45)
    assert v.returncode==0,v.stderr[-1500:]
    assert "verification and fake authorization denial PASS" in v.stdout
@pytest.mark.skipif(shutil.which("node") is None,reason="Node not installed")
def test_f2_f3_only_full_original_pack_acceptance():
    v=subprocess.run([shutil.which("node"),str(ROOT/"feature3-demo-interoperability.js"),
        "30","/nonexistent-retailgrowth-original-f3-pack"],capture_output=True,text=True,timeout=20)
    assert v.returncode==2
    assert "FEATURE2_F3_DEMO_INPUT_INVALID" in v.stderr
    assert not v.stdout.strip()
