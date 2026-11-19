"""Offline real ffmpeg b-roll opt-in runner has zero-network plan and safe flags."""
from pathlib import Path
import subprocess
import sys
import json
def test_5s_video_builder_plan_has_zero_writes(tmp_path):
    runner=Path(__file__).resolve().parents[1]/"test-fixtures/clothing-shop-pexels/render-offline-reference.py"
    result=subprocess.run([sys.executable,str(runner),"--output-dir",str(tmp_path)],
                          capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    data=json.loads(result.stdout)
    assert data["mode"]=="PLAN_NO_MEDIA_WRITTEN"
    assert data["can_publish"] is False
    assert list(tmp_path.iterdir())==[]
