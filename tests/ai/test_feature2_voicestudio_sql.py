"""No live SQL/credentials: feature2 VoiceStudio original-key RPC client boundary."""
import io
import json
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from feature2_voicestudio_sql import VoiceStudioSqlStore, VoiceStudioSqlDenied  # noqa: E402

SHOP, CAMPAIGN, JOB, ACTOR, ASSET = (str(uuid4()) for _ in range(5))
SHA = sha256(b"trusted reviewed plan").hexdigest()
ORIGINAL = sha256(b"mock wav original").hexdigest()
RENDER = sha256(b"mock wav F4").hexdigest()
SECRET = "sb_secret_" + "placeholder-example-no-real-key"


class Response(io.BytesIO):
    def __init__(self, data, url, *, status=200, mime="application/json"):
        super().__init__(data)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": mime}

    def geturl(self):
        return self.url


class Backend:
    def __init__(self):
        self.requests = []
        self.next_reply = None
        self.status = 200
        self.mime = "application/json"
        self.redirect = False

    def __call__(self, req, timeout):
        self.requests.append((req, timeout))
        name = req.full_url.rsplit("/", 1)[-1]
        if name == "feature2_voicestudio_claim":
            payload = {
                "shop_id": SHOP, "campaign_id": CAMPAIGN,
                "request_id": JOB, "plan_sha256": SHA,
                "status": "CLAIMED_ONCE", "paid_inference_calls": 0,
            }
        elif name == "feature2_voicestudio_register":
            payload = {
                "status": "REGISTERED_PRIVATE_NEEDS_REVIEW",
                "shop_id": SHOP, "campaign_id": CAMPAIGN, "request_id": JOB,
                "original_sha256": ORIGINAL, "render_sha256": RENDER,
                "publish_approved": False,
            }
        elif name == "feature2_voicestudio_receipt":
            payload = {
                "audio_asset_id": ASSET,
                "shop_id": SHOP, "campaign_id": CAMPAIGN,
                "request_id": JOB, "plan_sha256": SHA,
                "original_sha256": ORIGINAL, "render_sha256": RENDER,
                "private": True, "review_status": "NEEDS_REVIEW",
                "commercial_rights_confirmed": True,
                "publish_approved": False,
            }
        else:
            raise AssertionError("unknown RPC endpoint")
        data = json.dumps(self.next_reply if self.next_reply is not None else payload).encode("utf-8")
        return Response(
            data, "https://evil.example/" if self.redirect else req.full_url,
            status=self.status, mime=self.mime,
        )


def store(backend):
    return VoiceStudioSqlStore("https://fixture.supabase.co", SECRET, ACTOR, transport=backend)


def proof():
    return {
        "original_object_key": f"{SHOP}/voicestudio/{CAMPAIGN}/{JOB}/original.wav",
        "render_object_key": f"{SHOP}/voicestudio/{CAMPAIGN}/{JOB}/render.wav",
        "original_sha256": ORIGINAL, "render_sha256": RENDER,
        "original_bytes": 32044, "render_bytes": 480044,
        "requires_human_review": True, "publish_approved": False,
    }


def claim():
    return {
        "shop_id": SHOP, "campaign_id": CAMPAIGN, "request_id": JOB,
        "status": "CLAIMED_ONCE", "plan_sha256": SHA,
        "paid_inference_calls": 0,
    }


def test_uses_only_three_server_post_rpc_paths_with_private_key():
    backend = Backend()
    sql = store(backend)
    assert sql.claim_once(SHOP, CAMPAIGN, JOB, SHA) == claim()
    assert sql.register_verified_private_pair(SHOP, CAMPAIGN, JOB, claim(), proof())["status"] == "REGISTERED_PRIVATE_NEEDS_REVIEW"
    assert sql.read_private_receipt(SHOP, CAMPAIGN, JOB)["audio_asset_id"] == ASSET
    assert [x.full_url.rsplit("/", 1)[-1] for x, _ in backend.requests] == [
        "feature2_voicestudio_claim",
        "feature2_voicestudio_register",
        "feature2_voicestudio_receipt",
    ]
    for request, timeout in backend.requests:
        assert request.get_method() == "POST"
        assert request.get_header("Apikey") == SECRET
        assert request.get_header("Authorization") is None
        assert timeout == 12
        body = json.loads(request.data)
        assert body["p_actor_id"] == ACTOR
        assert body["p_shop_id"] == SHOP
        assert body["p_campaign_id"] == CAMPAIGN
        assert body["p_request_id"] == JOB


@pytest.mark.parametrize("bad", [
    {"origin": "http://fixture.supabase.co"},
    {"origin": "https://fixture.supabase.co/path"},
    {"origin": "https://fixture.supabase.co@evil.test"},
    {"origin": "https://fixture.supabase.co?secret=leak"},
    {"actor_id": "not-a-uuid"},
])
def test_invalid_caller_or_origin_denied_before_network(bad):
    backend = Backend()
    kwargs = {
        "origin": "https://fixture.supabase.co",
        "secret": SECRET, "actor_id": ACTOR, "transport": backend,
    }
    kwargs.update(bad)
    with pytest.raises(VoiceStudioSqlDenied):
        VoiceStudioSqlStore(**kwargs)
    assert backend.requests == []


@pytest.mark.parametrize("invalid", [
    {"request_id": "other"},
    {"plan_sha256": "0"},
    {"shop_id": str(uuid4())},
])
def test_bad_claim_ack_denied(invalid):
    backend = Backend()
    backend.next_reply = {**claim(), **invalid}
    with pytest.raises(VoiceStudioSqlDenied):
        store(backend).claim_once(SHOP, CAMPAIGN, JOB, SHA)


@pytest.mark.parametrize("edit", [
    {"original_sha256": "bad"},
    {"original_object_key": "other-shop/voice.wav"},
    {"render_bytes": True},
    {"render_bytes": 0},
    {"requires_human_review": False},
    {"publish_approved": True},
])
def test_invalid_registration_evidence_never_calls_sql(edit):
    backend = Backend()
    with pytest.raises(VoiceStudioSqlDenied):
        store(backend).register_verified_private_pair(
            SHOP, CAMPAIGN, JOB, claim(), {**proof(), **edit},
        )
    assert backend.requests == []


def test_different_sql_registration_ack_rejected():
    backend = Backend()
    backend.next_reply = {
        "status": "REGISTERED_PRIVATE_NEEDS_REVIEW",
        "shop_id": str(uuid4()), "campaign_id": CAMPAIGN,
        "request_id": JOB, "original_sha256": ORIGINAL,
        "render_sha256": RENDER, "publish_approved": False,
    }
    with pytest.raises(VoiceStudioSqlDenied):
        store(backend).register_verified_private_pair(
            SHOP, CAMPAIGN, JOB, claim(), proof(),
        )


@pytest.mark.parametrize("backend_options", [
    {"status": 201}, {"status": 307}, {"mime": "text/plain"},
    {"redirect": True}, {"next_reply": []}, {"next_reply": {}},
])
def test_denies_mismatched_status_redirect_and_fake_json(backend_options):
    backend = Backend()
    for name, value in backend_options.items():
        setattr(backend, name, value)
    with pytest.raises(VoiceStudioSqlDenied):
        store(backend).claim_once(SHOP, CAMPAIGN, JOB, SHA)


def test_receipt_refuses_unreviewed_or_publishable_asset():
    for changed in ({"review_status": "APPROVED"},
                    {"commercial_rights_confirmed": False},
                    {"private": False}, {"publish_approved": True},
                    {"audio_asset_id": str(uuid4())}):
        backend = Backend()
        backend.next_reply = {
            "audio_asset_id": ASSET,
            "shop_id": SHOP, "campaign_id": CAMPAIGN, "request_id": JOB,
            "plan_sha256": SHA,
            "original_sha256": ORIGINAL, "render_sha256": RENDER,
            "private": True, "review_status": "NEEDS_REVIEW",
            "commercial_rights_confirmed": True, "publish_approved": False,
            **changed,
        }
        if changed.get("audio_asset_id") and changed["audio_asset_id"] != ASSET:
            # A valid other UUID is legal for a newly minted receipt; its
            # authority is still bound by the current trusted DB reader.
            continue
        with pytest.raises(VoiceStudioSqlDenied):
            store(backend).read_private_receipt(SHOP, CAMPAIGN, JOB)
