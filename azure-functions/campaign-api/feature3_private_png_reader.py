"""Private Feature3 generated PNG reader; never issue a signed Storage URL.

Backend-only building block for a future reviewed streamed download handler.
Requires a verified Supabase user JWT, actual JWT/RLS tenant reads, and an
independently trusted live generated-output rights/release authorization.
Re-checks access after the private binary read, so a revoked user/model does
not get a new download from this request. Does not revoke PREVIOUSLY ISSUED
60-second signed URLs or guarantee a race-free DB read transaction.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from PIL import Image, UnidentifiedImageError

from tenant_store import StorageUnavailable, canonical_uuid

_SHA = re.compile(r"^[a-f0-9]{64}$")
# Match the *whole* canonical origin. urlsplit() can silently strip C0
# whitespace and embedded CR/LF/TAB before validation.
_SUPABASE_ORIGIN = re.compile(
    r"https://[a-z0-9][a-z0-9-]{0,62}\.supabase\.co(?::443)?/?")
_PUBLISHABLE_KEY = re.compile(r"sb_publishable_[A-Za-z0-9_-]{6,4090}")
_MAX = 25 * 1024 * 1024


class PrivateGeneratedDownloadDenied(PermissionError):
    """Do not reveal existence, revoked rights or the private Storage path."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class Feature3RevocablePNGReader:
    def __init__(self, *, tenant_store, verify_user_jwt, current_output_rights,
                 transport=None):
        if (not callable(verify_user_jwt) or
                not callable(current_output_rights) or
                not all(callable(getattr(tenant_store, name, None)) for name in (
                    "member", "feature3_gpu_job", "feature3_generated_asset"))):
            raise ValueError("Signed JWT, tenant store and live output rights required")
        origin = getattr(tenant_store, "origin", None)
        if (type(origin) is not str or
                _SUPABASE_ORIGIN.fullmatch(origin) is None):
            raise ValueError("Exact private Supabase HTTPS project origin required")
        public_key = getattr(tenant_store, "key", None)
        # A service_role JWT API key or arbitrary key must not be supplied
        # as an authenticated user's private Storage apikey.
        if (type(public_key) is not str or
                _PUBLISHABLE_KEY.fullmatch(public_key) is None):
            raise ValueError("User JWT private reader requires public client key")
        self.tenant = tenant_store
        self.verify = verify_user_jwt
        self.rights = current_output_rights
        self.origin = origin.rstrip("/")
        self.key = public_key
        self.transport = transport or build_opener(_NoRedirect()).open

    def _current(self, token, actor, shop, job):
        # All reads go through the *actual* user's JWT and existing RLS, not
        # a service role key. This is deliberately performed twice.
        # Treat a broken current JWT/RLS adapter as denial, not a private
        # image authorization or a raw backend exception in an HTTP response.
        try:
            member = self.tenant.member(token, actor, shop)
        except (StorageUnavailable, OSError):
            # A transport/RLS outage is opaque 503 at the HTTP adapter,
            # not a false 404 for a known-missing private asset.
            raise
        except Exception:
            raise PrivateGeneratedDownloadDenied(
                "Private generated output unavailable") from None
        if member is not True:
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        try:
            row = self.tenant.feature3_gpu_job(token, shop, job)
        except (StorageUnavailable, OSError):
            # A transport/RLS outage is opaque 503 at the HTTP adapter,
            # not a false 404 for a known-missing private asset.
            raise
        except Exception:
            raise PrivateGeneratedDownloadDenied(
                "Private generated output unavailable") from None
        # Injected tenant adapters must not impersonate identities via __eq__.
        if (type(row) is not dict or
                type(row.get("id")) is not str or row["id"] != job or
                type(row.get("shop_id")) is not str or row["shop_id"] != shop or
                type(row.get("status")) is not str or row["status"] != "SUCCEEDED"):
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        asset_id = canonical_uuid(row.get("output_asset_id"))
        try:
            asset = self.tenant.feature3_generated_asset(
                token, shop, job, asset_id)
        except (StorageUnavailable, OSError):
            # A transport/RLS outage is opaque 503 at the HTTP adapter,
            # not a false 404 for a known-missing private asset.
            raise
        except Exception:
            raise PrivateGeneratedDownloadDenied(
                "Private generated output unavailable") from None
        key = asset.get("object_path") if isinstance(asset, dict) else None
        prefix = f"{shop}/feature3/gpu/{job}/"
        # The TenantStore currently validates these fields, but this is
        # also a trust boundary for any future injected store adapter.
        # A path alone cannot prove that the registered row belongs to this
        # generated output rather than an uploaded/foreign media asset.
        if (type(asset) is not dict or type(key) is not str or
                type(asset.get("id")) is not str or asset["id"] != asset_id or
                type(asset.get("shop_id")) is not str or asset["shop_id"] != shop or
                type(asset.get("storage_bucket")) is not str or
                asset["storage_bucket"] != "retailgrowth-media" or
                type(asset.get("source")) is not str or
                asset["source"] != "GENERATED" or
                not key.startswith(prefix) or
                not key.endswith(".png") or
                not _SHA.fullmatch(key[len(prefix):-4]) or
                type(asset.get("mime_type")) is not str or
                asset["mime_type"] != "image/png"):
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        # Must be a real backend check of original source rights/approval
        # and immutable output evidence, NOT a caller-created True from UI.
        try:
            current_rights = self.rights(shop, job, asset_id)
        except (StorageUnavailable, OSError):
            # A genuine backend transport failure must remain an opaque 503,
            # never be confused with a deliberate rights denial (404).
            raise
        except Exception:
            # A reviewer outage cannot fall back to the Storage key, JWT
            # membership or a historical rights approval.
            raise PrivateGeneratedDownloadDenied(
                "Private generated output unavailable") from None
        if current_rights is not True:
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        return asset_id, key, key[len(prefix):-4]

    def _read(self, key, token):
        url = (self.origin +
               "/storage/v1/object/authenticated/retailgrowth-media/" +
               quote(key, safe="/"))
        request = Request(url, method="GET",
                          headers={"apikey":self.key,
                                   "Authorization":"Bearer "+token,
                                   "Accept":"image/png",
                                   "Cache-Control":"no-store"})
        try:
            with self.transport(request, timeout=10) as response:
                # Malformed HTTP/gateway response is never a private grant.
                if (not callable(getattr(response, "geturl", None)) or
                        not callable(getattr(response, "getcode", None)) or
                        not callable(getattr(response, "read", None)) or
                        response.geturl() != url or response.getcode() != 200):
                    raise PrivateGeneratedDownloadDenied(
                        "Unconfirmed authenticated private image")
                headers = getattr(response, "headers", None)
                if not callable(getattr(headers, "get", None)):
                    raise PrivateGeneratedDownloadDenied(
                        "Unconfirmed authenticated private image")
                length = headers.get("Content-Length")
                mime = headers.get("Content-Type")
                content_encoding = headers.get("Content-Encoding")
                # A private immutable object is always a complete 200 response.
                # Reject proxy-supplied partial-content metadata before body IO.
                if headers.get("Content-Range") is not None:
                    raise PrivateGeneratedDownloadDenied(
                        "Untrusted partial private PNG response")
                # No intermediary is allowed to transform an immutable
                # SHA-named private object. Ambiguous transfer framing can
                # conceal extra bytes or disagree with Content-Length.
                transfer_encoding = headers.get("Transfer-Encoding")
                if transfer_encoding is not None:
                    if (type(transfer_encoding) is not str or
                            transfer_encoding.strip().lower() != "chunked" or
                            headers.get("Content-Length") is not None):
                        raise PrivateGeneratedDownloadDenied(
                            "Untrusted private PNG transfer framing")
                # Refuse folded, invisible or unbounded HTTP metadata before
                # any authenticated private PNG body is consumed.
                def printable_header(value):
                    return (type(value) is str and 1 <= len(value) <= 256 and
                            all(32 <= ord(ch) <= 126 for ch in value))
                if content_encoding is not None and (
                        not printable_header(content_encoding) or
                        content_encoding.strip().lower() != "identity"):
                    raise PrivateGeneratedDownloadDenied(
                        "Untrusted encoded private PNG response")
                if (length is not None and
                        (type(length) is not str or not 1 <= len(length) <= 8 or
                         not length.isascii() or
                         not length.isdigit() or int(length) > _MAX)):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private image Content-Length")
                if (not printable_header(mime) or
                        mime.strip().lower() != "image/png"):
                    raise PrivateGeneratedDownloadDenied("Invalid private image MIME")
                raw = response.read(_MAX + 1)
        except PrivateGeneratedDownloadDenied:
            raise
        except Exception:
            # Never leak raw HTTP/Storage credentials or adapter diagnostics.
            raise PrivateGeneratedDownloadDenied(
                "Authenticated private media request unavailable") from None
        if type(raw) is not bytes or not 100 <= len(raw) <= _MAX:
            raise PrivateGeneratedDownloadDenied("Untrusted private image bytes")
        # A syntactically plausible but incorrect response length is not an
        # original-byte attestation even if Pillow can decode the payload.
        # Missing Content-Length is allowed for chunked private transport;
        # the immutable SHA-named key is independently checked by read().
        if length is not None and int(length)!=len(raw):
            raise PrivateGeneratedDownloadDenied(
                "Private image response length changed")
        # Reject bytes appended after PNG IEND, including hidden payloads.
        # Pillow may successfully decode a PNG while silently ignoring such
        # trailing data; the private output contract is exactly one PNG.
        offset = 8
        if not raw.startswith(bytes.fromhex("89504e470d0a1a0a")):
            raise PrivateGeneratedDownloadDenied("Untrusted private PNG structure")
        seen_header = False
        seen_pixels = False
        seen_palette = False
        seen_transparency = False
        png_color_type = None
        palette_entries = None
        transparency_entries = None
        pixels_finished = False
        # Bound parser work independently of the 25 MiB byte limit: a PNG
        # can contain millions of tiny ancillary chunks with valid CRCs.
        # A generated poster needs nowhere near this many chunks.
        chunk_count = 0
        while offset + 12 <= len(raw):
            chunk_count += 1
            if chunk_count > 4096:
                raise PrivateGeneratedDownloadDenied(
                    "Excessive private PNG chunk count")
            chunk_size = int.from_bytes(raw[offset:offset + 4], "big")
            chunk_type = raw[offset + 4:offset + 8]
            end = offset + 12 + chunk_size
            if end > len(raw):
                raise PrivateGeneratedDownloadDenied("Untrusted private PNG structure")
            # A valid single-image PNG starts with exactly one 13-byte IHDR
            # and contains IDAT before its final zero-length IEND. Enforce
            # this before handing potentially hostile bytes to Pillow.
            if not seen_header:
                if chunk_type != b"IHDR" or chunk_size != 13:
                    raise PrivateGeneratedDownloadDenied("Missing private PNG header")
                seen_header = True
                # IHDR data starts after the 4-byte length and 4-byte type.
                # Its color-type byte is data[9], i.e. chunk offset + 17.
                png_color_type = raw[offset + 17]
                # Reject impossible PNG IHDR bit-depth/color combinations
                # before any palette or transparency metadata is interpreted.
                bit_depth = raw[offset + 16]
                allowed_depths = {
                    0: (1, 2, 4, 8, 16),
                    2: (8, 16),
                    3: (1, 2, 4, 8),
                    4: (8, 16),
                    6: (8, 16),
                }
                if bit_depth not in allowed_depths.get(png_color_type, ()):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private PNG IHDR color/bit depth")
                # PNG compression and filter methods must be zero. Interlace
                # may only be the standard noninterlaced or Adam7 mode.
                # Validate these bytes before decoding or serving the image.
                if (raw[offset + 18] != 0 or raw[offset + 19] != 0 or
                        raw[offset + 20] not in (0, 1)):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private PNG IHDR encoding methods")
            elif chunk_type == b"IHDR":
                raise PrivateGeneratedDownloadDenied("Duplicate private PNG header")
            # Unknown critical chunks cannot be safely interpreted by the
            # consumer. PNG IDAT chunks must be contiguous; otherwise a
            # decoder may silently ignore ambiguous or hidden pixel data.
            if (chunk_type[0] & 0x20) == 0 and chunk_type not in (
                    b"IHDR", b"PLTE", b"IDAT", b"IEND"):
                raise PrivateGeneratedDownloadDenied(
                    "Untrusted private PNG critical chunk")
            # PNG chunk names are exactly four ASCII letters. The third
            # letter is reserved and must be uppercase; reject ambiguous
            # or future-incompatible names before Pillow parses the bytes.
            if (len(chunk_type) != 4 or
                    any(not (65 <= c <= 90 or 97 <= c <= 122)
                        for c in chunk_type) or
                    not 65 <= chunk_type[2] <= 90):
                raise PrivateGeneratedDownloadDenied(
                    "Untrusted private PNG chunk name")
            # APNG control/frame chunks are not valid for a single immutable
            # generated poster. Pillow can report one frame for an animated
            # container with only one declared frame; reject the container
            # semantics explicitly, including SHA-matched synthetic payloads.
            if chunk_type in (b"acTL", b"fcTL", b"fdAT"):
                raise PrivateGeneratedDownloadDenied(
                    "Animated private PNG container not permitted")
            # Generated private posters are pixel-only artifacts. PNG textual
            # and EXIF chunks can carry hidden customer data, external links,
            # or unreviewed rights claims even when pixels and SHA match.
            # Refuse these chunks instead of trusting Pillow's info mapping.
            # ICC profiles, suggested palettes and calibration chunks may
            # also contain opaque user-controlled metadata; generated PNGs
            # do not need these to deliver verified pixels.
            if chunk_type in (b"tEXt", b"zTXt", b"iTXt", b"eXIf",
                              b"iCCP", b"sPLT", b"pCAL", b"sCAL"):
                raise PrivateGeneratedDownloadDenied(
                    "Private PNG embedded metadata not permitted")
            # Palette entries are RGB triples (1..256 entries). A malformed
            # PLTE can be ignored by some decoders yet accepted as a PNG.
            # Transparency metadata must precede the first pixel chunk.
            if chunk_type == b"PLTE" and (chunk_size == 0 or
                    chunk_size > 768 or chunk_size % 3 != 0):
                raise PrivateGeneratedDownloadDenied(
                    "Invalid private PNG palette size")
            # Grayscale PNGs cannot carry PLTE. Indexed palette entries
            # must fit the IHDR bit depth, even when unused by pixel data.
            if chunk_type == b"PLTE":
                bit_depth = raw[24]
                if (png_color_type in (0, 4) or
                        (png_color_type == 3 and
                         chunk_size // 3 > (1 << bit_depth))):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private PNG palette for color type")
            if chunk_type == b"tRNS":
                # Transparency must match IHDR color type; indexed alpha
                # requires a preceding palette and cannot exceed its entries.
                if (png_color_type not in (0, 2, 3) or
                        (png_color_type == 0 and chunk_size != 2) or
                        (png_color_type == 2 and chunk_size != 6) or
                        (png_color_type == 3 and (
                            palette_entries is None or
                            not 1 <= chunk_size <= palette_entries))):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private PNG transparency payload")
                if seen_pixels or seen_transparency:
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private PNG transparency order")
                seen_transparency = True
                transparency_entries = chunk_size
            if chunk_type == b"PLTE":
                if seen_palette or seen_pixels:
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private PNG palette order")
                seen_palette = True
                palette_entries = chunk_size // 3
            # Revalidate indexed metadata at the pixel boundary, including
            # a palette that must exist and a transparency table that must
            # never exceed the palette size.
            if chunk_type == b"IDAT" and png_color_type == 3:
                if (not seen_palette or palette_entries is None or
                        (seen_transparency and transparency_entries >
                         palette_entries)):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid indexed private PNG metadata")
            if chunk_type == b"IDAT":
                if pixels_finished:
                    raise PrivateGeneratedDownloadDenied(
                        "Noncontiguous private PNG pixels")
                seen_pixels = True
            elif seen_pixels:
                pixels_finished = True
            if chunk_type == b"IEND":
                if not seen_pixels or chunk_size != 0:
                    raise PrivateGeneratedDownloadDenied("Untrusted private PNG terminator")
                if end != len(raw):
                    raise PrivateGeneratedDownloadDenied("Untrusted trailing PNG bytes")
                break
            offset = end
        else:
            raise PrivateGeneratedDownloadDenied("Missing private PNG terminator")
        try:
            with Image.open(BytesIO(raw)) as img:
                if (img.format != "PNG" or getattr(img,"n_frames",1) != 1 or
                        not 256 <= img.width <= 8192 or
                        not 256 <= img.height <= 8192 or
                        img.width*img.height > 24_000_000 or
                        any(k.lower() in ("exif","xmp","xml:com.adobe.xmp")
                            for k in img.info)):
                    raise PrivateGeneratedDownloadDenied("Untrusted private PNG format")
                img.verify()
            # PNG.verify() checks container/chunk CRCs, but does not decode
            # compressed IDAT pixels. A CRC-repaired corrupt zlib stream can
            # pass verify() and the immutable SHA while failing at display.
            # Require a full decode before returning any private image bytes.
            with Image.open(BytesIO(raw)) as decoded:
                if decoded.format != "PNG":
                    raise PrivateGeneratedDownloadDenied("Untrusted private PNG format")
                decoded.load()
        except (OSError, ValueError, UnidentifiedImageError, SyntaxError,
                EOFError, RuntimeError, Image.DecompressionBombError) as exc:
            raise PrivateGeneratedDownloadDenied("Untrusted private PNG pixels") from exc
        return raw

    def _verified_actor(self, token):
        # JWT expiration, revocation and actor identity are checked at BOTH
        # ends of a private byte read. Never expose verifier error details.
        try:
            return canonical_uuid(self.verify(token))
        except Exception:
            raise PrivateGeneratedDownloadDenied(
                "Authenticated private output unavailable") from None

    def read(self, *, user_token, shop_id, job_id):
        """Return private binary *in process*; no public or signed URLs.

        The trusted HTTP handler must independently verify the current JWT
        and must not cache or log returned bytes, object keys or credentials.
        Neither a successful read nor an output receipt grants publication.
        """
        if (not isinstance(user_token,str) or not 12 <= len(user_token) <= 8192 or
                any(not 33 <= ord(ch) <= 126 for ch in user_token) or
                user_token.startswith(("sb_secret_","sb_publishable_"))):
            raise PrivateGeneratedDownloadDenied("Signed retailer token required")
        try:
            shop,job=canonical_uuid(shop_id),canonical_uuid(job_id)
            actor=self._verified_actor(user_token)
            asset_id,key,digest=self._current(user_token,actor,shop,job)
            image=self._read(key,user_token)
            if sha256(image).hexdigest()!=digest:
                raise PrivateGeneratedDownloadDenied("Private output checksum mismatch")
            # Re-authorize AFTER fetching bytes, immediately before returning.
            # Reject changed job identity, rights revision, current membership,
            # object path, or revoked output source (via trusted callback).
            after_id,after_key,after_digest=self._current(user_token,actor,shop,job)
            if (after_id,after_key,after_digest)!=(asset_id,key,digest):
                raise PrivateGeneratedDownloadDenied("Private output changed during read")
            # Even a matching RLS/media snapshot cannot authorize an expired
            # JWT or a replaced actor by the time the final bytes are served.
            if self._verified_actor(user_token)!=actor:
                raise PrivateGeneratedDownloadDenied(
                    "Authenticated private output unavailable")
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise PrivateGeneratedDownloadDenied(
                "Authenticated private output unavailable") from exc
        return {"shop_id":shop,"job_id":job,"media_asset_id":asset_id,
                "image_sha256":digest,"mime_type":"image/png",
                "image_bytes":image,"private":True,
                "signed_url_issued":False,"approved_model":False,
                "publish_approved":False}
