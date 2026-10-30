"""Hosted debug must be read-only on actual media/drafts and no paid model."""
from pathlib import Path
import runpy
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/ops"))
SCRIPT=ROOT/"scripts/ops/feature2_dev_trend_readonly_diagnosis.py"
WORKFLOW=ROOT/".github/workflows/retail-dev-feature2-readonly-diagnosis.yml"

def test_diagnostic_requires_operator_and_has_no_network_side_effects(monkeypatch):
    d=runpy.run_path(str(SCRIPT))
    monkeypatch.delenv("RGAI_F2_READONLY_DIAG",raising=False)
    with pytest.raises(RuntimeError,match="Missing read-only diagnostic approval"):
        d["main"]()

def test_exact_authenticated_get_only_and_no_second_upload_or_paid_model():
    code=SCRIPT.read_text()
    workflow=WORKFLOW.read_text()
    assert "SIGNED_DEV_GET_ONLY" in code
    assert '("content-drafts","trend-recommendations")' in code
    assert 'for attempt in range(2)' in code
    assert 'if status!="503": break' in code
    assert 'method="GET"' in code
    assert 'shop_ai_budget_controls' in code
    assert 'active":False' in code
    assert "upload" not in code.lower()
    assert "register_uploaded_image" not in code
    assert "Feature2AiActivation" not in code
    assert "AzureFeature2" not in code
    assert "environment: dev" in workflow
    assert "refs/heads/main" in workflow
    assert "AUTHORIZED_FEATURE2_DEV_READONLY_DIAG" in workflow
    assert "workflow_dispatch:" in workflow

def test_response_diagnostics_never_dump_nonerror_payload_or_secret(monkeypatch):
    d=runpy.run_path(str(SCRIPT))
    class Response:
        status=503
        headers={"X-Request-ID":"sensitive-trace"}
        def read(self,n): return b'{"error":"TREND_STORAGE_UNAVAILABLE","untrustedSecret":"TOKEN"}'
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(d["urllib"].request,"urlopen",lambda req,timeout:Response())
    result=d["check_get"]("https://rgai-dev-functions-d4e5ddbd.azurewebsites.net/api/shops/test/trend-recommendations",
                         "sb_publishable_fake","fake-signed")
    assert result==( "503","TREND_STORAGE_UNAVAILABLE",True )
