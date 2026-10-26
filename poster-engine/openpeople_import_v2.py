"""Optional offline OpenPeople synthetic-character importer for Feature 3.

OpenPeople README identifies *images* as CC-BY 4.0, separate from MIT code.
No commercial-use approval is inferred from the README alone. An independent
rights curator/license review must still approve each asset and attribution.

The caller stages an exact approved repository snapshot locally; this adapter
NEVER clones repositories, downloads models, accesses the network, starts GPU,
or registers an unapproved user as the platform curator.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import re

from model_library_v2 import ModelCandidate, ModelLibraryDenied, import_model_image

_REVISIONS = re.compile(r"^[a-f0-9]{40}$")
_BLOB_SHA = re.compile(r"^[a-f0-9]{40}$")
_PERSON = re.compile(r"^P[0-9]{3}$")
_ASSETS = {
    "studio_posture": ("studio_posture.jpg", "full_body"),
    "studio_portrait": ("studio_portrait.jpg", "portrait"),
    "amateur_posture": ("amateur_posture.jpg", "full_body"),
    "amateur_selfie": ("amateur_selfie.jpg", "portrait"),
}
MAX_INPUT_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class OpenPeopleSelection:
    """A single still from a locally staged, immutable upstream repository."""
    dataset_root: Path
    source_revision: str
    person_id: str
    image_kind: str = "studio_posture"
    expected_image_git_blob_sha: str = ""


def import_openpeople_still(*, selection, owner_shop_id, scope,
                            license_evidence_sha256, source_rights_reviewed,
                            authorize_import, verify_image_license,
                            write_private_png, register_model):
    if not isinstance(selection, OpenPeopleSelection):
        raise ModelLibraryDenied("Pinned local OpenPeople selection required")
    if (not isinstance(selection.source_revision, str)
        or not _REVISIONS.fullmatch(selection.source_revision)
        or not isinstance(selection.person_id, str)
        or not _PERSON.fullmatch(selection.person_id)
        or not 1 <= int(selection.person_id[1:]) <= 100
        or selection.image_kind not in _ASSETS
        or not isinstance(selection.expected_image_git_blob_sha, str)
        or not _BLOB_SHA.fullmatch(selection.expected_image_git_blob_sha)):
        raise ModelLibraryDenied("Invalid pinned OpenPeople identity or approved still type")
    if source_rights_reviewed is not True:
        raise ModelLibraryDenied("Independent asset license/attribution review required")
    root = Path(selection.dataset_root)
    if not root.is_dir() or root.is_symlink():
        raise ModelLibraryDenied("An already staged private dataset directory is required")
    name, pose = _ASSETS[selection.image_kind]
    relative = (Path("openpeople") / "data" / "curated" /
                selection.person_id / "assets" / name)
    full_path = root / relative
    # Reject symlinked path components, even if the final resolved path lies
    # within the checkout. No arbitrary filenames or thumbnails are accepted.
    scan = root
    for element in relative.parts:
        scan = scan / element
        if scan.is_symlink():
            raise ModelLibraryDenied("Linked source files/directories are not allowed")
    if not full_path.is_file() or full_path.stat().st_size > MAX_INPUT_BYTES:
        raise ModelLibraryDenied("Pinned OpenPeople photo is missing or oversized")
    content = full_path.read_bytes()
    # Exact Git object-byte check against independently reviewed upstream
    # tree: pinned COMMIT ALONE does not authenticate loose local JPG bytes.
    git_blob = sha1(b"blob " + str(len(content)).encode("ascii") +
                    bytes([0]) + content).hexdigest()
    if git_blob != selection.expected_image_git_blob_sha:
        raise ModelLibraryDenied("Staged source image differs from pinned Git blob")
    source = ("https://github.com/Prompt-Haus/OpenPeople/blob/" +
              selection.source_revision + "/" + relative.as_posix())
    model = ModelCandidate(
        owner_shop_id=owner_shop_id,
        scope=scope,
        source_kind="opensource_render",
        source_uri=source,
        license_id="CC-BY-4.0",
        license_evidence_sha256=license_evidence_sha256,
        synthetic_adult=True,
        third_party_assets_cleared=True,  # Rechecked by trusted rights callback.
        label=f"OpenPeople {selection.person_id} {selection.image_kind}",
        pose=pose,
        attribution="OpenPeople by Prompt Haus — CC BY 4.0",
    )
    return import_model_image(
        candidate=model,
        image_bytes=content,
        authorize_import=authorize_import,
        verify_image_license=verify_image_license,
        write_private_png=write_private_png,
        register_model=register_model,
    )
