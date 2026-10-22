"""Verifies token forwarding and tenant-filter predicates (no network)."""
import io
import json
import sys
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from tenant_store import TenantStore

USER, SHOP, ASSET = (str(uuid4()) for _ in range(3))


class MockResponse:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.data).encode()


def test_membership_and_assets_uses_bearer_and_tenant_scope():
    requests = []
    def transport(req, timeout):
        requests.append(req)
        path = urlsplit(req.full_url).path
        if path.endswith("shop_memberships"): return MockResponse([{"role": "EDITOR"}])
        if path.endswith("media_assets"): return MockResponse([{"id": ASSET}])
        return MockResponse([])
    store = TenantStore("https://retail.supabase.co", "publishable-key", transport)
    assert store.member("valid-user-jwt", USER, SHOP, write=True)
    assert store.assets("valid-user-jwt", SHOP, (ASSET,))
    assert all(req.get_header("Authorization") == "Bearer valid-user-jwt" for req in requests)
    assert all(req.get_header("Apikey") == "publishable-key" for req in requests)
    membership = parse_qs(urlsplit(requests[0].full_url).query)
    media = parse_qs(urlsplit(requests[1].full_url).query)
    assert membership["user_id"] == ["eq." + USER]
    assert membership["shop_id"] == ["eq." + SHOP]
    assert membership["active"] == ["eq.true"]
    assert media["shop_id"] == ["eq." + SHOP]


def test_forged_asset_and_inactive_member_rejected():
    def transport(req, timeout): return MockResponse([])
    store = TenantStore("https://retail.supabase.co", "publishable-key", transport)
    assert not store.member("jwt", USER, SHOP)
    assert not store.assets("jwt", SHOP, [ASSET])


def test_campaign_foreign_row_hidden_even_from_bad_backend_response():
    cid = str(uuid4())
    def transport(req, timeout):
        if "/campaigns?" in req.full_url:
            return MockResponse([{"id": cid, "shop_id": SHOP, "status": "DRAFT"}])
        if "/shop_memberships?" in req.full_url: return MockResponse([])
        raise AssertionError("should not request days")
    store = TenantStore("https://retail.supabase.co", "publishable-key", transport)
    assert store.campaign("jwt", USER, cid) is None
