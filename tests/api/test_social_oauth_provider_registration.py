"""Mock-only independently gated Meta/LinkedIn OAuth application registry."""
import base64
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_oauth import OAuthDenied
from social_oauth_http import build_oauth_api
from social_provider_oauth_transport import provider_oauth_transport

SHOP="10000000-0000-4000-8000-000000000001"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class Tenant:
    def _request(self,*args,**kwargs):
        return [{"shop_id":SHOP,"user_id":USER,"role":"OWNER"}]


class State:
    def __init__(self):self.calls=[]
    def issue(self,**kwargs):self.calls.append(kwargs)


def settings():
    return {
        "RETAIL_PART2_SOCIAL_ENABLED":"true",
        "RETAIL_PART2_OAUTH_ENABLED":"true",
        "RETAIL_SUPABASE_URL":"https://test.supabase.co",
        "RETAIL_SUPABASE_PUBLISHABLE_KEY":"public-key",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY":"sb_secret_"+"s"*32,
        "RETAIL_PART2_VAULT_KEY_B64":base64.b64encode(b"k"*32).decode(),
        "RETAIL_PART2_VAULT_VERSION":"1",
        "RETAIL_YOUTUBE_CLIENT_ID":"google-app",
        "RETAIL_YOUTUBE_CLIENT_SECRET":"google-confidential",
        "RETAIL_YOUTUBE_OAUTH_REDIRECT_URI":"https://studio.example/social/oauth/callback/youtube",
    }


def build(config):
    state=State()
    service=build_oauth_api(config,verifier=lambda token: USER,
        tenant_store=Tenant(),repository=state,
        transport=lambda *args,**kwargs:None)
    return service,state


def test_only_explicitly_reviewed_oauth_apps_appear_in_registry():
    service,state=build(settings())
    assert set(service.lifecycle.providers)=={"youtube"}
    assert service.handle("start","Bearer user-jwt",{
        "shop_id":SHOP,"provider":"linkedin"})[0]==403
    assert state.calls==[]


def test_linkedin_and_meta_independent_server_feature_flags():
    config=settings()
    config.update({
        "RETAIL_PART2_LINKEDIN_OAUTH_ENABLED":"true",
        "RETAIL_LINKEDIN_CLIENT_ID":"linkedin-app",
        "RETAIL_LINKEDIN_CLIENT_SECRET":"linkedin-confidential",
        "RETAIL_LINKEDIN_OAUTH_REDIRECT_URI":
          "https://studio.example/social/oauth/callback/linkedin",
        "RETAIL_PART2_META_OAUTH_ENABLED":"true",
        "RETAIL_META_APP_ID":"123456789",
        "RETAIL_META_APP_SECRET":"meta-confidential",
        "RETAIL_META_GRAPH_VERSION":"v26.0",
        "RETAIL_META_FACEBOOK_REDIRECT_URI":
          "https://studio.example/social/oauth/callback/facebook",
        "RETAIL_META_INSTAGRAM_REDIRECT_URI":
          "https://studio.example/social/oauth/callback/instagram",
    })
    api,state=build(config)
    assert set(api.lifecycle.providers)=={"youtube","linkedin","facebook","instagram"}
    for name,host in [
        ("linkedin","www.linkedin.com"),
        ("facebook","www.facebook.com"),
        ("instagram","www.facebook.com")
    ]:
        code,payload=api.handle("start","Bearer user-jwt",{
            "shop_id":SHOP,"provider":name})
        assert code==200 and urlsplit(payload["authorization_url"]).hostname==host
        assert name==state.calls[-1]["provider"]
        assert "meta-confidential" not in json.dumps(payload)
        assert "linkedin-confidential" not in json.dumps(payload)
    assert len(state.calls)==3


def test_no_provider_registered_denied_even_if_social_switch_enabled():
    config=settings()
    for key in ("RETAIL_YOUTUBE_CLIENT_ID","RETAIL_YOUTUBE_CLIENT_SECRET",
                "RETAIL_YOUTUBE_OAUTH_REDIRECT_URI"):
        config.pop(key)
    with pytest.raises(OAuthDenied,match="no reviewed provider"):
        build(config)


class Response:
    def __init__(self,url,data):self.url=url;self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,limit):return json.dumps(self.data).encode()


def test_transport_enforces_official_https_host_action_and_no_raw_error():
    calls=[]
    def fake(req,timeout):
        calls.append(req)
        return Response(req.full_url,{"access_token":"server-only-token"})
    data,_=provider_oauth_transport(
        "POST","https://www.linkedin.com/oauth/v2/accessToken",
        form={"grant_type":"authorization_code","code":"one-time-private"},
        transport=fake)
    assert data["access_token"]=="server-only-token"
    assert len(calls)==1 and calls[0].get_method()=="POST"
    assert "code=one-time-private" not in calls[0].full_url
    with pytest.raises(OAuthDenied):
        provider_oauth_transport(
            "POST","https://evil.example/oauth/v2/accessToken",
            form={"code":"private"},transport=fake)
    with pytest.raises(OAuthDenied):
        provider_oauth_transport("GET",
            "http://graph.facebook.com/v26.0/me/accounts",
            headers={"Authorization":"Bearer private"},transport=fake)
    assert len(calls)==1


def test_no_injected_transport_error_exposes_confidential_token():
    def fail(*a,**kw):raise RuntimeError("CLIENT_SECRET_DO_NOT_LOG")
    with pytest.raises(OAuthDenied) as exc:
        provider_oauth_transport("GET",
          "https://graph.facebook.com/v26.0/me/accounts",
          headers={"Authorization":"Bearer SECRET"},transport=fail)
    assert "CLIENT_SECRET" not in str(exc.value)
    assert exc.value.__cause__ is None
