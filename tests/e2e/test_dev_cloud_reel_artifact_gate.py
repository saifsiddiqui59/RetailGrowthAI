"""A downloadable cloud MP4 is retained only AFTER real ffprobe validation."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CANARY=ROOT/"tests/e2e/retail_dev_canary_once.py"
WORKFLOW=ROOT/".github/workflows/retail-dev-test-accounts-canary-once.yml"


def test_signed_private_h264_aac_proof_precedes_optional_artifact():
    s=CANARY.read_text()
    assert s.index("validate_private_reel_ffprobe(result)") < s.index(
        '(output/"retailgrowthai-dev-cloud-reel.mp4").write_bytes(data)')
    assert 'artifact_dir!="output/video-acceptance"' in s
    assert 'CANARY_REAL_CLOUD_REEL_ARTIFACT_READY=true' in s
    assert 'CANARY_TEMP_FIXTURES_CLEANUP=' in s
    assert 'len(data)>80*1024*1024' in s


def test_artifact_only_on_protected_explicit_dev_workflow_dispatch():
    s=WORKFLOW.read_text()
    assert "workflow_dispatch:" in s
    assert "    branches: [main]" not in s
    assert "environment: dev" in s
    assert "AUTHORIZED_RETAILGROWTHAI_DEV_ONLY" in s
    assert "RGAI_DEV_VIDEO_ARTIFACT_DIR: output/video-acceptance" in s
    assert "if: always() && inputs.mode == 'browser-upload'" in s
    assert "retailgrowthai-dev-live-cloud-30s-reel" in s
    assert "output/video-acceptance/retailgrowthai-dev-cloud-reel.mp4" in s
    assert "if-no-files-found: warn" in s
    assert "RETAIL_NOTIFICATIONS_ENABLED=true" not in s
