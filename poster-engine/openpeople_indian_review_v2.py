"""Authoritative offline review packet validator for Indian-themed OpenPeople.

The browser exports an *untrusted* review request. It NEVER constitutes license
permission, human approval, upload permission or access to another retailer.
This module pins candidate source/profile and expected Git blobs independently
of browser code and rejects altered status/rights/URL/hash/metadata.

The downstream import still requires trusted operator license and tenant
callbacks, and validates exact local JPEG Git object bytes before registering
an immutable private asset. No network, GPU or SaaS backend deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import json

from model_library_v2 import ModelLibraryDenied
from openpeople_import_v2 import OpenPeopleSelection

UPSTREAM_REVISION = "231f73aa43b32a38001759944baa01d7d154ce26"
UPSTREAM_REPO = "Prompt-Haus/OpenPeople"
SOURCE_LICENSE_CLAIM = "CC-BY-4.0"
STATUS = "PENDING_SOURCE_AND_IMAGE_LICENSE_REVIEW"

# GitHub exact tree: https://github.com/Prompt-Haus/OpenPeople/tree/<revision>
# Descriptions are SYNTHETIC SOURCE PROMPT fields, NOT actual nationality.
CANDIDATES = {
    "P009": ("88% Indian, 12% Western Latin American", "182cae68986ef8a42ad21f554ebbb38a1735b400",
             "c5f3072519fe7818eca529f7be1f33d30d16ad5e", "882f15e631e1a5b6f698ae9afbb781d69154e4f4"),
    "P006": ("80% South Indian, 20% East African", "000ad8d9e024d8164d02f75c1876da52f64f38ca",
             "c84d6cb84b50a7cbfb40c3449899f4b8b5c19294", "f6bcb8edf8b25ba0e32dee57e0d4feb6e35a8e25"),
    "P079": ("58% Eastern Indian, 42% South Asian", "e887cdd8cb1c0f834cc62a1c80b2be79f0f6335c",
             "0a73a528e971efbb25e3a4db540d8e52beaa3ba3", "e900b302e1b8c98d6edeb2727c01909593e7fdfe"),
    "P033": ("39% Middle Eastern, 61% Indian", "aec47efd099bd366d0e0a6d8d90c20f92706df75",
             "0206fd10a6a404355bdbfb6e103cabfa27cbe9b8", "774db25015e0149b2781100bd1632e17d7b752a3"),
    "P054": ("54% Central Indian, 46% Middle Eastern", "89ff26b4c9073ce6be13374be13c310adb3d1257",
             "cba1ac62784adaf4a36e74e0e4ca9bfcb758e11d", "e077734482ebc8a087a5154873d2324208ae112e"),
    "P059": ("81% Indian, 19% American", "022e568318d10967e91bb3c4cd37154a6a299dff",
             "2bb4f9a5eba0fc6625287b7bfcdfaba1ad60e5ba", "3297950b3e91a1b612d74622df6d24d492ff01c4"),
    "P025": ("12% Hispanic, 88% Central Indian", "06674584533b0cdd0dc4abb34d8053cb500c40bb",
             "dc3873aa3ed41e2b3a732924e13521ce6c5b3035", "addd285e41b2f14a526d8f2ed973dd5403f4eca9"),
    "P016": ("71% East Indian, 29% East Australian", "badde612f57bb41ef8f9887f400ef821b2fb3e95",
             "7e14b4625cbb6a575f7b124dab0681f267f2a1d9", "db7d20829340a7130537b945f30700aa71f5e8d6"),
}

KINDS = {"studio_posture": 2, "studio_portrait": 3}


def expected_review_packet(person_id, image_kind):
    item = CANDIDATES.get(person_id)
    if item is None or image_kind not in KINDS:
        raise ModelLibraryDenied("Unrecognized licensed-source review candidate")
    source = ("https://github.com/" + UPSTREAM_REPO + "/blob/" +
              UPSTREAM_REVISION + "/openpeople/data/curated/" + person_id +
              "/assets/" + image_kind + ".jpg")
    return {
        "schema": "retailgrowth.model-review-request.v1",
        "source_repository": UPSTREAM_REPO,
        "source_revision": UPSTREAM_REVISION,
        "person_id": person_id,
        "image_kind": image_kind,
        "image_git_blob_sha": item[KINDS[image_kind]],
        "metadata_git_blob_sha": item[1],
        "source_url": source,
        "attribution": "OpenPeople by Prompt Haus — CC BY 4.0 (source claim; verify)",
        "source_license_claim": SOURCE_LICENSE_CLAIM,
        "source_profile_description": item[0],
        "source_profile_is_synthetic": True,
        "status": STATUS,
        "licensed_for_retailgrowth": False,
        "rights_evidence_verified": False,
        "visual_quality_approved": False,
        "commercially_reusable": False,
        "saved_to_private_library": False,
        "approved": False,
        "published": False,
        "generation_gpu_calls": 0,
    }


def validate_review_packet(packet, *, dataset_root):
    """Verify each field EXACTLY, then return a locked local import selection.

    A successful verification only means the request matches a known pinned
    source identity. Real asset commercial approval still requires the separate
    independent operator calls in import_openpeople_still().
    """
    if not isinstance(packet, dict):
        raise ModelLibraryDenied("Structured curator review request required")
    person_id = packet.get("person_id")
    kind = packet.get("image_kind")
    try:
        expected = expected_review_packet(person_id, kind)
    except (TypeError, ValueError, ModelLibraryDenied) as exc:
        raise ModelLibraryDenied("Unsupported source candidate") from exc
    # Exact mapping comparison fails if any approval boolean is changed,
    # source commit/hash is changed, hidden extra field is added, or names
    # are tampered with. Avoid list/schema interpretation or URL downloads.
    if packet != expected or any(type(packet[k]) is not type(v)
                                 for k, v in expected.items()):
        raise ModelLibraryDenied("Source packet differs from reviewed pinned catalog")
    if not isinstance(dataset_root, (str, Path)):
        raise ModelLibraryDenied("Trusted private staged source path required")
    return OpenPeopleSelection(
        dataset_root=Path(dataset_root),
        source_revision=UPSTREAM_REVISION,
        person_id=person_id,
        image_kind=kind,
        expected_image_git_blob_sha=expected["image_git_blob_sha"],
    )


def parse_review_packet_file(raw_json, *, dataset_root):
    if not isinstance(raw_json, (str, bytes)) or len(raw_json) > 6000:
        raise ModelLibraryDenied("Bounded curator review packet required")
    try:
        packet = json.loads(raw_json)
    except (ValueError, UnicodeError) as exc:
        raise ModelLibraryDenied("Invalid review packet JSON") from exc
    return validate_review_packet(packet, dataset_root=dataset_root)
