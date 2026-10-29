"""Run original-feature3 byte pin checker with no network or user account."""
import subprocess
import shutil
import json
import sys
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


# Genuine ORIGINAL OpenVTO bytes, not stand-in pictures: F3's existing
# pinned Git revision, Git blob sha1, image decoder and SHA-256 are required.
# The runner performs read-only public upstream downloads with no model
# inference, Azure/Supabase calls, user photo or commercial approval.
@pytest.fixture(scope="module")
def actual_pinned_feature3_originals(tmp_path_factory):
    root=Path(__file__).resolve().parents[2]
    folder=tmp_path_factory.mktemp("f2-f3-real-openvto")
    cli=root/"poster-engine"/"feature3_demo_inputs_v1.py"
    assert cli.is_file(), "Existing F3 original media generator missing from integrated main"
    result=subprocess.run([sys.executable,str(cli),"--output-dir",str(folder)],
                          capture_output=True,text=True,timeout=110,check=False)
    assert result.returncode==0,("Pinned OpenVTO test media unavailable; "
                                 "not a verified positive F3 handoff: "+result.stderr[-1800:])
    receipt=json.loads(result.stdout)
    assert receipt["status"]=="VERIFIED_SYNTHETIC_DEMO_ONLY"
    assert receipt["customer_publish_approved"] is False
    assert set(receipt["files"])=={"model_posture.jpg","model_avatar.png","garment_front.jpg"}
    return folder

@pytest.mark.parametrize("seconds",[15,30,60])
def test_actual_director_export_consumes_genuine_feature3_original_bytes(
        actual_pinned_feature3_originals,seconds):
    node=shutil.which("node")
    assert node, "Node runtime required for actual compiled exporter acceptance"
    command=[node,str(ROOT/"feature3-demo-interoperability.js"),
             str(seconds),str(actual_pinned_feature3_originals)]
    process=subprocess.run(command,capture_output=True,text=True,timeout=40)
    assert process.returncode==0,process.stderr[-1800:]
    packet=json.loads(process.stdout)
    assert packet["duration_seconds"]==seconds
    assert packet["feature3"]["original_bytes_rechecked"] is True
    assert packet["feature3"]["rights"]=="MIT_TEST_DEMO_ONLY"
    assert packet["feature3"]["garment_worn_by_model_verified"] is False
    assert len(packet["feature3"]["assets"])==3
    assert len(packet["feature4"]["timeline"])==seconds//5
    assert len(packet["feature5"]["clip_requests"])==seconds//5
    assert packet["feature4"]["render_approved"] is False
    assert packet["feature5"]["provider_call_permitted"] is False
    assert packet["feature5"]["cost_reserved"] is False
    assert packet["approval"]["customer_publish_approved"] is False
    sha=packet["feature3"]["assets"]["model_posture.jpg"]["sha256"]
    assert packet["feature5"]["demo_first_frame_sha256"]==sha
    assert packet["feature5"]["actual_private_first_frame_id"] is None
    assert len(sha)==64
