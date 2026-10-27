from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"scripts/ops/feature2_real_model_one_shot.py"
WF=ROOT/".github/workflows/retail-dev-feature2-real-model-one-shot.yml"

def test_feature2_paid_one_shot_has_scoped_approval_and_actual_auditable_limits():
    s=SOURCE.read_text()
    ast.parse(s)
    assert 'RGAI_F2_ONESHOT_AUTHORIZED' in s
    assert 'FEATURE2_APPROVED_ONE_SHOT_020' in s
    assert 'MAX_TOTAL = 0.20' in s and 'MAX_CALL = 0.05' in s
    assert 'shop_ai_budget_controls?select=shop_id&limit=1' in s
    assert 'FEATURE2_REAL_AZURE_7DAY_DRAFT=PASS' in s
    assert 'AzureFoundryProvider._post_json' in s
    assert 'Feature2BudgetStore' in s and 'ledger.settle' in s
    assert 'prefer_representation=False' in s
    assert 'return=minimal' in s
    assert 'retail_onboarding_status' in s
    assert 'SYNTHETIC_DEV_USER_REQUIRES_GENUINE_PLATFORM_ADMIN_APPROVAL' in s
    assert 'admin_users["users"]' in s
    assert 'bearer=token["access_token"]' in s
    assert 'shop_memberships?shop_id=eq.' in s
    assert '"enabled":False' in s
    assert '"can_publish":False' in s
    assert 'RETAIL_FOUNDRY_REAL_AI_ENABLED' not in s
    assert 'for attempt in' not in s
    assert 'range(3)' not in s
    assert 'while True' not in s

def test_feature2_paid_one_shot_workflow_requires_exact_main_approval_and_dev_oidc():
    s=WF.read_text()
    assert 'branches: [main]' in s and 'environment: dev' in s
    assert 'workflow_dispatch:' in s
    assert 'AUTHORIZED_FEATURE2_DEV_020_AFTER_ONBOARDING_APPROVAL' in s
    assert "startsWith(github.event.head_commit.message, 'release(dev): isolated Feature2 genuine GPT-4.1-mini test')" in s
    assert 'cancel-in-progress: false' in s
    assert 'id-token: write' in s
    assert 'secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY' in s
    assert 'Azure/static-web-apps-deploy' not in s
    assert 'config appsettings set' not in s
    assert 'db push' not in s
