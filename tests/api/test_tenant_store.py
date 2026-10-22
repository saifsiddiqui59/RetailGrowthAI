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


def test_draft_rpc_passes_user_jwt_and_conditional_old_values():
    captured = []
    def transport(req, timeout):
        captured.append(req)
        return MockResponse(True)
    store = TenantStore("https://retail.supabase.co", "publishable-key", transport)
    cid, did = str(uuid4()), str(uuid4())
    expected = {"topic": "old", "linkedin": {"post_text": "old"}, "instagram": {"caption": "old"}}
    changes = {"topic": "new", "linkedin": {"post_text": "new"}, "instagram": {"caption": "new"}}
    assert store.save_day("signed-user-token", SHOP, cid, did, expected, changes)
    req = captured[0]
    assert urlsplit(req.full_url).path == "/rest/v1/rpc/save_campaign_day"
    assert req.get_method() == "POST"
    assert req.get_header("Authorization") == "Bearer signed-user-token"
    assert req.get_header("Apikey") == "publishable-key"
    sent = json.loads(req.data)
    assert sent == {
        "p_shop_id": SHOP, "p_campaign_id": cid, "p_day_id": did,
        "p_expected": expected, "p_changes": changes,
    }


def test_draft_rpc_false_and_malformed_result_are_not_success():
    from tenant_store import StorageUnavailable
    import pytest
    store = TenantStore("https://retail.supabase.co", "publishable-key",
                        lambda req, timeout: MockResponse(False))
    assert store.save_day("jwt", SHOP, str(uuid4()), str(uuid4()), {}, {}) is False
    store.transport = lambda req, timeout: MockResponse({"updated": True})
    with pytest.raises(StorageUnavailable):
        store.save_day("jwt", SHOP, str(uuid4()), str(uuid4()), {}, {})
