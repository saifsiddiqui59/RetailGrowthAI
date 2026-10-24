"""Poster history may only return RLS-visible saved designs for the same day."""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from poster_draft_api import PosterDraftAPI
from http_api import HTTPAPI
from security import AuthenticationError

UID, SID, CID, DID, PID, SOURCE, JOB = (str(uuid4()) for _ in range(7))


class Store:
    def __init__(self):
        self.enabled = True
        self.called = 0

    def campaign(self, token, user, campaign):
        if token != "JWT" or user != UID or campaign != CID or not self.enabled:
            return None
        return {"id": CID, "shop_id": SID, "status": "DRAFT",
                "days": [{"id": DID, "shop_id": SID, "campaign_id": CID}]}

    def member(self, token, user, shop, write=False):
        return token == "JWT" and user == UID and shop == SID and not write

    def posters_for_day(self, token, shop_id, campaign_id, day_id):
        assert (token,shop_id,campaign_id,day_id) == ("JWT",SID,CID,DID)
        self.called += 1
        return [{"id":PID,"shop_id":SID,"campaign_id":CID,"day_id":DID,
                 "status":"READY","revision":1,"template":"editorial","format":"square",
                 "business_name":"Clothing Shop", "accent_color":"#AA6644",
                 "background_color":"#F5F0E8","offer_text":None,
                 "source_asset_id":SOURCE,"output_asset_id":str(uuid4()),
                 "job_id":JOB,"job_status":"SUCCEEDED"}]


def api(store=None, configured=True):
    store = store or Store()
    def verify(token):
        if token != "JWT": raise AuthenticationError("missing user token")
        return UID
    return HTTPAPI(verify, store, poster_api=PosterDraftAPI(store) if configured else None), store


def request(api, campaign=CID, day=DID, bearer="Bearer JWT"):
    return api.handle("GET", f"/campaigns/{campaign}/days/{day}/posters", bearer)


def test_member_can_reopen_exact_day_without_exposing_storage_path():
    service, store = api()
    status, result = request(service)
    assert status == 200 and len(result["posters"]) == 1
    poster = result["posters"][0]
    assert poster["poster_id"] == PID and poster["job_id"] == JOB
    assert poster["job_status"] == "SUCCEEDED"
    assert not set(poster) & {"shop_id", "object_path", "signed_url", "created_by"}
    assert store.called == 1


def test_foreign_campaign_and_unknown_day_do_not_list_private_drafts():
    service, store = api()
    assert request(service, str(uuid4()))[0] == 404
    assert request(service, CID, str(uuid4()))[0] == 404
    assert store.called == 0


def test_no_auth_or_disabled_flag_does_not_query_store():
    service, store = api()
    assert request(service, bearer="")[0] == 401
    disabled, store = api(store, configured=False)
    assert request(disabled)[0] == 503
    assert store.called == 0


def test_rejects_malformed_ids_and_any_other_method():
    service, store = api()
    assert request(service, campaign="invalid")[0] == 400
    assert request(service, day="invalid")[0] == 400
    assert service.handle("POST",f"/campaigns/{CID}/days/{DID}/posters","Bearer JWT",{})[0] == 404
    assert store.called == 0
