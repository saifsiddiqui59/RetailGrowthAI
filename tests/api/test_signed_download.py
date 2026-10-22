"""Signed URLs are minted under the user JWT and never from external paths."""
import io
import json
import sys
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from tenant_store import TenantStore, StorageUnavailable

SID = str(uuid4())


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return json.dumps(self.payload).encode()


def test_signed_url_is_scoped_to_user_and_private_path():
    actual = SID + "/renders/safe.mp4"
    captured = []
    def fake(req, timeout):
        captured.append(req)
        from urllib.parse import quote
        return Response({"signedURL": "/object/sign/retailgrowth-media/" + quote(actual, safe="/") + "?token=test"})
    store = TenantStore("https://my-retail.supabase.co", "publishable", transport=fake)
    url = store.sign_download("user-token", SID, actual)
    assert url.endswith("?token=test")
    assert captured[0].get_header("Authorization") == "Bearer user-token"
    assert b'60' in captured[0].data


def test_foreign_path_and_external_url_rejected():
    store = TenantStore("https://my-retail.supabase.co", "publishable", transport=lambda *_: None)
    with pytest.raises(ValueError):
        store.sign_download("user-token", SID, str(uuid4()) + "/render.mp4")
    with pytest.raises(ValueError):
        store.sign_download("user-token", SID, SID + "/../escape.mp4")


def test_malicious_signing_response_denied():
    store = TenantStore("https://my-retail.supabase.co", "publishable",
                        transport=lambda req, timeout: Response({"signedURL": "https://evil.example/a"}))
    with pytest.raises(StorageUnavailable):
        store.sign_download("user-token", SID, SID + "/safe.mp4")
