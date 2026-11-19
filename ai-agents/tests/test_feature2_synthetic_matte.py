"""Exact actual offline PNG bytes and provenance, without Pillow/provider."""
from pathlib import Path
from hashlib import sha256
import json
import struct
import subprocess
import sys
def test_original_png_reproducible_and_nonpublishable(tmp_path):
    script=Path(__file__).resolve().parents[1]/"test-fixtures"/"clothing-shop-pexels"/"generate-synthetic-matte.py"
    command=[sys.executable,str(script),"--output-dir",str(tmp_path)]
    first=subprocess.run(command,capture_output=True,text=True,timeout=40)
    assert first.returncode==0,first.stderr
    img=(tmp_path/"feature2-synthetic-first-frame.png").read_bytes()
    assert img[:8]==b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II",img[16:24])==(1080,1920)
    info=json.loads((tmp_path/"source-provenance.json").read_text())
    assert info["sha256"]==sha256(img).hexdigest()
    assert info["can_publish"] is False
    assert info["paid_motion_authorized"] is False
    assert info["private_asset_id"] is None
    second=subprocess.run(command,capture_output=True,text=True,timeout=40)
    assert second.returncode==0
    assert img==(tmp_path/"feature2-synthetic-first-frame.png").read_bytes()
    assert json.loads(first.stdout)==json.loads(second.stdout)
