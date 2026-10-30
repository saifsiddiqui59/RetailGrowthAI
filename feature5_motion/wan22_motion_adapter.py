"""Wan2.2 native provider-profile adapter for Feature2 briefs routed by Feature4.

Source: Wan-Video/Wan2.2@1ea34ff48f87168174e12956e200b1d908b1c5ff
  wan/configs/__init__.py: TI2V 5B sizes 704x1280 and 1280x704
  wan/configs/wan_ti2v_5B.py: 121 frames, 24 fps
  generate.py + wan/utils/prompt_extend.py: shared TI2V task, optional I2V image
This adapts official task/sizing/prompt-mode selection to the EXISTING
ComfyUI native graph constructors; no alternate renderer or GPU launch.
Copyright 2024-2025 Alibaba Wan Team Authors; Apache-2.0 upstream.
No upstream policy rewriter, model download, LLM or HTTP is invoked.
"""
from __future__ import annotations

import hashlib
import json
import re
import math
from dataclasses import dataclass

from .infra.feature35_comfy_api_graphs import (
    wan22_ti2v_5b, offline_graph_validate, WorkflowError,
)

PROVIDER = "wan22_ti2v_5b_comfy_v1"
WAN_SOURCE = "1ea34ff48f87168174e12956e200b1d908b1c5ff"
COMFY_SOURCE = "79cf64c21a1dba50749945ba9fe2e3a692f45438"
WEIGHTS_REV = "ee6f4a40737a995bf5818954cfce6d59443b0f04"
ENCODER_REV = "123acf1cc74bccbb9bfff8ac1ee72edc08c2341d"
NATIVE_SIZES = {(704, 1280), (1280, 704)}
NATIVE_FRAMES, NATIVE_FPS, MIN_VRAM_GIB = 121, 24, 24
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
BASENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,128}[.](png|jpg|jpeg|webp)$")
DIRECTION_KEYS = set("""contract shop_id campaign_id scene_id shot_id shot_start_seconds
 duration_seconds reference_media_id product_sku garment_lock scene_goal subject
 character_continuity wardrobe camera lighting environment choreography generation_prompt
 negative_constraints requested_profile previous_shot_id next_shot_id reference_facts_sha256""".split())
DISPATCH_KEYS = set("""source_feature route_owner shop_id campaign_id approval_id review_hash
 shot reviewed coordinator_technical_profile_approved lease_token""".split())
NODE_INPUTS = {
    "UNETLoader": {"unet_name", "weight_dtype"},
    "CLIPLoader": {"clip_name", "type"},
    "VAELoader": {"vae_name"},
    "Wan22ImageToVideoLatent": {"width", "height", "length", "vae", "start_image"},
    "KSampler": {"seed", "steps", "positive", "negative", "latent_image", "model"},
    "VAEDecode": {"samples", "vae"},
    "CreateVideo": {"images", "fps"},
    "SaveVideo": {"video", "filename_prefix"},
}
NODES = set(NODE_INPUTS)


class WanCompatibilityError(ValueError):
    pass


def _id(v, name):
    if not isinstance(v, str) or not ID.fullmatch(v):
        raise WanCompatibilityError("Invalid " + name)
    return v


def _sha(v, name):
    if not isinstance(v, str) or not SHA.fullmatch(v):
        raise WanCompatibilityError("Invalid " + name)
    return v


def _text(v, name, maximum=800):
    if not isinstance(v, str) or not v.strip() or len(v) > maximum or "://" in v:
        raise WanCompatibilityError("Invalid or oversized " + name)
    if any(ord(ch) < 32 and ch not in "\n\t" for ch in v):
        raise WanCompatibilityError("Unsafe " + name)
    return v.strip()


def _time(v):
    if type(v) not in (int, float) or not 0 <= v <= 60:
        raise WanCompatibilityError("Invalid motion timing")
    return float(v)


def capability(*, width, height, fps, frames, gpu_vram_gib, revisions):
    if (width, height) not in NATIVE_SIZES or fps != NATIVE_FPS or frames != NATIVE_FRAMES:
        raise WanCompatibilityError("Wan TI2V-5B supports native 704x1280/1280x704, 121 frames, 24 fps; not native 1080p")
    if type(gpu_vram_gib) not in (int, float) or not math.isfinite(gpu_vram_gib) or gpu_vram_gib < MIN_VRAM_GIB:
        raise WanCompatibilityError("Unverified/insufficient Wan VRAM; upstream documents minimum 24GiB")
    if revisions != {"diffusion": WEIGHTS_REV, "text_encoder": ENCODER_REV}:
        raise WanCompatibilityError("Unapproved installed model checkpoint revisions")
    return True


def validate_runtime_node_types(object_info):
    """Actual private /object_info readback must be supplied by operator; no network."""
    if type(object_info) is not dict or NODES - set(object_info):
        raise WanCompatibilityError("ComfyUI installed native node set unknown")
    for name, required in NODE_INPUTS.items():
        node = object_info[name]
        inp = node.get("input") if type(node) is dict else None
        if type(inp) is not dict:
            raise WanCompatibilityError("ComfyUI node has no input contract: " + name)
        offered = set()
        for group in ("required", "optional"):
            part = inp.get(group, {})
            if type(part) is not dict:
                raise WanCompatibilityError("ComfyUI malformed native node input")
            offered.update(part)
        if required - offered:
            raise WanCompatibilityError("ComfyUI missing expected native inputs: " + name)
    return True


def private_first_frame(media, *, ref, shop):
    """Caller must source media grant from current server JWT/RLS and private byte hash."""
    required = {"asset_id", "shop_id", "mime_type", "staged_basename",
                "sha256", "source_sha256", "source_facts_sha256", "width", "height",
                "approved", "private", "commercial_rights",
                "human_likeness_approved"}
    if type(media) is not dict or set(media) != required:
        raise WanCompatibilityError("Current authoritative media grant required")
    if media["asset_id"] != ref or media["shop_id"] != shop or any(
        media[k] is not True for k in ("approved", "private", "commercial_rights",
                                      "human_likeness_approved")
    ):
        raise WanCompatibilityError("Foreign/revoked/unlicensed private media")
    name, mime = media["staged_basename"], media["mime_type"]
    if not isinstance(name, str) or not BASENAME.fullmatch(name) or ".." in name:
        raise WanCompatibilityError("Unsafe private staged basename")
    extension = name.lower().rsplit(".", 1)[-1]
    if extension not in {"image/png": {"png"}, "image/jpeg": {"jpg", "jpeg"},
                         "image/webp": {"webp"}}.get(mime, set()):
        raise WanCompatibilityError("Image MIME/extension disagreement")
    _sha(media["sha256"], "first-frame SHA256")
    _sha(media["source_sha256"], "original approved source SHA256")
    _sha(media["source_facts_sha256"], "Feature3 approved reference fingerprint")
    w,h=media["width"],media["height"]
    if (type(w) is not int or type(h) is not int or
        not 256 <= w <= 8192 or not 256 <= h <= 8192 or
        abs(w/h - 704/1280) > 0.025):
        raise WanCompatibilityError("I2V first-frame aspect ratio does not match native portrait profile")
    return name


@dataclass(frozen=True)
class WanShotPackage:
    provider: str
    task: str
    graph: dict
    prompt: str
    prompt_sha256: str
    lineage: dict
    lineage_sha256: str
    status: str = "NOT_GENERATED_REVIEW_REQUIRED"


def compile_motion_direction(*, dispatch, approved_reference, profile,
                             gpu_vram_gib, installed_revisions, runtime_nodes=None):
    """Adapt reviewed Feature2 text exactly; compile only, never submit to ComfyUI.

    This is not a public API. Feature4 and coordinator must independently verify
    signatures, lease, ledger reservation, media approval and private bytes.
    """
    if (type(dispatch) is not dict or set(dispatch) != DISPATCH_KEYS or
        dispatch["source_feature"] != "feature2" or
        dispatch["route_owner"] != "feature4" or
        dispatch["reviewed"] is not True or
        dispatch["coordinator_technical_profile_approved"] is not True):
        raise WanCompatibilityError("Trusted Feature4-reviewed dispatch required")
    shot = dispatch["shot"]
    if type(shot) is not dict or set(shot) != DIRECTION_KEYS or shot["contract"] != "motion_direction_v1":
        raise WanCompatibilityError("Unsupported Feature2 motion_direction_v1")
    shop, campaign = _id(dispatch["shop_id"],"shop"), _id(dispatch["campaign_id"],"campaign")
    _id(dispatch["approval_id"],"approval"); _id(dispatch["lease_token"],"lease")
    _sha(dispatch["review_hash"],"review")
    if (shot["shop_id"],shot["campaign_id"]) != (shop,campaign):
        raise WanCompatibilityError("Cross-tenant/campaign creative dispatch")
    for k in ("scene_id","shot_id"): _id(shot[k],k)
    for k in ("previous_shot_id","next_shot_id"):
        if shot[k] is not None: _id(shot[k],k)
    _sha(shot["reference_facts_sha256"],"Feature3 approved reference facts")
    _time(shot["shot_start_seconds"])
    duration = _time(shot["duration_seconds"])
    if duration != 5:
        raise WanCompatibilityError("Only five-second model shots reviewed; Feature4 owns timeline trimming")
    for k in ("scene_goal","subject","character_continuity","wardrobe",
              "lighting","environment","product_sku"):
        _text(shot[k],k)
    garment = shot["garment_lock"]
    locks = ("color","neckline","sleeves","hem","embroidery")
    if type(garment) is not dict or not set(locks) <= set(garment):
        raise WanCompatibilityError("Missing garment preservation facts")
    for k in locks: _text(garment[k],"garment "+k)
    camera = shot["camera"]
    if type(camera) is not dict or set(camera) != {"framing","lens","composition","movement"}:
        raise WanCompatibilityError("Incomplete camera instructions")
    for k in camera: _text(camera[k],"camera "+k)
    pieces=shot["choreography"]
    if not isinstance(pieces,list) or not 2 <= len(pieces) <= 10:
        raise WanCompatibilityError("At least two detailed motion segments required")
    cursor=0.0
    for seg in pieces:
        if type(seg) is not dict or set(seg) != {
            "start_seconds","end_seconds","human_action","camera_action","fabric_response"
        }:
            raise WanCompatibilityError("Missing timed body/camera/fabric instructions")
        a,b=_time(seg["start_seconds"]),_time(seg["end_seconds"])
        if abs(a-cursor)>0.001 or not a < b <= duration:
            raise WanCompatibilityError("Gap, overlap or out-of-range physical motion")
        cursor=b
        for k in ("human_action","camera_action","fabric_response"): _text(seg[k],k)
    if abs(cursor-duration)>0.001:
        raise WanCompatibilityError("Motion must specify starting through finishing pose")
    prompt=_text(shot["generation_prompt"],"approved Feature2 prompt",1600)
    if len(prompt)<180:
        raise WanCompatibilityError("Professional cinematic motion prompt required")
    negatives=shot["negative_constraints"]
    if not isinstance(negatives,list) or not 3 <= len(negatives) <= 16:
        raise WanCompatibilityError("At least three negative constraints required")
    for item in negatives: _text(item,"negative",120)
    req=shot["requested_profile"]
    if type(req) is not dict or req != {
        "kind":"image_to_video","aspect_ratio":"9:16",
        "target_width":1080,"target_height":1920,"target_fps":24,
        "provider_profile_verified":False,"inference_approved":False
    }:
        raise WanCompatibilityError("Feature2 editorial target/review state mismatch")
    if type(profile) is not dict or profile != {
        "provider":PROVIDER,"task":"ti2v-5B","width":704,"height":1280,
        "fps":24,"frames":121,"model_source_commit":WAN_SOURCE,
        "comfy_source_commit":COMFY_SOURCE
    }:
        raise WanCompatibilityError("Unapproved native technical profile")
    capability(width=704,height=1280,fps=24,frames=121,
               gpu_vram_gib=gpu_vram_gib,revisions=installed_revisions)
    if runtime_nodes is not None: validate_runtime_node_types(runtime_nodes)
    ref=_id(shot["reference_media_id"],"approved reference")
    filename=private_first_frame(approved_reference,ref=ref,shop=shop)
    if approved_reference["source_facts_sha256"] != shot["reference_facts_sha256"]:
        raise WanCompatibilityError("Feature3 approved reference revision changed")

    # Adapt Wan official prompt_extension technical T2V-vs-I2V selection
    # deterministically. Never run upstream's optional cloud/local Qwen rewriter.
    annotations=[
        "Continuity: "+shot["character_continuity"],
        "Wardrobe: "+shot["wardrobe"],
        "Garment facts: "+"; ".join(k+" "+garment[k] for k in locks),
        "Camera: "+"; ".join(k+" "+camera[k] for k in ("framing","lens","composition","movement")),
        "Lighting: "+shot["lighting"]+"; environment: "+shot["environment"],
    ]
    for p in pieces:
        annotations.append("{}-{}s: {}; camera {}; fabric {}".format(
            p["start_seconds"],p["end_seconds"],p["human_action"],
            p["camera_action"],p["fabric_response"]))
    technical_prompt=prompt+"\n"+"\n".join(annotations)
    if len(technical_prompt)>3000:
        raise WanCompatibilityError("Cannot fit full approved prompt and garment locks; request revision")
    negative_prompt=", ".join(negatives)
    if len(negative_prompt)>1000:
        raise WanCompatibilityError("Negative constraints exceed native budget")
    # Reproducible per-approved-shot seed; not chosen by client.
    approved_digest=hashlib.sha256(json.dumps(
        [shot,dispatch["review_hash"]],sort_keys=True,separators=(",",":")
    ).encode("utf8")).hexdigest()
    seed=int(approved_digest[:12],16)
    try:
        graph=wan22_ti2v_5b(prompt=technical_prompt,seed=seed,
                            approved_input_file=filename,width=704,height=1280,
                            frames=121,fps=24)
        graph["prompt"]["5"]["inputs"]["text"]=negative_prompt
        offline_graph_validate(graph)
    except WorkflowError as e:
        raise WanCompatibilityError("Native ComfyUI API graph rejected") from e
    lineage={
        "shop_id":shop,"campaign_id":campaign,"scene_id":shot["scene_id"],
        "shot_id":shot["shot_id"],"source_feature":"feature2",
        "routed_by":"feature4","approval_id":dispatch["approval_id"],
        "review_hash":dispatch["review_hash"],"lease_token":dispatch["lease_token"],
        "source_asset_id":ref,"source_sha256":approved_reference["source_sha256"],
        "staged_first_frame_sha256":approved_reference["sha256"],
        "reference_facts_sha256":shot["reference_facts_sha256"],
        "target_final_editorial":[1080,1920,24],
        "actual_native_request":[704,1280,24,121],
        "model_revision":WEIGHTS_REV,"text_encoder_revision":ENCODER_REV,
        "upstream_commit":WAN_SOURCE,"provider":PROVIDER,
    }
    lineage_sha=hashlib.sha256(json.dumps(lineage,sort_keys=True,
                      separators=(",",":")).encode()).hexdigest()
    return WanShotPackage(PROVIDER,"image_to_video",graph,technical_prompt,
                          hashlib.sha256(json.dumps({"positive":technical_prompt,"negative":negative_prompt},sort_keys=True,separators=(",",":")).encode()).hexdigest(),
                          lineage,lineage_sha)


def pending_feature4_receipt(package):
    """Compiled graph alone never counts as an approved/generated Feature4 clip."""
    if not isinstance(package,WanShotPackage):
        raise WanCompatibilityError("Unknown provider output")
    return {"status":"NOT_GENERATED","provider":package.provider,
            "lineage_sha256":package.lineage_sha256,
            "prompt_sha256":package.prompt_sha256,
            "review_required":True,"approved_for_feature4":False,
            "gpu_started":False}
