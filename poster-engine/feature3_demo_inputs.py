"""Pinned, licence-documented OpenVTO synthetic demo input for Features 4/5.

Only for offline integration/demos, never commercial customer approval. This
downloads ORIGINAL upstream bytes, not generated VTON output; no provider,
Supabase, user JWT, paid GPU or external service role is ever contacted.
"""
from __future__ import annotations

import argparse
from hashlib import sha1, sha256
from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError

REPOSITORY = "Prompt-Haus/OpenVTO"
REVISION = "10140178cdb198ff17ad7b226c432bd63d732fc2"
SOURCE_ROOT = f"https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/"
LICENSE = f"https://github.com/{REPOSITORY}/blob/{REVISION}/LICENSE"
LICENSE_EVIDENCE = f"https://github.com/{REPOSITORY}/blob/{REVISION}/README.md"
MAX_BYTES = 3 * 1024 * 1024

# The Git blob identities and sizes below were retrieved from the exact pinned
# upstream Git tree, NOT guessed from filenames or a floating GitHub branch.
SOURCES = (
    ("synthetic_avatar.png", "packages/sdk/openvto/assets/avatars/1.png",
     "fc88e5d07282009a14b0bd58fbdd58bc2f89ace0", 1207867, "PNG"),
    ("synthetic_garment_front.jpg",
     "packages/sdk/openvto/assets/clothes/shirts/1_front.jpg",
     "878fde8857f58862723f85d7f8bd723c65a8e498", 32633, "JPEG"),
    ("synthetic_model_pose.jpg", "packages/sdk/openvto/assets/people/1_posture.jpg",
     "72a86a60280976ce5c73db9525d9648b54d1126a", 103914, "JPEG"),
)


class DemoPackDenied(ValueError):
    """Upstream source or local image integrity could not be trusted."""


def _get(url, *, opener):
    response = opener(Request(url, headers={"User-Agent": "RetailGrowthAI-DemoPack/1.0"}), timeout=15)
    with response as stream:
        if stream.geturl() != url:
            raise DemoPackDenied("Redirected source bytes are not authorized")
        return stream.read(MAX_BYTES + 1)


def _validate(raw, *, expected_git_sha, expected_size, image_format):
    if type(raw) is not bytes or len(raw) != expected_size or len(raw) > MAX_BYTES:
        raise DemoPackDenied("Original demo bytes or length differ from pinned source")
    blob_sha = sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
    if blob_sha != expected_git_sha:
        raise DemoPackDenied("Upstream original Git blob SHA mismatch")
    try:
        with Image.open(BytesIO(raw)) as image:
            if (image.format != image_format or
                getattr(image, "n_frames", 1) != 1 or
                image.width < 128 or image.height < 128 or
                image.width * image.height > 24_000_000):
                raise DemoPackDenied("Unsupported demo image format or dimensions")
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError) as exc:
        raise DemoPackDenied("Invalid upstream demo image bytes") from exc
    return sha256(raw).hexdigest()


def export_demo_input_pack(output_dir, *, opener=urlopen):
    """Materialize genuine upstream demo source bytes into a local test folder.

    No signed rights or production publishing gates are created by this call.
    Call with an explicit local folder. No unknown URLs or user-defined paths.
    """
    dest = Path(output_dir).expanduser()
    if dest.exists() and not dest.is_dir():
        raise DemoPackDenied("Demo pack destination must be a directory")
    dest.mkdir(parents=True, exist_ok=True)
    validated = []
    for name, relative, gitsha, size, fmt in SOURCES:
        if (not relative.startswith("packages/sdk/openvto/assets/") or
            "/../" in relative or name != Path(name).name):
            raise DemoPackDenied("Untrusted demo asset path")
        url = SOURCE_ROOT + relative
        try:
            raw = _get(url, opener=opener)
            digest = _validate(raw, expected_git_sha=gitsha,
                               expected_size=size, image_format=fmt)
        except DemoPackDenied:
            raise
        except (OSError, TimeoutError, ValueError) as exc:
            raise DemoPackDenied("Pinned upstream demo asset unavailable") from exc
        validated.append((name, raw, relative, gitsha, digest, fmt))
    # Persist only after every pinned byte stream was validated.
    with tempfile.TemporaryDirectory(prefix=".feature3-demo-", dir=dest) as temporary:
        staged = Path(temporary)
        for name, raw, _relative, _gitsha, _digest, _fmt in validated:
            (staged / name).write_bytes(raw)
        metadata = {
            "schema": "retailgrowth.feature3-demo-input-pack.v1",
            "source_repository": REPOSITORY,
            "source_revision": REVISION,
            "source_license": "MIT",
            "source_license_url": LICENSE,
            "source_license_evidence_url": LICENSE_EVIDENCE,
            "provenance": "Original OpenVTO synthetic, Git-blob-pinned demo media",
            "rights_scope": "Testing and demonstration only; no retailer SKU or customer ownership assertion",
            "model_is_synthetic": True,
            "real_person_likeness_release_required_for_this_demo": False,
            "actual_vton_inference_performed": False,
            "customer_approved": False,
            "publish_approved": False,
            "gpu_authorized": False,
            "assets": [
                {"filename": name, "source_path": relative,
                 "source_git_blob_sha1": gitsha, "sha256": digest,
                 "bytes": len(raw), "mime_type": "image/png" if fmt == "PNG" else "image/jpeg",
                 "rights_verified_for_customer": False}
                for name, raw, relative, gitsha, digest, fmt in validated
            ],
            "feature4": {
                "timeline_source_frame": "synthetic_avatar.png",
                "garment_product_still": "synthetic_garment_front.jpg",
                "model_pose_reference": "synthetic_model_pose.jpg",
                "media_license": "MIT demo only", "publish_approved": False,
            },
            "feature5": {
                "image_to_video_first_frame": "synthetic_avatar.png",
                "garment_reference": "synthetic_garment_front.jpg",
                "model_pose_reference": "synthetic_model_pose.jpg",
                "requires_tenant_rights_validation": True,
                "requires_new_worker_lease_and_cost_reservation": True,
                "provider_call_permitted": False,
                "actual_vton_inference_performed": False,
            },
        }
        (staged / "manifest.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for name, *_ in validated:
            os.replace(staged / name, dest / name)
        os.replace(staged / "manifest.json", dest / "manifest.json")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and SHA-verify OpenVTO MIT test images")
    parser.add_argument("--output", required=True, help="Local offline demo asset folder")
    args = parser.parse_args()
    result = export_demo_input_pack(args.output)
    print(json.dumps({"status": "VERIFIED_OFFLINE_DEMO_INPUTS",
                      "files": [row["filename"] for row in result["assets"]],
                      "provider_call_permitted": False}, sort_keys=True))
