"""Offline-only creation/verification of immutable signed Instagram exports."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
import json, sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_immutable_export import ImmutableSocialExportWriter, ExportDenied

SHOP="31000000-0000-4000-8000-000000000001"
JOB="62000000-0000-4000-8000-000000000001"
CONTENT=b"mocked fully rights-reviewed verified mp4 bytes"
SHA=sha256(CONTENT).hexdigest()
ROOT="https://retail.test.supabase.co"


class Authority:
    def __init__(self):
        self.calls=[]
        self.allowed=True
    def allow_export(self,*args):
        self.calls.append(args)
        return self.allowed


class Response:
    status=200
    def __init__(self,url,data):
        self.url=url
        self.body=BytesIO(data)
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False


def make_store():
    calls=[]
    media={"bytes":CONTENT,"signed":True,"malicious":False}
    def transport(request,timeout):
        assert timeout==45 and request.get_header("Apikey")=="sb_secret_testing"
        calls.append(request)
        if "/storage/v1/object/retailgrowth-social-exports/" in request.full_url:
            if request.get_method()=="POST":
                assert request.get_header("X-upsert")=="false"
                assert request.get_header("Content-type")=="video/mp4"
                assert sha256(request.data).hexdigest()==SHA
                return Response(request.full_url,b'{"Key":"private-export"}')
            assert request.get_method()=="GET"
            return Response(request.full_url,media["bytes"])
        assert request.get_method()=="POST"
        assert "/storage/v1/object/sign/retailgrowth-social-exports/" in request.full_url
        assert json.loads(request.data)=={"expiresIn":7200}
        if media["malicious"]:
            signed="/object/sign/retailgrowth-media/unsafe.mp4?token=fake"
        else:
            signed=request.full_url.split("/storage/v1",1)[1]+"?token=REAL-SIGNED-VERIFICATION-TOKEN-123456"
        return Response(request.full_url,json.dumps({"signedURL":signed}).encode())
    return transport,calls,media


def fixture(tmp_path):
    file=tmp_path/"private.mp4";file.write_bytes(CONTENT)
    transport,calls,media=make_store()
    authority=Authority()
    writer=ImmutableSocialExportWriter(origin=ROOT,service_key="sb_secret_testing",
       claim_authority=authority,enabled=True,transport=transport)
    kwargs=dict(shop_id=SHOP,job_id=JOB,revision=7,source_sha256=SHA,
       source_path=file,private_root=tmp_path)
    return writer,kwargs,authority,calls,media


def test_exact_copy_once_readback_and_signed_result(tmp_path):
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    result=writer.create_signed_export(**kwargs)
    assert result["state"]=="IMMUTABLE_EXPORT_VERIFIED"
    assert result["source_sha256"]==SHA
    assert result["object_path"]==f"{SHOP}/video/{JOB}/7/{SHA}.mp4"
    assert result["signed_url"].startswith(ROOT+"/storage/v1/object/sign/retailgrowth-social-exports/")
    assert [r.get_method() for r in calls]==["POST","GET","POST"]
    assert authority.calls==[(SHOP,JOB,7,SHA)]*2


@pytest.mark.parametrize("change",[
    lambda kw:kw.update(source_sha256="0"*64),
    lambda kw:kw.update(source_sha256="untrusted"),
    lambda kw:kw.update(revision=0),
    lambda kw:kw.update(revision=True),
    lambda kw:kw.update(job_id="arbitrary-path"),
    lambda kw:kw.update(expires_seconds=1),
])
def test_bad_source_claim_or_parameters_no_write(tmp_path,change):
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    change(kwargs)
    with pytest.raises(ExportDenied):
        writer.create_signed_export(**kwargs)
    assert calls==[]


def test_mutated_private_source_and_symlink_never_upload(tmp_path):
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    kwargs["source_path"].write_bytes(b"tampered content")
    with pytest.raises(ExportDenied,match="HASH_MISMATCH"):
        writer.create_signed_export(**kwargs)
    assert calls==[]
    link=tmp_path/"link.mp4"
    link.symlink_to(kwargs["source_path"])
    kwargs["source_path"]=link
    with pytest.raises(ExportDenied,match="PATH_INVALID"):
        writer.create_signed_export(**kwargs)
    assert calls==[]


def test_mismatched_export_readback_never_creates_url(tmp_path):
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    media["bytes"]=b"altered after upload"
    with pytest.raises(ExportDenied,match="REMOTE_HASH_MISMATCH"):
        writer.create_signed_export(**kwargs)
    assert [x.get_method() for x in calls]==["POST","GET"]


def test_remote_export_signature_path_cannot_be_forged(tmp_path):
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    media["malicious"]=True
    with pytest.raises(ExportDenied,match="SIGNED_URL_UNTRUSTED"):
        writer.create_signed_export(**kwargs)
    assert [x.get_method() for x in calls]==["POST","GET","POST"]


def test_revoked_claim_before_export_or_signing_is_denied(tmp_path):
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    authority.allowed=False
    with pytest.raises(ExportDenied,match="CLAIM_DENIED"):
        writer.create_signed_export(**kwargs)
    assert calls==[]
    writer,kwargs,authority,calls,media=fixture(tmp_path)
    previous=authority.allow_export
    def revoking(*args):
        ok=previous(*args)
        authority.allowed=False
        return ok
    authority.allow_export=revoking
    with pytest.raises(ExportDenied,match="CLAIM_REVOKED"):
        writer.create_signed_export(**kwargs)
    assert [x.get_method() for x in calls]==["POST","GET"]


def test_export_cannot_be_enabled_by_import_or_without_a_verified_authority():
    with pytest.raises(ExportDenied,match="RELEASE_DISABLED"):
        ImmutableSocialExportWriter(origin=ROOT,service_key="sb_secret_testing",
            claim_authority=Authority())
    with pytest.raises(ExportDenied,match="AUTHORITY_MISSING"):
        ImmutableSocialExportWriter(origin=ROOT,service_key="sb_secret_testing",
            claim_authority=None,enabled=True)
