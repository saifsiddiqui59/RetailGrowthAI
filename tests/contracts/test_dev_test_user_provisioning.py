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
    v["SUPABASE_SERVICE_ROLE_KEY"]="sb_secret_"+"x"*40
    v["RGAI_TEST_OWNER_PASSWORD"]="different-from-any-real-password-111"
    v["RGAI_TEST_EDITOR_PASSWORD"]=v["RGAI_TEST_OWNER_PASSWORD"]
    with pytest.raises(s.ProvisionError,match="different passwords"):
        s.validate_env(v,apply=True)
    v["RGAI_TEST_EDITOR_PASSWORD"]="different-from-any-real-password-222"
    assert s.validate_env(v,apply=True)["mode"]=="APPLY"

def test_opaque_new_key_never_sent_as_bearer_or_to_redirect_target():
    import io
    key="sb_secret_"+"x"*40
    received=[]
    class Reply(io.BytesIO):
        status=200
    def opener(request,timeout):
        received.append((request.full_url,dict(request.header_items())))
        return Reply(b'{"users":[]}')
    result=s.do_request("GET",env()["SUPABASE_URL"]+
                        "/auth/v1/admin/users?page=1&per_page=1000",key,
                        opener=opener)
    assert result=={"users":[]}
    assert len(received)==1
    url,headers=received[0]
    assert url.startswith("https://"+s.DEV_REF+".supabase.co/auth/")
    assert headers["Apikey"]==key
    assert "Authorization" not in headers
    with pytest.raises(s.ProvisionError,match="redirect denied"):
        s.NoRedirects().redirect_request(None,None,302,"",{},
            "https://foreign.example/auth/v1/admin/users")


def test_legacy_service_jwt_uses_bearer_and_does_not_print_secret():
    import io
    key="eyJ"+"a"*36+".bbb.ccc"
    recorded=[]
    class Reply(io.BytesIO):
        status=201
    def opener(request,timeout):
        recorded.append(dict(request.header_items()))
        return Reply(b'{"email":"rgai-owner-test@retailgrowth.test","id":"test-only"}')
    result=s.do_request("POST",env()["SUPABASE_URL"]+
        "/auth/v1/admin/users",key,{"email":s.ACCOUNTS["owner"]},
        opener=opener)
    assert result["id"]=="test-only"
    assert recorded[0]["Authorization"]=="Bearer "+key
    assert recorded[0]["Apikey"]==key


def test_unrecognized_local_admin_identity_denied_before_network():
    v=env()
    v.update({"RGAI_DEV_TEST_USERS_APPLY":"YES",
              "SUPABASE_SERVICE_ROLE_KEY":"arbitrary-invalid-key-"+"x"*40,
              "RGAI_TEST_OWNER_PASSWORD":"synthetic-owner-secret-111",
              "RGAI_TEST_EDITOR_PASSWORD":"synthetic-editor-secret-222"})
    with pytest.raises(s.ProvisionError,match="Service role key"):
        s.validate_env(v,apply=True)
