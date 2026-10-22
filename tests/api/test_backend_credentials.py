"""Backend credentials and media collision regression checks."""
import io
import json
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError
from uuid import uuid4
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from admin_store import AdminStore, backend_headers
from private_media import PrivateMedia
from tenant_store import StorageUnavailable


class Response:
    status = 200
    def __init__(self, payload=None): self.payload = [] if payload is None else payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, *args): return json.dumps(self.payload).encode()


def test_opaque_and_legacy_credential_headers():
    assert backend_headers("sb_secret_ci-only") == {"apikey": "sb_secret_ci-only"}
    legacy = "eyJabc.eyJxyz.signature"
    assert backend_headers(legacy)["Authorization"] == "Bearer " + legacy
    with pytest.raises(ValueError):
        backend_headers("not-a-key")


def test_service_role_status_cleanup_is_tenant_and_owner_scoped():
    captured = []
    cid, sid, uid = (str(uuid4()) for _ in range(3))
    def transport(req, timeout):
        captured.append(req)
        return Response([{"id": cid}])
    admin = AdminStore("https://retail.supabase.co", "sb_secret_ci-only", transport)
    admin.fail_pending(cid, sid, uid)
    assert captured[0].get_method() == "PATCH"
    assert captured[0].get_header("Authorization") is None
    assert "shop_id=eq." + sid in captured[0].full_url
    assert "created_by=eq." + uid in captured[0].full_url


def test_private_output_collision_is_never_accepted_as_success():
    sid, jid = str(uuid4()), str(uuid4())
    def collision(req, timeout):
        raise HTTPError(req.full_url, 409, "exists", {}, io.BytesIO())
    private = PrivateMedia("https://retail.supabase.co", "sb_secret_ci-only", collision)
    with tempfile.TemporaryDirectory() as directory:
        file = Path(directory) / "clip.mp4"
        file.write_bytes(b"x" * 500)
        with pytest.raises(StorageUnavailable, match="collision"):
            private.upload(sid, jid, file)
