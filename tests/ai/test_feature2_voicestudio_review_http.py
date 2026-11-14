"""Source-only HTTP response contract; no Azure route or cloud credentials."""
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
import feature2_voicestudio_review_http as http  # noqa: E402


def _call(auth="Bearer valid-test-token-do-not-use"):
    return http.private_original_review_response(
        request=SimpleNamespace(headers={"Authorization": auth}),
        shop_id=str(uuid4()), campaign_id=str(uuid4()), request_id=str(uuid4()),
        verify_token=lambda _: str(uuid4()), tenant_store=object(),
        sql_store_factory=lambda _: object(), private_storage=object(),
    )


def test_private_audio_response_never_cacheable_on_denial():
    status, headers, body = _call()
    assert status == 404 and body == b""
    assert headers["Cache-Control"] == "no-store, private"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Type" not in headers


def test_missing_authorization_fails_without_calling_dependencies():
    status, headers, body = _call(None)
    assert status == 401 and body == b""
    assert headers["Pragma"] == "no-cache"


def test_private_wav_success_has_exact_length_and_no_storage_identifier(monkeypatch):
    payload = b"RIFF" + b"x" * 48
    monkeypatch.setattr(http, "read_current_voiceover_for_review", lambda **_: payload)
    status, headers, body = _call()
    assert status == 200 and body == payload
    assert headers["Content-Type"] == "audio/wav"
    assert headers["Content-Length"] == str(len(payload))
    assert headers["Cache-Control"] == "no-store, private"


def test_provider_exception_does_not_leak_message_or_private_bytes(monkeypatch):
    def broken(**_):
        raise RuntimeError("sensitive backend SQL diagnostic")
    monkeypatch.setattr(http, "read_current_voiceover_for_review", broken)
    status, headers, body = _call()
    assert status == 503 and body == b""
    assert "sensitive" not in repr((headers, body))


def test_nonbytes_service_result_is_never_disclosed(monkeypatch):
    # Reject str, bytearray and memoryview: only immutable, checked WAV bytes pass.
    for result in ("RIFFprivate", bytearray(b"RIFFprivate"), memoryview(b"RIFFprivate")):
        monkeypatch.setattr(http, "read_current_voiceover_for_review", lambda **_: result)
        status, headers, body = _call()
        assert status == 404 and body == b""
        assert "Content-Type" not in headers
        assert "Content-Length" not in headers


def test_missing_authorization_does_not_invoke_service(monkeypatch):
    calls = []
    monkeypatch.setattr(http, "read_current_voiceover_for_review", lambda **_: calls.append(1))
    for auth in (None, b"Bearer secret", ["Bearer secret"], 123):
        status, headers, body = _call(auth)
        assert status == 401 and body == b""
        assert headers["Cache-Control"] == "no-store, private"
    assert calls == []


def test_review_denial_does_not_expose_private_response(monkeypatch):
    def denied(**_):
        raise http.VoiceStudioReviewDenied("private original key and token")
    monkeypatch.setattr(http, "read_current_voiceover_for_review", denied)
    status, headers, body = _call()
    assert status == 404 and body == b""
    assert "Content-Type" not in headers
    assert "Content-Length" not in headers
    assert "private original key" not in repr((headers, body))


def test_malformed_request_headers_fail_closed_without_service(monkeypatch):
    calls = []
    monkeypatch.setattr(http, "read_current_voiceover_for_review", lambda **_: calls.append(1))
    for request in (None, object(), SimpleNamespace(headers=None),
                    SimpleNamespace(headers=[]),
                    SimpleNamespace(headers=SimpleNamespace(get=lambda _: (_ for _ in ()).throw(ValueError("bad header")))),
                    SimpleNamespace(headers=SimpleNamespace(get=lambda _: (_ for _ in ()).throw(KeyError("Authorization")))),
                    SimpleNamespace(headers=SimpleNamespace(get=lambda _: (_ for _ in ()).throw(IndexError("Authorization"))))):
        status, headers, body = http.private_original_review_response(
            request=request, shop_id=str(uuid4()), campaign_id=str(uuid4()),
            request_id=str(uuid4()), verify_token=lambda _: str(uuid4()),
            tenant_store=object(), sql_store_factory=lambda _: object(),
            private_storage=object(),
        )
        assert status == 401 and body == b""
        assert headers["Cache-Control"] == "no-store, private"
        assert "Content-Type" not in headers
    assert not calls


def test_private_wav_http_security_headers_on_success_and_denial(monkeypatch):
    monkeypatch.setattr(http, "read_current_voiceover_for_review", lambda **_: b"RIFF" + b"x" * 48)
    for auth, expected in (("Bearer valid-test-token-do-not-use", 200), (None, 401)):
        status, headers, _ = _call(auth)
        assert status == expected
        assert headers["Vary"] == "Authorization"
        assert headers["Referrer-Policy"] == "no-referrer"
        assert headers["Cache-Control"] == "no-store, private"


def test_empty_private_audio_is_denied_without_audio_headers(monkeypatch):
    # Even a buggy backend reader must not return a successful empty WAV.
    monkeypatch.setattr(http, "read_current_voiceover_for_review", lambda **_: b"")
    status, headers, body = _call()
    assert status == 404 and body == b""
    assert headers["Cache-Control"] == "no-store, private"
    assert "Content-Type" not in headers
    assert "Content-Length" not in headers
