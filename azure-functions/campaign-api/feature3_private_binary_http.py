"""Strict no-URL Feature3 generated PNG HTTP response adapter (source-only).

The production Azure entrypoint must supply a real Feature3RevocablePNGReader
with current JWT/RLS and independent live output rights, not a test stub.
This module intentionally registers NO public HTTP route or feature flag.
Never use an uploaded token or a browser-supplied media asset id to authorize
a private image. Existing 60-second signed URLs cannot be retroactively revoked.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re

from PIL import Image, UnidentifiedImageError
from zlib import crc32

from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import canonical_uuid

_SHA=re.compile(r"^[a-f0-9]{64}$")
_MAX=25*1024*1024
# The trusted reader validates full pixels; this HTTP boundary independently
# rejects non-PNG or trailing-payload receipts before publishing private bytes.
_PNG_MAGIC=b"\x89PNG\r\n\x1a\n"
_PNG_IEND=b"\x00\x00\x00\x00IEND\xaeB\x60\x82"


def _valid_png_chunks(raw):
    """Independently verify chunk boundaries and CRC before returning private bytes.

    The trusted reader still owns full pixel decode and current access rights.
    This check prevents a forged self-consistent SHA receipt with corrupted PNG
    chunk framing from being returned by the HTTP boundary.
    """
    if not raw.startswith(_PNG_MAGIC) or not raw.endswith(_PNG_IEND):
        return False
    offset=8
    saw_idat=False
    idat_closed=False
    saw_plte=False
    saw_trns=False
    palette_entries=0
    idat_bytes=0
    # IHDR color type is fixed at byte 25 of a PNG stream. Only indexed
    # color requires a palette; grayscale must never carry one.
    color_type=raw[25] if len(raw)>=29 else -1
    bit_depth=raw[24] if len(raw)>=29 else -1
    # Validate the complete IHDR rather than trusting a self-consistent SHA.
    # A forged reader receipt must not emit malformed private PNG bytes.
    if len(raw)<45:
        return False
    width=int.from_bytes(raw[16:20],"big")
    height=int.from_bytes(raw[20:24],"big")
    if (not 1<=width<=16384 or not 1<=height<=16384 or
            width*height>16_777_216 or
            (color_type,bit_depth) not in {
                (0,1),(0,2),(0,4),(0,8),(0,16),
                (2,8),(2,16),(3,1),(3,2),(3,4),(3,8),
                (4,8),(4,16),(6,8),(6,16)
            } or raw[26]!=0 or raw[27]!=0 or raw[28] not in (0,1)):
        return False
    chunks=0
    while offset+12<=len(raw):
        chunks+=1
        if chunks>4096:
            return False
        length=int.from_bytes(raw[offset:offset+4],"big")
        kind=raw[offset+4:offset+8]
        end=offset+12+length
        if (end>len(raw) or not all(65<=c<=90 or 97<=c<=122 for c in kind) or
                not 65<=kind[2]<=90):
            return False
        if crc32(raw[offset+4:end-4]) & 0xffffffff != int.from_bytes(raw[end-4:end],"big"):
            return False
        if offset==8 and (kind!=b"IHDR" or length!=13):
            return False
        if offset!=8 and kind==b"IHDR":
            return False
        # PNG critical chunks are fixed; an unknown critical chunk or
        # interleaved IDAT sequence must never reach the private response.
        if kind[0] in range(65,91) and kind not in (b"IHDR",b"PLTE",b"IDAT",b"IEND"):
            return False
        # Reject ancillary text/EXIF chunks that can leak private metadata.
        # A valid CRC and SHA do not make embedded customer data safe.
        if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            return False
        if kind==b"PLTE":
            if (saw_plte or saw_idat or saw_trns or color_type in (0,4) or
                    length==0 or length>768 or length%3!=0 or
                    (color_type==3 and length//3>(1<<bit_depth))):
                return False
            saw_plte=True
            palette_entries=length//3
        if kind==b"tRNS":
            # Transparency must precede IDAT and be unique. Indexed
            # transparency must follow PLTE and fit its entry count.
            if (saw_trns or saw_idat or color_type not in (0,2,3) or
                    (color_type==0 and length!=2) or
                    (color_type==2 and length!=6) or
                    (color_type in (0,2) and length in (2,6) and
                     any(int.from_bytes(raw[offset+8+i:offset+10+i], "big") >= (1 << bit_depth)
                         for i in range(0, length, 2))) or
                    (color_type==3 and
                     (not saw_plte or length==0 or length>palette_entries))):
                return False
            saw_trns=True
        if kind==b"IDAT":
            if idat_closed:
                return False
            idat_bytes += length
            saw_idat=True
        elif saw_idat:
            idat_closed=True
        if kind==b"IEND":
            return (length==0 and saw_idat and idat_bytes>0 and end==len(raw) and
                    (color_type!=3 or saw_plte))
        offset=end
    return False
_KEYS=frozenset((
    "shop_id","job_id","media_asset_id","image_sha256","mime_type",
    "image_bytes","private","signed_url_issued","approved_model","publish_approved"
))


class Feature3PrivateBinaryHTTP:
    """Build private bytes and strict HTTP headers after successful JWT rights."""

    def __init__(self, *, reader):
        if not callable(getattr(reader,"read",None)):
            raise ValueError("Verified JWT/RLS output byte reader required")
        self.reader=reader

    @staticmethod
    def _deny(status):
        # Fixed opaque errors; never disclose existence or rights of a shop.
        return status,b"",{
            "Content-Type":"application/octet-stream",
            "Cache-Control":"no-store, private, max-age=0",
            "Pragma":"no-cache",
            "X-Content-Type-Options":"nosniff",
            "Content-Security-Policy":"default-src 'none'",
            "Vary":"Authorization",
        }

    def handle(self, *, method, authorization, shop_id, job_id):
        if method!="GET":
            status,body,headers=self._deny(405)
            return status,body,{**headers,"Allow":"GET"}
        if (type(authorization) is not str or
                not authorization.startswith("Bearer ") or
                not 12<=len(authorization)<=8200 or
                any(ord(c)<33 or ord(c)>126 for c in authorization[7:])):
            return self._deny(401)
        token=authorization[7:]
        if token.startswith(("sb_secret_","sb_publishable_")):
            return self._deny(401)
        try:
            shop=canonical_uuid(shop_id)
            job=canonical_uuid(job_id)
            receipt=self.reader.read(user_token=token,shop_id=shop,job_id=job)
        except (PrivateGeneratedDownloadDenied,ValueError,TypeError,KeyError):
            return self._deny(404)
        except Exception:
            # A temporarily unresponsive authoritative rights/source reader
            # is not evidence that an asset is missing or safe to serve.
            return self._deny(503)
        try:
            if (type(receipt) is not dict or set(receipt)!=_KEYS or
                    receipt.get("shop_id")!=shop or receipt.get("job_id")!=job or
                    receipt.get("mime_type")!="image/png" or
                    receipt.get("private") is not True or
                    receipt.get("signed_url_issued") is not False or
                    receipt.get("approved_model") is not False or
                    receipt.get("publish_approved") is not False):
                return self._deny(503)
            canonical_uuid(receipt.get("media_asset_id"))
            raw=receipt.get("image_bytes")
            digest=receipt.get("image_sha256")
            if (type(raw) is not bytes or not 100<=len(raw)<=_MAX or
                    not _valid_png_chunks(raw) or
                    type(digest) is not str or not _SHA.fullmatch(digest) or
                    sha256(raw).hexdigest()!=digest):
                return self._deny(503)
        except (ValueError,TypeError,KeyError):
            return self._deny(503)
        # The reader normally decodes pixels, but the HTTP adapter must also
        # fail closed if a future injected reader returns a forged CRC-valid
        # receipt containing corrupt or truncated compressed pixel data.
        try:
            with Image.open(BytesIO(raw)) as image:
                if (image.format != "PNG" or getattr(image, "n_frames", 1) != 1 or
                        image.width * image.height > 16_777_216):
                    return self._deny(503)
                image.load()
        except (OSError, ValueError, SyntaxError, EOFError, RuntimeError,
                UnidentifiedImageError, Image.DecompressionBombError):
            return self._deny(503)
        # Safe filename never uses an uploaded asset name or object path.
        return 200,raw,{
            "Content-Type":"image/png",
            "Content-Length":str(len(raw)),
            "X-Feature3-Shop-Id":shop,
            "X-Feature3-Job-Id":job,
            "X-Feature3-Media-Asset-Id":receipt["media_asset_id"],
            "X-Feature3-Image-Sha256":digest,
            "Content-Disposition":f'attachment; filename="feature3-{job}.png"',
            "Cache-Control":"no-store, private, max-age=0",
            "Pragma":"no-cache",
            "X-Content-Type-Options":"nosniff",
            "Content-Security-Policy":"default-src 'none'",
            "Vary":"Authorization",
        }
