"""Retained JWT/RLS permissions around disabled VoiceStudio HTTP handoff.

All tests are synthetic; no network, real JWT, paid ASR or rights approvals.
"""
from uuid import uuid4
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from feature2_voicestudio_http import VoiceStudioSignedAPI  # noqa: E402
from feature2_voicestudio_sql import VoiceStudioSqlDenied  # noqa: E402
from security import AuthenticationError  # noqa: E402

SHOP, CAMPAIGN, JOB, USER, ASSET = (str(uuid4()) for _ in range(5))


class Tenant:
    def __init__(self):
        self.calls = []
        self.allow = True
        self.revoke_after_one = False

    def member(self, token, uid, shop, *, write=False):
        self.calls.append((token, uid, shop, write))
        if self.revoke_after_one and len(self.calls) > 1:
            return False
        return self.allow and token == "valid-token" and uid == USER and shop == SHOP and write


class SQL:
    def __init__(self, *, revoked=False):
        self.revoked = revoked
        self.calls = 0

    def read_current_plan(self, shop, campaign):
        self.calls += 1
        if self.revoked:
            raise VoiceStudioSqlDenied("private scripted source revoked")
        return {
            "shop_id": shop, "campaign_id": campaign,
            "voice": "alloy", "duration_seconds": 15,
        }

    def claim_once(self, *args): pass
    def register_verified_private_pair(self, *args): pass
    def read_private_receipt(self, *args): pass


def fixture(**changes):
    tenant, sql = Tenant(), SQL()
    worker_calls = []
    def worker(**kwargs):
        worker_calls.append(kwargs)
        return {
            "shop_id": SHOP, "campaign_id": CAMPAIGN,
            "request_id": JOB, "audio_asset_id": ASSET,
            "review_status": "NEEDS_REVIEW", "approved_to_render_or_publish": False,
            "private_audio_url": None,
        }
    verify = lambda token: USER if token == "valid-token" else (_ for _ in ()).throw(AuthenticationError("bad JWT"))
    args = {
        "verify_token": verify,
        "tenant_store": tenant,
        "sql_store_factory": lambda uid: sql,
        "storage": object(),
        "base_url": "http://127.0.0.1:3900",
        "api_key": "server-private-key-only",
        "enabled": True, "commercial_model_verified": True,
        "worker": worker,
    }
    args.update(changes)
    return VoiceStudioSignedAPI(**args), tenant, sql, worker_calls


def body():
    return {"campaign_id": CAMPAIGN, "request_id": JOB}


def test_signed_editor_gets_review_only_receipt_without_private_audio_or_key():
    api, tenant, sql, calls = fixture()
    status, result = api.generate(SHOP, "Bearer valid-token", body())
    assert status == 202
    assert result["review_status"] == "NEEDS_REVIEW"
    assert result["audio_asset_id"] == ASSET
    assert result["approved_to_render_or_publish"] is False
    assert result["private_audio_url"] is None
    assert result["replay_on_timeout"] is False
    assert "api_key" not in result
    assert len(tenant.calls) == 2 and all(x[-1] for x in tenant.calls)
    assert sql.calls == 1
    assert len(calls) == 1
    assert calls[0]["voice"] == "alloy" and calls[0]["reel_seconds"] == 15
    assert calls[0]["base_url"] == "http://127.0.0.1:3900"


@pytest.mark.parametrize("auth", [
    "", "Basic secret", "Bearer ", "Bearer forged-user", None,
])
def test_anonymous_and_unverified_jwt_denied_before_db_or_model(auth):
    api, tenant, sql, calls = fixture()
    status, result = api.generate(SHOP, auth, body())
    assert status == 401
    assert result["error"] == "UNAUTHORIZED"
    assert tenant.calls == [] and sql.calls == 0 and calls == []


@pytest.mark.parametrize("invalid", [
    {}, {"request_id": JOB}, {"campaign_id": CAMPAIGN},
    {"campaign_id": CAMPAIGN, "request_id": JOB, "voice": "evil"},
    {"campaign_id": CAMPAIGN, "request_id": "not-a-uuid"},
    {"campaign_id": "foreign", "request_id": JOB},
])
def test_browser_cannot_override_script_voice_model_or_approval(invalid):
    api, tenant, sql, calls = fixture()
    status, result = api.generate(SHOP, "Bearer valid-token", invalid)
    assert status == 400
    assert sql.calls == 0 and calls == []


def test_foreign_shop_denied_by_live_membership_before_sql_and_provider():
    api, tenant, sql, calls = fixture()
    status, result = api.generate(str(uuid4()), "Bearer valid-token", body())
    assert status == 404 and result["error"] == "NOT_FOUND"
    assert sql.calls == 0 and calls == []


def test_disabled_configuration_never_claims_or_calls_provider():
    for flags in ({"enabled": False}, {"commercial_model_verified": False}):
        api, tenant, sql, calls = fixture(**flags)
        status, _ = api.generate(SHOP, "Bearer valid-token", body())
        assert status == 503
        assert sql.calls == 0 and calls == []


def test_revocation_during_worker_denies_audio_asset_disclosure():
    api, tenant, sql, calls = fixture()
    tenant.revoke_after_one = True
    status, result = api.generate(SHOP, "Bearer valid-token", body())
    assert status == 403 and result["error"] == "VOICE_ACCESS_REVOKED"
    assert len(calls) == 1


def test_backend_sql_denial_is_redacted_as_503_not_client_400():
    sql = SQL(revoked=True)
    api, tenant, _, calls = fixture(sql_store_factory=lambda uid: sql)
    status, result = api.generate(SHOP, "Bearer valid-token", body())
    assert status == 503 and result["error"] == "VOICE_STUDIO_UNAVAILABLE"
    assert "revoked" not in str(result)
    assert calls == []


def test_worker_source_failure_is_unavailable_not_approved():
    def worker(**kwargs):
        raise TimeoutError("provider uncertain SQL ACK private secret")
    api, tenant, sql, calls = fixture(worker=worker)
    status, result = api.generate(SHOP, "Bearer valid-token", body())
    assert status == 503 and result == {"error": "VOICE_STUDIO_UNAVAILABLE"}


def test_forged_worker_receipt_not_returned_as_client_error():
    def worker(**kwargs):
        return {
            "shop_id": SHOP, "campaign_id": CAMPAIGN, "request_id": JOB,
            "audio_asset_id": "fake", "review_status": "NEEDS_REVIEW",
            "approved_to_render_or_publish": False, "private_audio_url": None,
        }
    api, tenant, sql, calls = fixture(worker=worker)
    status, result = api.generate(SHOP, "Bearer valid-token", body())
    assert status == 503 and result == {"error": "VOICE_PRIVATE_REVIEW_UNVERIFIED"}
