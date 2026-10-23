"""Mock transport tests for backend-only OAuth RPC; never contact Supabase."""
import importlib.util
from pathlib import Path
import json
import sys
from datetime import datetime,timedelta,timezone
import pytest
ROOT=Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("social_oauth_repository",ROOT/"social_oauth_repository.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
SHOP="10000000-0000-4000-8000-000000000001"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ACC="20000000-0000-4000-8000-000000000001"
NOW=datetime.now(timezone.utc)
class Response:
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(self.data).encode()
class Fake:
    def __init__(self,results):self.results=list(results);self.requests=[]
    def __call__(self,req,timeout):
        self.requests.append((req,timeout))
        return Response(self.results.pop(0))

def test_atomic_issue_consume_and_token_ciphertext_only():
    digest=b"a"*32; cipher=b"x"*84
    stored={"state_digest":digest.hex(),"shop_id":SHOP,"user_id":USER,
        "provider":"linkedin","expires_at":(NOW+timedelta(minutes=10)).isoformat(),
        "consumed_at":None,
        "verifier_ciphertext":cipher.hex(),"exact_redirect_uri":"https://retail.example/callback"}
    fake=Fake([True,stored,True,True])
    r=m.SocialOAuthRpcRepository("https://example.supabase.co","sb_secret_not_real",transport=fake)
    r.issue(digest=digest,shop_id=SHOP,user_id=USER,provider="linkedin",
        expires_at=NOW+timedelta(minutes=10),
        exact_redirect_uri="https://retail.example/callback",
        verifier_ciphertext=cipher)
    previous=r.consume(digest=digest,shop_id=SHOP,user_id=USER,
        provider="linkedin",before=NOW)
    assert previous["state_digest"]==digest and previous["verifier_ciphertext"]==cipher
    r.connect_atomic(id=ACC,shop_id=SHOP,connected_by=USER,provider="linkedin",
        provider_account_id="urn:li:person:abc",display_name="Example",
        granted_scopes=["w_member_social"],access_token_ciphertext=cipher,
        refresh_token_ciphertext=None,encryption_key_version=1,expires_at=None)
    assert r.disconnect_atomic(shop_id=SHOP,account_id=ACC,actor=USER)
    paths=[req.full_url for req,_ in fake.requests]
    assert paths==[
        "https://example.supabase.co/rest/v1/rpc/"+n for n in
        ("p2_issue_oauth_state","p2_consume_oauth_state",
         "p2_connect_social_account","p2_disconnect_social_account")]
    payload=json.loads(fake.requests[2][0].data.decode())
    assert payload["p_access_hex"]==cipher.hex()
    assert "access_token" not in payload
    for req,t in fake.requests:
        assert "sb_secret_not_real" not in req.full_url
        assert t==10 and req.get_method()=="POST"

def test_missing_state_denies_replay_and_foreign_account_replies():
    fake=Fake([None,False])
    r=m.SocialOAuthRpcRepository("https://example.supabase.co","sb_secret_not_real",transport=fake)
    assert r.consume(digest=b"a"*32,shop_id=SHOP,user_id=USER,
                     provider="linkedin",before=NOW) is None
    assert r.disconnect_atomic(shop_id=SHOP,account_id=ACC,actor=USER) is False

def test_bad_origin_and_ciphertext_are_rejected_before_http():
    with pytest.raises(ValueError):
        m.SocialOAuthRpcRepository("http://example.supabase.co","sb_secret_not_real")
    fake=Fake([])
    r=m.SocialOAuthRpcRepository("https://example.supabase.co","sb_secret_not_real",transport=fake)
    with pytest.raises(m.OAuthDenied):
        r.connect_atomic(id=ACC,shop_id=SHOP,connected_by=USER,provider="linkedin",
        provider_account_id="id",display_name="Test",granted_scopes=["write"],
        access_token_ciphertext=b"short",refresh_token_ciphertext=None,
        encryption_key_version=1,expires_at=None)
    assert not fake.requests

def test_foreign_response_never_accepted_as_client_state():
    fake=Fake([{"state_digest":(b"a"*32).hex(),"shop_id":SHOP,"user_id":USER,
    "provider":"linkedin","expires_at":(NOW+timedelta(minutes=10)).isoformat(),
    "consumed_at":None,"verifier_ciphertext":(b"x"*84).hex(),
    "exact_redirect_uri":"https://retail.example/callback"}])
    r=m.SocialOAuthRpcRepository("https://example.supabase.co","sb_secret_not_real",transport=fake)
    with pytest.raises(m.StorageUnavailable):
        r.consume(digest=b"b"*32,shop_id=SHOP,user_id=USER,
                provider="linkedin",before=NOW)
