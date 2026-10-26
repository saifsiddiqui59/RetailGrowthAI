"""Feature #2 adapter denies foreign shops and never persists unreviewed publishing."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature2_adapter import TrendFeatureAdapter
from ai_agents.trend_intelligence import collect

NOW = datetime(2026, 10, 26, 8, tzinfo=timezone.utc)
USER, SHOP, ASSET = (str(uuid4()) for _ in range(3))
RSS = b"<rss><channel><item><title>Saree fashion</title><link>https://trends.google.com/trending?geo=IN</link></item></channel></rss>"
S = collect(NOW, environ={"RETAIL_TRENDS_GOOGLE_RSS_ENABLED": "1"},
            get=lambda url, *, timeout: RSS)

class Store:
    def member(self, token, user, shop, *, write=False):
        return token == "signed-1" and user == USER and shop == SHOP
    def assets(self, token, shop, asset_ids):
        return token == "signed-1" and shop == SHOP and tuple(asset_ids) == (ASSET,)

class Shared:
    def load(self, region):
        assert region == "IN"
        return S

class Drafts:
    def __init__(self):
        self.saved = []
    def save_draft(self, token, user, sid, draft):
        assert draft["review"]["can_publish"] is False
        assert all(day["review_status"] == "DRAFT" for day in draft["campaign"]["days"])
        self.saved.append((token, user, sid, draft))
        return str(uuid4())


def profile(token, user, sid):
    assert token == "signed-1" and user == USER
    return dict(shop_id=sid, name="Boutique", category="clothing", city="Nagpur",
                brand_voice="helpful", language="en-IN", products=["saree"],
                audience="retail customers", objective="awareness",
                platforms=["linkedin", "instagram"], cta="Ask for details")


def campaign():
    return {"shop_id": SHOP, "brief": "Create clothing outfit ideas",
            "duration_days": 7, "start_date": "2026-10-27",
            "timezone": "Asia/Kolkata", "language": "en-IN",
            "platforms": ["linkedin", "instagram"],
            "media_asset_ids": [ASSET], "offer": None}


def make_adapter(drafts=None, reader=profile):
    return TrendFeatureAdapter(lambda token: USER if token == "signed-1" else
                               (_ for _ in ()).throw(ValueError("bad token")),
                               Store(), reader, Shared(), drafts, lambda: NOW)


def test_get_uses_membership_and_never_exposes_other_shops():
    api = make_adapter()
    code, body = api.handle("GET", SHOP, "Bearer signed-1")
    assert code == 200 and len(body["recommendations"]) == 1
    assert body["recommendations"][0]["approval_status"] == "DRAFT"
    assert api.handle("GET", str(uuid4()), "Bearer signed-1")[0] == 404
    assert api.handle("GET", SHOP, "")[0] == 401
    assert api.handle("GET", SHOP, "Bearer invalid-user-token")[0] == 401
    assert api.handle("POST", SHOP, "Bearer invalid-user-token",
                      {"trend_id": S["trends"][0]["trend_id"], "campaign": campaign()})[0] == 401


def test_post_requires_persistence_and_server_verified_media():
    no_store = make_adapter()
    assert no_store.handle("POST", SHOP, "Bearer signed-1", {
        "trend_id": S["trends"][0]["trend_id"], "campaign": campaign()})[0] == 503
    drafts = Drafts()
    api = make_adapter(drafts)
    trend_id = S["trends"][0]["trend_id"]
    code, body = api.handle("POST", SHOP, "Bearer signed-1", {
        "trend_id": trend_id, "campaign": campaign()})
    assert code == 201 and body["status"] == "DRAFT"
    assert len(drafts.saved) == 1
    assert api.handle("POST", SHOP, "Bearer signed-1",
                      {"trend_id": "not-a-trend", "campaign": campaign()})[0] == 409
    foreign = campaign()
    foreign["shop_id"] = str(uuid4())
    assert api.handle("POST", SHOP, "Bearer signed-1",
                      {"trend_id": trend_id, "campaign": foreign})[0] == 403
    assert len(drafts.saved) == 1


def test_cross_shop_profile_leak_is_denied():
    def evil(token, user, sid):
        p = profile(token, user, sid)
        p["shop_id"] = str(uuid4())
        return p
    assert make_adapter(reader=evil).handle("GET", SHOP, "Bearer signed-1")[0] == 404


def test_new_retailer_missing_city_is_guided_without_fabricating_trends_or_saving():
    def incomplete(token, user, sid):
        record = profile(token, user, sid)
        record["city"] = ""
        record["category"] = "general"
        record["products"] = []
        return record

    class MustNotLoad:
        def load(self, region):
            raise AssertionError("An incomplete business must not load or personalize trends")

    drafts = Drafts()
    api = make_adapter(drafts, incomplete)
    api.snapshot_store = MustNotLoad()
    status, body = api.handle("GET", SHOP, "Bearer signed-1")
    assert status == 200
    assert body == {
        "shop_id": SHOP, "profile_required": True,
        "recommendations": [], "sources": [], "complete": False,
        "observed_at": None,
    }
    status, body = api.handle("POST", SHOP, "Bearer signed-1", {
        "trend_id": S["trends"][0]["trend_id"], "campaign": campaign(),
    })
    assert (status, body) == (422, {"error": "BUSINESS_PROFILE_INCOMPLETE"})
    assert drafts.saved == []
    assert api.handle("GET", SHOP, "Bearer forged")[0] == 401
    assert api.handle("GET", str(uuid4()), "Bearer signed-1")[0] == 404


def test_saved_drafts_use_user_jwt_even_when_source_and_profile_are_unavailable():
    drafts = Drafts()

    def only_signed_user_read(token, sid, limit=5):
        assert token == "signed-1" and sid == SHOP and limit == 5
        return [{"id": str(uuid4()), "shop_id": SHOP, "review_state": "DRAFT"}]

    drafts.list_drafts = only_signed_user_read
    adapter = make_adapter(drafts)
    adapter.profile_reader = None
    adapter.snapshot_store = None
    code, body = adapter.list_drafts(SHOP, "Bearer signed-1")
    assert code == 200 and body["shop_id"] == SHOP and len(body["drafts"]) == 1
    assert adapter.list_drafts(SHOP, "Bearer bad-token")[0] == 401
    assert adapter.list_drafts(str(uuid4()), "Bearer signed-1")[0] == 404
    assert adapter.list_drafts(SHOP, "")[0] == 401
    assert make_adapter().list_drafts(SHOP, "Bearer signed-1") == (
        503, {"error": "CONTENT_DRAFT_STORE_NOT_CONFIGURED"})
