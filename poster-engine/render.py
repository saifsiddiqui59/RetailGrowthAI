#!/usr/bin/env python3
"""Offline, tenant-scoped promotional PNG renderer for RetailGrowthAI Part 1.

Caller must validate Supabase/RLS authorization BEFORE staging local asset bytes.
This second boundary validates shop/campaign ownership, rights, paths and input.
No network calls, hosted writes, publishing or implicit promotional discounts.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

RESOLUTIONS = {"square": (1080, 1080), "portrait": (1080, 1350)}
TEMPLATES = frozenset({"editorial", "bold", "minimal"})
COMMERCIAL_LICENSES = frozenset({"owned", "cc0", "royalty_free", "commercial"})
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
ASSET_ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class PosterError(ValueError):
    """Unsafe, invalid or unsupported poster input."""


def _text(value, field, max_len, *, required=True):
    if not isinstance(value, str) or len(value) > max_len:
        raise PosterError(f"{field}: expected text up to {max_len} characters")
    cleaned = value.strip()
    if required and not cleaned:
        raise PosterError(f"{field}: text is required")
    if any(ord(c) < 32 and c != "\n" for c in cleaned):
        raise PosterError(f"{field}: control characters are forbidden")
    return cleaned


def _color(value, field):
    if not isinstance(value, str) or not COLOR.fullmatch(value):
        raise PosterError(f"{field}: expected #RRGGBB")
    return value


def _asset(manifest, root, asset_id, shop_id, *, allow_test_media=False):
    if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
        raise PosterError("Invalid asset ID")
    records = manifest.get("assets")
    record = records.get(asset_id) if isinstance(records, dict) else None
    if not isinstance(record, dict) or record.get("kind") != "image":
        raise PosterError("Image asset ID is not in the authorized manifest")
    if record.get("shop_id", shop_id) != shop_id:
        raise PosterError("Asset belongs to a different shop")
    rights = record.get("rights")
    valid_licenses = COMMERCIAL_LICENSES | ({"synthetic_test"} if allow_test_media else set())
    if (not isinstance(rights, dict) or rights.get("commercial_use") is not True
            or rights.get("license") not in valid_licenses
            or not isinstance(rights.get("source"), str) or not rights["source"].strip()
            or not isinstance(rights.get("evidence"), str) or not rights["evidence"].strip()):
        raise PosterError("Commercial use and asset-rights evidence are required")
    relative = record.get("path")
    if (not isinstance(relative, str) or not relative or "://" in relative
            or "\\" in relative or Path(relative).is_absolute()):
        raise PosterError("Assets must have a server-staged relative file path")
    root = Path(root).resolve(strict=True)
    try:
        path = (root / relative).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PosterError("Staged asset is missing") from exc
    if not path.is_relative_to(root) or not path.is_file():
        raise PosterError("Asset path escapes the staging root")
    if path.suffix.lower() not in IMAGE_EXTENSIONS or not 0 < path.stat().st_size <= MAX_IMAGE_BYTES:
        raise PosterError("Image extension or size is unsupported")
    try:
        with Image.open(path) as opened:
            if opened.width * opened.height > MAX_IMAGE_PIXELS or opened.width < 32 or opened.height < 32:
                raise PosterError("Image dimensions out of range")
            if getattr(opened, "n_frames", 1) != 1:
                raise PosterError("Animated assets are unsupported")
            return ImageOps.exif_transpose(opened).convert("RGBA")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise PosterError("Unreadable or unsafe staged image") from exc


def _font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size=size)
    except OSError as exc:
        raise PosterError("DejaVu Sans font is required in the render runtime") from exc


def _wrap(draw, text, font, max_width, max_lines=4):
    words = text.split()
    if not words:
        return []
    lines = []
    current = ""
    for word in words:
        proposal = f"{current} {word}".strip()
        if draw.textbbox((0, 0), proposal, font=font)[2] <= max_width:
            current = proposal
            continue
        if current:
            lines.append(current)
            current = word
        else:
            prefix = ""
            for char in word:
                if draw.textbbox((0, 0), prefix + char + "…", font=font)[2] > max_width:
                    break
                prefix += char
            lines.append(prefix + "…")
            current = ""
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        raise PosterError("Text does not fit the requested width")
    if " ".join(lines).replace("…", "").strip() != text.strip():
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + "…", font=font)[2] > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip(" .") + "…"
    return lines


def _lines(draw, text, position, font, color, max_width, max_lines=4, spacing=13):
    x, y = position
    for line in _wrap(draw, text, font, max_width, max_lines):
        draw.text((x, y), line, fill=color, font=font)
        y += font.size + spacing
    return y


def _fit_image(image, size):
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))


def _contrast_text(color):
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return "#171921" if 0.2126 * r + 0.7152 * g + 0.0722 * b >= 0.56 else "#FFFFFF"


def _validate_context(campaign, manifest, day_index):
    if not isinstance(campaign, dict) or not isinstance(manifest, dict):
        raise PosterError("Campaign and manifest must be objects")
    shop_id, campaign_id = campaign.get("shop_id"), campaign.get("id")
    if not isinstance(shop_id, str) or not shop_id or not isinstance(campaign_id, str) or not campaign_id:
        raise PosterError("Campaign identifiers are required")
    if manifest.get("shop_id") != shop_id:
        raise PosterError("Cross-tenant manifest rejected")
    days = campaign.get("days")
    if not isinstance(days, list) or type(day_index) is not int:
        raise PosterError("Invalid campaign day list or index")
    matches = [d for d in days if isinstance(d, dict) and d.get("day_index") == day_index]
    if len(matches) != 1:
        raise PosterError("Exactly one matching day index required")
    day = matches[0]
    if day.get("shop_id") != shop_id or day.get("campaign_id") != campaign_id:
        raise PosterError("Cross-campaign or cross-shop day rejected")
    if campaign.get("status") != "DRAFT" or day.get("review_status") != "DRAFT":
        raise PosterError("Only unapproved campaign drafts may be rendered")
    return shop_id, day


@dataclass(frozen=True)
class PosterOptions:
    template: str = "editorial"
    size: str = "square"
    accent: str = "#C36F4A"
    background: str = "#F9F3E8"
    business_name: str = "Retailer"
    offer_text: str | None = None
    product_asset_id: str | None = None
    logo_asset_id: str | None = None


def render_poster(campaign, manifest, asset_root, day_index, output, options=None, *, allow_test_media=False):
    """Produce reviewable offline PNG; never registers media or publishes it."""
    options = options or PosterOptions()
    if not isinstance(options, PosterOptions):
        raise PosterError("Expected PosterOptions")
    if options.template not in TEMPLATES or options.size not in RESOLUTIONS:
        raise PosterError("Unsupported template or aspect ratio")
    accent, background = _color(options.accent, "accent"), _color(options.background, "background")
    brand = _text(options.business_name, "business_name", 70)
    offer = _text(options.offer_text, "offer_text", 110) if options.offer_text is not None else None
    shop_id, day = _validate_context(campaign, manifest, day_index)
    title = _text(day.get("topic"), "day.topic", 140)
    reel = day.get("instagram", {}).get("reel", {})
    cta = _text(reel.get("cta"), "instagram.reel.cta", 110)
    storyboard = reel.get("storyboard")
    if not isinstance(storyboard, list) or not storyboard:
        raise PosterError("Draft must contain staged storyboard media")
    referenced = [segment.get("asset_id") for segment in storyboard if isinstance(segment, dict)]
    source_id = options.product_asset_id or referenced[0]
    if source_id not in referenced:
        raise PosterError("Product media must come from this campaign day")
    photo = _asset(manifest, asset_root, source_id, shop_id, allow_test_media=allow_test_media)
    logo = (_asset(manifest, asset_root, options.logo_asset_id, shop_id, allow_test_media=allow_test_media)
            if options.logo_asset_id else None)
    w, h = RESOLUTIONS[options.size]
    canvas = Image.new("RGB", (w, h), background)
    draw = ImageDraw.Draw(canvas)
    ink = _contrast_text(background)
    margin = 74
    if options.template == "editorial":
        top = 145
        photo_h = round(h * 0.49)
        canvas.paste(_fit_image(photo, (w - 2 * margin, photo_h)).convert("RGB"), (margin, top))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((margin, 112, margin + 91, 121), fill=accent)
        draw.text((margin + 111, 92), brand.upper()[:35], fill=ink, font=_font(28, True))
        ty = _lines(draw, title, (margin, top + photo_h + 36), _font(58, True), ink,
                    w - 2 * margin, 2, 11)
        if offer:
            _lines(draw, offer, (margin, ty + 5), _font(31, True), accent,
                   w - 2 * margin, 2, 8)
        footer_y = h - 113
        draw.rounded_rectangle((margin, footer_y, w - margin, h - 49), radius=22, fill=accent)
        draw.text((margin + 27, footer_y + 17), cta[:56],
                  fill=_contrast_text(accent), font=_font(28, True))
    elif options.template == "bold":
        photo_h = round(h * 0.57)
        canvas.paste(_fit_image(photo, (w, photo_h)).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, photo_h, w, h), fill=accent)
        draw.rounded_rectangle((margin, 56, margin + 440, 111), radius=21, fill=background)
        draw.text((margin + 21, 67), brand.upper()[:24], fill=ink, font=_font(24, True))
        y = _lines(draw, title, (margin, photo_h + 53), _font(64, True),
                   _contrast_text(accent), w - 2 * margin, 3, 9)
        if offer:
            _lines(draw, offer, (margin, y + 7), _font(32, True),
                   _contrast_text(accent), w - 2 * margin, 2, 10)
        draw.rectangle((margin, h - 126, margin + 90, h - 118), fill=background)
        draw.text((margin, h - 108), cta[:60], fill=_contrast_text(accent), font=_font(28))
    else:
        draw.rectangle((margin, 82, w - margin, 85), fill=accent)
        draw.text((margin, 106), brand.upper()[:33], fill=ink, font=_font(30, True))
        photo_top = 200
        photo_h = round(h * 0.50)
        canvas.paste(_fit_image(photo, (w - 2 * margin, photo_h)).convert("RGB"),
                     (margin, photo_top))
        draw = ImageDraw.Draw(canvas)
        y = _lines(draw, title, (margin, photo_top + photo_h + 34), _font(50, True),
                   ink, w - 2 * margin, 2, 10)
        if offer:
            _lines(draw, offer, (margin, y + 12), _font(31), accent,
                   w - 2 * margin, 2, 8)
        draw.rectangle((margin, h - 106, w - margin, h - 103), fill=accent)
        draw.text((margin, h - 89), cta[:65], fill=ink, font=_font(29))
    if logo:
        thumb = logo.copy()
        thumb.thumbnail((118, 118), Image.Resampling.LANCZOS)
        plate = Image.new("RGBA", (thumb.width + 22, thumb.height + 22), "#FFFFFF")
        plate.alpha_composite(thumb, (11, 11))
        px, py = w - margin - plate.width, 32 if options.template == "bold" else 18
        canvas.paste(plate.convert("RGB"), (px, py))
    target = Path(output)
    if target.suffix.lower() != ".png":
        raise PosterError("Poster output must be .png")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=True)
    return {"path": str(target), "width": w, "height": h, "template": options.template,
            "shop_id": shop_id, "day_index": day_index, "source_asset_id": source_id}


def main():
    parser = argparse.ArgumentParser(description="Render an offline RetailGrowthAI poster PNG")
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--day", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--business", required=True)
    parser.add_argument("--template", choices=sorted(TEMPLATES), default="editorial")
    parser.add_argument("--size", choices=sorted(RESOLUTIONS), default="square")
    parser.add_argument("--accent", default="#C36F4A")
    parser.add_argument("--background", default="#F9F3E8")
    parser.add_argument("--offer", default=None, help="Explicit human-approved offer only")
    parser.add_argument("--product-asset-id")
    parser.add_argument("--logo-asset-id")
    args = parser.parse_args()
    result = render_poster(json.loads(args.campaign.read_text(encoding="utf8")),
                           json.loads(args.manifest.read_text(encoding="utf8")),
                           args.asset_root, args.day, args.output,
                           PosterOptions(args.template, args.size, args.accent, args.background,
                                         args.business, args.offer, args.product_asset_id, args.logo_asset_id))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
