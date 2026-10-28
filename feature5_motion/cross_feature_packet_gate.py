"""Read-only Feature3/F4/Part3 contract gateway for native Wan2.2, GPU OFF.

The shape is grounded in Feature3 PR #561's actual consumer_packets_v1
and the Feature4 PR #322 / Part3 PR #125 provider names. It rejects the
legacy Hunyuan/Wan2.7 profiles rather than misrouting costly inference.
No provider POST, paid job, approval, Storage write or browser entitlement.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from hashlib import sha256
import json
import re

from .contracts import canonical_uuid
from .feature3_reference_bridge import stage_approved_fashion_first_frame
from .wan22_motion_adapter import WanCompatibilityError, PROVIDER

SHA = re.compile(r"^[0-9a-f]{64}$")
SHOT_CAMERAS = {"static","slow_push_in","pan_left","pan_right","background_orbit"}
BUNDLE_KEYS = {
    "schema","shop_id","brief_id","source","feature2","feature4","feature5",
    "feature7","mock_orchestration_only","gpu_authorized",
    "paid_inference_authorized","publish_approved",
}
F3_KEYS = {
    "reference_fingerprint","first_frame_asset_id","first_frame_sha256",
    "lease_claim_required","fresh_rights_check_required",
    "cost_reservation_required","provider_call_permitted",
}
F4_KEYS = {"reference_fingerprint","timeline","output_requires_human_review"}
F2_KEYS = {"reference_fingerprint","approved_brief_revision","shots","duration_seconds"}
SOURCE_KEYS = {
    "shop_id","garment_asset_id","garment_sha256","model_asset_id",
    "model_id","model_sha256","model_pose","first_frame_asset_id",
    "first_frame_sha256","model_rights_revision",
    "garment_rights_revision","garment_approval_revision",
    "garment","preservation",
}
SUPPORTED = {
    "provider":PROVIDER, "model_id":"wan2.2-ti2v-5b",
    "width":704, "height":1280, "frames":121, "fps":24,
    "duration_seconds":5,
}
OLD_PROFILES = {"hunyuanvideo-1.5-480p", "wan2.7-i2v-2026-04-25",
                "wan2.7-t2v-2026-06-12"}


def _sha(v):
    return type(v) is str and SHA.fullmatch(v) is not None


def _id(v):
    try:
        return canonical_uuid(v)
    except (TypeError, ValueError):
        raise WanCompatibilityError("Noncanonical cross-feature identity") from None


def _json_digest(value):
    try:
        encoded=json.dumps(value,sort_keys=True,separators=(",",":"),
                           allow_nan=False).encode()
    except (TypeError,ValueError) as exc:
        raise WanCompatibilityError("Unserializable cross-feature packet") from exc
    if len(encoded)>28_000:
        raise WanCompatibilityError("Oversized cross-feature packet")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class NativeInputPacket:
    shop_id: str
    brief_id: str
    source_asset_id: str
    reference_fingerprint: str
    garment_sha256: str
    approved_shots: int
    duration_seconds: int
    input_packet_sha256: str
    status: str = "FRESH_SOURCE_PACKET_ONLY_NO_GPU_ENTITLEMENT"
    can_submit_provider: bool = False
    can_publish: bool = False


def qualify_feature3_packet(*, expected_packet, read_current_packet):
    """Match genuine Feature3 #561 source metadata against current server read.

    The injected reader MUST reassemble the packet from current signed/RLS
    fashion reference, rights, garment, reviewer and approved brief DB rows.
    Neither the packet nor this return value authorizes provider/Storage use.
    Feature5 must independently call Feature3 resolve_first_frame after its
    active durable Part3 claim before paid inference.
    """
    if type(expected_packet) is not dict or not callable(read_current_packet):
        raise WanCompatibilityError("Feature3 trusted packet reader required")
    if set(expected_packet)!=BUNDLE_KEYS or (
        expected_packet["schema"]!="retailgrowth.feature3-offline-consumer-packets.v1"
        or expected_packet["mock_orchestration_only"] is not True
        or any(expected_packet[k] is not False for k in
               ("gpu_authorized","paid_inference_authorized","publish_approved"))):
        raise WanCompatibilityError("Unrecognized Feature3 GPU-OFF packet")
    shop=_id(expected_packet["shop_id"])
    brief=_id(expected_packet["brief_id"])
    original_hash=_json_digest(expected_packet)
    try:
        fresh=read_current_packet(shop,brief)
    except Exception as exc:
        raise WanCompatibilityError("Feature3 private packet refresh unavailable") from exc
    if (type(fresh) is not dict or
        _json_digest(fresh)!=original_hash or fresh!=expected_packet):
        raise WanCompatibilityError("Stale/revoked Feature3 packet")
    src=expected_packet["source"]
    f2=expected_packet["feature2"]
    f4=expected_packet["feature4"]
    f5=expected_packet["feature5"]
    f7=expected_packet["feature7"]
    if (any(type(v) is not dict for v in (src,f2,f4,f5,f7)) or
        set(src)!=SOURCE_KEYS or set(f2)!=F2_KEYS or
        set(f4)!=F4_KEYS or set(f5)!=F3_KEYS or
        set(f7)!={"optional_approved_upload",
                 "editor_requires_fresh_media_rights","publish_approved"}):
        raise WanCompatibilityError("Incompatible Feature3 consumer packet contract")
    if (src["shop_id"]!=shop or
        not all(_id(src[k]) for k in
                ("garment_asset_id","model_asset_id","model_id","first_frame_asset_id")) or
        not all(_sha(src[k]) for k in
                ("garment_sha256","model_sha256","first_frame_sha256")) or
        f5["first_frame_asset_id"]!=src["first_frame_asset_id"] or
        f5["first_frame_sha256"]!=src["first_frame_sha256"] or
        not all(_sha(d["reference_fingerprint"]) for d in (f2,f4,f5)) or
        f5["provider_call_permitted"] is not False or
        not all(f5[k] is True for k in
                ("lease_claim_required","fresh_rights_check_required",
                 "cost_reservation_required")) or
        f4["output_requires_human_review"] is not True or
        f7["editor_requires_fresh_media_rights"] is not True or
        f7["publish_approved"] is not False):
        raise WanCompatibilityError("Feature3 references or disabled gates invalid")
    if (type(f2["approved_brief_revision"]) is not int or
        f2["approved_brief_revision"]<1 or
        f2["duration_seconds"] not in (15,30,60) or
        type(f2["duration_seconds"]) is not int or
        type(f2["shots"]) is not list or
        type(f4["timeline"]) is not list or
        len(f4["timeline"])!=len(f2["shots"]) or
        not 1<=len(f2["shots"])<=12):
        raise WanCompatibilityError("Invalid cross-feature shot lengths")
    offset=0
    for shot,timeline in zip(f2["shots"],f4["timeline"]):
        if type(shot) is not dict or type(timeline) is not dict:
            raise WanCompatibilityError("Malformed approved shot")
        if (set(shot)!={"start_second","duration_seconds","camera","scene",
                       "overlay","preserve_garment_identity"} or
            set(timeline)!=set(shot)|{"first_frame_asset_id"} or
            timeline["first_frame_asset_id"]!=src["first_frame_asset_id"] or
            any(timeline[k]!=shot[k] for k in shot) or
            shot["start_second"]!=offset or
            type(shot["duration_seconds"]) is not int or
            not 1<=shot["duration_seconds"]<=15 or
            shot["camera"] not in SHOT_CAMERAS or
            shot["preserve_garment_identity"] is not True):
            raise WanCompatibilityError("Feature4 timeline drift from approved Feature2 shots")
        offset+=shot["duration_seconds"]
    if offset!=f2["duration_seconds"]:
        raise WanCompatibilityError("Unapproved brief duration drift")
    return NativeInputPacket(shop,brief,src["first_frame_asset_id"],
                             f5["reference_fingerprint"],src["garment_sha256"],
                             len(f2["shots"]),offset,original_hash)


def check_coordinator_motion_profile(raw):
    """Never silently convert Part3 Wan2.7 or Feature4 Hunyuan to Wan2.2.

    Requires explicit provider/model/cost/schema reconciliation by coordinator,
    not merely an approved camera/shot or a model string from a client.
    """
    if type(raw) is not dict or set(raw)!=set(SUPPORTED):
        raise WanCompatibilityError("Provider schema must be versioned and exact")
    if raw != SUPPORTED:
        raise WanCompatibilityError("Part3/Feature4 model profile mismatch: no implicit paid conversion")
    return "NATIVE_PROFILE_MATCH_ONLY_NOT_AUTHORIZED_TO_RUN"


@contextmanager
def stage_fresh_feature3_consumer_input(
    *, expected_packet, read_current_packet, expected_fashion_manifest,
    current_fashion_readers, verify_worker_job, resolve_first_frame,
    private_job_dir, technical_letterbox_approved=False,
):
    """Real F3 packet -> separately reverified private first frame, GPU OFF.

    Require current independently fetched Feature3 #561 consumer metadata,
    matching original fashion manifest and original byte SHA, while passing
    the existing real Feature3 trusted resolver. Refresh packet again AFTER
    staging to catch a revoked model/garment approval during CPU preparation.
    No launch, upload, credits or production permissions.
    """
    proof=qualify_feature3_packet(
        expected_packet=expected_packet,
        read_current_packet=read_current_packet)
    manifest=expected_fashion_manifest
    if (type(manifest) is not dict or
        manifest.get("schema")!="retailgrowth.fashion-reference-bundle.v1" or
        manifest.get("purpose")!="image_to_video" or
        manifest.get("shop_id")!=proof.shop_id or
        manifest.get("reference_fingerprint")!=proof.reference_fingerprint):
        raise WanCompatibilityError("Approved fashion first-frame lineage not current")
    try:
        sources=manifest["sources"]
        source=expected_packet["source"]
        matched=(
            sources["first_frame"]["source_asset_id"]==proof.source_asset_id and
            sources["first_frame"]["sha256"]==source["first_frame_sha256"] and
            sources["garment"]["source_asset_id"]==source["garment_asset_id"] and
            sources["model"]["source_asset_id"]==source["model_asset_id"])
    except (KeyError,TypeError):
        matched=False
    if not matched:
        raise WanCompatibilityError("Feature3 original garment/model/try-on changed")
    with stage_approved_fashion_first_frame(
        expected_manifest=manifest,
        current_readers=current_fashion_readers,
        verify_worker_job=verify_worker_job,
        resolve_first_frame=resolve_first_frame,
        private_job_dir=private_job_dir,
        technical_letterbox_approved=technical_letterbox_approved,
        require_model_wearing_garment=True,
    ) as (file,grant,technical):
        if (grant["shop_id"]!=proof.shop_id or
            grant["asset_id"]!=proof.source_asset_id or
            grant["source_sha256"]!=source["first_frame_sha256"] or
            grant["source_facts_sha256"]!=proof.reference_fingerprint or
            grant["private"] is not True):
            raise WanCompatibilityError("Private first frame not from pinned packet")
        again=qualify_feature3_packet(
            expected_packet=expected_packet,
            read_current_packet=read_current_packet)
        if again!=proof:
            raise WanCompatibilityError("Feature3 approval changed during staging")
        yield file,grant,technical,proof
