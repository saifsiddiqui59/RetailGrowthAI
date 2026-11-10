"""Feature2 cross-feature draft approval source tests (zero AI/cloud calls)."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_feature2_to_feature4_handoff_is_source_review_only():
    root=Path(__file__).resolve().parents[1] / "creative-director"
    node=shutil.which("node")
    assert node, "Node is necessary for actual MIT source tests"
    r=subprocess.run([node,str(root / "tests" / "test-handoff-approval.js")],
                     cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     timeout=20,check=False)
    assert r.returncode==0, r.stdout
    assert "model and publication OFF" in r.stdout
