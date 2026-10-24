"""Poster worker security and dispatch tests. No cloud credentials or uploads."""
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from poster_worker import process_poster, dispatch_posters, RetryablePoster
from tenant_store import StorageUnavailable

JID, SID, PID, CID, DID, AID, UID, TOKEN = (str(uuid4()) for _ in range(8))


class Admin:
    def __init__(self):
        self.status = "QUEUED"
        self.authorized = True
        self.claim = True
        self.drift = False
        self.wrong_rights = False
        self.completed = []
        self.failures = []
        self.confirmations = []

    def poster_status(self, jid): return self.status
    def claim_poster(self, jid):
        if not self.claim: return None
        return {"id": JID, "shop_id": SID, "poster_id": PID,
                "requested_by": UID, "attempts": 1, "revision": 1,
                "claim_token": TOKEN, "snapshot": {
                    "topic": "Everyday Clothing", "day_index": 1,
                    "day_id": DID, "cta": "Visit store"}}
    def poster_authorized(self, job): return self.authorized
    def poster_sources(self, job):
        p = {"id": PID, "shop_id": SID, "campaign_id": CID, "day_id": DID,
             "revision": 1, "status": "RENDERING", "template": "editorial",
             "format": "square", "accent_color": "#C36F4A",
             "background_color": "#F9F3E8", "business_name": "Clothing Studio",
             "offer_text": None, "source_asset_id": AID, "logo_asset_id": None}
        campaign = {"id": CID, "shop_id": SID, "status": "DRAFT"}
        day = {"id": DID, "shop_id": SID, "campaign_id": CID,
               "day_index": 1, "topic": "Changed without review" if self.drift else "Everyday Clothing",
               "review_status": "DRAFT",
               "instagram": {"reel": {"cta": "Visit store", "storyboard": [{"asset_id": AID}]}}}
        asset = {"id": AID, "shop_id": SID, "storage_bucket": "retailgrowth-media",
                 "object_path": SID + "/uploads/" + AID + ".png", "mime_type": "image/png",
                 "source": "UPLOAD", "license_name": "unknown" if self.wrong_rights else "owned",
                 "license_url": None, "attribution": "Merchant-owned photographed product"}
        return p, campaign, day, {AID: asset}
    def complete_poster(self, job, key): self.completed.append((job,key))
    def fail_poster(self, job, permanent=False): self.failures.append(permanent)
    def claim_outbox(self, limit=10): return [{"id": JID, "job_id": JID, "lease_token": TOKEN}]
    def confirm_outbox(self, event, sent): self.confirmations.append(sent)


class Media:
    def __init__(self): self.uploaded = []
    def download(self, sid, key, destination):
        Image.new("RGB",(300,300),"#CC3300").save(destination)
    def upload_png(self, sid, pid, token, output, *, format_name):
        assert output.is_file()
        self.uploaded.append((sid,pid,token,format_name))
        return f"{sid}/posters/{pid}/{token}.png"


def fake_render(campaign, manifest, root, day_index, output, options):
    assert campaign["id"] == CID and campaign["days"][0]["topic"] == "Everyday Clothing"
    assert list(manifest["assets"]) == [AID]
    assert options.product_asset_id == AID
    Image.new("RGB",(1080,1080),"#CC3300").save(output)
    return {"width": 1080, "height": 1080}


def test_claim_render_and_private_upload_then_fenced_completion():
    admin, media = Admin(), Media()
    assert process_poster(JID,admin,media,render_fn=fake_render) == "SUCCEEDED"
    assert media.uploaded == [(SID,PID,TOKEN,"square")]
    assert admin.completed[0][1] == f"{SID}/posters/{PID}/{TOKEN}.png"


@pytest.mark.parametrize("variant", ["denied", "drift", "rights"])
def test_revocation_and_content_drift_never_upload(variant):
    admin, media = Admin(), Media()
    if variant == "denied": admin.authorized = False
    elif variant == "drift": admin.drift = True
    else: admin.wrong_rights = True
    if variant == "denied":
        assert process_poster(JID,admin,media,render_fn=fake_render) == "DENIED"
        assert admin.failures == [True]
    else:
        with pytest.raises(StorageUnavailable):
            process_poster(JID,admin,media,render_fn=fake_render)
        assert admin.failures == [False]
    assert not media.uploaded and not admin.completed


def test_busy_and_finished_jobs_do_not_render():
    admin = Admin()
    admin.claim = False
    with pytest.raises(RetryablePoster):
        process_poster(JID,admin,Media(),render_fn=fake_render)
    admin.status = "SUCCEEDED"
    assert process_poster(JID,admin,Media(),render_fn=fake_render) == "ALREADY_FINAL"


def test_wrong_claim_rejected_before_source_fetch():
    admin=Admin()
    original=admin.claim_poster
    admin.claim_poster=lambda jid:{**original(jid),"claim_token":str(uuid4()),"id":str(uuid4())}
    with pytest.raises(StorageUnavailable):
        process_poster(JID,admin,Media(),render_fn=fake_render)
    assert not admin.completed


def test_outbox_success_and_retry_are_acknowledged_explicitly():
    admin=Admin()
    class Queue:
        def enqueue(self,jid): assert jid == JID
    assert dispatch_posters(admin,Queue())==1
    assert admin.confirmations == [True]
    admin=Admin()
    class Broken:
        def enqueue(self,jid): raise OSError("queue unavailable")
    assert dispatch_posters(admin,Broken())==0
    assert admin.confirmations == [False]


def test_outbox_invalid_id_cannot_enqueue():
    admin=Admin()
    admin.claim_outbox=lambda n:[{"id":JID,"job_id":"../escape","lease_token":TOKEN}]
    with pytest.raises(ValueError):
        dispatch_posters(admin,object())
