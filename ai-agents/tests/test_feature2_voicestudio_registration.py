"""Offline complete VoiceStudio -> private Supabase WAV -> SQL-CAS callback harness.

Every request is synthetic and all model calls use a fake local transport.
The production model/provider is NOT enabled or commercially certified.
"""
from __future__ import annotations

import io
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4
from urllib.error import HTTPError
import wave

import pytest

from ai_agents.feature2_voicestudio_registration import run_verified_private_voice_job
from ai_agents.feature2_voicestudio_adapter import VoiceStudioUnavailable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from feature2_voicestudio_storage import VoiceStudioPrivateStorage, PrivateVoiceStorageDenied  # noqa: E402


def wav():
    out = io.BytesIO()
    with wave.open(out, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x01\x02" * 16000)
    return out.getvalue()


class Reply(io.BytesIO):
    def __init__(self, url, data, *, status=200, content_type="audio/wav"):
        super().__init__(data)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}

    def geturl(self):
        return self.url


class StubPrivateNetwork:
    def __init__(self):
        self.objects = {}
        self.speech_calls = 0
        self.calls = []
        self.tamper_get = False
        self.fail_second_put = False

    def __call__(self, req, timeout):
        self.calls.append((req.get_method(), req.full_url))
        url = req.full_url
        if url.endswith("/v1/audio/speech"):
            self.speech_calls += 1
            return Reply(url, wav())
        if "/storage/v1/object/retailgrowth-media/" not in url:
            raise AssertionError("untrusted network destination")
        if req.get_method() == "POST":
            if url in self.objects:
                raise HTTPError(url, 409, "no-upsert", {}, None)
            if self.fail_second_put and url.endswith("/render.wav"):
                raise HTTPError(url, 503, "uncertain write acknowledgement", {}, None)
            self.objects[url] = req.data
            return Reply(url, b"", status=201)
        if req.get_method() == "GET" and url in self.objects:
            contents = self.objects[url]
            if self.tamper_get:
                contents = contents[:-1] + bytes([contents[-1] ^ 1])
            return Reply(url, contents)
        raise HTTPError(url, 404, "private WAV missing", {}, None)


class TrustedSQL:
    def __init__(self):
        self.shop = str(uuid4())
        self.other_shop = str(uuid4())
        self.campaign = str(uuid4())
        self.job = str(uuid4())
        self.asset = str(uuid4())
        self.claimed = set()
        self.registrations = 0
        self.revoke_during_register = False
        self.plan = {
            "shop_id": self.shop,
            "campaign_id": self.campaign,
            "voiceover_script": "Fictional retailer voice test.",
            "plan_sha256": sha256(b"reviewed private script").hexdigest(),
            "voice": "alloy",
            "duration_seconds": 15,
            "active_editor": True,
            "script_review": "APPROVED_FOR_NARRATION",
            "can_publish": False,
        }
        self.receipt = None

    def read_plan(self, shop, campaign):
        if shop != self.shop or campaign != self.campaign:
            return None
        return dict(self.plan)

    def claim(self, shop, campaign, request, plan_sha):
        if (shop != self.shop or campaign != self.campaign
                or request in self.claimed or plan_sha != self.plan["plan_sha256"]):
            return None
        self.claimed.add(request)
        return {
            "shop_id": shop, "campaign_id": campaign,
            "request_id": request, "plan_sha256": plan_sha,
            "status": "CLAIMED_ONCE", "paid_inference_calls": 0,
        }

    def register(self, shop, campaign, request, claim, proof):
        assert (shop, campaign, request) == (self.shop, self.campaign, self.job)
        assert claim["plan_sha256"] == self.plan["plan_sha256"]
        assert proof["requires_human_review"] is True
        assert proof["publish_approved"] is False
        self.registrations += 1
        if self.revoke_during_register:
            self.plan["active_editor"] = False
        self.receipt = {
            "audio_asset_id": self.asset,
            "shop_id": shop, "campaign_id": campaign,
            "request_id": request, "plan_sha256": claim["plan_sha256"],
            "original_sha256": proof["original_sha256"],
            "render_sha256": proof["render_sha256"],
            "private": True, "review_status": "NEEDS_REVIEW",
            "commercial_rights_confirmed": True,
            "publish_approved": False,
        }
        return {
            "status": "REGISTERED_PRIVATE_NEEDS_REVIEW",
            "shop_id": shop, "campaign_id": campaign, "request_id": request,
            "original_sha256": proof["original_sha256"],
            "render_sha256": proof["render_sha256"],
            "publish_approved": False,
        }

    def read_receipt(self, shop, campaign, request):
        if (shop, campaign, request) != (self.shop, self.campaign, self.job):
            return None
        return dict(self.receipt) if self.receipt is not None else None


def start(sql, network, **changes):
    store = VoiceStudioPrivateStorage(
        "https://fixture.supabase.co", "sb_secret_not-a-live-key-123456",
        transport=network,
    )
    kwargs = {
        "shop_id": sql.shop, "campaign_id": sql.campaign,
        "request_id": sql.job, "voice": "alloy", "reel_seconds": 15,
        "base_url": "http://127.0.0.1:3900",
        "api_key": "not-live-private-voice-key",
        "storage": store, "read_current_plan": sql.read_plan,
        "claim_once": sql.claim,
        "register_verified_private_pair": sql.register,
        "read_private_receipt": sql.read_receipt,
        "enabled": True, "commercial_model_verified": True,
        "transport": network,
    }
    kwargs.update(changes)
    return run_verified_private_voice_job(**kwargs)


def test_real_components_compose_once_only_private_wav_then_sql_registration():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    result = start(sql, network)
    assert result["schema"] == "retailgrowth.feature2-voicestudio-private-review.v1"
    assert result["shop_id"] == sql.shop
    assert result["audio_asset_id"] == sql.asset
    assert result["review_status"] == "NEEDS_REVIEW"
    assert result["approved_to_render_or_publish"] is False
    assert network.speech_calls == 1
    assert sql.registrations == 1
    assert len(network.objects) == 2
    assert [m for m, _ in network.calls] == ["POST", "POST", "POST", "GET", "GET"]
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network)
    assert network.speech_calls == 1
    assert sql.registrations == 1


def test_foreign_tenant_scope_refused_before_claim_or_egress():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network, shop_id=sql.other_shop)
    assert not sql.claimed and network.calls == []


@pytest.mark.parametrize("plan_change", [
    {"active_editor": False}, {"voice": "another"},
    {"script_review": "DRAFT"}, {"can_publish": True},
])
def test_revoked_or_unapproved_plan_does_not_generate(plan_change):
    sql, network = TrustedSQL(), StubPrivateNetwork()
    sql.plan.update(plan_change)
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network)
    assert network.speech_calls == 0


def test_unknown_model_not_called_before_authorization():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    for flags in ({"enabled": False}, {"commercial_model_verified": False}):
        with pytest.raises(VoiceStudioUnavailable):
            start(sql, network, **flags)
    assert network.calls == []


def test_tampered_storage_readback_denies_sql_registration():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    network.tamper_get = True
    with pytest.raises(PrivateVoiceStorageDenied):
        start(sql, network)
    assert network.speech_calls == 1
    assert sql.registrations == 0
    assert len(network.objects) == 2
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network)
    assert network.speech_calls == 1


def test_half_written_private_output_not_registered_or_retried():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    network.fail_second_put = True
    with pytest.raises(PrivateVoiceStorageDenied):
        start(sql, network)
    assert len(network.objects) == 1
    assert sql.registrations == 0
    assert network.speech_calls == 1
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network)
    assert network.speech_calls == 1


def test_revoked_after_sql_registration_does_not_return_success():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    sql.revoke_during_register = True
    with pytest.raises(VoiceStudioUnavailable, match="revoked"):
        start(sql, network)
    assert sql.registrations == 1
    assert network.speech_calls == 1


def test_registration_ack_must_be_exact_and_no_silent_replay():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    def uncertain(*args):
        return {"status": "UNCONFIRMED"}
    with pytest.raises(VoiceStudioUnavailable, match="SQL registration"):
        start(sql, network, register_verified_private_pair=uncertain)
    assert network.speech_calls == 1 and sql.registrations == 0
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network)
    assert network.speech_calls == 1


def test_missing_authoritative_sql_registration_blocks_egress():
    sql, network = TrustedSQL(), StubPrivateNetwork()
    with pytest.raises(VoiceStudioUnavailable):
        start(sql, network, register_verified_private_pair=None)
    assert network.calls == [] and not sql.claimed
