"""Ultra-low-cost, tenant-checked DRAFT previews for Feature #3.

Keep this distinct from review_export_v2: previews are small Pillow rasters
made BEFORE full-size generation and may wrap fonts differently; they NEVER
satisfy final approval or publication. Server supplies already authorized,
private staged media and current rate/usage gate. No GPU or network.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from studio_v2 import DesignError, FORMATS, render_design, validate_design
from render_workflow_v2 import design_fingerprint

DRAFT_SCALE = .25
MAX_DRAFT_PREVIEW_BYTES = 3 * 1024 * 1024


def render_draft_preview(design, manifest, staged_root, output_path, *,
                         reserve_preview_quota):
    """Prepare one lightweight unapproved preview after an atomic tenant quota gate.

    reserve_preview_quota(shop_id, design_sha) is a server-owned durable,
    idempotent rate-limit operation (it must verify membership and quotas).
    Never permit a client-provided fake callback in a live HTTP handler.
    """
    checked = validate_design(design)
    if not callable(reserve_preview_quota):
        raise DesignError("Authenticated tenant preview budget gate required")
    path = Path(output_path)
    if (path.suffix.lower() != ".png" or not path.parent.is_dir() or
        path.is_symlink() or path.exists()):
        raise DesignError("Draft preview requires a new private PNG output path")
    doc_hash = design_fingerprint(checked)
    if reserve_preview_quota(checked["shop_id"], doc_hash) is not True:
        raise DesignError("Draft preview quota exhausted or tenant not authorized")
    info = render_design(checked, manifest, staged_root, path, scale=DRAFT_SCALE)
    size = path.stat().st_size
    if size <= 100 or size > MAX_DRAFT_PREVIEW_BYTES:
        path.unlink(missing_ok=True)
        raise DesignError("Draft preview exceeded bounded output budget")
    full_width, full_height = FORMATS[checked["format"]]
    return {
        "shop_id": checked["shop_id"],
        "design_sha256": doc_hash,
        "path": str(path),
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "bytes": size,
        "width": info["width"],
        "height": info["height"],
        "full_width": full_width,
        "full_height": full_height,
        "pixel_ratio": round((info["width"] * info["height"]) /
                             (full_width * full_height), 4),
        "inference": False,
        "final_pixel_parity": False,
        "approved": False,
        "preview_only": True,
        "requires_full_resolution_review_before_publishing": True,
    }
