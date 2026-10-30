"""Private, zero-GPU visual-review pilot for source-pinned OpenPeople stills.

This is an operator-side review aid, NOT license clearance, a SaaS image
catalog, a signed customer preview or a production image import.
Requires exact browser review packets and genuine locally staged Git objects.
Creates a marked contact sheet and an unapproved provenance receipt in a
new mode-0700 local directory; it never downloads or uploads third-party media.
"""
from __future__ import annotations

from hashlib import sha1, sha256
from io import BytesIO
from pathlib import Path
import json
import os

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from model_library_v2 import ModelLibraryDenied
from openpeople_import_v2 import OpenPeopleSelection, MAX_INPUT_BYTES
from openpeople_indian_review_v2 import parse_review_packet_file

_CANONICAL_ROOT = Path('openpeople/data/curated')
_KINDS = frozenset({'studio_posture', 'studio_portrait'})


def read_verified_still(selection: OpenPeopleSelection) -> bytes:
    """Read only an exact hash-pinned JPG from a private staged checkout.

    This intentionally duplicates the import-time integrity check: operator
    review cannot silently accept swapped images or an unpinned source.
    Import later re-verifies rights and bytes independently.
    """
    if not isinstance(selection, OpenPeopleSelection):
        raise ModelLibraryDenied('Trusted source selection required')
    from openpeople_indian_review_v2 import CANDIDATES, UPSTREAM_REVISION
    candidate = CANDIDATES.get(selection.person_id)
    kind_index = {'studio_posture': 2, 'studio_portrait': 3}.get(selection.image_kind)
    if (candidate is None or kind_index is None or
            selection.source_revision != UPSTREAM_REVISION or
            candidate[kind_index] != selection.expected_image_git_blob_sha):
        raise ModelLibraryDenied('Selection is not on the immutable pilot allowlist')
    root = Path(selection.dataset_root)
    if not root.is_dir() or root.is_symlink():
        raise ModelLibraryDenied('Private staged source directory required')
    rel = _CANONICAL_ROOT / selection.person_id / 'assets' / (selection.image_kind + '.jpg')
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ModelLibraryDenied('Symlinked staged source is not permitted')
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ModelLibraryDenied('Source JPEG missing or too large')
    content = path.read_bytes()
    git_sha = sha1(b'blob ' + str(len(content)).encode('ascii') + b'\0' + content).hexdigest()
    if git_sha != selection.expected_image_git_blob_sha:
        raise ModelLibraryDenied('Staged image does not match pinned upstream Git blob')
    return content


def _write_private(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_contact_sheet(rows: list[tuple[dict, bytes]], out_dir: Path) -> dict:
    """Render exact staged JPG pixels, visibly flagged as UNAPPROVED."""
    if not 1 <= len(rows) <= 3:
        raise ModelLibraryDenied('Pilot review must contain 1-3 source stills')
    width, tile_h, pad = 400, 450, 24
    sheet = Image.new('RGB', (width * len(rows), tile_h), '#f1f1f1')
    draw = ImageDraw.Draw(sheet)
    records = []
    for n, (packet, raw) in enumerate(rows):
        try:
            with Image.open(BytesIO(raw)) as image:
                if (image.format != 'JPEG' or getattr(image, 'n_frames', 1) != 1 or
                        image.width < 256 or image.height < 256 or
                        image.width * image.height > 24_000_000):
                    raise ModelLibraryDenied('Invalid image format/size for pilot')
                image.load()
                w, h = image.size
                thumb = ImageOps.contain(image.convert('RGB'), (width - 2 * pad, 365))
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise ModelLibraryDenied('Cannot decode source JPG safely') from exc
        x = width * n
        sheet.paste(thumb, (x + (width - thumb.width) // 2, 48 + (365 - thumb.height) // 2))
        draw.text((x + pad, 14), f"{packet['person_id']} / {packet['image_kind']}", fill='#111111')
        draw.rectangle((x, tile_h - 35, x + width - 1, tile_h), fill='#a51f1f')
        draw.text((x + pad, tile_h - 26), 'UNAPPROVED - PRIVATE SOURCE REVIEW', fill='white')
        records.append({
            'person_id': packet['person_id'], 'image_kind': packet['image_kind'],
            'git_blob_sha1': packet['image_git_blob_sha'],
            'source_jpg_sha256': sha256(raw).hexdigest(),
            'source_width': w, 'source_height': h,
            'source_url': packet['source_url'],
            'rights_verified': False, 'quality_approved': False,
            'ad_suitability_approved': False,
            'likeness_reviewed': False, 'eligible_for_library_import': False,
        })
    encoded = BytesIO()
    sheet.save(encoded, format='PNG')
    _write_private(out_dir / 'pilot-contact-sheet-UNAPPROVED.png', encoded.getvalue())
    result = {
        'schema': 'retailgrowth.openpeople-private-pilot-review.v1',
        'status': 'UNAPPROVED_PRIVATE_REVIEW_ONLY',
        'commercial_rights_cleared': False,
        'ready_for_cloud_import': False,
        'source_asset_count': len(records),
        'source_assets': records,
        'contact_sheet_sha256': sha256(encoded.getvalue()).hexdigest(),
        'required_human_checks': [
            'Commercial image and underlying provider redistribution/advertising terms',
            'CC BY 4.0 attribution and downstream asset licensing',
            'Photorealism, anatomy, hands, eyes and fashion suitability',
            'Synthetic-face accidental likeness and apparent adult age',
            'Pose/crop and source garment obstruction for try-on',
        ],
        'generation_gpu_calls': 0,
    }
    _write_private(out_dir / 'pilot-review-UNAPPROVED.json',
                   (json.dumps(result, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    return result


def build_private_pilot_review(raw_packets, *, dataset_root, output_dir):
    """Consume 1-3 browser packets; no caller-supplied hash override accepted."""
    if not isinstance(raw_packets, (list, tuple)) or not 1 <= len(raw_packets) <= 3:
        raise ModelLibraryDenied('Review at most three distinct pinned stills')
    seen = set()
    rows = []
    for raw_packet in raw_packets:
        selection = parse_review_packet_file(raw_packet, dataset_root=dataset_root)
        key = (selection.person_id, selection.image_kind)
        if key in seen:
            raise ModelLibraryDenied('Duplicate source still in one pilot')
        seen.add(key)
        image = read_verified_still(selection)
        packet = json.loads(raw_packet)
        rows.append((packet, image))
    out_dir = Path(output_dir)
    if out_dir.is_symlink() or out_dir.exists():
        raise ModelLibraryDenied('New, private output directory required; do not overwrite reviews')
    out_dir.mkdir(mode=0o700)
    try:
        return _write_contact_sheet(rows, out_dir)
    except BaseException:
        for p in out_dir.iterdir():
            p.unlink()
        out_dir.rmdir()
        raise
