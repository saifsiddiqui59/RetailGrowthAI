"""Queue worker fail-closed tests. FFmpeg binary verified separately in video-engine/ci.sh."""
import sys
from pathlib import Path
from uuid import uuid4

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from render_worker import process_render, RetryableRender

JID, SID, CID, DID, UID, AID = (str(uuid4()) for _ in range(6))


class Admin:
    def __init__(self):
        self.status = "QUEUED"
        self.authorized = True
        self.claimed = True
        self.failures = []
        self.outputs = []

    def render_status(self, job_id): return self.status
    def claim_render(self, job_id):
        return {"id": JID, "shop_id": SID, "campaign_id": CID, "day_id": DID,
                "requested_by": UID, "preset": "instagram_reel_30s",
                "attempts": 1} if self.claimed else None
    def render_authorized(self, job): return self.authorized
    def render_sources(self, job):
        return (
            {"id": CID, "shop_id": SID, "status": "DRAFT"},
            {"id": DID, "shop_id": SID, "campaign_id": CID, "day_index": 1,
             "review_status": "DRAFT",
             "instagram": {"reel": {"duration_seconds": 30, "aspect_ratio": "9:16",
                "music_asset_id": None, "cta": "Visit",
                "storyboard": [
                    {"start_seconds": t, "duration_seconds": 10,
                     "overlay_text": "Scene", "asset_id": AID}
                    for t in (0, 10, 20)
                ]}}},
            {AID: {"id": AID, "shop_id": SID, "storage_bucket": "retailgrowth-media",
                   "mime_type": "image/png", "source": "UPLOAD",
                   "license_name": "owned", "license_url": "https://rights.example", "object_path": SID + "/pic.png"}},
        )
    def complete_render(self, job, path): self.outputs.append(path)
    def render_failure(self, job, code, permanent=False): self.failures.append((code, permanent))


class Media:
    def download(self, sid, path, dest):
        dest.write_bytes(b"stubbed image; codec output tested independently")
    def upload(self, sid, jid, file):
        assert file.exists()
        return sid + "/renders/" + jid + ".mp4"


def fake_render(storyboard, images, music, cta, output, **kwargs):
    output.write_bytes(b"fake-mp4")
    return {"video_codec": "h264", "audio_codec": "aac", "duration_seconds": 30}


def test_worker_stages_only_authorized_media_then_records_output():
    admin=Admin()
    assert process_render(JID, admin, Media(), render_fn=fake_render) == "SUCCEEDED"
    assert admin.outputs == [SID + "/renders/" + JID + ".mp4"]


def test_repeated_job_or_revoked_member_never_renders():
    admin=Admin()
    admin.status="SUCCEEDED"
    assert process_render(JID, admin, Media(), render_fn=lambda *_a, **_k: pytest.fail("should not render")) == "ALREADY_FINAL"
    admin=Admin()
    admin.authorized=False
    assert process_render(JID, admin, Media(), render_fn=lambda *_a, **_k: pytest.fail("should not render")) == "DENIED"
    assert admin.failures == [("ACCESS_REVOKED", True)]


def test_busy_claim_is_retried():
    admin=Admin()
    admin.claimed=False
    with pytest.raises(RetryableRender):
        process_render(JID, admin, Media(), render_fn=fake_render)


def test_unlicensed_asset_fails_and_does_not_upload():
    admin=Admin()
    original=admin.render_sources
    def broken(job):
        campaign,day,assets=original(job)
        assets[AID]["license_name"]="unknown"
        return campaign,day,assets
    admin.render_sources=broken
    with pytest.raises(Exception):
        process_render(JID, admin, Media(), render_fn=fake_render)
    assert admin.failures == [("RENDER_FAILED", False)]


def test_worker_success_receipt_only_after_actual_completed_render():
    db=Admin()
    spans=[]
    assert process_render(JID, db, Media(), render_fn=fake_render,
                          span_sink=spans.append) == "SUCCEEDED"
    assert db.outputs
    assert len(spans)==1
    span=spans[0]
    assert span["feature"]=="F4"
    assert span["status"]=="SUCCEEDED"
    assert span["operation"]=="render.complete"
    assert span["metadata"] == {
        "codec":"h264/aac", "video_width":1080, "video_height":1920,
        "duration_seconds":30,
    }
    assert span["persisted"] is False
    assert not any("/renders/" in str(value) for value in span.values())


def test_render_denied_records_no_false_render_success():
    db=Admin()
    db.authorized=False
    spans=[]
    assert process_render(JID, db, Media(), render_fn=fake_render,
                          span_sink=spans.append) == "DENIED"
    assert db.failures == [("ACCESS_REVOKED", True)]
    assert len(spans)==1 and spans[0]["status"]=="DENIED"
