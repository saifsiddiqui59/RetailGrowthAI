"""Private Feature3 approved garment reference -> Wan first-frame staging bridge.

No browser media grant, URL or storage access here. Caller supplies the real
Feature3 resolve_first_frame function and currently claim-fenced trusted readers.
A mocked reader is allowed ONLY inside CPU-only unit tests. The returned grant
does NOT authorize GPU inference or publication.

No destructive garment crop/stretch: explicit approved letterbox/scale to native
Wan2.2 portrait resolution, preserving aspect ratio, with immutable source and
prepared SHA256 plus reviewed Feature3 reference fingerprint.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .wan22_motion_adapter import WanCompatibilityError

F3_SCHEMA = "retailgrowth.fashion-reference-bundle.v1"
TARGET = (704, 1280)
MAX_INPUT = 25 * 1024 * 1024


@contextmanager
def stage_approved_fashion_first_frame(
    *, expected_manifest, current_readers, verify_worker_job,
    resolve_first_frame, private_job_dir, technical_letterbox_approved=False,
    require_model_wearing_garment=True,
):
    """Re-check Feature3 private bytes *after* verified claim and rights.

    The input is a server-authorized F3 manifest only, not data from the UI.
    Staged bytes are deleted even if Wan compilation or mocked inference fails.
    """
    if (type(expected_manifest) is not dict or
        expected_manifest.get("schema") != F3_SCHEMA or
        expected_manifest.get("purpose") != "image_to_video" or
        expected_manifest.get("output_approved") is not False or
        expected_manifest.get("gpu_authorized") is not False or
        type(current_readers) is not dict or
        not callable(verify_worker_job) or
        not callable(resolve_first_frame)):
        raise WanCompatibilityError("Feature3 current read-only bundle required")
    # A model-library photo next to a kurti photo is NOT a garment try-on.
    has_reviewed_worn_frame = (
        type(expected_manifest.get("model")) is dict and
        type(expected_manifest.get("try_on_review")) is dict and
        expected_manifest["try_on_review"].get("state") == "HUMAN_REVIEW_PASSED"
    )
    if require_model_wearing_garment and not has_reviewed_worn_frame:
        raise WanCompatibilityError("A wearer shot requires an independently reviewed actual try-on first frame")
    if technical_letterbox_approved is not True:
        raise WanCompatibilityError("Feature4 must approve explicit non-cropping native portrait preparation")
    # Actual Feature3 resolver independently revalidates JTW/RLS source, grants,
    # latest product/media/model reviews and raw private bytes and hash.
    source = resolve_first_frame(
        expected_manifest=expected_manifest,
        current_readers=current_readers,
        verify_worker_job=verify_worker_job,
    )
    frame=expected_manifest["sources"]["first_frame"]
    if (type(source) is not dict or
        source.get("shop_id") != expected_manifest.get("shop_id") or
        source.get("source_asset_id") != frame.get("source_asset_id") or
        source.get("sha256") != frame.get("sha256") or
        source.get("mime_type") != frame.get("mime_type") or
        source.get("dimensions") != frame.get("dimensions") or
        source.get("gpu_authorized") is not False):
        raise WanCompatibilityError("Feature3 first-frame changed since current approval")
    raw=source.get("image_bytes")
    if type(raw) is not bytes or not 100 <= len(raw) <= MAX_INPUT:
        raise WanCompatibilityError("Invalid private first-frame byte payload")
    original_sha=sha256(raw).hexdigest()
    if original_sha != frame["sha256"]:
        raise WanCompatibilityError("First-frame bytes do not match approved source")
    if source["mime_type"] not in ("image/png","image/jpeg","image/webp"):
        raise WanCompatibilityError("Unsupported current Feature3 image MIME")
    try:
        with Image.open(BytesIO(raw)) as im:
            if (getattr(im,"n_frames",1) != 1 or
                im.format != {"image/png":"PNG","image/jpeg":"JPEG","image/webp":"WEBP"}[source["mime_type"]] or
                [im.width,im.height] != source["dimensions"] or
                not 256 <= im.width <= 8192 or not 256 <= im.height <= 8192):
                raise WanCompatibilityError("Private image dimensions do not match decoded bytes")
            frame_rgb=im.convert("RGB")
            # Fit without cropping or changing subject proportions, pad around.
            frame_rgb.thumbnail(TARGET,Image.Resampling.LANCZOS)
            prepared=Image.new("RGB", TARGET, (24,24,24))
            xy=((TARGET[0]-frame_rgb.width)//2,(TARGET[1]-frame_rgb.height)//2)
            prepared.paste(frame_rgb,xy)
            result=BytesIO()
            prepared.save(result,format="PNG",optimize=True)
            prepared_bytes=result.getvalue()
    except (OSError,UnidentifiedImageError,Image.DecompressionBombError,ValueError) as exc:
        raise WanCompatibilityError("Unable to prepare authorized private first frame") from exc
    root=Path(private_job_dir)
    if root.is_symlink() or not root.is_dir():
        raise WanCompatibilityError("Missing non-symlink private leased work directory")
    if root.stat().st_mode & 0o077:
        raise WanCompatibilityError("Private worker directory must not grant group/other access")
    name="f3_"+original_sha[:24]+"_wan.png"
    target=root/name
    if target.exists() or target.is_symlink():
        raise WanCompatibilityError("Existing attempt first frame; do not overwrite or retry")
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    if hasattr(os,"O_NOFOLLOW"): flags|=os.O_NOFOLLOW
    made=False
    try:
        fd=os.open(target,flags,0o600);made=True
        with os.fdopen(fd,"wb") as stream:
            stream.write(prepared_bytes)
        grant={
            "asset_id":source["source_asset_id"],"shop_id":source["shop_id"],
            "mime_type":"image/png","staged_basename":name,
            "sha256":sha256(prepared_bytes).hexdigest(),
            "source_sha256":original_sha,
            "source_facts_sha256":expected_manifest["reference_fingerprint"],
            "width":TARGET[0],"height":TARGET[1],
            "approved":True,"private":True,"commercial_rights":True,
            "human_likeness_approved":has_reviewed_worn_frame,
        }
        yield target,grant,{
            "staging":"EXPLICIT_ASPECT_PRESERVING_LETTERBOX",
            "original_dimensions":source["dimensions"],
            "prepared_dimensions":list(TARGET),
            "image_content_cropped":False,
            "original_image_sha256":original_sha,
            "prepared_image_sha256":grant["sha256"],
            "garment_visual_fidelity_verified":False,
            "paid_gpu_approved":False,
        }
    finally:
        if made and target.is_file() and not target.is_symlink():
            target.unlink()


def resolve_feature3_materialized_first_frame(
    *, expected_manifest, current_readers, verify_worker_job,
    materialize_feature5_input,
):
    """Adapt Feature3's own trusted worker bytes API to existing F5 staging.

    Feature3 PR #604 owns materialize_feature5_input and its current private
    readers/lease checks. Never accept a browser-produced dict or treat image
    bytes as paid provider/marketing permission. Inject the actual Feature3
    function after coordinator integration, not a duplicate media resolver.
    """
    if (type(expected_manifest) is not dict or
        expected_manifest.get("schema") != F3_SCHEMA or
        expected_manifest.get("purpose") != "image_to_video" or
        expected_manifest.get("gpu_authorized") is not False or
        expected_manifest.get("output_approved") is not False or
        type(current_readers) is not dict or
        not callable(verify_worker_job) or
        not callable(materialize_feature5_input)):
        raise WanCompatibilityError("Trusted Feature3 worker input required")
    result=materialize_feature5_input(
        expected_manifest=expected_manifest,
        current_readers=current_readers,
        verify_motion_job=verify_worker_job,
    )
    exact={
        "consumer","shop_id","first_frame_asset_id",
        "reference_fingerprint","sha256","mime_type","dimensions",
        "image_bytes","provider_call_permitted","gpu_authorized",
        "publish_approved",
    }
    try:
        frame=expected_manifest["sources"]["first_frame"]
        valid=(type(result) is dict and set(result)==exact and
            result["consumer"]=="feature5" and
            result["shop_id"]==expected_manifest["shop_id"] and
            result["reference_fingerprint"]==expected_manifest["reference_fingerprint"] and
            result["first_frame_asset_id"]==frame["source_asset_id"] and
            result["sha256"]==frame["sha256"] and
            result["mime_type"]==frame["mime_type"] and
            result["dimensions"]==frame["dimensions"] and
            result["provider_call_permitted"] is False and
            result["gpu_authorized"] is False and
            result["publish_approved"] is False and
            type(result["image_bytes"]) is bytes and
            100<=len(result["image_bytes"])<=MAX_INPUT and
            sha256(result["image_bytes"]).hexdigest()==frame["sha256"])
    except (TypeError,KeyError,ValueError):
        valid=False
    if not valid:
        raise WanCompatibilityError(
            "Feature3 worker supplied stale, unauthorized or changed first frame")
    # This is the established F3 resolve_first_frame shape. The existing F5
    # stage_approved_fashion_first_frame still re-decodes, re-hashes,
    # letterboxes and deletes these private bytes on context exit.
    return {
        "shop_id":result["shop_id"],
        "source_asset_id":result["first_frame_asset_id"],
        "sha256":result["sha256"],
        "mime_type":result["mime_type"],
        "dimensions":result["dimensions"],
        "image_bytes":result["image_bytes"],
        "gpu_authorized":False,
    }


def resolve_feature3_worker_handoff_first_frame(
    *, expected_manifest, current_readers, verify_worker_job,
    resolve_private_worker_inputs,
):
    """Adapt the actual Feature3 whole-fashion private-worker handoff.

    The source-owned resolver independently rereads the reviewed garment,
    model and actual worn first-frame bytes under the current leased worker,
    then refreshes approval after those reads. Feature5 also checks each
    immutable role against its own signed manifest, not only the first frame.
    Neither this adapter nor the resolver grants GPU/provider/publish access.
    """
    if (type(expected_manifest) is not dict or
        expected_manifest.get("schema") != F3_SCHEMA or
        expected_manifest.get("purpose") != "image_to_video" or
        expected_manifest.get("gpu_authorized") is not False or
        expected_manifest.get("output_approved") is not False or
        type(current_readers) is not dict or
        not callable(verify_worker_job) or
        not callable(resolve_private_worker_inputs)):
        raise WanCompatibilityError("Current trusted Feature3 full worker handoff required")
    package = resolve_private_worker_inputs(
        expected_manifest=expected_manifest,
        current_readers=current_readers,
        verify_worker_job=verify_worker_job,
    )
    keys = {"schema", "shop_id", "purpose", "source_fingerprint",
            "garment_identity", "images", "rights_checked",
            "recheck_before_next_job", "output_approved", "gpu_authorized",
            "provider_call_permitted"}
    if (type(package) is not dict or set(package) != keys or
        package["schema"] != "retailgrowth.feature3-worker-private-inputs.v1" or
        package["shop_id"] != expected_manifest["shop_id"] or
        package["purpose"] != "image_to_video" or
        package["source_fingerprint"] != expected_manifest["reference_fingerprint"] or
        package["garment_identity"] != expected_manifest["garment"] or
        package["rights_checked"] is not True or
        package["recheck_before_next_job"] is not True or
        package["output_approved"] is not False or
        package["gpu_authorized"] is not False or
        package["provider_call_permitted"] is not False or
        type(package["images"]) is not dict or
        set(package["images"]) != {"garment", "model", "first_frame"}):
        raise WanCompatibilityError("Stale or unreviewed Feature3 worker fashion bundle")
    sources = expected_manifest.get("sources")
    if type(sources) is not dict or set(sources) != {"garment", "model", "first_frame"}:
        raise WanCompatibilityError("Missing independently reviewed garment/model/frame")
    for role in ("garment", "model", "first_frame"):
        item = package["images"][role]
        ref = sources[role]
        if (type(item) is not dict or type(ref) is not dict or
            set(item) != {"source_asset_id", "sha256", "mime_type",
                          "dimensions", "image_bytes"} or
            item["source_asset_id"] != ref["source_asset_id"] or
            item["sha256"] != ref["sha256"] or
            item["mime_type"] != ref["mime_type"] or
            item["dimensions"] != ref["dimensions"] or
            type(item["image_bytes"]) is not bytes or
            not 100 <= len(item["image_bytes"]) <= MAX_INPUT or
            sha256(item["image_bytes"]).hexdigest() != item["sha256"]):
            raise WanCompatibilityError(
                "Feature3 private " + role + " does not match reviewed original bytes")
    frame = package["images"]["first_frame"]
    return {
        "shop_id": package["shop_id"],
        "source_asset_id": frame["source_asset_id"],
        "sha256": frame["sha256"],
        "mime_type": frame["mime_type"],
        "dimensions": frame["dimensions"],
        "image_bytes": frame["image_bytes"],
        "gpu_authorized": False,
    }
