"""Allow anonymous public hosted browser QA, never live credentials or writes."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FLOW=ROOT/".github/workflows/p1-dev-public-responsive-browser-once.yml"
SCRIPT=ROOT/"frontend/e2e/dev-public-login-smoke.mjs"


def test_exact_one_shot_dev_public_origin_and_screenshots():
    flow=FLOW.read_text()
    script=SCRIPT.read_text()
    for x in ("branches: [main]","environment: dev",
              "test(dev): verify RetailGrowthAI public login responsive",
              "contents: read", "retailgrowthai-dev-public-login-responsive-qa",
              "node frontend/e2e/dev-public-login-smoke.mjs",
              "if-no-files-found: warn"):
        assert x in flow,x
    assert "https://purple-dune-06b5da200.2.azurestaticapps.net" in script
    for x in ("desktop","iphone-like","narrow-mobile","tablet",
              "PUBLIC_LOGIN_RESPONSIVE_PASS", "PUBLIC_PROTECTED_ROUTE_DENIED",
              "PUBLIC_DEV_BROWSER_SMOKE=PASS"):
        assert x in script,x


def test_no_tenant_auth_write_mutation_or_backend_configuration():
    flow=FLOW.read_text()
    script=SCRIPT.read_text()
    for forbidden in (
        "az functionapp", "az staticwebapp", "azure/login",
        "supabase db push", "apply_migration",
        "workflow_dispatch","create account and submit",
    ):
        assert forbidden not in flow,forbidden
    for forbidden in (
        "process.env.RETAIL_", "process.env.RGAI_DEV_SERVICE_KEY",
        "fetch(", "request.post(", "request.put(", "request.patch(",
        "getByRole('button', { name: 'Create your account' }).click()",
    ):
        assert forbidden not in script,forbidden
    # The workflow intentionally scans for privileged variable names; this
    # denylist is not a credential lookup or environment export.
    assert "! grep -Eq 'RGAI_DEV_SERVICE_KEY|RETAIL_SUPABASE_SERVICE_ROLE_KEY" in flow
    assert "baseURL" not in script or "example.com" not in script
