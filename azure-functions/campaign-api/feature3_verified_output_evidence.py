"""Feature3 read-only independently verified generated PNG operator evidence.

Source-only companion to an un-applied, service_role-only SQL RPC. Reads an
immutable output evidence row twice via an authoritative service-only RPC
and byte-hashes the actual private Storage PNG between both reads.

A row saying 'SUCCEEDED' is not independent proof that Storage has correct
bytes; the operator receipt is issued only on the exact verified binary.
This class cannot settle/refund/retry a job, delete Storage, approve an image,
publish media or turn on paid inference.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from PIL import Image, UnidentifiedImageError

from admin_store import backend_headers
from tenant_store import canonical_uuid

_MAX=25*1024*1024
_SHA=re.compile(r"^[a-f0-9]{64}$")
_KEYS=frozenset(("shop_id","job_id","media_asset_id",
                 "image_sha256","object_path","object_bytes",
                 "attempt","review_status","private"))


class Feature3EvidenceReadDenied(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        return None


class Feature3VerifiedOutputEvidenceReader:
    """Service-only source / not exposed as public retailer API."""

    def __init__(self, *, admin_store, transport=None):
        if (not callable(getattr(admin_store,"request",None)) or
                not isinstance(getattr(admin_store,"secret",None),str)):
            raise ValueError("Actual private backend PostgREST store required")
        origin=getattr(admin_store,"origin",None)
        u=urlsplit(origin) if isinstance(origin,str) else None
        if (not u or u.scheme!="https" or not u.hostname or
                not u.hostname.endswith(".supabase.co") or
                u.username or u.password or u.port not in (None,443) or
                u.path not in ("","/") or u.query or u.fragment):
            raise ValueError("Exact trusted Supabase origin required")
        self.db=admin_store
        self.origin=origin.rstrip("/")
        self.headers=backend_headers(admin_store.secret)
        self.transport=transport or build_opener(_NoRedirect()).open

    def _rpc(self,shop,job,asset):
        value=self.db.request("rpc/feature3_read_gpu_private_evidence",
                              method="POST",data={
            "p_shop_id":shop,"p_job_id":job,
            "p_media_asset_id":asset})
        prefix=f"{shop}/feature3/gpu/{job}/"
        if (not isinstance(value,dict) or set(value)!=_KEYS or
                value.get("shop_id")!=shop or value.get("job_id")!=job or
                value.get("media_asset_id")!=asset or
                value.get("private") is not True or
                value.get("review_status")!="UNREVIEWED" or
                type(value.get("attempt")) is not int or value["attempt"]!=1 or
                not isinstance(value.get("image_sha256"),str) or
                not _SHA.fullmatch(value["image_sha256"]) or
                value.get("object_path")!=prefix+value["image_sha256"]+".png" or
                type(value.get("object_bytes")) is not int or
                not 100<=value["object_bytes"]<=_MAX):
            raise Feature3EvidenceReadDenied("Unverified private output SQL proof")
        return value

    def _get_bytes(self,row):
        key=row["object_path"]
        url=self.origin+"/storage/v1/object/retailgrowth-media/"+quote(key,safe="/")
        req=Request(url,method="GET",headers={
            **self.headers, "Accept":"image/png","Cache-Control":"no-store"})
        try:
            with self.transport(req,timeout=15) as response:
                if response.geturl()!=url or response.getcode()!=200:
                    raise Feature3EvidenceReadDenied("Private byte response unconfirmed")
                headers=getattr(response,"headers",{})
                content_type=headers.get("Content-Type") if headers is not None else None
                content_length=headers.get("Content-Length") if headers is not None else None
                if content_type is not None and content_type.split(";",1)[0].strip().lower()!="image/png":
                    raise Feature3EvidenceReadDenied("Private bytes not PNG")
                if content_length is not None and (
                        not isinstance(content_length,str) or
                        not content_length.isascii() or
                        not content_length.isdigit() or
                        int(content_length)!=row["object_bytes"]):
                    raise Feature3EvidenceReadDenied("Private bytes length disagrees with SQL")
                payload=response.read(_MAX+1)
        except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:
            raise Feature3EvidenceReadDenied("Authenticated private output read denied") from exc
        if (type(payload) is not bytes or len(payload)!=row["object_bytes"] or
                sha256(payload).hexdigest()!=row["image_sha256"]):
            raise Feature3EvidenceReadDenied("Private PNG does not match immutable SQL proof")
        try:
            with Image.open(BytesIO(payload)) as image:
                if (image.format!="PNG" or getattr(image,"n_frames",1)!=1 or
                        not 256<=image.width<=8192 or
                        not 256<=image.height<=8192 or
                        image.width*image.height>24_000_000):
                    raise Feature3EvidenceReadDenied("Private output PNG unsuitable")
                image.verify()
        except (OSError,ValueError,UnidentifiedImageError,
                Image.DecompressionBombError) as exc:
            raise Feature3EvidenceReadDenied("Corrupted private output PNG") from exc
        return payload

    def __call__(self,shop_id,job_id,asset_id):
        try:
            shop=canonical_uuid(shop_id)
            job=canonical_uuid(job_id)
            asset=canonical_uuid(asset_id)
        except (TypeError,ValueError,AttributeError) as exc:
            raise Feature3EvidenceReadDenied("Invalid private GPU output identity") from exc
        first=self._rpc(shop,job,asset)
        self._get_bytes(first)
        if self._rpc(shop,job,asset)!=first:
            raise Feature3EvidenceReadDenied("Private output changed between checks")
        return {
            "shop_id":shop,"job_id":job,"media_asset_id":asset,
            "image_sha256":first["image_sha256"],
            "private":True,"attempt":1,"review_status":"UNREVIEWED",
        }
