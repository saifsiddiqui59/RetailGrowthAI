"""Consume Feature3's merged original-byte F5 demo packet, GPU OFF.

Only the Feature3-owned load_demo_consumer_bytes reads and verifies the source.
This bridge independently checks the exact three pinned media identities,
decodes them, and stages a temporary private native first frame for OFFLINE
ComfyUI graph and CPU media tests. It never authorizes a model, billing, or
publication and is NOT the live Feature3 tenant-rights worker resolver.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha1, sha256
from io import BytesIO
import os
from pathlib import Path
import re
import stat
import tempfile

from PIL import Image, UnidentifiedImageError

from .infra.feature35_comfy_api_graphs import offline_graph_validate, wan22_ti2v_5b
from .wan22_motion_adapter import WanCompatibilityError

SCHEMA = "retailgrowth.feature3-demo-consumer-bytes.v1"
REVISION = "10140178cdb198ff17ad7b226c432bd63d732fc2"
TARGET = (704, 1280)
MAX_BYTES = 3 * 1024 * 1024
# Original Feature3 source identities, NOT hashes of derivative/try-on output.
ORIGINALS = {
    "image_to_video_first_frame": ("synthetic_avatar.png", "fc88e5d07282009a14b0bd58fbdd58bc2f89ace0", "image/png", "PNG"),
    "garment_reference": ("synthetic_garment_front.jpg", "878fde8857f58862723f85d7f8bd723c65a8e498", "image/jpeg", "JPEG"),
    "model_pose_reference": ("synthetic_model_pose.jpg", "72a86a60280976ce5c73db9525d9648b54d1126a", "image/jpeg", "JPEG"),
}
DENIED = ("customer_approved", "publish_approved", "provider_call_permitted",
          "paid_inference_authorized", "actual_vton_inference_performed",
          "model_wears_product_garment")
ASSET_FIELDS = {"filename", "source_path", "source_git_blob_sha1", "sha256",
                "mime_type", "bytes", "image_bytes"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _checked_packet(packet):
    if (type(packet) is not dict or packet.get("schema") != SCHEMA
            or packet.get("feature") != "F5"
            or packet.get("source_repository") != "Prompt-Haus/OpenVTO"
            or packet.get("source_revision") != REVISION
            or packet.get("source_license") != "MIT demo only"
            or packet.get("requires_live_tenant_rights_and_worker_lease") is not True
            or any(packet.get(flag) is not False for flag in DENIED)):
        raise WanCompatibilityError("Feature3 demo packet cannot grant runtime or customer rights")
    assets = packet.get("assets")
    if type(assets) is not dict or set(assets) != set(ORIGINALS):
        raise WanCompatibilityError("Feature3 requires exactly three distinct source roles")
    checked = {}
    for role, (name, blob, mime, fmt) in ORIGINALS.items():
        item = assets[role]
        if type(item) is not dict or set(item) != ASSET_FIELDS:
            raise WanCompatibilityError("Feature3 original asset schema mismatch")
        raw = item.get("image_bytes")
        if (type(raw) is not bytes or not 100 <= len(raw) <= MAX_BYTES
                or type(item.get("bytes")) is not int or item["bytes"] != len(raw)
                or item.get("filename") != name
                or item.get("source_git_blob_sha1") != blob
                or item.get("mime_type") != mime
                or type(item.get("source_path")) is not str
                or not item["source_path"].startswith("packages/sdk/openvto/assets/")
                or type(item.get("sha256")) is not str
                or _SHA256.fullmatch(item["sha256"]) is None):
            raise WanCompatibilityError("Feature3 original image metadata mismatch")
        gitsha = sha1(("blob " + str(len(raw)) + "\0").encode("ascii") + raw).hexdigest()
        digest = sha256(raw).hexdigest()
        if gitsha != blob or digest != item["sha256"]:
            raise WanCompatibilityError("Changed Feature3 original bytes")
        try:
            with Image.open(BytesIO(raw)) as image:
                if (image.format != fmt or getattr(image, "n_frames", 1) != 1
                        or not 128 <= image.width <= 8192
                        or not 128 <= image.height <= 8192
                        or image.width * image.height > 24_000_000):
                    raise WanCompatibilityError("Invalid Feature3 decoded original")
                image.verify()
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError) as exc:
            raise WanCompatibilityError("Unverified Feature3 original image") from exc
        checked[role] = (raw, digest)
    if len({digest for _, digest in checked.values()}) != 3:
        raise WanCompatibilityError("Distinct model, garment and avatar references required")
    return checked


@contextmanager
def stage_verified_feature3_demo_for_f5(*, directory, scratch_parent, load_feature3_consumer_bytes):
    """Run the actual merged Feature3 producer, then private GPU-free graph prep.

    The callable MUST be the trusted in-process Feature3-owned module; not a
    browser-provided callback. Return only explicit TEST_ONLY evidence.
    """
    if not callable(load_feature3_consumer_bytes):
        raise WanCompatibilityError("Actual Feature3 byte producer required")
    try:
        packet = load_feature3_consumer_bytes(directory, "F5")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise WanCompatibilityError("Feature3 original-byte verification failed") from exc
    checked = _checked_packet(packet)
    parent = Path(scratch_parent)
    if (parent.is_symlink() or not parent.is_dir()
            or parent.stat().st_mode & 0o077):
        raise WanCompatibilityError("Private 0700 offline scratch directory required")
    with tempfile.TemporaryDirectory(prefix="f5-feature3-byte-test-", dir=parent) as private:
        root = Path(private)
        os.chmod(root, 0o700)
        raw, image_sha = checked["image_to_video_first_frame"]
        with Image.open(BytesIO(raw)) as original:
            rgb = original.convert("RGB")
            rgb.thumbnail(TARGET, Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", TARGET, (24, 24, 24))
            canvas.paste(rgb, ((TARGET[0] - rgb.width) // 2,
                               (TARGET[1] - rgb.height) // 2))
            out = BytesIO()
            canvas.save(out, format="PNG", optimize=True)
        path = root / "feature3_verified_demo_first_frame.png"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(out.getvalue())
        if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_nlink != 1:
            raise WanCompatibilityError("Private first-frame identity failed")
        graph = wan22_ti2v_5b(
            prompt=("OFFLINE TEST ONLY: fictional synthetic avatar motion reference. "
                    "Separate garment and pose images do not depict the wearer "
                    "wearing that product. No commercial inference or publication."),
            seed=42, approved_input_file=path.name, width=704, height=1280,
            frames=121, fps=24, output_prefix="rgai/feature5_f3_demo_only")
        offline_graph_validate(graph)
        evidence = {
            "schema": "retailgrowth.feature5-f3-verified-bytes-offline.v1",
            "source_revision": REVISION,
            "first_frame_sha256": image_sha,
            "garment_sha256": checked["garment_reference"][1],
            "model_pose_sha256": checked["model_pose_reference"][1],
            "prepared_first_frame_sha256": sha256(out.getvalue()).hexdigest(),
            "width": 704, "height": 1280, "fps": 24, "frames": 121,
            "original_garment_worn_by_model": False,
            "actual_wan_inference_performed": False,
            "customer_approved": False,
            "provider_call_permitted": False,
            "paid_inference_authorized": False,
            "publish_approved": False,
            "status": "OFFLINE_SOURCE_AND_GRAPH_ONLY",
        }
        yield path, graph, evidence
