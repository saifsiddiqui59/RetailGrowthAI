"""Feature #3 authoritative CPU poster preview and export parity.

The saved preview is downsampled DIRECTLY from the exact 1080px Pillow export,
not independently rerendered with different font wrapping or CSS/Canvas text.
This does not create private URLs or authorize uploaded media. The caller
must recheck shop media rights and signed output access on every request.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from PIL import Image

from studio_v2 import DesignError, FORMATS, render_design, validate_design
from render_workflow_v2 import design_fingerprint

PREVIEW_BOUND = 432


def create_review_pair(design, manifest, staged_root, destination, *,
                       preview_long_edge=PREVIEW_BOUND):
    """Render an immutable, pixel-derived review copy and full-resolution PNG.

    Output directory is an already trusted per-job private scratch directory.
    The caller must upload both outputs via scoped, immutable private storage.
    This source-only helper never creates a public URL or approves publishing.
    """
    checked = validate_design(design)
    if (type(preview_long_edge) is not int
        or not 128 <= preview_long_edge <= PREVIEW_BOUND):
        raise DesignError("Preview dimension must be bounded")
    folder = Path(destination)
    if not folder.is_dir() or folder.is_symlink():
        raise DesignError("Trusted private output folder required")
    full = folder / "poster-final.png"
    preview = folder / "poster-review-preview.png"
    if full.exists() or preview.exists():
        raise DesignError("Review outputs must not overwrite existing files")
    result = render_design(checked, manifest, staged_root, full)
    try:
        with Image.open(full) as source:
            if source.format != "PNG" or source.size != FORMATS[checked["format"]]:
                raise DesignError("Authoritative Pillow render size mismatch")
            source.load()
            thumb = source.copy()
            thumb.thumbnail((preview_long_edge, preview_long_edge),
                            Image.Resampling.LANCZOS)
            # Store a single RGB preview. It is a review image derived from
            # the original final pixels, never a separate web canvas render.
            thumb.convert("RGB").save(preview, format="PNG", optimize=True)
        return {
            "shop_id": checked["shop_id"],
            "schema": checked["schema"],
            "design_sha256": design_fingerprint(checked),
            "final_path": str(full),
            "preview_path": str(preview),
            "final_sha256": sha256(full.read_bytes()).hexdigest(),
            "preview_sha256": sha256(preview.read_bytes()).hexdigest(),
            "dimensions": list(FORMATS[checked["format"]]),
            "preview_dimensions": list(Image.open(preview).size),
            "preview_derived_from_final": True,
            "requires_explicit_review": True,
            "approved": False,
        }
    except BaseException:
        # Partial or ambiguous preview must not be published as complete.
        preview.unlink(missing_ok=True)
        full.unlink(missing_ok=True)
        raise


def verify_review_approval(*, receipt, reviewed_final_sha256, expected_shop_id,
                           expected_design_sha256):
    """Compare a human-reviewed frozen binary hash against immutable output.

    This function does NOT create an approval: a separate authenticated
    OWNER/EDITOR approval RPC must record the review and authorize publishing.
    """
    if not isinstance(receipt, dict) or receipt.get("shop_id") != expected_shop_id:
        raise DesignError("Cross-tenant or missing poster review receipt")
    if (receipt.get("approved") is not False
        or receipt.get("requires_explicit_review") is not True
        or receipt.get("preview_derived_from_final") is not True):
        raise DesignError("Invalid or previously approved review receipt")
    if (not isinstance(reviewed_final_sha256, str)
        or len(reviewed_final_sha256) != 64
        or receipt.get("final_sha256") != reviewed_final_sha256
        or receipt.get("design_sha256") != expected_design_sha256):
        raise DesignError("Poster design or final pixels changed after review")
    return {
        "shop_id": expected_shop_id,
        "design_sha256": expected_design_sha256,
        "verified_final_sha256": reviewed_final_sha256,
        "ready_for_authenticated_approval": True,
        "published": False,
    }
