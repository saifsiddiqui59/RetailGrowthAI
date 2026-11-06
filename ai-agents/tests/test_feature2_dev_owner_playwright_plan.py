"""Playwright OWNER smoke is manual, read-only and safe to plan without credentials."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / "feature2-dev-owner-readonly-playwright.mjs"

@pytest.mark.skipif(shutil.which("node") is None, reason="Node not installed")
def test_readonly_dev_playwright_script_syntax_and_dry_plan():
    syntax=subprocess.run(["node","--check",str(SCRIPT)],capture_output=True,
                          text=True,timeout=20)
    assert syntax.returncode==0,syntax.stderr
    result=subprocess.run(["node",str(SCRIPT),"--plan"],capture_output=True,
                          text=True,timeout=20)
    assert result.returncode==0,result.stderr
    plan=json.loads(result.stdout)
    assert plan["mode"]=="HOSTED_DEV_AUTHENTICATED_READONLY"
    assert plan["routes"]==["/account","/campaigns","/trends"]
    assert plan["needs_password_in_chat"] is False
    assert plan["needs_permanent_auth_file"] is False
    assert plan["playwright_uses_saved_browser_agent_profile"] is False
    assert plan["no_uploads"] and plan["no_paid_ai"] and plan["no_render_or_publish"]

@pytest.mark.skipif(shutil.which("node") is None, reason="Node not installed")
def test_readonly_dev_playwright_host_gate_denies_ci_and_default():
    env=os.environ.copy()
    env["CI"]="1"
    env["RGAI_DEV_READONLY_APPROVAL"]="I_APPROVE_RETAILGROWTHAI_DEV_OWNER_READONLY"
    env["RGAI_DEV_TEST_SHOP_ID"]="11111111-1111-4111-8111-111111111111"
    result=subprocess.run(["node",str(SCRIPT),"--run"],env=env,
                          capture_output=True,text=True,timeout=20)
    assert result.returncode==3
    assert "CI/Actions prohibited" in result.stderr
