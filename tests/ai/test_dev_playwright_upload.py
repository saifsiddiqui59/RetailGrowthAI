"""No hosted network: tests the DEV Playwright image-upload handoff guardrails."""
import importlib.util
import json
import pathlib
import subprocess
from unittest.mock import patch

import pytest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "e2e" / "retail_dev_canary_once.py"
spec = importlib.util.spec_from_file_location("retail_dev_canary_once", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SHOP = "0753c503-ce7f-4544-b8fe-609444ebf068"
ASSET = "019ba3fa-96ed-4b73-8f2a-6108ab317d9b"
PATH = SHOP + "/uploads/8b38cd1a-4be0-4ceb-b438-cdc937d6f1ef.png"

@pytest.fixture(autouse=True)
def fake_approval(monkeypatch):
    # Unit-only approval string; subprocess is mocked, no hosted or browser calls.
    monkeypatch.setenv("RGAI_DEV_CANARY_APPROVAL", "AUTHORIZED_RETAILGROWTHAI_DEV_ONLY")

def fake_completed(stdout, returncode=0):
    return subprocess.CompletedProcess(args=["node"], returncode=returncode, stdout=stdout, stderr="")

def test_playwright_upload_records_exact_shop_scoped_cleanup_path_before_success():
    output = ("CANARY_PLAYWRIGHT_OBJECT_PATH=" + PATH + "\n" +
              "CANARY_PLAYWRIGHT_UPLOAD=" + json.dumps({"asset_id": ASSET, "object_path": PATH}) + "\n")
    paths = []
    with patch.object(module.subprocess, "run", return_value=fake_completed(output)) as run:
        asset = module.upload_using_playwright(
            shop_id=SHOP, email="rgai-canary-abc-a@example.invalid",
            password="temporary-password-never-logged", image_bytes=module.image(), cleanup_paths=paths)
    assert asset == ASSET
    assert paths == [PATH]
    kwargs = run.call_args.kwargs
    assert kwargs["env"]["RGAI_DEV_PLAYWRIGHT_UPLOAD"] == "1"
    assert kwargs["env"]["RGAI_BROWSER_SHOP_ID"] == SHOP
    assert "RGAI_DEV_SERVICE_KEY" not in kwargs["env"]
    assert "RETAIL_SUPABASE_SERVICE_ROLE_KEY" not in kwargs["env"]
    assert kwargs["capture_output"] is True

@pytest.mark.parametrize("line", [
    "CANARY_PLAYWRIGHT_OBJECT_PATH=other-shop/uploads/8b38cd1a-4be0-4ceb-b438-cdc937d6f1ef.png",
    "CANARY_PLAYWRIGHT_OBJECT_PATH=" + SHOP + "/../leak.png",
    "CANARY_PLAYWRIGHT_OBJECT_PATH=" + SHOP + "/uploads/%2E%2E.png",
])
def test_untrusted_path_is_rejected_even_when_a_browser_claims_success(line):
    with patch.object(module.subprocess, "run", return_value=fake_completed(line)):
        with pytest.raises(RuntimeError, match="Untrusted"):
            module.upload_using_playwright(
                shop_id=SHOP, email="rgai-canary-x-a@example.invalid",
                password="temporary-password-never-logged",
                image_bytes=module.image(), cleanup_paths=[])

def test_fail_closed_but_remembers_uploaded_path_for_cleanup():
    paths = []
    with patch.object(module.subprocess, "run",
                      return_value=fake_completed("CANARY_PLAYWRIGHT_OBJECT_PATH=" + PATH + "\n", 1)):
        with pytest.raises(RuntimeError, match="browser upload failed"):
            module.upload_using_playwright(
                shop_id=SHOP, email="rgai-canary-x-a@example.invalid",
                password="temporary-password-never-logged",
                image_bytes=module.image(), cleanup_paths=paths)
    assert paths == [PATH]
