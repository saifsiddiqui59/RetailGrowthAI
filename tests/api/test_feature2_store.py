"""Feature #2 shared/tenant Supabase adapter contracts without any cloud secrets."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature2_store import TrendSnapshotStore, TenantDraftStore, authorized_profile_reader
from tenant_store import StorageUnavailable

NOW = datetime(2026, 10, 26, 10, tzinfo=timezone.utc)
SHOP, USER, ASSET = (str(uuid4()) for _ in range(3))
TOKEN = str(uuid4())


class Admin:
    def __init__(self):
        self.calls = []
        self.claimed = False
        self.saved = False

    def request(self, path, *, method="GET", query=None, data=None):
        self.calls.append((path, method, query, data))
        if path == "shop_content_drafts":
            assert method == "POST"
            assert data["shop_id"] == SHOP and data["created_by"] == USER
            assert data["content"]["review"]["can_publish"] is False
            assert data["trend_id"] == "b" * 32
            return [{"id": str(uuid4()), "shop_id": SHOP, "created_by": USER}]
        if path == "trend_snapshots":
            return ([{"region": "IN", "expires_at": "2026-10-27T10:00:00+00:00",
                      "snapshot": {"trends": [], "sources": [], "complete": False}}]
                    if self.saved else [])
        if path == "rpc/feature2_claim_collection":
            if self.claimed:
                return None
            self.claimed = True
            return TOKEN
        if path == "rpc/feature2_finish_collection":
            assert data["p_token"] == TOKEN
            self.saved = True
            return True
        raise AssertionError("unlisted worker endpoint: " + path)


def test_shared_daily_claim_is_atomic_and_fenced():
    admin = Admin()
    store = TrendSnapshotStore(admin, clock=lambda: NOW)
    assert store.load("IN") is None
    assert store.claim_day("IN", "2026-10-26")
    assert admin.calls[-1][0] == "rpc/feature2_claim_collection"
    store.save("IN", {"observed_at": NOW.isoformat(), "trends": [], "sources": []})
    assert store.load("IN")["complete"] is False
    with pytest.raises(StorageUnavailable):
        store.save("IN", {})
    duplicate = TrendSnapshotStore(admin, clock=lambda: NOW)
    assert duplicate.claim_day("IN", "2026-10-26") is False
    assert duplicate.load("IN") is not None
    with pytest.raises(ValueError):
        duplicate.claim_day("US", "2026-10-26")
    with pytest.raises(ValueError):
        duplicate.claim_day("IN", "2026-10-25")


class RlsTenant:
    def __init__(self):
        self.calls = []

    def _request(self, table, token, *, query=None, method="GET", data=None):
        self.calls.append((table, token, method, query, data))
        assert token == "signed-user-JWT"  # no service key
        if table == "business_profiles":
            return [{"shop_id": SHOP, "business_name": "Real Boutique",
                     "category": "Fashion retail", "city": "Nagpur",
                     "brand_voice": "friendly", "description": "No structured products"}]
        if table == "shop_content_drafts":
            assert method == "POST"
            assert data["shop_id"] == SHOP and data["created_by"] == USER
            assert data["content"]["review"]["can_publish"] is False
            assert data["trend_id"] == "b" * 32
            return [{"id": str(uuid4()), "shop_id": SHOP, "created_by": USER}]
        raise AssertionError("unexpected table")


def test_profile_reads_only_rls_business_row_without_claiming_a_product_catalog():
    tenant = RlsTenant()
    profile = authorized_profile_reader(tenant)("signed-user-JWT", USER, SHOP)
    assert profile["category"] == "clothing"
    assert profile["products"] == []  # description is not authoritative stock
    assert profile["city"] == "Nagpur"
    assert tenant.calls[0][0:3] == ("business_profiles", "signed-user-JWT", "GET")
    assert authorized_profile_reader(tenant)("signed-user-JWT", USER, str(uuid4())) is None


def test_draft_save_requires_verified_shop_and_returns_rls_insert_ack():
    admin = Admin()
    draft = {"campaign": {"shop_id": SHOP}, "content_days": [{"trend_id": "b" * 32}],
             "review": {"can_publish": False, "status": "DRAFT"}}
    saved = TenantDraftStore(admin).save_draft("signed-user-JWT", USER, SHOP, draft)
    assert saved
    assert admin.calls[0][0:2] == ("shop_content_drafts", "POST")
    with pytest.raises(PermissionError):
        TenantDraftStore(admin).save_draft("signed-user-JWT", USER, str(uuid4()), draft)
    with pytest.raises(ValueError):
        TenantDraftStore(admin).save_draft(
            "signed-user-JWT", USER, SHOP,
            {"campaign": {"shop_id": SHOP}, "content_days": [], "review": {}})


def test_rls_saved_draft_reads_are_shop_scoped_review_only_and_bounded():
    content = {"campaign": {"shop_id": SHOP, "days": []}, "content_days": [],
               "review": {"status": "DRAFT", "can_publish": False}}
    fixture = {"id": str(uuid4()), "shop_id": SHOP, "trend_id": "b" * 32,
               "created_at": NOW.isoformat(), "review_state": "DRAFT", "content": content}

    class UserOnlyReader:
        def __init__(self, rows):
            self.rows = rows
            self.calls = []
        def _request(self, table, token, *, query):
            self.calls.append((table, token, query))
            assert token == "signed-user-JWT"
            return self.rows

    reader = UserOnlyReader([fixture])
    result = TenantDraftStore(Admin(), reader).list_drafts("signed-user-JWT", SHOP)
    assert result[0]["id"] == fixture["id"] and result[0]["content"] == content
    assert reader.calls[0][0] == "shop_content_drafts"
    assert reader.calls[0][2]["shop_id"] == "eq." + SHOP
    assert reader.calls[0][2]["order"] == "created_at.desc"
    assert reader.calls[0][2]["limit"] == "5"
    with pytest.raises(StorageUnavailable):
        TenantDraftStore(Admin()).list_drafts("signed-user-JWT", SHOP)
    with pytest.raises(ValueError):
        TenantDraftStore(Admin(), reader).list_drafts("signed-user-JWT", SHOP, limit=20)
    for invalid in (
        {**fixture, "shop_id": str(uuid4())},
        {**fixture, "review_state": "APPROVED"},
        {**fixture, "content": {"campaign": {"shop_id": str(uuid4())},
                               "content_days": [], "review": content["review"]}},
        {**fixture, "content": {"campaign": {"shop_id": SHOP}, "content_days": [],
                               "review": {"status": "DRAFT", "can_publish": True}}},
    ):
        with pytest.raises(StorageUnavailable):
            TenantDraftStore(Admin(), UserOnlyReader([invalid])).list_drafts("signed-user-JWT", SHOP)
