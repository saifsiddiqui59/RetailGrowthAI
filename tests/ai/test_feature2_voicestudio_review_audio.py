"""Synthetic private VoiceStudio reviewer WAV authorization and revocation tests."""
from __future__ import annotations

import io
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4
import wave

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))

from feature2_voicestudio_review_audio import (  # noqa: E402
    VoiceStudioReviewDenied, read_current_voiceover_for_review,
)
from feature2_voicestudio_storage import (  # noqa: E402
    PrivateVoiceStorageDenied,
)

SHOP, CAMPAIGN, JOB, ASSET, USER = (str(uuid4()) for _ in range(5))
TOKEN = "valid-test-token-do-not-use"
PLAN_SHA = sha256(b"original approved plan").hexdigest()


def pcm():
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x01\x02" * 16000)
    return output.getvalue()


class Tenant:
    def __init__(self):
        self.allow = True
        self.revoke_on_second = False
        self.calls = []

    def member(self, token, uid, shop, *, write=False):
        self.calls.append((token, uid, shop, write))
        if self.revoke_on_second and len(self.calls) == 2:
            return False
        return self.allow and token == TOKEN and uid == USER and shop == SHOP and write


class SQL:
    def __init__(self):
        self.calls = []
        self.revoke_on_second = False
        self.foreign = False
        self.status = "NEEDS_REVIEW"

    def read_private_receipt(self, shop, campaign, request):
        self.calls.append((shop, campaign, request))
        return {
            "audio_asset_id": ASSET,
            "shop_id": str(uuid4()) if self.foreign else SHOP,
            "campaign_id": CAMPAIGN, "request_id": JOB,
            "plan_sha256": PLAN_SHA,
            "original_sha256": sha256(pcm()).hexdigest(),
            "private": True,
            "review_status": "REVOKED" if self.revoke_on_second and len(self.calls) == 2 else self.status,
            "commercial_rights_confirmed": True,
            "publish_approved": False,
        }


class Private:
    def __init__(self):
        self.calls = []
        self.tamper = False
        self.fail = False

    def read_verified_original(self, shop, campaign, request, digest):
        self.calls.append((shop, campaign, request, digest))
        if self.fail:
            raise PrivateVoiceStorageDenied("secret-backed reader failed")
        if self.tamper:
            raise PrivateVoiceStorageDenied("private bytes changed")
        return pcm()


def harness(**changes):
    tenant, sql, storage = Tenant(), SQL(), Private()
    tokens = []
    def verifier(token):
        tokens.append(token)
        if token != TOKEN:
            raise ValueError("unauthenticated")
        return USER
    args = {
        "shop_id": SHOP,
        "campaign_id": CAMPAIGN,
        "request_id": JOB,
        "authorization": "Bearer " + TOKEN,
        "verify_token": verifier,
        "tenant_store": tenant,
        "sql_store_factory": lambda uid: sql,
        "private_storage": storage,
    }
    args.update(changes)
    return args, tenant, sql, storage, tokens


def test_real_private_original_bytes_only_for_current_reviewer():
    args, tenant, sql, storage, tokens = harness()
    actual = read_current_voiceover_for_review(**args)
    assert actual == pcm()
    assert type(actual) is bytes
    assert len(storage.calls) == 1
    assert storage.calls[0] == (SHOP, CAMPAIGN, JOB, sha256(pcm()).hexdigest())
    assert len(tenant.calls) == 2 and all(call[-1] for call in tenant.calls)
    assert len(sql.calls) == 2 and tokens == [TOKEN, TOKEN]


@pytest.mark.parametrize("change", [
    {"authorization": "Bearer forged"},
    {"authorization": "Basic token"},
    {"authorization": None},
    {"shop_id": str(uuid4())},
    {"request_id": "bad-path/../../private.wav"},
    {"verify_token": None},
    {"sql_store_factory": None},
])
def test_invalid_token_scope_or_trusted_reader_denied(change):
    args, tenant, sql, storage, _ = harness(**change)
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert not storage.calls


def test_viewer_or_inactive_editor_cannot_read_private_bytes():
    args, tenant, sql, storage, _ = harness()
    tenant.allow = False
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert not storage.calls
    assert not sql.calls


def test_foreign_or_revoked_sql_receipt_denied_before_storage_get():
    for changed in ("foreign", "status"):
        args, tenant, sql, storage, _ = harness()
        if changed == "foreign": sql.foreign = True
        else: sql.status = "REVOKED"
        with pytest.raises(VoiceStudioReviewDenied):
            read_current_voiceover_for_review(**args)
        assert not storage.calls


def test_revocation_during_private_get_denies_audio_disclosure():
    args, tenant, sql, storage, _ = harness()
    sql.revoke_on_second = True
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1 and len(sql.calls) == 2


def test_revoked_editor_after_private_get_denies_audio_disclosure():
    args, tenant, sql, storage, _ = harness()
    tenant.revoke_on_second = True
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1 and len(tenant.calls) == 2


def test_storage_tamper_never_returns_bytes_or_secret():
    args, _, _, storage, _ = harness()
    storage.fail = True
    with pytest.raises(VoiceStudioReviewDenied) as error:
        read_current_voiceover_for_review(**args)
    assert "secret" not in str(error.value)
    assert len(storage.calls) == 1


def test_no_private_bytes_if_wrong_current_sql_digest():
    args, tenant, sql, storage, _ = harness()
    def corrupt(*ids):
        receipt = SQL.read_private_receipt(sql, *ids)
        receipt["original_sha256"] = "f" * 64
        return receipt
    sql.read_private_receipt = corrupt
    storage.tamper = True
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1


def test_bogus_original_payload_denied():
    args, tenant, sql, storage, _ = harness()
    storage.read_verified_original = lambda *ids: b"fake"
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
