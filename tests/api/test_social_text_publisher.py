"""Offline, injected Facebook Page and LinkedIn text provider request/receipt tests."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_dispatch import ProviderFailure
from social_text_publisher import SocialTextPublisher, network_text_transport
from social_providers import ProviderRequest

JOB="13000000-0000-4000-8000-000000000001"
SHOP="10000000-0000-4000-8000-000000000001"
ACCOUNT="11000000-0000-4000-8000-000000000001"


def ctx(provider="facebook"):
    external="123456789" if provider=="facebook" else "urn:li:person:member-123"
    required=["pages_manage_posts"] if provider=="facebook" else ["w_member_social"]
    return {"job":{"id":JOB,"shop_id":SHOP,"social_account_id":ACCOUNT,
                   "provider":provider,"caption":"Approved seasonal promotion",
                   "media_asset_id":None},
            "account":{"id":ACCOUNT,"shop_id":SHOP,"provider":provider,
                       "provider_account_id":external,
                       "granted_scopes":required},
            "provider_access_token":"SECRET-DO-NOT-LEAK"}


def test_facebook_post_requires_backend_enabled_and_confirmed_page_receipt():
    calls=[]
    def transport(request):
        calls.append(request)
        assert request.url=="https://graph.facebook.com/v26.0/123456789/feed"
        assert request.headers["Authorization"]=="Bearer SECRET-DO-NOT-LEAK"
        assert request.body["published"] is True
        assert request.body["message"]=="Approved seasonal promotion"
        return (200,{"id":"123456789_987654321"}, {})
    p=SocialTextPublisher(graph_version="v26.0",linkedin_version="202610",
                          enabled=True,transport=transport)
    receipt=p.publish(JOB,ctx())
    assert receipt.status=="PUBLISHED" and receipt.remote_id=="123456789_987654321"
    assert len(calls)==1 and "SECRET-DO-NOT-LEAK" not in repr(calls[0])
    disabled=SocialTextPublisher(graph_version="v26.0",linkedin_version="202610",
                                transport=transport)
    with pytest.raises(ProviderFailure) as denial:
        disabled.publish(JOB,ctx())
    assert denial.value.definitely_not_sent
    assert len(calls)==1


def test_linkedin_text_posts_required_author_scope_and_restli_receipt():
    requests=[]
    def transport(request):
        requests.append(request)
        assert request.url=="https://api.linkedin.com/rest/posts"
        assert request.headers["Linkedin-Version"]=="202610"
        assert request.headers["X-Restli-Protocol-Version"]=="2.0.0"
        assert request.body["author"]=="urn:li:person:member-123"
        assert request.body["lifecycleState"]=="PUBLISHED"
        return (201,{},{"x-restli-id":"urn:li:share:123456789"})
    publisher=SocialTextPublisher(graph_version="v26.0",linkedin_version="202610",
                                  transport=transport,enabled=True)
    assert publisher.publish(JOB,ctx("linkedin")).remote_id=="urn:li:share:123456789"
    bad=ctx("linkedin")
    bad["account"]["granted_scopes"]=["openid"]
    with pytest.raises(ProviderFailure) as e:
        publisher.publish(JOB,bad)
    assert e.value.definitely_not_sent
    assert len(requests)==1


def test_wrong_shop_provider_media_and_identifier_denied_before_any_provider_post():
    calls=[]
    publisher=SocialTextPublisher(graph_version="v26.0",linkedin_version="202610",
        transport=lambda req:calls.append(req),enabled=True)
    for bad in [
        {**ctx(),"job":{**ctx()["job"],"shop_id":"foreign"}},
        {**ctx(),"job":{**ctx()["job"],"media_asset_id":ACCOUNT}},
        {**ctx(),"account":{**ctx()["account"],"provider":"youtube"}},
        {**ctx(),"provider_access_token":""},
        ctx("instagram"),
    ]:
        with pytest.raises(ProviderFailure):
            publisher.publish(JOB,bad)
    assert calls==[]


def test_invalid_or_ambiguous_provider_response_must_not_be_retried():
    for response in [(200,{},{}),(503,{"error":"private"},{}),
                     (200,{"id":"123456789_12_other"},{}),
                     (200,{"id":"888_123"}, {})]:
        calls=[]
        def transport(req):
            calls.append(req)
            return response
        publisher=SocialTextPublisher(graph_version="v26.0",linkedin_version="202610",
                                      enabled=True,transport=transport)
        with pytest.raises(ProviderFailure) as e:
            publisher.publish(JOB,ctx())
        assert not e.value.definitely_not_sent
        assert e.value.code=="PROVIDER_RESULT_UNCERTAIN"
        assert len(calls)==1


def test_network_default_refuses_external_hosts_before_network():
    request=ProviderRequest("POST","https://malicious.invalid/steal",
                            headers={"Authorization":"Bearer token"},body={})
    with pytest.raises(ProviderFailure,match="UNAPPROVED_PROVIDER_ENDPOINT") as e:
        network_text_transport(request)
    assert e.value.definitely_not_sent


def test_exception_redaction_and_no_send_on_missing_scope():
    def failure(_):
        raise RuntimeError("provider access token SECRET-DO-NOT-LEAK")
    publisher=SocialTextPublisher(graph_version="v26.0",linkedin_version="202610",
                                  enabled=True,transport=failure)
    with pytest.raises(ProviderFailure) as e:
        publisher.publish(JOB,ctx("linkedin"))
    assert "SECRET" not in repr(e.value)
    assert e.value.__cause__ is None
