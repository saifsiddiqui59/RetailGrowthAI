"""Server-owned render/rights/revision gate; offline, no provider or cloud."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_video_certification import (
    SocialVideoReviewService, SocialVideoCertificationDenied,
)

SHOP = "31000000-0000-4000-8000-000000000001"
OTHER = "31000000-0000-4000-8000-000000000002"
ACTOR = "ffffffff-ffff-4fff-8fff-ffffffffffff"
JOB = "62000000-0000-4000-8000-000000000001"
ASSET = "81000000-0000-4000-8000-000000000001"
RENDER = "91000000-0000-4000-8000-000000000001"
PATH = f"{SHOP}/renders/{RENDER}.mp4"
BYTES = b"reviewed private generated clip bytes"
SHA = sha256(BYTES).hexdigest()
RIGHTS = sha256(b"independent signed stock/owner license evidence").hexdigest()
NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)
DUE = NOW + timedelta(days=2)
PROFILE = {
    "container": "mp4", "video_codec": "h264", "audio_codec": "aac",
    "width": 1080, "height": 1920, "pixel_format": "yuv420p",
    "duration_seconds": "30.000",
}


class Candidates:
    def __init__(self):
        self.current = {
            "shop_id": SHOP, "job_id": JOB, "media_asset_id": ASSET,
            "revision": 4, "source": "GENERATED",
            "storage_bucket": "retailgrowth-media",
            "object_path": PATH, "scheduled_at": DUE,
        }
        self.calls = []
        self.record_result = True
        self.bind_result = True

    def get_source(self, shop, job, actor):
        self.calls.append(("source", shop, job, actor))
        return self.current

    def record_review(self, *args):
        self.calls.append(("record",) + args)
        return self.record_result

    def bind_review(self, *args):
        self.calls.append(("bind",) + args)
        return self.bind_result


class Receipts:
    def __init__(self):
        self.receipt = {
            "shop_id": SHOP, "media_asset_id": ASSET,
            "object_path": PATH, "source": "PART1_RENDER_FINALIZED",
            "source_sha256": SHA,
        }
        self.calls = []

    def get_render_receipt(self, *args):
        self.calls.append(args)
        return self.receipt


class Rights:
    def __init__(self):
        self.clearance = {
            "shop_id": SHOP, "media_asset_id": ASSET, "reviewed_by": ACTOR,
            "revision": 4, "rights_kind": "GENERATED_RIGHTS_VERIFIED",
            "rights_evidence_sha256": RIGHTS,
            "rights_expires_at": DUE + timedelta(days=2),
        }
        self.calls = []

    def get_clearance(self, *args):
        self.calls.append(args)
        return self.clearance


class Reader:
    def __init__(self):
        self.calls = []
        self.content = BYTES

    def download(self, **kwargs):
        self.calls.append(kwargs)
        kwargs["destination"].write_bytes(self.content)
        return {"path": kwargs["destination"],
                "source_sha256": sha256(self.content).hexdigest(),
                "size_bytes": len(self.content)}


class Probe:
    def __init__(self):
        self.calls = []
        self.result = {"source_sha256": SHA, "ffprobe": PROFILE}

    def __call__(self, **kwargs):
        assert kwargs["source_path"].read_bytes() == BYTES
        self.calls.append(kwargs)
        return self.result


def setup():
    candidates, receipts, rights = Candidates(), Receipts(), Rights()
    reader, probe = Reader(), Probe()
    service = SocialVideoReviewService(
        candidates=candidates, receipts=receipts, rights=rights,
        private_reader=reader, probe=probe, clock=lambda: NOW)
    return service, candidates, receipts, rights, reader, probe


def certify(service):
    return service.certify(shop_id=SHOP, job_id=JOB, reviewer_id=ACTOR)


def test_happy_path_pins_source_sha_and_rights_to_exact_reviewed_job():
    service, candidates, receipts, rights, reader, probe = setup()
    result = certify(service)
    assert result == {
        "job_id": JOB, "shop_id": SHOP, "media_asset_id": ASSET,
        "revision": 4, "source_sha256": SHA,
        "state": "REVIEWED_NOT_PUBLISHABLE",
    }
    assert [x[0] for x in candidates.calls] == ["source", "record", "bind"]
    assert candidates.calls[1] == (
        "record", SHOP, ASSET, ACTOR, SHA, RIGHTS,
        "GENERATED_RIGHTS_VERIFIED", PROFILE,
        rights.clearance["rights_expires_at"],
    )
    assert candidates.calls[2] == ("bind", SHOP, JOB, ACTOR, 4, SHA)
    assert receipts.calls == [(SHOP, ASSET)]
    assert rights.calls == [(SHOP, ASSET, ACTOR, 4)]
    assert reader.calls[0]["expected_sha256"] == SHA
    assert len(probe.calls) == 1
    # The temporary private file is destroyed before caller sees a result.
    assert not reader.calls[0]["destination"].exists()


@pytest.mark.parametrize("mutation", [
    lambda c,r,l: c.current.update(shop_id=OTHER),
    lambda c,r,l: c.current.update(job_id=OTHER),
    lambda c,r,l: c.current.update(revision=0),
    lambda c,r,l: c.current.update(revision=True),
    lambda c,r,l: c.current.update(source="UPLOAD"),
    lambda c,r,l: c.current.update(storage_bucket="public"),
    lambda c,r,l: c.current.update(scheduled_at=NOW),
    lambda c,r,l: r.receipt.update(shop_id=OTHER),
    lambda c,r,l: r.receipt.update(media_asset_id=OTHER),
    lambda c,r,l: r.receipt.update(object_path="other/render.mp4"),
    lambda c,r,l: r.receipt.update(source="BROWSER_UPLOADED"),
    lambda c,r,l: r.receipt.update(source_sha256="0"*64),
    lambda c,r,l: r.receipt.update(source_sha256="not-a-hash"),
    lambda c,r,l: l.clearance.update(shop_id=OTHER),
    lambda c,r,l: l.clearance.update(media_asset_id=OTHER),
    lambda c,r,l: l.clearance.update(reviewed_by=OTHER),
    lambda c,r,l: l.clearance.update(revision=5),
    lambda c,r,l: l.clearance.update(rights_kind="UNREVIEWED"),
    lambda c,r,l: l.clearance.update(rights_expires_at=DUE),
    lambda c,r,l: l.clearance.update(rights_expires_at=None),
    lambda c,r,l: l.clearance.update(rights_evidence_sha256="missing"),
])
def test_authority_failure_never_downloads_or_persists(mutation):
    service, candidates, receipts, rights, reader, probe = setup()
    mutation(candidates, receipts, rights)
    with pytest.raises(SocialVideoCertificationDenied):
        certify(service)
    # A well-formed but false trusted SHA can only be disproved by a
    # bounded private read; it must still fail before FFprobe or persistence.
    if receipts.receipt["source_sha256"] == "0" * 64:
        assert len(reader.calls) == 1
        assert reader.calls[0]["expected_sha256"] == "0" * 64
    else:
        assert reader.calls == []
    assert probe.calls == []
    assert all(call[0] not in ("record", "bind") for call in candidates.calls)


def test_failed_download_or_probe_never_writes_review():
    service, candidates, receipts, rights, reader, probe = setup()
    reader.content = b"tampered by storage write"
    with pytest.raises(SocialVideoCertificationDenied):
        certify(service)
    assert all(call[0] not in ("record", "bind") for call in candidates.calls)
    service, candidates, receipts, rights, reader, probe = setup()
    probe.result = {"source_sha256": SHA, "ffprobe": {"video_codec": "h264", "audio_codec": "mp3"}}
    with pytest.raises(SocialVideoCertificationDenied, match="VIDEO_PROBE_DENIED"):
        certify(service)
    assert all(call[0] not in ("record", "bind") for call in candidates.calls)


def test_database_cas_refusal_never_reports_success():
    service, candidates, receipts, rights, reader, probe = setup()
    candidates.record_result = False
    with pytest.raises(SocialVideoCertificationDenied, match="VIDEO_REVIEW_NOT_DURABLE"):
        certify(service)
    assert all(call[0] != "bind" for call in candidates.calls)
    service, candidates, receipts, rights, reader, probe = setup()
    candidates.bind_result = False
    with pytest.raises(SocialVideoCertificationDenied, match="VIDEO_REVIEW_BIND_DENIED"):
        certify(service)


def test_untrusted_raw_ids_and_missing_authorities_denied():
    service, candidates, receipts, rights, reader, probe = setup()
    with pytest.raises(SocialVideoCertificationDenied):
        service.certify(shop_id=OTHER + "/../", job_id=JOB, reviewer_id=ACTOR)
    for name in ["candidates", "receipts", "rights", "private_reader"]:
        kwargs = {
            "candidates": candidates, "receipts": receipts, "rights": rights,
            "private_reader": reader,
        }
        kwargs[name] = None
        with pytest.raises(ValueError):
            SocialVideoReviewService(**kwargs)
