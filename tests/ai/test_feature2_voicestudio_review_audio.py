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
            "render_sha256": sha256(b"paired render receipt").hexdigest(),
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


def test_storage_returning_valid_length_but_wrong_sha_is_rejected_twice():
    args, tenant, sql, storage, _ = harness()
    original = pcm()
    storage.read_verified_original = lambda *ids: original[:-1] + bytes([original[-1] ^ 1])
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    # Invalid bytes are blocked before any second SQL/tenant read.
    assert len(sql.calls) == 1
    assert len(tenant.calls) == 1


def _jwt_harness():
    import jwt
    from datetime import datetime, timedelta, timezone
    from cryptography.hazmat.primitives.asymmetric import rsa
    from security import SupabaseJWTVerifier

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    issuer = "https://retail-test.supabase.co/auth/v1"

    class JWK:
        def __init__(self, public_key):
            self.key = public_key

    class Client:
        def get_signing_key_from_jwt(self, _token):
            return JWK(key.public_key())

    verifier = SupabaseJWTVerifier(
        "https://retail-test.supabase.co", jwks_client=Client()
    )

    def sign(**changes):
        claims = {
            "sub": USER, "iss": issuer, "aud": "authenticated",
            "role": "authenticated",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        claims.update(changes)
        return jwt.encode(claims, key, algorithm="RS256")
    return verifier, sign


def test_current_reviewer_accepts_real_verified_local_rsa_jwt():
    verify, sign = _jwt_harness()
    signed = sign()
    args, tenant, sql, storage, _ = harness(
        verify_token=verify, authorization="Bearer " + signed
    )
    tenant.member = lambda token, uid, shop, write=False: (
        token == signed and uid == USER and shop == SHOP and write
    )
    assert read_current_voiceover_for_review(**args) == pcm()
    assert len(storage.calls) == 1 and len(sql.calls) == 2


@pytest.mark.parametrize("claim", [
    {"iss": "https://foreign.supabase.co/auth/v1"},
    {"aud": "another-audience"},
    {"role": "service_role"},
    {"is_anonymous": True},
])
def test_current_reviewer_refuses_forged_or_cross_project_claims(claim):
    verify, sign = _jwt_harness()
    signed = sign(**claim)
    args, tenant, sql, storage, _ = harness(
        verify_token=verify, authorization="Bearer " + signed
    )
    tenant.member = lambda *a, **k: True
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 0 and len(sql.calls) == 0


@pytest.mark.parametrize("error", [ConnectionError("sql connection lost"), TimeoutError("sql timeout"), RuntimeError("sql uncertain acknowledgement")])
def test_uncertain_sql_receipt_failure_denies_without_private_get(error):
    args, _, sql, storage, _ = harness()
    def unavailable(*_ids):
        raise error
    sql.read_private_receipt = unavailable
    with pytest.raises(VoiceStudioReviewDenied, match="access denied"):
        read_current_voiceover_for_review(**args)
    assert not storage.calls


@pytest.mark.parametrize("error", [ConnectionError("storage connection lost"), TimeoutError("storage timeout"), RuntimeError("storage unknown outcome")])
def test_uncertain_private_read_failure_denies_without_retry(error):
    args, _, sql, storage, _ = harness()
    def unavailable(*_ids):
        storage.calls.append(_ids)
        raise error
    storage.read_verified_original = unavailable
    with pytest.raises(VoiceStudioReviewDenied, match="access denied"):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1
    assert len(sql.calls) == 1


@pytest.mark.parametrize("header", [
    "Bearer  " + TOKEN, "Bearer " + TOKEN + " ",
    "Bearer " + TOKEN + "\\n", "Bearer " + TOKEN + "\\t",
    "Bearer " + TOKEN + " extra",
])
def test_malformed_bearer_header_never_reaches_sql_or_storage(header):
    args, tenant, sql, storage, _ = harness(authorization=header)
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert not tenant.calls and not sql.calls and not storage.calls


def test_in_place_sql_receipt_revocation_during_private_get_is_denied():
    args, tenant, sql, storage, _ = harness()
    shared = SQL.read_private_receipt(sql, SHOP, CAMPAIGN, JOB)
    calls = []
    def reused_receipt(*ids):
        calls.append(ids)
        if len(calls) == 2:
            shared["review_status"] = "REVOKED"
        return shared
    sql.read_private_receipt = reused_receipt
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(calls) == 2 and len(storage.calls) == 1


@pytest.mark.parametrize("dependency", ["jwt", "sql", "storage"])
def test_unexpected_provider_exception_is_sanitized_and_never_retried(dependency):
    args, tenant, sql, storage, tokens = harness()
    def unexpected(*_args, **_kwargs):
        raise LookupError("private provider diagnostic must not escape")
    if dependency == "jwt":
        args["verify_token"] = unexpected
    elif dependency == "sql":
        sql.read_private_receipt = unexpected
    else:
        storage.read_verified_original = unexpected
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$") as exc:
        read_current_voiceover_for_review(**args)
    assert "private provider diagnostic" not in str(exc.value)
    assert exc.value.__cause__ is None
    assert len(storage.calls) == 0
    assert len(sql.calls) == (0 if dependency == "jwt" else 1 if dependency == "storage" else 0)
    assert len(tenant.calls) == (0 if dependency == "jwt" else 1)


@pytest.mark.parametrize("bad_render", [None, "", "f" * 63, "F" * 64, 123])
def test_missing_or_malformed_render_pair_receipt_denied_before_private_read(bad_render):
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def invalid_pair(*ids):
        receipt = original(*ids)
        receipt["render_sha256"] = bad_render
        return receipt
    sql.read_private_receipt = invalid_pair
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 0


def test_render_pair_digest_revoked_during_original_read_denies_disclosure():
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def changed_pair(*ids):
        receipt = original(*ids)
        if len(sql.calls) == 2:
            receipt["render_sha256"] = "a" * 64
        return receipt
    sql.read_private_receipt = changed_pair
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1 and len(sql.calls) == 2


def test_digest_matching_non_wav_denied_even_with_swapped_storage_reader():
    args, tenant, sql, storage, _ = harness()
    malicious = b"not-wave" + b"x" * 100
    digest = sha256(malicious).hexdigest()
    original_reader = sql.read_private_receipt
    def receipt(*ids):
        result = original_reader(*ids)
        result["original_sha256"] = digest
        return result
    sql.read_private_receipt = receipt
    storage.read_verified_original = lambda *ids: malicious
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1 and len(tenant.calls) == 1


def test_digest_matching_wav_with_hidden_trailing_bytes_denied():
    args, tenant, sql, storage, _ = harness()
    malicious = pcm() + b"hidden"
    digest = sha256(malicious).hexdigest()
    original_reader = sql.read_private_receipt
    def receipt(*ids):
        result = original_reader(*ids)
        result["original_sha256"] = digest
        return result
    sql.read_private_receipt = receipt
    storage.read_verified_original = lambda *ids: malicious
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1 and len(tenant.calls) == 1


def test_signed_identity_rotation_during_private_read_denies_audio():
    args, tenant, sql, storage, tokens = harness()
    identities = iter((USER, str(uuid4())))
    def rotating_verifier(token):
        tokens.append(token)
        return next(identities)
    args["verify_token"] = rotating_verifier
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1
    assert len(sql.calls) == 2
    assert len(tenant.calls) == 1
    assert tokens == [TOKEN, TOKEN]


def test_approved_plan_receipt_changed_during_private_read_denies_audio():
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def changed_plan(*ids):
        receipt = original(*ids)
        if len(sql.calls) == 2:
            receipt["plan_sha256"] = sha256(b"unreviewed replacement script").hexdigest()
        return receipt
    sql.read_private_receipt = changed_plan
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1 and len(sql.calls) == 2
    assert len(tenant.calls) == 1


@pytest.mark.parametrize("declared_offset", [-2, 2])
def test_digest_matching_wav_with_false_riff_length_denied(declared_offset):
    args, tenant, sql, storage, _ = harness()
    malformed = bytearray(pcm())
    declared = len(malformed) - 8 + declared_offset
    malformed[4:8] = declared.to_bytes(4, "little")
    payload = bytes(malformed)
    original_reader = sql.read_private_receipt
    def receipt(*ids):
        result = original_reader(*ids)
        result["original_sha256"] = sha256(payload).hexdigest()
        return result
    sql.read_private_receipt = receipt
    storage.read_verified_original = lambda *ids: payload
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1 and len(tenant.calls) == 1


def test_expired_jwt_during_private_read_denies_without_disclosing_bytes():
    args, tenant, sql, storage, _ = harness()
    checks = []
    def expires_after_get(token):
        checks.append(token)
        if len(checks) == 2:
            raise ValueError("expired signed JWT")
        return USER
    args["verify_token"] = expires_after_get
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert checks == [TOKEN, TOKEN]
    assert len(storage.calls) == 1 and len(sql.calls) == 2
    assert len(tenant.calls) == 1


def test_sql_receipt_failure_after_private_get_denies_without_retry():
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def disconnect_after_get(*ids):
        if len(sql.calls) == 1:
            sql.calls.append(ids)
            raise TimeoutError("private SQL connection diagnostic")
        return original(*ids)
    sql.read_private_receipt = disconnect_after_get
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$") as exc:
        read_current_voiceover_for_review(**args)
    assert exc.value.__cause__ is None
    assert len(storage.calls) == 1 and len(sql.calls) == 2
    assert len(tenant.calls) == 1


@pytest.mark.parametrize("field,invalid", [
    ("private", False),
    ("commercial_rights_confirmed", False),
    ("publish_approved", True),
    ("review_status", "APPROVED_FOR_EDITING"),
    ("audio_asset_id", str(uuid4()).upper()),
    ("plan_sha256", "0" * 63),
])
def test_receipt_requires_private_rights_and_unapproved_review_state(field, invalid):
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def changed(*ids):
        receipt = original(*ids)
        receipt[field] = invalid
        return receipt
    sql.read_private_receipt = changed
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1
    assert not storage.calls


def test_sql_reader_factory_failure_denies_before_storage_without_retry():
    args, tenant, sql, storage, _ = harness()
    calls = []
    def unavailable(uid):
        calls.append(uid)
        raise TimeoutError("private SQL reader factory unavailable")
    args["sql_store_factory"] = unavailable
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert calls == [USER]
    assert len(tenant.calls) == 1
    assert not storage.calls


def test_post_read_membership_provider_failure_denies_private_audio_without_retry():
    args, tenant, sql, storage, _ = harness()
    original_member = tenant.member
    def fails_after_private_get(*a, **kw):
        if len(tenant.calls) == 1:
            tenant.calls.append((a[0], a[1], a[2], kw.get("write", False)))
            raise TimeoutError("private membership provider failure")
        return original_member(*a, **kw)
    tenant.member = fails_after_private_get
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$") as exc:
        read_current_voiceover_for_review(**args)
    assert exc.value.__cause__ is None
    assert len(storage.calls) == 1 and len(sql.calls) == 2
    assert len(tenant.calls) == 2


def test_audio_asset_identity_rotation_during_private_read_denies_bytes():
    """An original-key job must not swap the private asset identity mid-read."""
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def rotated(*ids):
        receipt = original(*ids)
        if len(sql.calls) == 2:
            receipt["audio_asset_id"] = str(uuid4())
        return receipt
    sql.read_private_receipt = rotated
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1
    assert len(sql.calls) == 2
    assert len(tenant.calls) == 1


@pytest.mark.parametrize("field", ["shop_id", "campaign_id", "request_id"])
def test_receipt_foreign_scope_denied_before_private_storage_access(field):
    """A signed editor cannot read a receipt belonging to another original key."""
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def swapped(*ids):
        receipt = original(*ids)
        receipt[field] = str(uuid4())
        return receipt
    sql.read_private_receipt = swapped
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1
    assert len(tenant.calls) == 1
    assert not storage.calls


@pytest.mark.parametrize("field", ["audio_asset_id", "shop_id", "campaign_id", "request_id"])
def test_receipt_missing_identity_denied_without_private_get(field):
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def incomplete(*ids):
        receipt = original(*ids)
        receipt.pop(field)
        return receipt
    sql.read_private_receipt = incomplete
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1
    assert not storage.calls


@pytest.mark.parametrize("result", [1, "true", [], {"allowed": True}])
def test_non_boolean_membership_response_denied_before_private_get(result):
    """A malformed RLS adapter result must not grant access by truthiness."""
    args, tenant, sql, storage, _ = harness()
    tenant.member = lambda *a, **kw: result
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert not sql.calls and not storage.calls


@pytest.mark.parametrize("result", [1, "true", [True], {"allowed": True}])
def test_non_boolean_membership_response_after_private_get_denies_audio(result):
    """Do not disclose private bytes if the second membership read is malformed."""
    args, tenant, sql, storage, _ = harness()
    calls = []
    def membership(*a, **kw):
        calls.append((a, kw))
        return True if len(calls) == 1 else result
    tenant.member = membership
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(calls) == 2 and len(storage.calls) == 1 and len(sql.calls) == 2


def test_nonboolean_post_read_membership_denied():
    args, tenant, sql, storage, _ = harness()
    original_member = tenant.member
    calls = [0]
    def membership(token, uid, shop, *, write=False):
        calls[0] += 1
        if calls[0] == 2:
            return 1  # Truthy integer must never grant post-I/O access.
        return original_member(token, uid, shop, write=write)
    tenant.member = membership
    with pytest.raises(VoiceStudioReviewDenied):
        read_current_voiceover_for_review(**args)
    assert calls[0] == 2 and len(storage.calls) == 1 and len(sql.calls) == 2


@pytest.mark.parametrize("field,bad", [
    ("audio_asset_id", str(__import__("uuid").uuid1())),
    ("original_sha256", "A" * 64),
    ("render_sha256", "g" * 64),
    ("plan_sha256", 123),
    ("commercial_rights_confirmed", 1),
    ("publish_approved", 0),
    ("private", 1),
])
def test_malformed_receipt_types_and_digests_never_trigger_private_get(field, bad):
    """Fail closed on type-confused SQL booleans, UUID versions and digests."""
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def malformed(*ids):
        receipt = original(*ids)
        receipt[field] = bad
        return receipt
    sql.read_private_receipt = malformed
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1
    assert not storage.calls


def test_original_digest_rotated_after_private_get_denies_audio_without_retry():
    """A new original-key receipt cannot authorize bytes from the old key."""
    args, tenant, sql, storage, _ = harness()
    original = sql.read_private_receipt
    def rotated(*ids):
        receipt = original(*ids)
        if len(sql.calls) == 2:
            receipt["original_sha256"] = sha256(b"new original audio").hexdigest()
        return receipt
    sql.read_private_receipt = rotated
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1 and len(sql.calls) == 2
    assert len(tenant.calls) == 1


def test_in_place_original_digest_rotation_during_private_get_denies_audio():
    """Snapshot receipt fields even if the SQL adapter reuses its dictionary."""
    args, tenant, sql, storage, _ = harness()
    shared = SQL.read_private_receipt(sql, SHOP, CAMPAIGN, JOB)
    calls = []
    def reused(*ids):
        calls.append(ids)
        if len(calls) == 2:
            shared["original_sha256"] = sha256(b"rotated original").hexdigest()
        return shared
    sql.read_private_receipt = reused
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(storage.calls) == 1 and len(calls) == 2
    assert len(tenant.calls) == 1


@pytest.mark.parametrize("field", ["shop_id", "campaign_id", "request_id"])
def test_sql_scope_identifier_must_be_plain_string(field):
    """Reject non-string provider objects even when they compare equal to scope."""
    args, tenant, sql, storage, _ = harness()
    class EqualToScope:
        def __eq__(self, other):
            return True
    original = sql.read_private_receipt
    def malformed(*ids):
        receipt = original(*ids)
        receipt[field] = EqualToScope()
        return receipt
    sql.read_private_receipt = malformed
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(sql.calls) == 1
    assert not storage.calls


@pytest.mark.parametrize("field,forged", [
    ("private", 1),
    ("private", "true"),
    ("commercial_rights_confirmed", 1),
    ("commercial_rights_confirmed", "true"),
    ("publish_approved", 0),
    ("publish_approved", None),
    ("review_status", "APPROVED_FOR_EDITING"),
    ("original_sha256", "A" * 64),
    ("plan_sha256", "a" * 63),
])
def test_sql_receipt_type_confusion_and_approval_bypass_denied_before_audio(field, forged):
    """SQL adapter must not coerce booleans, approval states or digest formats."""
    args, tenant, sql, storage, _ = harness()
    original_reader = sql.read_private_receipt

    def forged_receipt(*ids):
        receipt = original_reader(*ids)
        receipt[field] = forged
        return receipt

    sql.read_private_receipt = forged_receipt
    with pytest.raises(VoiceStudioReviewDenied, match="^Private VoiceStudio review access denied$"):
        read_current_voiceover_for_review(**args)
    assert len(tenant.calls) == 1
    assert len(sql.calls) == 1
    assert storage.calls == []
