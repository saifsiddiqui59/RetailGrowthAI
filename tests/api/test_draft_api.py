"""HTTP draft editing: authorization, v1 contract, media checks, conflicts."""
import copy
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from http_api import HTTPAPI
from security import AuthenticationError

SAMPLE = json.loads((ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json").read_text())
CID, SID, DID = SAMPLE["id"], SAMPLE["shop_id"], SAMPLE["days"][0]["id"]
USER = str(uuid4())


class Store:
    def __init__(self):
        self.data = copy.deepcopy(SAMPLE)
        self.enabled = True
        self.write = True
        self.assets_allowed = True
        self.conflict = False
        self.saved = []
    def campaign(self, token, user, campaign_id):
        if not self.enabled or user != USER or token != "signed" or campaign_id != CID:
            return None
        return copy.deepcopy(self.data)
    def member(self, token, user, shop, *, write=False):
        return self.enabled and shop == SID and user == USER and token == "signed" and (not write or self.write)
    def assets(self, token, shop, asset_ids):
        return self.assets_allowed and shop == SID and token == "signed" and bool(asset_ids)
    def save_day(self, token, shop, campaign, day, expected, changes):
        self.saved.append((token, shop, campaign, day, expected, changes))
        if self.conflict: return False
        current = self.data["days"][0]
        if day != DID or any(current[k] != expected[k] for k in expected):
            return False
        current.update(copy.deepcopy(changes))
        return True


def app(store):
    def verify(token):
        if token != "signed": raise AuthenticationError()
        return USER
    return HTTPAPI(verify, store)


def edit():
    return {key: copy.deepcopy(SAMPLE["days"][0][key])
            for key in ("topic", "linkedin", "instagram")}


def route(campaign=CID, day=DID):
    return f"/campaigns/{campaign}/days/{day}"


def test_valid_save_returns_committed_day_with_identity_unchanged():
    store = Store()
    body = edit()
    body["linkedin"]["post_text"] = "A verified new marketing draft"
    status, payload = app(store).handle("PATCH", route(), "Bearer signed", body)
    assert status == 200 and payload["day"]["linkedin"]["post_text"] == body["linkedin"]["post_text"]
    assert payload["day"]["shop_id"] == SID
    assert len(store.saved) == 1
    assert store.saved[0][1:4] == (SID, CID, DID)


def test_unauthorized_and_cross_tenant_are_hidden():
    store = Store()
    assert app(store).handle("PATCH", route(), "", edit())[0] == 401
    assert app(store).handle("PATCH", route(), "Bearer forged", edit())[0] == 401
    assert app(store).handle("PATCH", route(str(uuid4())), "Bearer signed", edit())[0] == 404
    assert app(store).handle("PATCH", route(CID, str(uuid4())), "Bearer signed", edit())[0] == 404
    assert not store.saved


def test_viewer_or_revoked_editor_cannot_change_a_day():
    store = Store()
    store.write = False
    assert app(store).handle("PATCH", route(), "Bearer signed", edit()) == (403, {"error": "FORBIDDEN"})
    store.enabled = False
    assert app(store).handle("PATCH", route(), "Bearer signed", edit())[0] == 404
    assert not store.saved


def test_malicious_fields_and_invalid_timeline_fail_before_rpc():
    store = Store()
    body = edit()
    body["shop_id"] = str(uuid4())
    assert app(store).handle("PATCH", route(), "Bearer signed", body)[0] == 400
    body = edit()
    body["instagram"]["reel"]["storyboard"][0]["duration_seconds"] = 12
    assert app(store).handle("PATCH", route(), "Bearer signed", body)[0] == 400
    body = edit()
    body["topic"] = SAMPLE["days"][1]["topic"]
    assert app(store).handle("PATCH", route(), "Bearer signed", body)[0] == 400
    assert not store.saved


def test_assets_and_optimistic_conflicts_fail_closed():
    store = Store()
    store.assets_allowed = False
    assert app(store).handle("PATCH", route(), "Bearer signed", edit())[0] == 403
    store.assets_allowed = True
    store.conflict = True
    assert app(store).handle("PATCH", route(), "Bearer signed", edit()) == (409, {"error": "EDIT_CONFLICT"})
    assert len(store.saved) == 1


def test_non_draft_cannot_save():
    store = Store()
    store.data["status"] = "PLANNING"
    assert app(store).handle("PATCH", route(), "Bearer signed", edit())[0] == 409
    assert not store.saved
