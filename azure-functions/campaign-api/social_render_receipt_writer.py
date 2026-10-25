"""Part2 adapter for Part1's TRUSTED successful FFmpeg render finalization.

SOURCE ONLY, never registered on HTTP, queues or Part1 renderer. This must
only be called by the Part1 service while it still owns the private generated
output bytes, after the exact asset/render relation has been durably marked
SUCCEEDED. It cannot be used to backfill a hash from tenant-editable media,
and cannot attest license/music rights. DB RPC is append-only and requires
same-shop successful Part1 output and canonical finalized render path.
"""
from __future__ import annotations

from hashlib import sha256
import hmac
import json
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler,Request,build_opener

from admin_store import backend_headers
from social_media_evidence import inspect_staged_mp4,MediaEvidenceRejected
from tenant_store import canonical_uuid

_MAX=80*1024*1024


class RenderReceiptDenied(ValueError):
    """Never disclose local path, service key, provider media or DB response."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (TypeError,AttributeError,ValueError):
        raise RenderReceiptDenied("RENDER_ID_DENIED") from None


def _file_digest(path):
    data=sha256()
    size=0
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            size+=len(block)
            if size>_MAX:
                raise RenderReceiptDenied("RENDER_TOO_LARGE")
            data.update(block)
    if size<1:
        raise RenderReceiptDenied("RENDER_EMPTY")
    return data.hexdigest()


class FinalizedRenderReceiptWriter:
    def __init__(self, *, origin, service_key, inspector=None,
                 transport=None, enabled=False):
        if enabled is not True:
            raise RenderReceiptDenied("RENDER_RECEIPT_RELEASE_DISABLED")
        try:
            parsed=urlsplit(origin)
            if (not isinstance(origin,str) or origin!=origin.strip()
                    or any(ord(ch)<=32 or ord(ch)==127 for ch in origin)
                    or parsed.scheme!="https" or not parsed.hostname
                    or parsed.username or parsed.password
                    or parsed.port not in (None,443)
                    or parsed.path not in ("","/") or parsed.query or parsed.fragment):
                raise ValueError()
            self.headers=backend_headers(service_key)
        except (TypeError,ValueError):
            raise RenderReceiptDenied("RENDER_RECEIPT_BACKEND_INVALID") from None
        self.url=origin.rstrip("/")+"/rest/v1/rpc/p2_record_finalized_render_digest"
        self.inspector=inspector or inspect_staged_mp4
        self.transport=transport or build_opener(_NoRedirect()).open

    def record_from_trusted_render(self, *, shop_id, render_job_id,
                                   media_asset_id, source_path, private_root):
        sid,jid,aid=(_uuid(shop_id),_uuid(render_job_id),_uuid(media_asset_id))
        try:
            root=Path(private_root).resolve(strict=True)
            source=Path(source_path)
            if source.is_symlink():
                raise RenderReceiptDenied("RENDER_SOURCE_UNTRUSTED")
            actual=source.resolve(strict=True)
            if (actual==root or root not in actual.parents
                    or not actual.is_file()):
                raise RenderReceiptDenied("RENDER_SOURCE_UNTRUSTED")
            initial=actual.stat()
            if not 0<initial.st_size<=_MAX:
                raise RenderReceiptDenied("RENDER_SOURCE_SIZE_DENIED")
            trusted_sha=_file_digest(actual)
            inspected=self.inspector(source_path=actual,private_root=root,
                                     expected_sha256=trusted_sha)
            if (not isinstance(inspected,dict)
                    or not hmac.compare_digest(
                        inspected.get("source_sha256",""),trusted_sha)
                    or not isinstance(inspected.get("ffprobe"),dict)
                    or inspected["ffprobe"].get("video_codec")!="h264"
                    or inspected["ffprobe"].get("audio_codec")!="aac"):
                raise RenderReceiptDenied("RENDER_BYTE_PROFILE_DENIED")
            final=actual.stat()
            if (initial.st_dev,initial.st_ino,initial.st_mtime_ns,
                    initial.st_size)!=(final.st_dev,final.st_ino,
                    final.st_mtime_ns,final.st_size):
                raise RenderReceiptDenied("RENDER_SOURCE_CHANGED")
            if not hmac.compare_digest(_file_digest(actual),trusted_sha):
                raise RenderReceiptDenied("RENDER_SOURCE_CHANGED")
        except RenderReceiptDenied:
            raise
        except (MediaEvidenceRejected,OSError,ValueError,TypeError,AttributeError):
            raise RenderReceiptDenied("RENDER_SOURCE_UNAVAILABLE") from None

        # The database independently checks the successful Part1 render/output
        # lineage and writes the SHA only if no conflicting receipt exists.
        params={"p_shop":sid,"p_render":jid,"p_asset":aid,
                "p_digest":trusted_sha}
        req=Request(self.url,method="POST",
           data=json.dumps(params,separators=(",",":")).encode(),
           headers={**self.headers,"Content-Type":"application/json",
                    "Accept":"application/json"})
        try:
            with self.transport(req,timeout=10) as response:
                if response.geturl()!=self.url or response.status!=200:
                    raise RenderReceiptDenied("RENDER_RECEIPT_DB_DENIED")
                body=response.read(1025)
                if len(body)>1024 or json.loads(body) is not True:
                    raise RenderReceiptDenied("RENDER_RECEIPT_NOT_DURABLE")
        except RenderReceiptDenied:
            raise
        except (HTTPError,URLError,OSError,TypeError,UnicodeError,ValueError):
            raise RenderReceiptDenied("RENDER_RECEIPT_DB_UNAVAILABLE") from None

        return {"shop_id":sid,"render_job_id":jid,"media_asset_id":aid,
                "source_sha256":trusted_sha,
                "state":"TRUSTED_PART1_RENDER_DIGEST_RECORDED"}
