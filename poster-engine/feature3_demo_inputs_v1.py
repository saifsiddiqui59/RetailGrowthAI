"""Fetch byte-pinned, public OpenVTO fictional fashion demo inputs for Feature4/5.

TEST AND DEMONSTRATION ONLY. This does not import into customer Storage, create
approved tenant rights, call a VTON/GPU provider or assert a new generated try-on.
Only immutable, pinned Git source files from the small allowlisted manifest.
"""
from __future__ import annotations

import argparse
from hashlib import sha1, sha256
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/feature3/openvto_demo_sources_v1.json"
REV = "10140178cdb198ff17ad7b226c432bd63d732fc2"
MAX_BYTES = 3 * 1024 * 1024
ASSET_FILES = frozenset(("model_posture.jpg", "model_avatar.png", "garment_front.jpg"))
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PATH = re.compile(r"^packages/sdk/openvto/assets/(people|avatars|clothes/shirts)/[a-zA-Z0-9_]+[.](jpg|png)$")


class DemoInputDenied(ValueError):
    """The demo fixture is unavailable or was replaced."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DemoInputDenied("Redirected GitHub demo input refused")


def git_blob_sha1(data):
    if type(data) is not bytes:
        raise DemoInputDenied("Binary Git blob required")
    return sha1(b"blob " + str(len(data)).encode("ascii") + bytes((0,)) + data).hexdigest()


def validated_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get("schema") != "retailgrowth.feature3.synthetic-demo-inputs.v1" or (
        manifest.get("source_repository") != "Prompt-Haus/OpenVTO" or
        manifest.get("source_commit") != REV or
        manifest.get("license") != "MIT-demo-assets" or
        manifest.get("license_scope") != "testing-and-demonstration-only" or
        manifest.get("tenant_private") is not False or
        manifest.get("rights_approved_for_customer_publishing") is not False or
        manifest.get("virtual_tryon_generated_by_retailgrowth") is not False
    ):
        raise DemoInputDenied("Untrusted or commercially misrepresented demo manifest")
    f4, f5 = manifest.get("feature4"), manifest.get("feature5")
    if not isinstance(f4, dict) or not isinstance(f5, dict) or (
        f4.get("first_frame") != "model_posture.jpg" or
        f5.get("first_frame") != "model_posture.jpg" or
        f4.get("garment") != "garment_front.jpg" or
        f5.get("garment") != "garment_front.jpg" or
        f4.get("private_client_publish_allowed") is not False or
        f5.get("provider_call_authorized") is not False or
        f5.get("cost_reservation_authorized") is not False
    ):
        raise DemoInputDenied("Demo does not authorize video/publishing or paid inference")
    entries = manifest.get("assets")
    if not isinstance(entries, list) or len(entries) != 3 or (
        {entry.get("file") for entry in entries if isinstance(entry, dict)} != ASSET_FILES
    ):
        raise DemoInputDenied("Missing or unexpected source demo input")
    for a in entries:
        if not isinstance(a, dict) or set(a) != {
            "id", "role", "file", "mime_type", "size_bytes", "git_blob_sha1",
            "source_path", "source_url"
        }:
            raise DemoInputDenied("Invalid source image record")
        path = a["source_path"]
        if not isinstance(path, str) or not PATH.fullmatch(path) or (
            a["file"].endswith(".jpg") != (a["mime_type"] == "image/jpeg") or
            a["file"].endswith(".png") != (a["mime_type"] == "image/png") or
            not isinstance(a["size_bytes"], int) or
            not 100 <= a["size_bytes"] <= MAX_BYTES or
            not isinstance(a["git_blob_sha1"], str) or
            not HEX40.fullmatch(a["git_blob_sha1"])
        ):
            raise DemoInputDenied("Invalid image identity")
        url = a["source_url"]
        expected = "https://raw.githubusercontent.com/Prompt-Haus/OpenVTO/" + REV + "/" + path
        if url != expected or urlsplit(url).hostname != "raw.githubusercontent.com":
            raise DemoInputDenied("Unpinned or foreign image source")
    return manifest


def verify_demo_image(entry, data):
    if type(data) is not bytes or len(data) != entry["size_bytes"] or (
        git_blob_sha1(data) != entry["git_blob_sha1"]
    ):
        raise DemoInputDenied("Pinned demo image content changed")
    try:
        with Image.open(BytesIO(data)) as im:
            expected_format = "PNG" if entry["mime_type"] == "image/png" else "JPEG"
            if (im.format != expected_format or
                getattr(im, "n_frames", 1) != 1 or
                min(im.size) < 256 or max(im.size) > 8192 or
                im.width * im.height > 24_000_000):
                raise DemoInputDenied("Unsafe demo image dimensions or type")
            dimensions = list(im.size)
            im.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError,
            ValueError) as exc:
        raise DemoInputDenied("Image format could not be verified") from exc
    return {"file": entry["file"], "sha256": sha256(data).hexdigest(),
            "git_blob_sha1":entry["git_blob_sha1"], "size_bytes":len(data),
            "dimensions":dimensions,"mime_type":entry["mime_type"]}


def _fetch(url, maximum):
    opener = build_opener(_NoRedirect())
    request = Request(url,headers={"User-Agent":"RetailGrowthAI-Fashion-Demo-Fetch/1.0",
                                   "Accept":"image/png,image/jpeg"})
    with opener.open(request, timeout=25) as res:
        status = getattr(res, "status", 200)
        if status != 200:
            raise DemoInputDenied("No verified public demo source")
        data = res.read(maximum+1)
    if len(data) > maximum:
        raise DemoInputDenied("Oversized demo response")
    return data


def download_demo_inputs(output_dir, *, fetch=_fetch, manifest=None):
    """Materialize source-authenticated demo files; never touch signed tenants.

    Uses strict Git blob identity AND independent SHA256 of received image.
    Injection of fetch is for offline tests only; no mocking of a live download.
    """
    raw = validated_manifest(manifest if manifest is not None else
                             json.loads(SOURCE.read_text("utf-8")))
    folder = Path(output_dir)
    if folder.exists() and any(folder.iterdir()):
        raise DemoInputDenied("Refusing to overwrite existing demo directory")
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    evidence = []
    try:
        for entry in raw["assets"]:
            blob = fetch(entry["source_url"], entry["size_bytes"])
            proof = verify_demo_image(entry, blob)
            path = folder / entry["file"]
            path.write_bytes(blob)
            written.append(path)
            evidence.append(proof)
        package = {
            "schema":"retailgrowth.feature3.demo-input-package.v1",
            "source_repository":raw["source_repository"],
            "source_commit":raw["source_commit"],
            "license":raw["license"],
            "license_scope":raw["license_scope"],
            "tenant_private":False,
            "rights_approved_for_customer_publishing":False,
            "virtual_tryon_generated_by_retailgrowth":False,
            "feature4":raw["feature4"],"feature5":raw["feature5"],
            "files":evidence,
        }
        path=folder/"verified_manifest.json"
        path.write_text(json.dumps(package,indent=2)+"\n",encoding="utf-8")
        written.append(path)
        notice=folder/"SOURCE_AND_RIGHTS_NOTICE.txt"
        notice.write_text(
            "OpenVTO synthetic demo images copyright (c) 2026 Prompt Haus. MIT License.\n"
            "See pinned source https://github.com/Prompt-Haus/OpenVTO/tree/"+REV+"\n"
            "Only test/demo; do not claim customer product ownership, actual try-on,\n"
            "published brand rights or GPU provider output.\n",encoding="utf-8")
        written.append(notice)
        return package
    except BaseException:
        for path in written:
            path.unlink(missing_ok=True)
        raise


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True,help="Fresh workspace for demo JPEG/PNG")
    args=parser.parse_args()
    p=download_demo_inputs(args.output_dir)
    print(json.dumps({"status":"VERIFIED_SYNTHETIC_DEMO_ONLY",
                      "files":[f["file"] for f in p["files"]],
                      "source_commit":p["source_commit"],
                      "paid_inference":False,
                      "customer_publish_approved":False}))


if __name__ == "__main__":
    main()
