"""Server-only Part1 finalized render evidence writer, mocked RPC and file."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_render_receipt_writer import FinalizedRenderReceiptWriter,RenderReceiptDenied

SID="31000000-0000-4000-8000-000000000001"
RID="91000000-0000-4000-8000-000000000001"
AID="81000000-0000-4000-8000-000000000001"
DATA=b"synthetic trusted render mp4 byte fixture"
SHA=sha256(DATA).hexdigest()
ORIGIN="https://retail.test.supabase.co"

class Response:
    status=200
    def __init__(self,url,body):
        self.url=url;self.body=BytesIO(body)
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False

def fixture(tmp_path):
    path=tmp_path/"render.mp4";path.write_bytes(DATA)
    calls=[]
    seen=[]
    data={"allowed":True}
    def inspect(**params):
        seen.append(params)
        assert params["source_path"].read_bytes()==DATA
        assert params["expected_sha256"]==SHA
        return {"source_sha256":SHA,
                "ffprobe":{"video_codec":"h264","audio_codec":"aac"}}
    def transport(req,timeout):
        assert timeout==10
        assert req.get_header("Apikey")=="sb_secret_testing"
        assert req.full_url==ORIGIN+"/rest/v1/rpc/p2_record_finalized_render_digest"
        params=json.loads(req.data)
        calls.append(params)
        return Response(req.full_url,b"true" if data["allowed"] else b"false")
    writer=FinalizedRenderReceiptWriter(
        origin=ORIGIN,service_key="sb_secret_testing",
        inspector=inspect,transport=transport,enabled=True)
    req={"shop_id":SID,"render_job_id":RID,"media_asset_id":AID,
         "source_path":path,"private_root":tmp_path}
    return writer,req,calls,seen,data

def test_success_sha_computed_from_trusted_local_part1_finalizer(tmp_path):
    writer,req,calls,seen,data=fixture(tmp_path)
    output=writer.record_from_trusted_render(**req)
    assert output["state"]=="TRUSTED_PART1_RENDER_DIGEST_RECORDED"
    assert output["source_sha256"]==SHA
    assert calls==[{"p_shop":SID,"p_render":RID,"p_asset":AID,"p_digest":SHA}]
    assert len(seen)==1
    assert set(req)=={"shop_id","render_job_id","media_asset_id",
                       "source_path","private_root"}
    assert "source_sha256" not in req

def test_wrong_shop_render_asset_and_path_refused_before_backend(tmp_path):
    writer,req,calls,seen,data=fixture(tmp_path)
    for key in ("shop_id","render_job_id","media_asset_id"):
        params=req|{key:"untrusted/"}
        with pytest.raises(RenderReceiptDenied):
            writer.record_from_trusted_render(**params)
    assert calls==[]
    external=tmp_path.parent/"outside.mp4"
    external.write_bytes(DATA)
    with pytest.raises(RenderReceiptDenied,match="SOURCE_UNTRUSTED"):
        writer.record_from_trusted_render(**(req|{"source_path":external}))
    symlink=tmp_path/"alias.mp4"
    symlink.symlink_to(req["source_path"])
    with pytest.raises(RenderReceiptDenied,match="SOURCE_UNTRUSTED"):
        writer.record_from_trusted_render(**(req|{"source_path":symlink}))
    assert calls==[]

def test_mutated_source_and_false_inspection_do_not_record_digest(tmp_path):
    writer,req,calls,seen,data=fixture(tmp_path)
    # Change the file after the writer's first SHA, during the inspector.
    # The writer must catch the modified inode stat/digest BEFORE DB write.
    def mutating_inspector(**kwargs):
        req["source_path"].write_bytes(b"changed during inspection")
        return {"source_sha256":kwargs["expected_sha256"],
                "ffprobe":{"video_codec":"h264","audio_codec":"aac"}}
    writer.inspector=mutating_inspector
    with pytest.raises(RenderReceiptDenied,match="SOURCE_CHANGED"):
        writer.record_from_trusted_render(**req)
    assert calls==[]
    writer,req,calls,seen,data=fixture(tmp_path)
    writer.inspector=lambda **kwargs:{"source_sha256":"ff"*32,
                         "ffprobe":{"video_codec":"h264","audio_codec":"aac"}}
    with pytest.raises(RenderReceiptDenied,match="BYTE_PROFILE_DENIED"):
        writer.record_from_trusted_render(**req)
    assert calls==[]

def test_immutable_database_receipt_denial_does_not_report_success(tmp_path):
    writer,req,calls,seen,data=fixture(tmp_path)
    data["allowed"]=False
    with pytest.raises(RenderReceiptDenied,match="NOT_DURABLE"):
        writer.record_from_trusted_render(**req)
    assert len(calls)==1

def test_disabled_by_default_and_bad_service_origin(tmp_path):
    with pytest.raises(RenderReceiptDenied,match="RELEASE_DISABLED"):
        FinalizedRenderReceiptWriter(origin=ORIGIN,service_key="sb_secret_testing")
    for origin in ("http://retail.test.supabase.co",
                   "https://retail.test.supabase.co:8000",
                   "https://retail.test.supabase.co@attacker.invalid",
                   "https://retail.test.supabase.co/private",
                   "https://retail.test.supabase.co\n"):
        with pytest.raises(RenderReceiptDenied,match="BACKEND_INVALID"):
            FinalizedRenderReceiptWriter(origin=origin,service_key="sb_secret_testing",enabled=True)
