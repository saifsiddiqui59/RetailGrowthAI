"""F4 dedicated CPU worker/offline source checks; no hosted billing or approval."""
import ast
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(ROOT / "azure-functions" / "feature4-cpu-worker"))
from recovery_runtime import dispatch_feature4_cpu_outbox, reconcile_feature4_cpu, record_feature4_cpu_poison  # noqa
from cpu_backend import VerifiedFeature4Media, Feature4CpuAdmin  # noqa
from tenant_store import StorageUnavailable  # noqa

SHOP = "11111111-1111-4111-8111-111111111111"
JOB = "33333333-3333-4333-8333-333333333333"
LEASE = "55555555-5555-4555-8555-555555555555"
EVENT = "66666666-6666-4666-8666-666666666666"
TOKEN = "77777777-7777-4777-8777-777777777777"


class FakeAdmin:
    def __init__(self):
        self.events = [{"id": EVENT, "job_id": JOB, "lease_token": TOKEN}]
        self.acks = []
        self.reconciled = 0
        self.poison = []

    def feature4_outbox_claim(self, limit):
        return self.events

    def feature4_outbox_confirm(self, event, sent):
        self.acks.append((event["id"], sent))

    def feature4_record_poison(self, digest, job_id):
        self.poison.append((digest, job_id))

    def feature4_reconcile(self):
        self.reconciled += 1
        return self.reconciled


class FakeQueue:
    def __init__(self, fail=False):
        self.fail = fail
        self.messages = []

    def enqueue(self, job):
        if self.fail:
            raise OSError("simulated unavailable queue")
        self.messages.append(job)


def test_outbox_uses_isolated_uuid_queue_and_confirmed_cas_only():
    admin, queue = FakeAdmin(), FakeQueue()
    assert dispatch_feature4_cpu_outbox(admin, queue) == 1
    assert queue.messages == [JOB]
    assert admin.acks == [(EVENT, True)]
    assert reconcile_feature4_cpu(admin, queue) == {
        "recovered": 1, "dispatched": 1}


def test_failed_dispatch_is_nondestructive_and_bounded():
    admin, queue = FakeAdmin(), FakeQueue(fail=True)
    assert dispatch_feature4_cpu_outbox(admin, queue) == 0
    assert admin.acks == [(EVENT, False)]
    assert queue.messages == []
    with pytest.raises(ValueError):
        dispatch_feature4_cpu_outbox(admin, queue, limit=0)
    admin.events = [{"id": EVENT, "job_id": JOB, "lease_token": TOKEN,
                     "untrusted": "browser URL"}]
    with pytest.raises(StorageUnavailable):
        dispatch_feature4_cpu_outbox(admin, queue)
    assert len(admin.acks) == 1


def test_feature4_poison_receipt_is_durable_before_ack_and_never_grants_job():
    store = FakeAdmin()
    payload = JOB.encode("ascii")
    assert record_feature4_cpu_poison(store, payload) == JOB
    assert store.poison == [(hashlib.sha256(payload).hexdigest(), JOB)]
    assert record_feature4_cpu_poison(store, b"../untrusted") is None
    assert store.poison[-1][1] is None
    with pytest.raises(ValueError):
        record_feature4_cpu_poison(store, "untrusted")


class FakeMedia:
    def __init__(self, accept=True):
        self.accept = accept
        self.remote_checks = []
        self.object_keys = []

    def download(self, *args):
        return None

    def upload(self, shop_id, job_id, path, *, lease_token=None):
        key = f"{shop_id}/renders/{job_id}/{lease_token}.mp4"
        self.object_keys.append(key)
        return key

    def verify_uploaded_mp4(self, shop_id, key, expected):
        self.remote_checks.append((shop_id, key, expected))
        return self.accept


def test_private_worker_rechecks_uploaded_bytes_before_finalize(tmp_path):
    output = tmp_path / "result.mp4"
    output.write_bytes(b"F4 original CPU bytes" * 100)
    media = FakeMedia()
    wrapped = VerifiedFeature4Media(media)
    key = wrapped.upload(SHOP, JOB, output, lease_token=LEASE)
    assert key == f"{SHOP}/renders/{JOB}/{LEASE}.mp4"
    assert media.remote_checks == [
        (SHOP, key, hashlib.sha256(output.read_bytes()).hexdigest())]
    media.accept = False
    with pytest.raises(StorageUnavailable):
        wrapped.upload(SHOP, JOB, output, lease_token=LEASE)


class FakeStore:
    def feature4_render_status(self, jid):
        assert jid == JOB
        return "QUEUED"

    def claim_feature4_render(self, jid):
        assert jid == JOB
        return {"id": JOB}

    def feature4_render_authorized(self, claim):
        return claim["id"] == JOB

    def feature4_claim_current(self, claim):
        return claim["id"] == JOB

    def feature4_load_bundle(self, claim):
        return {"request": {"video_job_id": JOB}, "assets": {}}

    def complete_feature4_render(self, claim, key, proof, mode):
        return proof["sha256"] == "a" * 64

    def feature4_render_failure(self, claim, code, *, permanent=False):
        return code


def test_feature4_worker_adapter_does_not_use_v1_render_status_or_claim():
    adapter = Feature4CpuAdmin(FakeStore())
    assert adapter.render_status(JOB) == "QUEUED"
    assert adapter.claim_feature4_render(JOB) == {"id": JOB}
    assert adapter.render_authorized({"id": JOB}) is True
    assert adapter.feature4_claim_current({"id": JOB}) is True
    assert adapter.complete_feature4_render(
        {"id": JOB}, "private.mp4", {"sha256": "a" * 64},
        "AUTHORIZED_ASSEMBLY") is True
    assert adapter.render_failure({"id": JOB}, "RENDER_FAILED") == "RENDER_FAILED"


def test_queue_worker_never_indexes_on_default_off_and_never_reuses_v1():
    legacy = (ROOT / "azure-functions" / "campaign-api" / "function_app.py")
    text = legacy.read_text(encoding="utf-8")
    assert "def feature4_cpu_render_message(" not in text
    assert "def feature4_cpu_dispatch_timer(" not in text
    app = (ROOT / "azure-functions" / "feature4-cpu-worker" / "function_app.py")
    tree = ast.parse(app.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.If)
             and "RETAIL_FEATURE4_CPU_WORKER_ENABLED" in ast.unparse(n.test)]
    assert len(nodes) == 1
    scoped = ast.unparse(nodes[0])
    assert "retail-feature4-cpu-render" in scoped
    assert "def feature4_cpu_render_message(" in scoped
    assert "def feature4_cpu_dispatch_timer(" in scoped
    assert "def feature4_cpu_poison_message(" in scoped
    assert "retail-reel-render" not in scoped


# Live storage is NOT accessed: these fakes enforce the service-role
# read sequence that the SQL claim has already authorized.
from admin_store import AdminStore  # noqa: E402

PLAN = "99999999-9999-4999-8999-999999999999"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
MEDIA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
RIGHTS = {
    "id": MEDIA, "shop_id": SHOP,
    "path": SHOP + "/uploads/" + MEDIA + ".png",
    "mime": "image/png", "source": "UPLOAD", "license": "owned",
}


class SourceReader:
    feature4_load_bundle = AdminStore.feature4_load_bundle

    def __init__(self):
        self.current = True
        self.media = {
            "id": MEDIA, "shop_id": SHOP, "storage_bucket": "retailgrowth-media",
            "object_path": RIGHTS["path"], "mime_type": "image/png",
            "source": "UPLOAD", "license_name": "owned",
            "license_url": None, "attribution": None,
        }

    def feature4_claim_current(self, claim):
        return self.current

    def request(self, table, *, query=None):
        if table == "feature4_creative_plans":
            return [{
                "id": PLAN, "shop_id": SHOP, "campaign_id": CAMPAIGN,
                "state": "APPROVED", "review_sha256": "a"*64,
                "approved_direction": {
                    "script": {"approved": True, "source_feature": "feature2"}},
                "media_snapshot": [RIGHTS.copy()], "media_asset_ids": [MEDIA],
            }]
        if table == "media_assets":
            return [self.media.copy()]
        if table == "shops":
            return [{"name": "Synthetic Private Retailer"}]
        raise AssertionError("Unreviewed table requested: " + table)


def test_feature4_authoritative_bundle_accepts_owned_upload_without_fake_license_url():
    reader = SourceReader()
    claim = {
        "id": JOB, "shop_id": SHOP, "campaign_id": CAMPAIGN,
        "plan_id": PLAN, "approved_review_sha256": "a"*64,
        "idempotency_key": "b"*64,
    }
    source = reader.feature4_load_bundle(claim)
    assert set(source) == {"direction", "snapshot", "reviewed_hash"}
    assert source["snapshot"]["shop_id"] == SHOP
    assert source["snapshot"]["video_job_id"] == JOB
    assert source["snapshot"]["assets"][MEDIA]["rights_source"] == "retailer-owned-upload"
    assert source["snapshot"]["assets"][MEDIA]["rights_evidence"].startswith(
        "Retailer-declared ownership")
    reader.media["license_name"] = "unlicensed"
    with pytest.raises(StorageUnavailable):
        reader.feature4_load_bundle(claim)
    reader.media["license_name"] = "owned"
    reader.media["shop_id"] = "44444444-4444-4444-8444-444444444444"
    with pytest.raises(StorageUnavailable):
        reader.feature4_load_bundle(claim)
    reader.current = False
    with pytest.raises(StorageUnavailable):
        reader.feature4_load_bundle(claim)


def test_private_media_upload_uses_single_nofollow_fd_and_blocks_path_swap(tmp_path, monkeypatch):
    """No network POST if a renderer replaces the file after open."""
    import os
    from private_media import PrivateMedia
    original = tmp_path / "render.mp4"
    other = tmp_path / "untrusted.mp4"
    original.write_bytes(b"original h264 synthetic bytes" * 80)
    other.write_bytes(b"do-not-upload-secret-bytes" * 80)
    posted = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def transport(request, timeout):
        posted.append(request.data)
        return Response()

    media = PrivateMedia("https://storage.example.invalid", "sb_secret_synthetic_only_no_real_credentials",
                         transport=transport)
    assert media.upload(SHOP, JOB, original, lease_token=LEASE) == (
        f"{SHOP}/renders/{JOB}/{LEASE}.mp4")
    assert posted == [b"original h264 synthetic bytes" * 80]
    posted.clear()

    original.unlink()
    original.symlink_to(other)
    with pytest.raises(StorageUnavailable):
        media.upload(SHOP, JOB, original, lease_token=LEASE)
    assert posted == []

    original.unlink()
    original.write_bytes(b"original h264 synthetic bytes" * 80)
    real_open = os.open

    def swap_after_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if Path(path) == original:
            original.unlink()
            original.symlink_to(other)
        return fd

    monkeypatch.setattr("private_media.os.open", swap_after_open)
    with pytest.raises(StorageUnavailable):
        media.upload(SHOP, JOB, original, lease_token=LEASE)
    assert posted == []

