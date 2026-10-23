"""Part 3: offline provider poll -> private importer, never a paid API call."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from premium_poll_completion import PremiumPollCompletion, PremiumCompletionError

SID = "123e4567-e89b-42d3-a456-426614174001"
JID = "123e4567-e89b-42d3-a456-426614174002"
LEASE = "123e4567-e89b-42d3-a456-426614174003"
ASSET = "123e4567-e89b-42d3-a456-426614174004"
TASK = "provider-task-123456"
URL = "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/clip.mp4?Expires=9999999999"
MP4 = bytes.fromhex("00000018667479706d703432") + b"A" * 2100


class Store:
    def __init__(self):
        self.claims = 0
        self.finalizations = []
        self.claim = {"id": JID, "shop_id": SID, "attempt_token": LEASE,
                      "status": "IMPORTING", "reservation_confirmed": True,
                      "seconds": 5, "provider_task_id": TASK}
        self.complete = True

    def claim_import(self, job_id):
        self.claims += 1
        assert job_id == JID
        return self.claim

    def finalize(self, job_id, shop_id, token, path):
        self.finalizations.append((job_id, shop_id, token, path))
        return ({"status": "SUCCEEDED", "output_asset_id": ASSET}
                if self.complete else {"status": "FAILED"})


class Provider:
    def __init__(self, status="SUCCEEDED", url=URL):
        self.calls = []
        self.status, self.url = status, url

    def poll_private(self, task_id):
        self.calls.append(task_id)
        result = {"task_id": task_id, "status": self.status}
        if self.status == "SUCCEEDED":
            result["video_url"] = self.url
        return result


class Response:
    status = 200
    headers = {"Content-Type": "video/mp4",
               "Content-Length": str(len(MP4))}

    def __init__(self):
        self.stream = BytesIO(MP4)

    def read(self, size=-1):
        return self.stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class Opener:
    def __init__(self):
        self.calls = []

    def open(self, request, timeout):
        self.calls.append(request.full_url)
        return Response()


class Media:
    def __init__(self):
        self.uploads = []

    def upload(self, shop_id, job_id, path, *, lease_token):
        self.uploads.append((shop_id, job_id, lease_token, Path(path).stat().st_size))
        return f"{shop_id}/renders/{job_id}/{lease_token}.mp4"


def probe(_path):
    return {"format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "codec_name": "h264",
                         "width": 720, "height": 1280}]}


def construct(store=None, provider=None, media=None, opener=None, *, enabled=True):
    store, provider, media, opener = (
        store or Store(), provider or Provider(), media or Media(), opener or Opener()
    )
    return (PremiumPollCompletion(store, provider, media, enabled=enabled,
                                  probe=probe, opener=opener),
            store, provider, media, opener)


def test_disabled_by_default_never_claims_or_contacts_provider():
    worker, store, provider, media, opener = construct(enabled=False)
    with pytest.raises(PremiumCompletionError, match="disabled"):
        worker.run_once(JID)
    assert store.claims == 0 and provider.calls == [] and opener.calls == []


def test_successful_provider_poll_imports_once_and_returns_only_private_asset():
    worker, store, provider, media, opener = construct()
    result = worker.run_once(JID)
    assert result == {"job_id": JID, "status": "SUCCEEDED", "output_asset_id": ASSET}
    assert provider.calls == [TASK] and opener.calls == [URL]
    assert media.uploads == [(SID, JID, LEASE, len(MP4))]
    assert store.finalizations == [
        (JID, SID, LEASE, f"{SID}/renders/{JID}/{LEASE}.mp4")]
    assert "video_url" not in result and "provider_task_id" not in result


def test_stale_claim_avoids_provider_contact_or_upload():
    worker, store, provider, media, opener = construct()
    store.claim = None
    assert worker.run_once(JID) == {"job_id": JID, "status": "NOT_CLAIMED"}
    assert provider.calls == [] and media.uploads == []


@pytest.mark.parametrize("change", [
    {"reservation_confirmed": False}, {"status": "PENDING"},
    {"attempt_token": "foreign-tenant"}, {"shop_id": "other-tenant"},
    {"id": SID}, {"seconds": 18}, {"provider_task_id": "bad"},
])
def test_broken_fence_tenant_or_reservation_prevents_network(change):
    worker, store, provider, media, opener = construct()
    store.claim.update(change)
    with pytest.raises(PremiumCompletionError, match="claim is invalid"):
        worker.run_once(JID)
    assert provider.calls == [] and media.uploads == []


@pytest.mark.parametrize("status,expected", [
    ("PENDING", "AWAITING_PROVIDER"),
    ("RUNNING", "AWAITING_PROVIDER"),
    ("FAILED", "RECONCILE"),
    ("CANCELED", "RECONCILE"),
    ("UNKNOWN", "RECONCILE"),
])
def test_non_success_does_not_import_or_resubmit(status, expected):
    worker, store, provider, media, opener = construct(provider=Provider(status))
    assert worker.run_once(JID) == {"job_id": JID, "status": expected}
    assert provider.calls == [TASK]
    assert media.uploads == [] and opener.calls == []


@pytest.mark.parametrize("bad_url", [
    "https://evil.example/path.mp4?Expires=9999999999",
    "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/a.mp4?Expires=1",
    "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/a.mp4?Expires=foo",
    "https://dashscope-result-sh.oss-accelerate.aliyuncs.com/a.mp4?Expires=9999999999&Expires=9999999999",
])
def test_invalid_or_expired_provider_url_is_never_downloaded(bad_url):
    worker, store, provider, media, opener = construct(provider=Provider(url=bad_url))
    with pytest.raises(PremiumCompletionError) as info:
        worker.run_once(JID)
    assert bad_url not in str(info.value)
    assert media.uploads == [] and opener.calls == []


def test_rejected_database_finalization_does_not_claim_success():
    worker, store, provider, media, opener = construct()
    store.complete = False
    with pytest.raises(PremiumCompletionError):
        worker.run_once(JID)
    assert len(media.uploads) == 1 and len(store.finalizations) == 1


def test_unexpected_provider_response_is_sanitized_and_not_uploaded():
    class BadProvider:
        def poll_private(self, task):
            raise ValueError("secret signed URL and key")
    worker, store, provider, media, opener = construct(provider=BadProvider())
    with pytest.raises(PremiumCompletionError) as info:
        worker.run_once(JID)
    assert "secret" not in str(info.value) and opener.calls == []
    assert store.finalizations == []
