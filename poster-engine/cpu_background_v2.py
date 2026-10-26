"""Feature #3 optional zero-GPU SOLID BACKGROUND product cutout.

This is NOT rembg or AI segmentation. It supports uniformly lit product
packshots only, using simple deterministic Pillow chroma removal. Every output
needs visual human review and explicit registration with private media rights
before any later advertisement is saved or published.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

from studio_v2 import DesignError, _assets


def remove_solid_packshot_background(*, shop_id, asset_id, manifest,
                                     staged_root, output_path, threshold=30):
    if type(threshold) is not int or not 12 <= threshold <= 80:
        raise DesignError("Solid-background tolerance outside safe range")
    if not isinstance(manifest, dict) or manifest.get("shop_id") != shop_id:
        raise DesignError("Cross-tenant product cutout denied")
    source = _assets(manifest, staged_root, shop_id, asset_id)
    if source.width * source.height > 8_000_000:
        raise DesignError("CPU cutout requires a photo no larger than 8MP")
    photo = source.convert("RGB")
    w, h = photo.size
    # Corner patches are a conservative estimate of a flat studio backdrop;
    # do not guess a mask for scenery, patterned fabric or lifestyle photos.
    side = max(2, min(w, h) // 24)
    regions = [
        (0, 0, side, side),
        (w - side, 0, w, side),
        (0, h - side, side, h),
        (w - side, h - side, w, h),
    ]
    colours = [tuple(round(n) for n in ImageStat.Stat(photo.crop(box)).mean)
               for box in regions]
    background = tuple(round(sum(c[i] for c in colours) / 4) for i in range(3))
    variation = max(abs(c[i] - background[i]) for c in colours for i in range(3))
    if variation > 15:
        raise DesignError("Busy/uneven photo background; use licensed segmentation")
    flat = Image.new("RGB", (w, h), background)
    # Channel maximum catches bright red/blue products without weighting them
    # into a gray threshold. No bytes are fetched from remote URLs.
    difference = ImageChops.difference(photo, flat)
    channels = difference.split()
    max_diff = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    mask = max_diff.point(lambda intensity: 255 if intensity > threshold else 0)
    histogram = mask.histogram()
    foreground_ratio = histogram[255] / (w * h)
    if not .03 <= foreground_ratio <= .94:
        raise DesignError("Low-confidence solid-background removal; manual review required")
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.7))
    result = source.copy()
    result.putalpha(ImageChops.multiply(source.getchannel("A"), mask))
    target = Path(output_path)
    if target.suffix.lower() != ".png" or not target.parent.is_dir() or target.exists():
        raise DesignError("Trusted new private PNG output path required")
    result.save(target, format="PNG")
    return {
        "shop_id": shop_id,
        "source_asset_id": asset_id,
        "path": str(target),
        "background_rgb": list(background),
        "foreground_ratio": round(foreground_ratio, 4),
        "method": "cpu-flat-background-v1",
        "ai_inference": False,
        "source_media_registration_required": True,
        "review_required": True,
        "warning": "Background removal can erase garment details similar in color to the backdrop.",
    }
