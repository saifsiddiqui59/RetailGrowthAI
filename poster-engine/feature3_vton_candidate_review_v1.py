"""Feature3 virtual try-on offline output QA intake (not inference or approval).

Only accepts an independently attested, currently leased worker receipt
and actual private synthetic PNG bytes from trusted server callbacks. This
cannot claim visual fidelity: the next human must judge six garment features.
No GPU, FASHN, download URL, queue write, media commit or paid API.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from uuid import UUID
from PIL import Image, UnidentifiedImageError
from fashion_reference_v1 import FashionReferenceDenied, plan_virtual_try_on
from garment_review_v2 import FEATURES

_SHA = re.compile(r"[a-f0-9]{64}")
_EXPECTED = frozenset(("shop_id","provider_job_id","provider",
                       "source_fingerprint","model_asset_id","garment_asset_id",
                       "output_sha256","attempt","claim_token","output_png"))
_TRAITS = ("base_color","pattern","neckline","sleeves","length","embroidery")


def _uuid(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (ValueError, TypeError, AttributeError):
        return False


def intake_vton_candidate(*, approved_manifest, provider_response,
                          verify_current_private_worker):
    """Return private candidate metadata and NOT an approval or publish grant.

    verify_current_private_worker(shop, job, attempt, token, reference_sha,
                                  garment_id, model_id, output_sha) == True
    must consult current durable lease, independently licensed source rights,
    subscription, original image SHA and authorized private output bytes.
    """
    if (not isinstance(approved_manifest, dict)
        or approved_manifest.get("schema") != "retailgrowth.fashion-reference-bundle.v1"
        or approved_manifest.get("purpose") != "image_to_video"
        or approved_manifest.get("gpu_authorized") is not False
        or approved_manifest.get("output_approved") is not False
        or not isinstance(approved_manifest.get("model"), dict)
        or approved_manifest.get("try_on_review") is not None):
        raise FashionReferenceDenied("Current approved original and model references required")
    task = plan_virtual_try_on(manifest=approved_manifest)
    if (not isinstance(provider_response, dict) or set(provider_response) != _EXPECTED
        or not callable(verify_current_private_worker)):
        raise FashionReferenceDenied("Trusted one-shot VTON worker candidate required")
    shop, job, token = (provider_response.get(k) for k in
                         ("shop_id","provider_job_id","claim_token"))
    sources = approved_manifest.get("sources")
    if (not isinstance(sources, dict) or not isinstance(sources.get("garment"),dict)
        or not isinstance(sources.get("model"),dict)
        or not all(_uuid(v) for v in (shop,job,token))
        or shop != approved_manifest.get("shop_id")
        or provider_response.get("attempt") != 1
        or type(provider_response.get("attempt")) is not int
        or provider_response.get("provider") not in ("tryon-v1.6", "approved-vton-provider")
        or provider_response.get("source_fingerprint") != approved_manifest.get("reference_fingerprint")
        or provider_response.get("garment_asset_id") != task["garment_asset_id"]
        or provider_response.get("model_asset_id") != task["model_asset_id"]):
        raise FashionReferenceDenied("VTON provider claim/source not current or authorized")
    raw = provider_response.get("output_png")
    if type(raw) is not bytes or not 100 <= len(raw) <= 25*1024*1024:
        raise FashionReferenceDenied("No bounded private candidate image")
    try:
        with Image.open(BytesIO(raw)) as image:
            if (image.format!="PNG" or getattr(image,"n_frames",1)!=1 or
                not 256<=image.width<=8192 or not 256<=image.height<=8192 or
                image.width*image.height>24_000_000 or
                any(str(k).lower() in ("exif","xmp","xml:com.adobe.xmp") for k in image.info)):
                raise FashionReferenceDenied("Unsafe VTON generated candidate")
            image_size=(image.width,image.height)
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError) as exc:
        raise FashionReferenceDenied("Invalid VTON candidate image") from exc
    output_sha=sha256(raw).hexdigest()
    if not _SHA.fullmatch(provider_response.get("output_sha256", "")) or provider_response["output_sha256"] != output_sha:
        raise FashionReferenceDenied("Private generated VTON pixels changed")
    garment=approved_manifest.get("garment")
    if not isinstance(garment,dict) or any(
        type(garment.get(key)) is not str or not garment[key].strip() for key in _TRAITS):
        raise FashionReferenceDenied("Exact human-reviewed garment product required")
    if verify_current_private_worker(
       shop,job,1,token,approved_manifest["reference_fingerprint"],
       task["garment_asset_id"],task["model_asset_id"],output_sha) is not True:
        raise FashionReferenceDenied("No independently authorized leased VTON output")
    return {
        "schema":"retailgrowth.feature3-vton-candidate-review.v1",
        "shop_id":shop,"provider_job_id":job,
        "model_asset_id":task["model_asset_id"],
        "garment_asset_id":task["garment_asset_id"],
        "reference_fingerprint":approved_manifest["reference_fingerprint"],
        "output_sha256":output_sha,"dimensions":list(image_size),
        "status":"CANDIDATE_UNREVIEWED","generated_output_registered":False,
        "human_fidelity_checklist":[{"feature":name,"expected":garment[key]}
          for name,key in zip(FEATURES,_TRAITS)],
        "requires_two_independent_decisions":False,
        "publish_approved":False,"licensed_for_marketing":False,
        "provider_call_permitted":False,"gpu_authorized":False,
        "visual_fidelity_verified":False,
    }
