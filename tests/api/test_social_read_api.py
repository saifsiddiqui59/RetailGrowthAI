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
        def __init__(self,url):self.url=url
        def __enter__(self):return self
        def __exit__(self,*exc):return None
        def geturl(self):return self.url
        def read(self,limit):return ('[{"id":"abc","shop_id":"'+SHOP+'"}]').encode()
    def fake(request,timeout):
        requests.append((request,timeout));return Resp(request.full_url)
    store=api.SocialReadStore("https://supabase.example","public-key",transport=fake)
    assert store.list_rows("user-token",SHOP,"accounts")[0]["shop_id"]==SHOP
    req,timeout=requests[0]
    assert req.headers["Authorization"]=="Bearer user-token"
    assert "access_token" not in req.full_url
    assert parse_qs(urlparse(req.full_url).query)["shop_id"]==["eq."+SHOP]
    assert timeout==8

def test_store_refuses_foreign_response_even_if_backend_misconfigured():
    class Resp:
        def __init__(self,url):self.url=url
        def __enter__(self):return self
        def __exit__(self,*exc):return None
        def geturl(self):return self.url
        def read(self,limit):return ('[{"shop_id":"'+OTHER+'"}]').encode()
    store=api.SocialReadStore("https://supabase.example","public-key",
        transport=lambda req,timeout:Resp(req.full_url))
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



def test_social_read_rejects_backend_redirect_before_reading_user_data():
    class Foreign:
        def __init__(self):self.calls=0
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def geturl(self):return "https://malicious.example/collect"
        def read(self,limit):
            self.calls+=1
            return b"[]"
    foreign=Foreign()
    store=api.SocialReadStore("https://supabase.example","public-key",
                              transport=lambda req,timeout:foreign)
    with pytest.raises(api.StorageUnavailable,match="redirect"):
        store.list_rows("user-jwt-secret",SHOP,"accounts")
    assert foreign.calls==0


def test_social_read_bounded_response_and_default_no_redirect(monkeypatch):
    class Huge:
        def __init__(self,url):self.url=url
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def geturl(self):return self.url
        def read(self,limit):
            assert limit==1048577
            return b"x"*1048577
    store=api.SocialReadStore("https://supabase.example","public-key",
        transport=lambda request,timeout:Huge(request.full_url))
    with pytest.raises(api.StorageUnavailable,match="oversized"):
        store.list_rows("user-jwt",SHOP,"jobs")

    handlers=[]
    class Opener:
        def open(self,*args,**kwargs):raise AssertionError("no HTTP expected")
    def opener(handler):
        handlers.append(handler)
        return Opener()
    monkeypatch.setattr(api,"build_opener",opener)
    api.SocialReadStore("https://supabase.example","public-key")
    assert isinstance(handlers[0],api._NoRedirect)
    assert handlers[0].redirect_request(None,None,302,"redirect",{},
        "https://malicious.example/collect") is None


@pytest.mark.parametrize("origin",[
    "https://supabase.example:8443",
    "https://supabase.example/evil",
    "https://user:pass@supabase.example",
    "https://supabase.example?relay=1",
    "http://supabase.example",
])
def test_user_jwt_not_sent_to_unreviewed_supabase_origin(origin):
    with pytest.raises(ValueError):
        api.SocialReadStore(origin,"public-key",transport=lambda *_:None)



def test_job_status_error_code_sanitization_does_not_leak_provider_raw_errors():
    class Reader:
        def list_rows(self,token,shop_id,resource):
            assert resource == "jobs"
            return [
                {"id":"a1000000-0000-4000-8000-000000000001",
                 "shop_id":SHOP,"status":"RECONCILE","attempts":2,
                 "last_error_code":"PROVIDER_RESULT_UNCERTAIN",
                 "access_token":"never return"},
                {"id":"a1000000-0000-4000-8000-000000000002",
                 "shop_id":SHOP,"status":"FAILED","attempts":999,
                 "last_error_code":"Bearer secret-has-leaked",
                 "credential":"private"},
            ]
    svc=api.SocialReadAPI(lambda _: USER,Members(),Reader())
    code,result=svc.handle("GET","jobs","Bearer user-token",SHOP)
    assert code==200 and len(result["jobs"])==2
    assert result["jobs"][0]["last_error_code"]=="PROVIDER_RESULT_UNCERTAIN"
    assert result["jobs"][0]["attempts"]==2
    assert "credential" not in result["jobs"][1]
    assert "access_token" not in result["jobs"][0]
    assert "attempts" not in result["jobs"][1]
    assert "last_error_code" not in result["jobs"][1]


def test_audit_read_whitelists_fields_and_rejects_untrusted_event_codes():
    class Reader:
        def __init__(self):self.invalid=False
        def list_rows(self,token,shop_id,resource):
            assert resource=="audit"
            return [{"id":"c1000000-0000-4000-8000-000000000001",
                     "shop_id":SHOP,
                     "event_code":"SOCIAL_CONTENT_APPROVED" if not self.invalid
                        else "Bearer private client token",
                     "job_id":"c2000000-0000-4000-8000-000000000001",
                     "provider_access_token":"secret",
                     "raw_error":"Never show"}]
    reader=Reader()
    svc=api.SocialReadAPI(lambda _:USER,Members(),reader)
    code,result=svc.handle("GET","audit","Bearer user-token",SHOP)
    assert code==200 and result["audit"][0]["event_code"]=="SOCIAL_CONTENT_APPROVED"
    assert "raw_error" not in result["audit"][0]
    assert "provider_access_token" not in result["audit"][0]
    reader.invalid=True
    assert svc.handle("GET","audit","Bearer user-token",SHOP)==(
        503,{"error":"SERVICE_UNAVAILABLE"})
