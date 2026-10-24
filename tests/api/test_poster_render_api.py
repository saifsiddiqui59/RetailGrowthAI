"""Poster render API: user JWT and tenant-safe private signed PNG downloads."""
import sys
from pathlib import Path
from uuid import uuid4
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"azure-functions"/"campaign-api"))
from poster_render_api import PosterRenderAPI
from http_api import HTTPAPI

SID, UID, PID, JID, AID = (str(uuid4()) for _ in range(5))


class Store:
    def __init__(self):
        self.write = True
        self.visible = True
        self.status = "SUCCEEDED"
        self.mime = "image/png"
        self.path = f"{SID}/posters/{PID}/00000000-0000-4000-8000-000000000001.png"
        self.calls=[]
    def poster_draft(self, token, uid, pid):
        self.calls.append("draft")
        return {"id":PID,"shop_id":SID} if self.visible and pid==PID else None
    def member(self, token, uid, sid, write=False):
        self.calls.append("member_write" if write else "member_read")
        return self.visible and sid==SID and (self.write or not write)
    def request_poster_job(self, token, pid):
        assert token=="JWT" and pid==PID
        return JID
    def poster_job(self, token, uid, jid):
        self.calls.append("job")
        if not self.visible or jid!=JID: return None
        return {"id":JID,"poster_id":PID,"shop_id":SID,"status":self.status,
                "output_asset_id":AID,"error_code":None}
    def asset(self, token, sid, aid):
        self.calls.append("asset")
        assert sid==SID and aid==AID
        return {"shop_id":SID,"mime_type":self.mime,"object_path":self.path}
    def sign_download(self, token, sid, path):
        assert token=="JWT" and sid==SID and path==self.path
        self.calls.append("signed")
        return "https://private.example/signed?token=ci-only"


def test_request_auth_and_idempotent_job_boundary():
    store=Store(); api=PosterRenderAPI(store)
    assert api.create("JWT",UID,PID)==(202,{"job_id":JID,"status":"QUEUED"})
    assert store.calls==["draft","member_write"]


def test_viewer_and_foreign_cannot_initiate_render():
    store=Store();store.write=False
    assert PosterRenderAPI(store).create("JWT",UID,PID)[0]==403
    store.visible=False
    assert PosterRenderAPI(store).create("JWT",UID,PID)[0]==404


def test_read_status_and_signed_download_use_user_membership():
    store=Store();api=PosterRenderAPI(store)
    assert api.get("JWT",UID,JID)[1]["status"]=="SUCCEEDED"
    code,body=api.download("JWT",UID,JID)
    assert code==200 and "token=" in body["url"]
    assert store.calls[-1]=="signed"


@pytest.mark.parametrize("status",["QUEUED","RUNNING","FAILED"])
def test_pending_or_failed_job_cannot_mint_download(status):
    store=Store();store.status=status
    assert PosterRenderAPI(store).download("JWT",UID,JID)[0]==409
    assert "signed" not in store.calls


def test_foreign_job_and_non_png_or_wrong_output_path_fail_closed():
    store=Store();store.visible=False
    assert PosterRenderAPI(store).download("JWT",UID,JID)[0]==404
    store.visible=True;store.mime="video/mp4"
    assert PosterRenderAPI(store).download("JWT",UID,JID)[0]==404
    store.mime="image/png";store.path=f"{SID}/renders/foreign.png"
    assert PosterRenderAPI(store).download("JWT",UID,JID)[0]==404
    assert "signed" not in store.calls


def test_http_is_disabled_without_explicit_secure_poster_render_flag():
    store=Store()
    api=HTTPAPI(lambda token:UID,store,poster_render_api=None)
    assert api.handle("POST",f"/poster-drafts/{PID}/renders","Bearer JWT",{})[0]==503
    assert api.handle("GET",f"/poster-jobs/{JID}/download","Bearer JWT")[0]==503
    api=HTTPAPI(lambda token:UID,store,poster_render_api=PosterRenderAPI(store))
    assert api.handle("POST",f"/poster-drafts/{PID}/renders","Bearer JWT",{})[0]==202
    assert api.handle("POST",f"/poster-drafts/{PID}/renders","Bearer JWT",{"extra":1})[0]==400
    assert api.handle("GET",f"/poster-jobs/{JID}","Bearer JWT")[0]==200
    assert api.handle("GET",f"/poster-jobs/{JID}/download","Bearer JWT")[0]==200
