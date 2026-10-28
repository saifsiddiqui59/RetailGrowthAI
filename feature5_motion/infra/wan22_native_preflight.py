"""Source-only native Wan / ComfyUI runtime contract and lock verification.

Official source: Comfy-Org/ComfyUI @
79cf64c21a1dba50749945ba9fe2e3a692f45438:
comfy_extras/nodes_wan.py: Wan22ImageToVideoLatent
comfy_extras/nodes_video.py: SaveVideo.execute expects codec dictionary,
not string. Its format dynamic combo can carry {"format":"mp4",
"codec":{"codec":"h264"}}. The existing pinned Wan API graph is reused.

Everything here is LOCAL READ/VALIDATE ONLY. Caller must obtain actual
/object_info from a protected authenticated private runtime. Supplying JSON
from a browser is NOT proof of the installed software or authorization.
No requests, code execution, GPU, image pulls or Azure writes in this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .feature35_comfy_api_graphs import CHECKPOINTS, offline_graph_validate, wan22_ti2v_5b, WorkflowError
from ..wan22_motion_adapter import (
    COMFY_SOURCE, WAN_SOURCE, WanCompatibilityError,
    NODE_INPUTS, validate_runtime_node_types,
)

SHA256 = re.compile(r"^[a-f0-9]{64}$")
OCI = re.compile(r"^[a-z0-9.-]+(?::[0-9]+)?/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$")
SHA40 = re.compile(r"^[a-f0-9]{40}$")
VERSION = re.compile(r"^[0-9]+[.][0-9]+(?:[.][0-9]+)?(?:[+a-zA-Z0-9.-]+)?$")
MAX_JSON = 2 * 1024 * 1024
NODE_ALLOWLIST = frozenset((
    "UNETLoader", "CLIPLoader", "VAELoader", "CLIPTextEncode",
    "LoadImage", "Wan22ImageToVideoLatent", "ModelSamplingSD3",
    "KSampler", "VAEDecode", "CreateVideo", "SaveVideo",
))
# The minimum reviewed wheel set is NOT a complete transitive dependency
# lock; the operator must additionally supply an immutable all-wheels manifest.
REQUIRED_PACKAGES = frozenset((
    "torch", "torchvision", "torchsde", "transformers", "safetensors",
    "av", "Pillow", "comfyui-frontend-package",
))


def validate_runtime_lock(lock, *, approved_image_digest, reviewed_wheel_sha256):
    """Refuse all unreviewed or mutable image/runtime dependency states.

    Locks and approved hashes must be provided by an independent operator.
    This checks *matching declarations*, not actual container/wheel bytes.
    """
    if type(lock) is not dict or set(lock) != {
        "schema", "source_commit", "wan_source_commit", "image", "python_version",
        "base_image", "wheels_sha256", "source_license_reviewed",
        "comfy_gpl_distribution_reviewed", "checkpoint_licenses_reviewed",
        "cuda_and_nvidia_eula_reviewed", "runtime_gpu_enabled",
    }:
        raise WanCompatibilityError("Incomplete immutable Comfy runtime lock")
    if (lock["schema"] != "retailgrowth.wan22.runtime-lock.v1" or
        lock["source_commit"] != COMFY_SOURCE or
        lock["wan_source_commit"] != WAN_SOURCE or
        not isinstance(lock["image"], str) or not OCI.fullmatch(lock["image"]) or
        lock["image"] != approved_image_digest or
        not isinstance(lock["base_image"], str) or not OCI.fullmatch(lock["base_image"]) or
        not isinstance(lock["python_version"],str) or
        not VERSION.fullmatch(lock["python_version"])):
        raise WanCompatibilityError("Unapproved pinned source, Python or immutable OCI image")
    if any(lock[key] is not True for key in (
        "source_license_reviewed", "comfy_gpl_distribution_reviewed",
        "checkpoint_licenses_reviewed", "cuda_and_nvidia_eula_reviewed"
    )):
        raise WanCompatibilityError("Commercial runtime dependency/redistribution review missing")
    if lock["runtime_gpu_enabled"] is not False:
        raise WanCompatibilityError("GPU activation is out of scope for source preflight")
    wheels = lock["wheels_sha256"]
    if type(wheels) is not dict or type(reviewed_wheel_sha256) is not dict or (
        set(wheels) != set(reviewed_wheel_sha256) or
        not REQUIRED_PACKAGES <= set(wheels)
    ):
        raise WanCompatibilityError("Complete reviewed pinned wheel set required")
    for name, proof in wheels.items():
        if (not isinstance(name,str) or len(name) > 100 or not name or
            type(proof) is not dict or set(proof) != {"version","sha256"} or
            not isinstance(proof["version"],str) or not VERSION.fullmatch(proof["version"]) or
            not isinstance(proof["sha256"],str) or not SHA256.fullmatch(proof["sha256"]) or
            proof != reviewed_wheel_sha256[name]):
            raise WanCompatibilityError("Unpinned or changed dependency wheel")
    return True


def _actual_input_names(spec):
    if type(spec) is not dict or type(spec.get("input")) is not dict:
        raise WanCompatibilityError("Installed node object_info not provided")
    inp = spec["input"]
    groups=[]
    for key in ("required","optional"):
        group = inp.get(key,{})
        if type(group) is not dict:
            raise WanCompatibilityError("Invalid installed node input group")
        groups.append(group)
    return groups[0], groups[1]


def _allowlist_enums(value, descriptor):
    """Fail closed on real advertised filename choices when enum is supplied."""
    if (type(descriptor) is not list or not descriptor or
        not isinstance(descriptor[0], (list, str))):
        raise WanCompatibilityError("Malformed installed Comfy widget descriptor")
    if isinstance(descriptor[0], list) and value not in descriptor[0]:
        raise WanCompatibilityError("Model/input not installed in runtime selector")


def validate_native_graph_against_object_info(graph, object_info, *, expected_input_filename=None, expected_negative_prompt=None):
    """Check actual node names, required/optional inputs, and checkpoint choices.

    Real protected server must supply its object_info directly. Source-only
    fixture testing is useful but cannot replace that live readback.
    """
    try:
        offline_graph_validate(graph)
    except WorkflowError as exc:
        raise WanCompatibilityError("Invalid private native graph") from exc
    validate_runtime_node_types(object_info)
    nodes = graph["prompt"]
    if not 11 <= len(nodes) <= 12:
        raise WanCompatibilityError("Unexpected Wan graph node count")
    classes = {n["class_type"] for n in nodes.values()}
    if classes - NODE_ALLOWLIST or not {"Wan22ImageToVideoLatent","SaveVideo"} <= classes:
        raise WanCompatibilityError("Unapproved native graph node")
    expected = {
        "unet_name": CHECKPOINTS["wan"][0],
        "clip_name": CHECKPOINTS["wan"][1],
        "vae_name": CHECKPOINTS["wan"][2],
    }
    for node in nodes.values():
        name = node["class_type"]
        if name not in object_info:
            raise WanCompatibilityError("Missing native Comfy node " + name)
        required, optional = _actual_input_names(object_info[name])
        actual = node["inputs"]
        if set(actual) - (set(required) | set(optional)):
            raise WanCompatibilityError("Unsupported Comfy input for " + name)
        if set(required) - set(actual):
            raise WanCompatibilityError("Missing required native input for " + name)
        for key,value in actual.items():
            desc=(required | optional)[key]
            if key in expected and value != expected[key]:
                raise WanCompatibilityError("Staged Wan checkpoint changed")
            if key in ("unet_name","clip_name","vae_name"):
                _allowlist_enums(value,desc)
    savers=[n for n in nodes.values() if n["class_type"] == "SaveVideo"]
    if len(savers) != 1 or savers[0]["inputs"].get("format") != {
        "format":"mp4","codec":{"codec":"h264"}
    } or "codec" in savers[0]["inputs"]:
        raise WanCompatibilityError("Pinned SaveVideo requires explicit dynamic MP4/H264 settings")
    lengths=[n["inputs"] for n in nodes.values() if n["class_type"]=="Wan22ImageToVideoLatent"]
    if len(lengths)!=1 or (
        lengths[0].get("width"),lengths[0].get("height"),lengths[0].get("length")
    ) not in ((704,1280,121),(1280,704,121)):
        raise WanCompatibilityError("Unsupported native Wan model size or frame count")
    # An allowlisted class and correct node count do NOT prove that its edges,
    # sampler, negative conditioning, seed, file paths or output graph are safe.
    # Reconstruct the entire reviewed graph with strictly typed user-adjustable
    # fields; *every* node, ID, link, fixed setting and wrapper key must match.
    try:
        latent = nodes["7"]["inputs"]
        sampler = nodes["9"]["inputs"]
        approved_input_file = nodes["6"]["inputs"]["image"] if "6" in nodes else None
        canonical = wan22_ti2v_5b(
            prompt=nodes["4"]["inputs"]["text"],
            seed=sampler["seed"],
            approved_input_file=approved_input_file,
            width=latent["width"], height=latent["height"], frames=latent["length"],
            fps=nodes["11"]["inputs"]["fps"],
            output_prefix=nodes["12"]["inputs"]["filename_prefix"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise WanCompatibilityError("Invalid pinned Wan node values or IDs") from exc
    # Feature2's Creative Director owns a scene-specific negative prompt.
    # The actual dispatcher MUST independently fence the entire positive+
    # negative prompt digest against the authoritative Part3 paid claim.
    if expected_negative_prompt is not None:
        if (type(expected_negative_prompt) is not str or
            not 1 <= len(expected_negative_prompt) <= 1000 or
            any(ord(ch)<32 and ch not in "\n\t" for ch in expected_negative_prompt)):
            raise WanCompatibilityError("Unreviewed Feature2 negative constraints")
        canonical["prompt"]["5"]["inputs"]["text"]=expected_negative_prompt
    if graph != canonical:
        raise WanCompatibilityError("Wan graph topology or pinned sampler settings changed")
    # Topology checks CANNOT know whether an otherwise valid image basename
    # was actually approved. Bind it to the independently reauthorized F3
    # private staging record; never trust a filename from the graph itself.
    if expected_input_filename is not None and approved_input_file != expected_input_filename:
        raise WanCompatibilityError("Wan first-frame basename differs from current Feature3 private grant")
    return True


def check_small_safetensors_header(path, *, expected_size, max_header_bytes=10*1024*1024):
    """Optional fast local header parse; NOT a full checkpoint SHA256 proof.

    Used after mounting the existing private read-only model share, not in
    general CI. Reject links and malformed lengths without loading 10GB.
    """
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size != expected_size:
        raise WanCompatibilityError("Wrong model file identity/byte count")
    try:
        with p.open("rb") as f:
            size=int.from_bytes(f.read(8),"little")
            if not 2 <= size <= max_header_bytes or size+8>expected_size:
                raise ValueError("Invalid model header")
            raw=f.read(size)
            if len(raw)!=size:
                raise ValueError("Truncated model header")
            doc=json.loads(raw)
            if type(doc) is not dict or not doc or any(
                not isinstance(k,str) or not isinstance(v,dict)
                for k,v in doc.items()
            ):
                raise ValueError("Unrecognized safetensors header")
    except (OSError,ValueError,UnicodeError,TypeError) as exc:
        raise WanCompatibilityError("Invalid local safetensors metadata") from exc
    return {"stat_bytes":expected_size,"header_sha256":hashlib.sha256(raw).hexdigest(),
            "model_sha256_verified":False,"gpu_started":False}


def audit_offline_wheelhouse(root, *, reviewed_wheel_sha256):
    """Hash actual approved wheel bytes locally, without networking, pip or GPU.

    Independently reviewed hashes must be supplied by a trusted operator.
    A mere declared hash or image digest does not prove supplied wheel bytes.
    Check wheel package/version identity, zip metadata and complete package
    set. No files are extracted or executed.
    """
    import stat
    from email.parser import Parser
    from zipfile import BadZipFile, ZipFile

    if type(reviewed_wheel_sha256) is not dict or not REQUIRED_PACKAGES <= set(reviewed_wheel_sha256):
        raise WanCompatibilityError("An independently approved complete wheel manifest is required")
    directory = Path(root)
    if directory.is_symlink() or not directory.is_dir():
        raise WanCompatibilityError("Wheelhouse must be an existing non-symlink directory")
    def normalize(n):
        return re.sub(r"[-_.]+", "-", n).lower()
    registered = {normalize(k): (k,v) for k,v in reviewed_wheel_sha256.items()}
    if len(registered) != len(reviewed_wheel_sha256):
        raise WanCompatibilityError("Ambiguous normalized wheel package names")
    seen = set()
    total = 0
    for path in sorted(directory.iterdir()):
        if path.is_symlink() or not path.is_file() or not path.name.endswith(".whl"):
            raise WanCompatibilityError("Wheelhouse has unexpected, non-wheel or linked entries")
        if len(seen) >= 256:
            raise WanCompatibilityError("Wheelhouse has too many dependencies")
        # PEP 427 wheel name: distribution-version(-build)-python-abi-platform.whl
        pieces = path.name[:-4].split("-")
        if len(pieces) not in (5,6) or not pieces[0] or not pieces[1] or not all(pieces[-3:]):
            raise WanCompatibilityError("Malformed wheel filename")
        package = normalize(pieces[0])
        if package not in registered or package in seen:
            raise WanCompatibilityError("Duplicate or unapproved dependency wheel")
        name, proof = registered[package]
        if (type(proof) is not dict or set(proof) != {"version","sha256"} or
            pieces[1] != proof["version"] or
            not isinstance(proof["sha256"],str) or not SHA256.fullmatch(proof["sha256"])):
            raise WanCompatibilityError("Wheel version or approved digest mismatch")
        info = path.stat()
        size = info.st_size
        if not 100 <= size <= 8 * 1024 ** 3 or not stat.S_ISREG(info.st_mode):
            raise WanCompatibilityError("Wheel has invalid byte size")
        total += size
        if total > 24 * 1024 ** 3:
            raise WanCompatibilityError("Wheelhouse exceeds reviewed storage envelope")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for data in iter(lambda:stream.read(1024*1024),b""):
                digest.update(data)
        if digest.hexdigest() != proof["sha256"] or path.stat().st_size != size:
            raise WanCompatibilityError("Actual dependency wheel SHA256 does not match approval")
        try:
            with ZipFile(path) as archive:
                members = archive.namelist()
                if not members or len(members) > 50000 or any(
                    x.startswith("/") or "\\" in x or
                    ".." in x.split("/") or "\x00" in x
                    for x in members
                ):
                    raise WanCompatibilityError("Malformed or unsafe wheel archive entries")
                metadata = [x for x in members if x.endswith(".dist-info/METADATA")]
                wheelmeta = [x for x in members if x.endswith(".dist-info/WHEEL")]
                if len(metadata) != 1 or len(wheelmeta) != 1:
                    raise WanCompatibilityError("Missing or ambiguous wheel metadata")
                for entry in metadata + wheelmeta:
                    if archive.getinfo(entry).file_size > 512 * 1024:
                        raise WanCompatibilityError("Oversized wheel identity metadata")
                record = Parser().parsestr(archive.read(metadata[0]).decode("utf8"))
                if normalize(record.get("Name", "")) != package or record.get("Version") != proof["version"]:
                    raise WanCompatibilityError("Embedded wheel identity differs from filename")
                if not archive.read(wheelmeta[0]).startswith(b"Wheel-Version:"):
                    raise WanCompatibilityError("Invalid wheel metadata")
        except WanCompatibilityError:
            raise
        except (OSError, ValueError, UnicodeError, BadZipFile) as exc:
            raise WanCompatibilityError("Unreadable offline wheel archive") from exc
        seen.add(package)
    if seen != set(registered):
        raise WanCompatibilityError("Wheelhouse missing approved dependencies")
    return {"wheel_count":len(seen),"total_bytes":total,
            "actual_file_hashes_checked":True,"gpu_started":False,
            "offline_no_network":True}


def render_reviewed_require_hashes(reviewed_wheel_sha256):
    """Deterministic, one-wheel-per-dependency offline pip hash requirements.

    Does not resolve dependencies or prove CUDA compatibility. The approved
    manifest must be complete and independently reviewed by an operator.
    """
    if (type(reviewed_wheel_sha256) is not dict or
        not REQUIRED_PACKAGES <= set(reviewed_wheel_sha256) or
        not 1 <= len(reviewed_wheel_sha256) <= 256):
        raise WanCompatibilityError("Cannot generate lock without complete reviewed wheel inventory")
    safe_name = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
    normalized = set()
    result = []
    for name, proof in reviewed_wheel_sha256.items():
        if not isinstance(name,str) or not safe_name.fullmatch(name):
            raise WanCompatibilityError("Unsafe dependency name in reviewed lock")
        pkg = re.sub(r"[-_.]+","-",name).lower()
        if pkg in normalized:
            raise WanCompatibilityError("Alias collision in dependency lock")
        normalized.add(pkg)
        if (type(proof) is not dict or set(proof) != {"version","sha256"} or
            not isinstance(proof["version"],str) or not VERSION.fullmatch(proof["version"]) or
            not isinstance(proof["sha256"],str) or not SHA256.fullmatch(proof["sha256"])):
            raise WanCompatibilityError("Invalid dependency version or approved digest")
        result.append((pkg,pkg+"=="+proof["version"]+" --hash=sha256:"+proof["sha256"]))
    return "\n".join(line for _,line in sorted(result))+"\n"


def validate_offline_requirements_file(path, *, reviewed_wheel_sha256):
    """The build input must be EXACTLY the fully reviewed offline wheel lock."""
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > 128*1024:
        raise WanCompatibilityError("Missing or unsafe hashlocked pip input file")
    expected=render_reviewed_require_hashes(reviewed_wheel_sha256)
    try:
        content=p.read_text(encoding="utf8")
    except (OSError,UnicodeError) as exc:
        raise WanCompatibilityError("Unreadable hashlocked pip requirements file") from exc
    if content != expected:
        raise WanCompatibilityError("Offline pip requirements differ from reviewed wheel byte inventory")
    return True
