"""Offline poster draft API permission tests; no live Supabase, queues or media writes."""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from http_api import HTTPAPI
from poster_draft_api import PosterDraftAPI
from security import AuthenticationError

USER, FOREIGN_USER, SHOP, CAMPAIGN, DAY, PHOTO, LOGO, POSTER = [str(uuid4()) for _ in range(8)]


class Store:
    def __init__(self):
        self.writable = True
        self.allowed_assets = True
        self.rpc_result = POSTER
        self.inserted = []
        self.status = "DRAFT"

    def campaign(self, token, user, cid):
        if token != "retailer-token" or user != USER or cid != CAMPAIGN:
            return None
        return {
            "id": CAMPAIGN, "shop_id": SHOP, "status": self.status,
            "days": [{
                "id": DAY, "shop_id": SHOP, "campaign_id": CAMPAIGN,
                "review_status": "DRAFT",
                "instagram": {"reel": {"storyboard": [{"asset_id": PHOTO}]}}
            }]
        }

    def member(self, token, user, shop, *, write=False):
        return token == "retailer-token" and user == USER and shop == SHOP and (
            self.writable or not write
        )

    def assets(self, token, shop, ids):
        return self.allowed_assets and token == "retailer-token" and shop == SHOP and (
            ids == [PHOTO] or ids == [PHOTO, LOGO]
        )

    def create_poster_draft(self, token, fields):
        self.inserted.append((token, fields))
        return self.rpc_result

    def poster_draft(self, token, user, draft_id):
        if draft_id != POSTER or not self.member(token, user, SHOP):
            return None
        return {"id": POSTER, "shop_id": SHOP, "campaign_id": CAMPAIGN,
                "day_id": DAY, "status": "DRAFT", "template": "editorial",
                "format": "portrait", "source_asset_id": PHOTO,
                "business_name": "Clothing Studio", "accent_color": "#BB6644",
                "background_color": "#FEF8F3", "offer_text": None,
                "output_asset_id": None}


def params(**updates):
    return {
        **{"day_id": DAY, "source_asset_id": PHOTO, "logo_asset_id": None,
           "template": "editorial", "format": "portrait",
           "business_name": "Clothing Studio", "accent_color": "#BB6644",
           "background_color": "#FEF8F3", "offer_text": None},
        **updates,
    }


def app(store, *, configured=True):
    def verify(token):
        if token == "retailer-token":
            return USER
        if token == "foreign-token":
            return FOREIGN_USER
        raise AuthenticationError("unknown token")
    return HTTPAPI(verify, store, poster_api=PosterDraftAPI(store) if configured else None)


def post(store, body=None, *, bearer="Bearer retailer-token", path=None):
    return app(store).handle("POST", path or "/campaigns/" + CAMPAIGN + "/posters",
                             bearer, params() if body is None else body)


def test_owner_metadata_draft_from_saved_storyboard_with_no_worker_side_effects():
    store = Store()
    status, response = post(store)
    assert status == 201
    assert response == {"poster_id": POSTER, "status": "DRAFT"}
    assert len(store.inserted) == 1
    token, fields = store.inserted[0]
    assert token == "retailer-token"
    assert fields == {
        "p_shop_id": SHOP, "p_campaign_id": CAMPAIGN, "p_day_id": DAY,
        "p_source_asset_id": PHOTO, "p_logo_asset_id": None,
        "p_template": "editorial", "p_format": "portrait",
        "p_business_name": "Clothing Studio", "p_accent_color": "#BB6644",
        "p_background_color": "#FEF8F3", "p_offer_text": None,
    }


def test_no_jwt_foreign_user_and_non_writer_rejected_before_rpc():
    store = Store()
    assert post(store, bearer="")[0] == 401
    assert post(store, bearer="Bearer foreign-token")[0] == 404
    store.writable = False
    assert post(store) == (403, {"error": "FORBIDDEN"})
    assert store.inserted == []


def test_unregistered_or_other_day_asset_and_logo_cannot_create():
    store = Store()
    assert post(store, params(source_asset_id=str(uuid4())))[0] == 403
    assert post(store, params(day_id=str(uuid4())))[0] == 404
    store.allowed_assets = False
    assert post(store)[0] == 403
    assert store.inserted == []


def test_no_draft_promotion_and_no_fake_offer_or_unknown_keys():
    store = Store()
    store.status = "PLANNING"
    assert post(store)[0] == 409
    store.status = "DRAFT"
    assert post(store, params(template="nonexistent"))[0] == 400
    assert post(store, params(accent_color="red"))[0] == 400
    assert post(store, params(business_name="Shop\nSECRET"))[0] == 400
    assert post(store, params(offer_text="\x00"))[0] == 400
    assert post(store, params(extra_service_key="fake"))[0] == 400
    assert store.inserted == []


def test_rights_denied_by_transactional_sql_rpc_stays_denied():
    store = Store()
    store.rpc_result = None
    assert post(store) == (403, {"error": "POSTER_DRAFT_DENIED"})
    assert len(store.inserted) == 1


def test_disabled_endpoints_do_not_write_or_leak_cross_tenant_drafts():
    store = Store()
    endpoint = app(store, configured=False)
    assert endpoint.handle("POST", "/campaigns/" + CAMPAIGN + "/posters",
                           "Bearer retailer-token", params())[0] == 503
    assert endpoint.handle("GET", "/poster-drafts/" + POSTER,
                           "Bearer retailer-token")[0] == 503
    assert store.inserted == []
    endpoint = app(store)
    assert endpoint.handle("GET", "/poster-drafts/" + POSTER,
                           "Bearer retailer-token") == (200, {
        "poster_id": POSTER, "status": "DRAFT",
        "campaign_id": CAMPAIGN, "day_id": DAY, "template": "editorial",
        "format": "portrait", "business_name": "Clothing Studio",
        "accent_color": "#BB6644", "background_color": "#FEF8F3",
        "offer_text": None, "source_asset_id": PHOTO, "output_asset_id": None,
    })
    assert endpoint.handle("GET", "/poster-drafts/" + POSTER,
                           "Bearer foreign-token")[0] == 404
    assert endpoint.handle("GET", "/poster-drafts/garbage",
                           "Bearer retailer-token")[0] == 400
