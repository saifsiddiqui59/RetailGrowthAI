"""Human inspection workflow for AI virtual try-on fidelity — never auto-certify.

A visual sheet compares only verified, private, same-tenant assets; results are
qualitative human review, not an algorithmic claim that a garment is identical.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from studio_v2 import DesignError, _assets

FEATURES = ("color", "pattern", "neckline", "sleeves", "length", "embroidery")


def build_review_sheet(*, shop_id, garment_asset_id, model_asset_id,
                       manifest, staged_root, output_path, inference_verified=False):
    """Only staged server-authorized garment and synthetic try-on source IDs."""
    if type(inference_verified) is not bool:
        raise DesignError("AI inference verification must be server-derived")
    if not isinstance(manifest, dict) or manifest.get("shop_id") != shop_id:
        raise DesignError("Cross-tenant comparison denied")
    if garment_asset_id == model_asset_id:
        raise DesignError("Comparison requires distinct source and generated assets")
    garment = _assets(manifest, staged_root, shop_id, garment_asset_id)
    model = _assets(manifest, staged_root, shop_id, model_asset_id)
    sheet = Image.new("RGB", (1200, 860), "#F7F4F0")
    draw = ImageDraw.Draw(sheet)
    try:
        regular = ImageFont.truetype("DejaVuSans.ttf", 25)
        heading = ImageFont.truetype("DejaVuSans-Bold.ttf", 29)
    except OSError as exc:
        raise DesignError("DejaVu fonts required for compare sheet") from exc
    for i, (image, heading_text) in enumerate((
        (garment, "UPLOADED GARMENT"),
        (model, "VERIFIED AI OUTPUT — REVIEW" if inference_verified
         else "SYNTHETIC / UNVERIFIED IMAGE"),
    )):
        x = 30 + i * 600
        draw.rounded_rectangle((x, 20, x + 540, 790),
                               radius=18, fill="#FFFFFF")
        draw.text((x + 20, 38), heading_text, font=heading, fill="#191B20")
        thumb = ImageOps.contain(image.convert("RGB"), (500, 665),
                                method=Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (540 - thumb.width) // 2, 100))
    draw.text((35, 803), "AI may change fabric colour, print, neckline, sleeves, length or embroidery.",
              font=regular, fill="#6C2C27")
    path = Path(output_path)
    if path.suffix.lower() != ".png":
        raise DesignError("Review sheet must be a local PNG")
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, "PNG", optimize=True)
    return {"path": str(path), "shop_id": shop_id,
            "source_asset_id": garment_asset_id,
            "try_on_asset_id": model_asset_id,
            "requires_human_review": True, "inference_verified": inference_verified,
            "features": list(FEATURES)}


def validate_review(*, review, shop_id, source_asset_id, output_asset_id):
    """Explicit reviewer decisions, not silent model-based fidelity certification.

    The authenticated reviewer identity and asset lineage must be checked by
    the calling server before storing this record. Human approval is distinct
    from publishing approval; no automated publish or output mutation.
    """
    if not isinstance(review, dict) or set(review) != {
        "shop_id", "source_asset_id", "output_asset_id", "checks",
        "reviewer_confirmation", "notes",
    } or review["shop_id"] != shop_id or review["source_asset_id"] != source_asset_id        or review["output_asset_id"] != output_asset_id:
        raise DesignError("Review cannot target a different shop or asset version")
    checks = review["checks"]
    if not isinstance(checks, dict) or set(checks) != set(FEATURES) or        any(type(value) is not bool for value in checks.values()):
        raise DesignError("Six explicit visual checks are required")
    if type(review["reviewer_confirmation"]) is not bool:
        raise DesignError("Explicit reviewer confirmation required")
    notes = review["notes"]
    if not isinstance(notes, str) or len(notes) > 500 or        any(ord(char) < 32 for char in notes):
        raise DesignError("Invalid review notes")
    approved = review["reviewer_confirmation"] and all(checks.values())
    if not approved and not notes.strip():
        raise DesignError("Rejected or uncertain garment needs a review note")
    return {"status": "HUMAN_REVIEW_PASSED" if approved else "REGENERATION_REQUIRED",
            "human_reviewed": True, "checked_features": list(FEATURES),
            "publish_approved": False,
            "warning": "Garment resemblance was reviewed by a person; "
                       "AI output is not guaranteed identical to the garment."}
