"""Live HTTP adapter unit tests: never leak raw SQL errors or self-grant paid tiers."""
import io
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from tenant_store import TenantStore, SubscriptionDenied, StorageUnavailable  # noqa: E402
from admin_store import AdminStore  # noqa: E402
from http_api import HTTPAPI  # noqa: E402

SHOP=str(uuid4())
USER=str(uuid4())
ASSET=str(uuid4())

def fail_transport(code):
    def transport(req, timeout=None):
        body=json.dumps({"code":code,"message":"PRIVATE CUSTOMER EMAIL NEVER LOG"}).encode()
        raise HTTPError(req.full_url,400,"failure",{},io.BytesIO(body))
    return transport

@pytest.mark.parametrize("code",["RG001","RG002"])
def test_auth_jwt_postgrest_quota_error_normalized(code):
    store=TenantStore("https://rg.example.supabase.co","sb_publishable_example",transport=fail_transport(code))
    with pytest.raises(SubscriptionDenied) as e:
        store._request("campaigns","jwt",method="POST",data={})
    assert e.value.code==code
    assert "PRIVATE" not in str(e.value)

@pytest.mark.parametrize("code",["RG001","RG002"])
def test_service_role_render_quota_error_normalized(code):
    store=AdminStore("https://rg.example.supabase.co","sb_secret_example",transport=fail_transport(code))
    with pytest.raises(SubscriptionDenied) as e:
        store.request("render_jobs",method="POST",data={})
    assert e.value.code==code
    assert "PRIVATE" not in str(e.value)

def test_unknown_sql_state_fails_closed_as_service_unavailable():
    store=TenantStore("https://rg.example.supabase.co","sb_publishable_example",
                      transport=fail_transport("OTHER_ERROR"))
    with pytest.raises(StorageUnavailable):
        store._request("campaigns","jwt",method="POST",data={})

class Store:
    def member(self, token, uid, shop_id, write=False):
        return True
    def assets(self, token, shop_id, ids):
        return True
    def save_pending(self, token, uid, cid, brief):
        raise SubscriptionDenied("RG002")

def campaign_body():
    return {"shop_id": SHOP,"brief":"Seven local shop marketing ideas",
            "duration_days":7,"start_date":"2026-11-01",
            "timezone":"Asia/Kolkata","language":"en-IN",
            "platforms":["linkedin","instagram"],
            "media_asset_ids":[ASSET],"offer":None}

def test_quota_exceeded_returns_fixed_429_without_database_message():
    api=HTTPAPI(lambda t:USER,Store(),planning_queue=object(),
                failure_store=object(),durable_outbox=True)
    code,response=api.handle("POST","/campaigns","Bearer verified",campaign_body())
    assert (code,response)==(429,{"error":"QUOTA_EXCEEDED"})

def test_expired_plan_returns_fixed_402():
    class ExpiredStore(Store):
        def save_pending(self,*a):
            raise SubscriptionDenied("RG001")
    api=HTTPAPI(lambda t:USER,ExpiredStore(),planning_queue=object(),
                failure_store=object(),durable_outbox=True)
    code,response=api.handle("POST","/campaigns","Bearer verified",campaign_body())
    assert (code,response)==(402,{"error":"SUBSCRIPTION_REQUIRED"})

def test_subscription_does_not_bypass_missing_token():
    api=HTTPAPI(lambda t:USER,Store(),planning_queue=object(),
                failure_store=object(),durable_outbox=True)
    assert api.handle("POST","/campaigns","",campaign_body())==(401,{"error":"UNAUTHORIZED"})

def test_render_quota_429_same_guard_and_denies_no_token():
    class Render:
        def create(self,*a):
            raise SubscriptionDenied("RG002")
    api=HTTPAPI(lambda t:USER,Store(),render_api=Render(),
                planning_queue=object(),failure_store=object())
    path="/campaigns/"+str(uuid4())+"/renders"
    assert api.handle("POST",path,"Bearer verified",{})==(429,{"error":"QUOTA_EXCEEDED"})
    assert api.handle("POST",path,"",{})==(401,{"error":"UNAUTHORIZED"})
