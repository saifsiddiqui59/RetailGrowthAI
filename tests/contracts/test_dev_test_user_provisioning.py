"""DEV Auth Admin provisioning guard tests. No network or real credentials."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("auth_setup",ROOT/"scripts/dev/provision_test_users.py")
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

def env():
    return {"SUPABASE_PROJECT_REF":s.DEV_REF,
            "SUPABASE_URL":f"https://{s.DEV_REF}.supabase.co"}

def test_dry_run_never_requires_secret_or_performs_auth_action():
    assert s.validate_env(env())["mode"]=="DRY_RUN"

def test_reject_prod_and_foreign_project():
    v=env()
    v["SUPABASE_PROJECT_REF"]="another"
    with pytest.raises(s.ProvisionError,match="existing RetailGrowthAI DEV"):
        s.validate_env(v)
    v=env()
    v["SUPABASE_URL"]="https://production.supabase.co"
    with pytest.raises(s.ProvisionError,match="exact expected DEV"):
        s.validate_env(v)

def test_apply_requires_local_key_and_unique_16char_secrets():
    v=env()
    with pytest.raises(s.ProvisionError,match="guard"):
        s.validate_env(v,apply=True)
    v["RGAI_DEV_TEST_USERS_APPLY"]="YES"
    with pytest.raises(s.ProvisionError,match="key"):
        s.validate_env(v,apply=True)
    v["SUPABASE_SERVICE_ROLE_KEY"]="x"*48
    v["RGAI_TEST_OWNER_PASSWORD"]="different-from-any-real-password-111"
    v["RGAI_TEST_EDITOR_PASSWORD"]=v["RGAI_TEST_OWNER_PASSWORD"]
    with pytest.raises(s.ProvisionError,match="different passwords"):
        s.validate_env(v,apply=True)
    v["RGAI_TEST_EDITOR_PASSWORD"]="different-from-any-real-password-222"
    assert s.validate_env(v,apply=True)["mode"]=="APPLY"
