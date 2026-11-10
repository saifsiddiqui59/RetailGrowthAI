"""Exercise all four real Python VoiceStudio adapters together, with fake SQL.

Not an actual Supabase migration or a real voice model. This ensures the
worker adapters' exact argument/result signatures compose without bypasses.
"""
import io
import json
from pathlib import Path
import sys
from uuid import uuid4

import pytest

from ai_agents.feature2_voicestudio_adapter import VoiceStudioUnavailable
from ai_agents.feature2_voicestudio_registration import run_verified_private_voice_job
from test_feature2_voicestudio_registration import TrustedSQL, StubPrivateNetwork

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from feature2_voicestudio_sql import VoiceStudioSqlStore, VoiceStudioSqlDenied  # noqa: E402
from feature2_voicestudio_storage import VoiceStudioPrivateStorage  # noqa: E402


class SqlResponse(io.BytesIO):
    def __init__(self, url, data):
        super().__init__(json.dumps(data).encode("utf-8"))
        self.url = url
        self.status = 200
        self.headers = {"Content-Type": "application/json"}

    def geturl(self):
        return self.url


class SqlNetwork:
    def __init__(self, trusted, actor):
        self.trusted = trusted
        self.actor = actor
        self.calls = []
        self.fake_claim = None
        self.revoked = False

    def __call__(self, req, timeout):
        self.calls.append((req.full_url, json.loads(req.data)))
        assert timeout == 12
        assert req.get_header("Apikey").startswith("sb_secret_")
        args = json.loads(req.data)
        assert args["p_actor_id"] == self.actor
        s, c = args["p_shop_id"], args["p_campaign_id"]
        if s != self.trusted.shop or c != self.trusted.campaign or self.revoked:
            raise PermissionError("test current membership revoked")
        operation = req.full_url.rsplit("/", 1)[-1]
        if operation == "feature2_voicestudio_plan":
            result = self.trusted.read_plan(s, c)
        elif operation == "feature2_voicestudio_claim":
            result = self.trusted.claim(s, c, args["p_request_id"], args["p_plan_sha256"])
            self.fake_claim = result
        elif operation == "feature2_voicestudio_register":
            assert self.fake_claim is not None
            result = self.trusted.register(
                s, c, args["p_request_id"], self.fake_claim, {
                    "original_sha256": args["p_original_sha256"],
                    "render_sha256": args["p_render_sha256"],
                    "original_bytes": args["p_original_bytes"],
                    "render_bytes": args["p_render_bytes"],
                    "requires_human_review": True,
                    "publish_approved": False,
                },
            )
        elif operation == "feature2_voicestudio_receipt":
            result = self.trusted.read_receipt(s, c, args["p_request_id"])
        else:
            raise AssertionError("unexpected SQL endpoint")
        if result is None:
            raise PermissionError("test SQL claim/receipt unavailable")
        return SqlResponse(req.full_url, result)


def build():
    trusted = TrustedSQL()
    actor = str(uuid4())
    sql_net = SqlNetwork(trusted, actor)
    sql = VoiceStudioSqlStore(
        "https://fixture.supabase.co", "sb_secret_test-not-real-123456789",
        actor, transport=sql_net,
    )
    private_net = StubPrivateNetwork()
    store = VoiceStudioPrivateStorage(
        "https://fixture.supabase.co", "sb_secret_test-not-real-123456789",
        transport=private_net,
    )
    kwargs = dict(
        shop_id=trusted.shop, campaign_id=trusted.campaign,
        request_id=trusted.job, voice="alloy", reel_seconds=15,
        base_url="http://127.0.0.1:3900",
        api_key="fake-provider-key-no-use",
        storage=store,
        read_current_plan=sql.read_current_plan,
        claim_once=sql.claim_once,
        register_verified_private_pair=sql.register_verified_private_pair,
        read_private_receipt=sql.read_private_receipt,
        enabled=True, commercial_model_verified=True,
        transport=private_net,
    )
    return trusted, sql_net, private_net, kwargs


def test_original_key_sql_client_real_storage_and_f2_producer_compose():
    trusted, sql_net, private_net, args = build()
    result = run_verified_private_voice_job(**args)
    assert result["audio_asset_id"] == trusted.asset
    assert result["review_status"] == "NEEDS_REVIEW"
    assert result["approved_to_render_or_publish"] is False
    assert trusted.registrations == 1
    assert private_net.speech_calls == 1
    assert len(private_net.objects) == 2
    assert [url.rsplit("/", 1)[-1] for url, _ in sql_net.calls].count("feature2_voicestudio_plan") >= 2
    assert [url.rsplit("/", 1)[-1] for url, _ in sql_net.calls].count("feature2_voicestudio_register") == 1
    with pytest.raises((VoiceStudioUnavailable, VoiceStudioSqlDenied, PermissionError)):
        run_verified_private_voice_job(**args)
    assert private_net.speech_calls == 1


def test_sql_membership_revocation_prevents_provider_and_storage_egress():
    trusted, sql_net, private_net, args = build()
    sql_net.revoked = True
    with pytest.raises(VoiceStudioSqlDenied, match="denied or uncertain"):
        run_verified_private_voice_job(**args)
    assert private_net.calls == [] and trusted.registrations == 0


def test_sql_backend_lost_registration_ack_has_no_second_original_attempt():
    trusted, sql_net, private_net, args = build()
    original = sql_net.__call__
    def lost_ack(req, timeout):
        if req.full_url.endswith("feature2_voicestudio_register"):
            raise TimeoutError("SQL may already have committed")
        return original(req, timeout)
    sql_net.__call__ = lost_ack
    # SqlStore retained the original bound callback at construction, so
    # replace only this trusted worker-side instance for this test.
    args["register_verified_private_pair"] = lambda *a: (_ for _ in ()).throw(TimeoutError("uncertain SQL ACK"))
    with pytest.raises(TimeoutError):
        run_verified_private_voice_job(**args)
    assert private_net.speech_calls == 1
    assert trusted.registrations == 0
    with pytest.raises((VoiceStudioUnavailable, VoiceStudioSqlDenied, PermissionError)):
        run_verified_private_voice_job(**args)
    assert private_net.speech_calls == 1
