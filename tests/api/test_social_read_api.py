"""Social read endpoint: no live database, user-scoped row boundaries only."""
import importlib.util
import sys
from pathlib import Path
from uuid import UUID
from urllib.parse import urlparse, parse_qs
import pytest

root=Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"
sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location("social_read_api",root/"social_read_api.py")
api=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=api
spec.loader.exec_module(api)

SHOP="10000000-0000-4000-8000-000000000001"
OTHER="10000000-0000-4000-8000-000000000002"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

class Members:
    def __init__(self, allowed=True): self.allowed=allowed
    def member(self,token,user_id,shop_id):
        assert token=="user-token" and user_id==USER
        return self.allowed

class ReadRows:
    def __init__(self):self.calls=[]
    def list_rows(self,token,shop_id,resource):
        self.calls.append((token,shop_id,resource))
        return [{"id":"20000000-0000-4000-8000-000000000001",
                 "shop_id":SHOP,"provider":"linkedin",
                 "connection_status":"CONNECTED",
                 "access_token_ciphertext":"SHOULD_NOT_BE_IN_RESPONSE"}]

def test_member_gets_only_allowed_fields_not_credentials():
    reader=ReadRows()
    service=api.SocialReadAPI(lambda t: USER,Members(),reader)
    code,payload=service.handle("GET","accounts","Bearer user-token",SHOP)
    assert code==200 and len(payload["accounts"])==1
    assert "access_token_ciphertext" not in payload["accounts"][0]
    assert reader.calls==[("user-token",SHOP,"accounts")]

def test_denials_never_query_social_table():
    reader=ReadRows()
    service=api.SocialReadAPI(lambda t: USER,Members(False),reader)
    assert service.handle("GET","accounts","Bearer user-token",SHOP)[0]==403
    assert service.handle("GET","jobs","Bearer user-token",OTHER)[0]==403
    assert service.handle("GET","accounts","bad",SHOP)[0]==401
    assert service.handle("POST","accounts","Bearer user-token",SHOP)[0]==404
    assert service.handle("GET","oauth","Bearer user-token",SHOP)[0]==404
    assert service.handle("GET","accounts","Bearer user-token","../")[0]==400
    assert reader.calls==[]

def test_store_uses_user_jwt_and_fixed_rls_filter_only():
    requests=[]
    class Resp:
        def __enter__(self):return self
        def __exit__(self,*exc):return None
        def read(self):return ('[{"id":"abc","shop_id":"'+SHOP+'"}]').encode()
    def fake(request,timeout):
        requests.append((request,timeout));return Resp()
    store=api.SocialReadStore("https://supabase.example","public-key",transport=fake)
    assert store.list_rows("user-token",SHOP,"accounts")[0]["shop_id"]==SHOP
    req,timeout=requests[0]
    assert req.headers["Authorization"]=="Bearer user-token"
    assert "access_token" not in req.full_url
    assert parse_qs(urlparse(req.full_url).query)["shop_id"]==["eq."+SHOP]
    assert timeout==8

def test_store_refuses_foreign_response_even_if_backend_misconfigured():
    class Resp:
        def __enter__(self):return self
        def __exit__(self,*exc):return None
        def read(self):return ('[{"shop_id":"'+OTHER+'"}]').encode()
    store=api.SocialReadStore("https://supabase.example","public-key",transport=lambda *a,**k:Resp())
    with pytest.raises(api.StorageUnavailable):
        store.list_rows("user-token",SHOP,"jobs")

def test_reviewed_campaign_days_and_job_snapshots_read_through_rls_only():
    class Reader:
        def __init__(self):self.calls=[]
        def list_rows(self,token,shop_id,resource):
            self.calls.append((token,shop_id,resource))
            if resource=="days":
                return [{"id":"12000000-0000-4000-8000-000000000001",
                    "shop_id":SHOP,"review_status":"APPROVED",
                    "linkedin":{"post_text":"Business-reviewed text"},
                    "token":"forbidden", "access_token_ciphertext":"private"}]
            return [{"id":"13000000-0000-4000-8000-000000000001",
                    "shop_id":SHOP,"provider":"linkedin","revision":1,
                    "caption":"Exact pending copy",
                    "access_token_ciphertext":"never-return"}]
    read=Reader()
    service=api.SocialReadAPI(lambda t: USER,Members(),read)
    code,days=service.handle("GET","days","Bearer user-token",SHOP)
    assert code==200 and days["days"][0]["linkedin"] == {
        "post_text":"Business-reviewed text"}
    assert "token" not in days["days"][0]
    code,jobs=service.handle("GET","jobs","Bearer user-token",SHOP)
    assert code==200 and jobs["jobs"][0]["revision"]==1
    assert jobs["jobs"][0]["caption"]=="Exact pending copy"
    assert "access_token_ciphertext" not in jobs["jobs"][0]
    assert read.calls==[
        ("user-token",SHOP,"days"),("user-token",SHOP,"jobs")]
