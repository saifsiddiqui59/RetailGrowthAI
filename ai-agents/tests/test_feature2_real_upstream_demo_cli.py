"""Real original Open Creative Director executable synthetic preview, no GPU or paid API."""
import json
import shutil
import subprocess
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1] / "creative-director/scripts/offline-demo.js"

@pytest.mark.parametrize("duration,scenes", [(15,3),(30,6),(60,12)])
def test_usable_source_only_director_preview(duration,scenes):
    node=shutil.which("node")
    assert node
    summary=subprocess.run(
        [node,str(SCRIPT),str(duration),"--summary"],
        capture_output=True,text=True,timeout=25,check=False,
    )
    assert summary.returncode==0,summary.stderr
    x=json.loads(summary.stdout)
    assert x["scenes"]==x["motion_shots"]==scenes
    assert x["duration_seconds"]==duration
    assert x["upstream"]=="Kuble-Lab/open-creative-director"
    assert x["caption_source_original_upstream"].endswith("explainer-cues.js")
    assert x["caption_lines"]>=1
    assert x["gpu_enabled"] is False and x["billed_calls"]==0
    assert x["video_rendered"] is False
    assert x["model_generated"] is False
    assert x["can_publish"] is False
    assert x["rights_evidence_real"] is False
    assert "bundle" not in x
    full=subprocess.run([node,str(SCRIPT),str(duration),"--json"],
                        capture_output=True,text=True,timeout=25,check=False)
    assert full.returncode==0,full.stderr
    detail=json.loads(full.stdout)
    assert detail["bundle"]["approval_record"]["can_publish"] is False
    assert detail["bundle"]["approval_record"]["plan_sha256"]==x["editorial_plan_sha256"]
    assert detail["caption_preview"]["state"]=="WORD_TIMES_PREVIEW_PENDING_ORIGINAL_AUDIO_WAVEFORM_REVIEW"

@pytest.mark.parametrize("arguments", [["14","--summary"],["15","--exec"],["15","--json","--upload"],[]])
def test_demo_rejects_any_billable_or_invalid_argument(arguments):
    node=shutil.which("node")
    r=subprocess.run([node,str(SCRIPT),*arguments],
                     capture_output=True,text=True,timeout=15,check=False)
    assert r.returncode==2
    assert not r.stdout
    assert "Usage:" in r.stderr
