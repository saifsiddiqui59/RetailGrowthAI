"""GPU-OFF image composition for Feature5 production-input review only.

This composes an annotated first-frame REVIEW BOARD from independently
authorized Feature3 private pixels. It is NOT FLUX/AI image generation,
virtual try-on, Wan motion, a licence grant, or a customer advertisement.
No network, inference, subscriptions or paid provider calls.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import stat

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from .contracts import canonical_uuid
from .wan22_motion_adapter import WanCompatibilityError

GRANT_KEYS = frozenset({
    "asset_id", "shop_id", "mime_type", "staged_basename", "sha256",
    "source_sha256", "source_facts_sha256", "width", "height",
    "approved", "private", "commercial_rights", "human_likeness_approved",
})


def _regular_private(path):
    if path.is_symlink():
        raise WanCompatibilityError("Private CPU image must not be symlinked")
    try:
        info=path.stat(follow_symlinks=False)
    except OSError as exc:
        raise WanCompatibilityError("Missing private CPU image") from exc
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
        info.st_mode & 0o077 or not 0 < info.st_size <= 25*1024*1024):
        raise WanCompatibilityError("Unsafe private CPU source image")
    return info


def compose_review_first_frame(*, stage_png, grant, private_attempt_dir,
                               job_id, attempt_token, verify_existing_fenced_rights):
    """Create one private, explicitly non-AI review PNG; fail closed on revocation.

    verify_existing_fenced_rights must be a server-side existing DB and current
    Feature3 grant check (shop, job, attempt, asset, source SHA, prepared SHA).
    Synthetic test callbacks DO NOT authorize real merchant publication.
    """
    if (type(grant) is not dict or set(grant) != GRANT_KEYS or
        any(grant.get(k) is not True for k in
            ("approved","private","commercial_rights","human_likeness_approved")) or
        grant["mime_type"] != "image/png" or
        (grant["width"],grant["height"]) != (704,1280) or
        not callable(verify_existing_fenced_rights)):
        raise WanCompatibilityError("An active approved Feature3 private first frame is required")
    try:
        shop=canonical_uuid(grant["shop_id"])
        asset=canonical_uuid(grant["asset_id"])
        job=canonical_uuid(job_id)
        attempt=canonical_uuid(attempt_token)
    except (TypeError,ValueError,KeyError) as exc:
        raise WanCompatibilityError("Invalid CPU image tenant/job identity") from exc
    for key in ("sha256","source_sha256","source_facts_sha256"):
        value=grant[key]
        if type(value) is not str or len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
            raise WanCompatibilityError("Invalid approved Feature3 image digest")
    root=Path(private_attempt_dir)
    source=Path(stage_png)
    if (root.is_symlink() or not root.is_dir() or
        root.stat().st_mode & 0o077 or
        source.name != grant["staged_basename"] or
        source.parent.resolve(strict=True) != root.resolve(strict=True)):
        raise WanCompatibilityError("First frame must be inside dedicated private attempt directory")
    before=_regular_private(source)
    if verify_existing_fenced_rights(
        shop,job,attempt,asset,grant["source_sha256"],grant["sha256"]) is not True:
        raise WanCompatibilityError("Missing current tenant/job/Feature3 rights fence")
    with source.open("rb") as stream:
        raw=stream.read(25*1024*1024+1)
    if sha256(raw).hexdigest()!=grant["sha256"]:
        raise WanCompatibilityError("Current private first frame does not match approved bytes")
    try:
        with Image.open(BytesIO(raw)) as original:
            if (original.format != "PNG" or
                getattr(original,"n_frames",1)!=1 or original.size!=(704,1280)):
                raise WanCompatibilityError("Unexpected source frame format")
            canvas=original.convert("RGB")
            canvas.load()
    except (UnidentifiedImageError,Image.DecompressionBombError,OSError,ValueError) as exc:
        raise WanCompatibilityError("Approved Feature3 image is not decodable") from exc
    draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,0,704,92),fill=(22,26,39))
    draw.rectangle((0,1175,704,1280),fill=(22,26,39))
    font=ImageFont.load_default()
    draw.text((24,27),"CPU REVIEW BOARD | NO FLUX / NO WAN INFERENCE",
              font=font,fill=(255,244,215))
    draw.text((24,1205),"NOT A GENERATED FASHION IMAGE OR CUSTOMER AD",
              font=font,fill=(255,221,183))
    output=BytesIO()
    canvas.save(output,format="PNG",optimize=True)
    payload=output.getvalue()
    name="cpu_review_"+job+"_"+attempt+".png"
    destination=root/name
    if destination.exists() or destination.is_symlink():
        raise WanCompatibilityError("CPU preview exists; never overwrite previous attempt")
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    if hasattr(os,"O_NOFOLLOW"):
        flags|=os.O_NOFOLLOW
    created=False
    try:
        descriptor=os.open(destination,flags,0o600)
        created=True
        with os.fdopen(descriptor,"wb") as stream:
            stream.write(payload)
        after=_regular_private(source)
        if (before.st_dev!=after.st_dev or before.st_ino!=after.st_ino or
            before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns or
            sha256(source.read_bytes()).hexdigest()!=grant["sha256"]):
            raise WanCompatibilityError("Feature3 approved private bytes changed during composition")
        if verify_existing_fenced_rights(
            shop,job,attempt,asset,grant["source_sha256"],grant["sha256"]) is not True:
            raise WanCompatibilityError("Feature3 rights revoked during CPU image composition")
        return destination, {
            "schema":"feature5_cpu_review_board_v1",
            "shop_id":shop,"job_id":job,"attempt_token":attempt,
            "source_asset_id":asset,"source_sha256":grant["source_sha256"],
            "prepared_sha256":grant["sha256"],
            "review_png_sha256":sha256(payload).hexdigest(),
            "width":704,"height":1280,
            "generation_backend":"PIL_CPU_COMPOSITION",
            "flux_inference_executed":False,"wan_inference_executed":False,
            "virtual_tryon_proven":False,"model_likeness_approved_for_ad":False,
            "approved_for_feature4":False,
            "eligible_for_customer_ad":False,
            "status":"SYNTHETIC_OR_APPROVED_REFERENCE_REVIEW_ONLY",
        }
    except BaseException:
        if created and destination.is_file() and not destination.is_symlink():
            destination.unlink()
        raise
