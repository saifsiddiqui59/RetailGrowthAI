import json
import subprocess
import sys
from pathlib import Path
def test_real_cpu_benchmark_preflight_is_no_write_without_model_weights(tmp_path):
    script=Path(__file__).resolve().parents[1]/"test-fixtures"/"retailer-voice"/"run-real-kokoro-cpu.py"
    p=subprocess.run([sys.executable,str(script),"--plan"],cwd=tmp_path,
                    capture_output=True,text=True,timeout=20)
    assert p.returncode==0,p.stderr
    obj=json.loads(p.stdout)
    assert obj["actual_inference_executed"] is False
    assert obj["weights_downloaded_by_this_tool"] is False
    assert obj["model_sha256"] and obj["voices_sha256"]
    assert list(tmp_path.iterdir())==[]
