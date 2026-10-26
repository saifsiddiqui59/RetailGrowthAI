"""Feature #3 additive CPU design contract; existing Part 1 APIs remain unchanged.

No browser URLs, AI inference, migration or upload occurs here. Image layers
resolve exclusively through the existing rights-verified staged asset manifest.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps

SCHEMA = "retailgrowth.poster.v2"
FORMATS = {"square": (1080, 1080), "portrait": (1080, 1350), "story": (1080, 1920)}
TEMPLATES = ("fashion", "luxury", "streetwear", "ethnic", "festival",
             "restaurant", "general", "new_arrivals", "clearance", "seasonal")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
MAX_LAYERS = 24


class DesignError(ValueError):
    pass


def _text(value, length=140, required=True):
    if not isinstance(value, str) or len(value) > length:
        raise DesignError("Invalid text length")
    value = value.strip()
    if (required and not value) or any(ord(char) < 32 for char in value):
        raise DesignError("Empty or unsafe text")
    return value


def _color(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise DesignError("Invalid hex color")
    return value


def _norm(value):
    if type(value) not in (int, float) or not 0 <= value <= 1:
        raise DesignError("Invalid normalized coordinate")
    return float(value)


def validate_design(raw):
    """Fail closed on unknown keys/types; do not trust browser-saved JSON."""
    if not isinstance(raw, dict) or set(raw) != {
        "schema", "shop_id", "format", "template", "background", "layers"
    } or raw["schema"] != SCHEMA:
        raise DesignError("Invalid versioned poster document")
    shop = _text(raw["shop_id"], 100)
    if not ID.fullmatch(shop):
        raise DesignError("Invalid tenant ID")
    if raw["format"] not in FORMATS or raw["template"] not in TEMPLATES:
        raise DesignError("Unsupported poster template or format")
    background = _color(raw["background"])
    layers = raw["layers"]
    if not isinstance(layers, list) or not 1 <= len(layers) <= MAX_LAYERS:
        raise DesignError("Invalid layer count")
    checked, seen = [], set()
    for layer in layers:
        if not isinstance(layer, dict) or layer.get("type") not in ("text", "image", "rect"):
            raise DesignError("Invalid layer")
        expected = {"id", "type", "x", "y", "w", "h"}
        if layer["type"] == "text":
            expected |= {"text", "color", "font_size", "bold"}
        elif layer["type"] == "rect":
            expected |= {"color"}
        else:
            expected |= {"asset_id"}
        if set(layer) != expected:
            raise DesignError("Unknown or missing layer properties")
        lid = _text(layer["id"], 48)
        if not ID.fullmatch(lid) or lid in seen:
            raise DesignError("Duplicate or unsafe layer ID")
        seen.add(lid)
        x, y, w, h = (_norm(layer[k]) for k in ("x", "y", "w", "h"))
        if w < .01 or h < .01 or x + w > 1.00001 or y + h > 1.00001:
            raise DesignError("Layer extends outside the poster")
        part = dict(layer)
        if layer["type"] == "text":
            part["text"] = _text(layer["text"], 160)
            part["color"] = _color(layer["color"])
            if type(layer["font_size"]) is not int or not 12 <= layer["font_size"] <= 150:
                raise DesignError("Invalid font size")
            if type(layer["bold"]) is not bool:
                raise DesignError("Invalid font weight")
        elif layer["type"] == "rect":
            part["color"] = _color(layer["color"])
        else:
            if not isinstance(layer["asset_id"], str) or not ID.fullmatch(layer["asset_id"]):
                raise DesignError("Image must use a trusted asset ID")
        checked.append(part)
    return {**raw, "shop_id": shop, "background": background, "layers": checked}


def compose_poster(*, shop_id, mode, prompt, business_name, headline=None,
                   cta="Visit our store", approved_offer=None, source_asset_id=None,
                   template=None, format="square", logo_asset_id=None, accent="#C05F43",
                   background="#FCF4EC"):
    """Deterministic text/image-to-poster; no offer or price is inferred from a prompt."""
    _text(prompt, 800)
    name = _text(business_name, 70)
    title = _text(headline or ("Explore " + name), 100)
    action = _text(cta, 100)
    _color(accent)
    _color(background)
    if mode not in ("text", "image") or (mode == "image" and not source_asset_id):
        raise DesignError("Image-to-poster requires an authorized asset ID")
    if source_asset_id is not None and (not isinstance(source_asset_id, str)
                                        or not ID.fullmatch(source_asset_id)):
        raise DesignError("Image must use a trusted asset ID")
    if logo_asset_id is not None and (not isinstance(logo_asset_id, str)
                                     or not ID.fullmatch(logo_asset_id)):
        raise DesignError("Logo must be a registered image asset ID")
    if template is None:
        words = prompt.lower()
        template = next((key for key, hints in {
            "festival": ("diwali", "navratri", "festival", "christmas"),
            "ethnic": ("ethnic", "saree", "kurta"),
            "streetwear": ("streetwear", "sneaker"),
            "restaurant": ("restaurant", "food", "menu"),
            "luxury": ("luxury", "premium", "boutique"),
            "clearance": ("clearance",),
            "new_arrivals": ("new arrival",),
            "seasonal": ("summer", "winter", "seasonal"),
        }.items() if any(word in words for word in hints)), "fashion")
    if template not in TEMPLATES or format not in FORMATS:
        raise DesignError("Invalid template or format")
    # Distinct art direction without 10 competing raster implementations.
    # The retailer's approved brand colors take precedence over these defaults.
    palettes = {
        "fashion": ("#C05F43", "#FCF4EC"),
        "luxury": ("#A98A4B", "#F5F0E5"),
        "streetwear": ("#F4511E", "#F2F2F2"),
        "ethnic": ("#A93E4A", "#FFF1DB"),
        "festival": ("#CE8831", "#FFF3DB"),
        "restaurant": ("#B54A28", "#FCF2E5"),
        "general": ("#286B6A", "#F2F7F6"),
        "new_arrivals": ("#4469A3", "#F5F7FF"),
        "clearance": ("#D63E32", "#FFF1EE"),
        "seasonal": ("#55744E", "#F5F7EA"),
    }
    if accent == "#C05F43" and background == "#FCF4EC":
        accent, background = palettes[template]
    image_rects = {
        "luxury": (.12, .17, .76, .43), "streetwear": (0, .15, 1, .48),
        "ethnic": (.08, .16, .84, .46), "festival": (.07, .19, .86, .43),
        "restaurant": (.07, .16, .86, .48), "clearance": (0, .15, 1, .48),
    }
    ix, iy, iw, ih = image_rects.get(template, (.07, .16, .86, .47))
    headline_size = 58 if template in ("streetwear", "clearance") else 48 if template == "luxury" else 52
    label = {
        "fashion": "THE STYLE EDIT", "luxury": "THE EDIT",
        "streetwear": "BOLD STYLE", "ethnic": "THE ETHNIC EDIT",
        "festival": "FESTIVE EDIT", "restaurant": "MENU SPOTLIGHT",
        "general": "DISCOVER MORE", "new_arrivals": "THE LATEST EDIT",
        "clearance": "SHOP THE EDIT", "seasonal": "SEASONAL EDIT",
    }[template]
    layers = [
        {"id": "brand", "type": "text", "x": .07, "y": .055, "w": .86, "h": .07,
         "text": name.upper(), "color": "#23232B", "font_size": 37, "bold": True},
        {"id": "accent-rule", "type": "rect",
         "x": .07 if template != "streetwear" else 0, "y": .135,
         "w": .23 if template != "clearance" else .86, "h": .012, "color": accent},
    ]
    if logo_asset_id:
        # An optional registered brand logo is a contain-fit alpha layer at
        # upper right. Keep the brand caption clear of the logo plate.
        layers[0]["w"] = .68
        layers.append({"id": "logo", "type": "image", "x": .79, "y": .03,
                       "w": .14, "h": .085, "asset_id": logo_asset_id})
    if source_asset_id:
        layers.append({"id": "product", "type": "image", "x": ix, "y": iy,
                       "w": iw, "h": ih, "asset_id": source_asset_id})
    else:
        layers += [
            {"id": "decorative", "type": "rect", "x": ix, "y": iy,
             "w": iw, "h": ih, "color": accent},
            {"id": "concept-label", "type": "text", "x": .13, "y": .38,
             "w": .74, "h": .12, "text": label, "color": "#FFFFFF",
             "font_size": 62, "bold": True},
        ]
    layers += [
        {"id": "headline", "type": "text", "x": .07, "y": .665, "w": .86, "h": .12,
         "text": title, "color": "#23232B", "font_size": headline_size, "bold": True},
    ]
    if approved_offer is not None:
        # This parameter must originate from an approved campaign/merchant record,
        # not extracted from the prompt by a model or regex.
        offer = _text(approved_offer, 85)
        layers.append({"id": "offer", "type": "text", "x": .07, "y": .80,
                       "w": .86, "h": .075, "text": offer, "color": accent,
                       "font_size": 44, "bold": True})
    layers.append({"id": "cta", "type": "text", "x": .07, "y": .92, "w": .86,
                   "h": .06, "text": action, "color": "#23232B", "font_size": 27,
                   "bold": False})
    return validate_design({"schema": SCHEMA, "shop_id": shop_id, "format": format,
                            "template": template, "background": background,
                            "layers": layers})


def _font(px, bold):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, px)
    except OSError as exc:
        raise DesignError("Server requires the DejaVu font") from exc


def _draw_fitted_text(draw, text, x, y, width, height, font_size, color, bold, scale):
    """Render EVERY authorized character or fail; never silently cut prices/offers.

    Pillow is the authoritative raster for saved/exported versions. A browser
    Konva preview is non-authoritative until visual parity has been reviewed.
    """
    target = max(8, round(font_size * scale))
    for px in range(target, 7, -1):
        font = _font(px, bold)
        lines, line, words = [], "", text.split()
        def fits(candidate):
            return draw.textbbox((0, 0), candidate, font=font, anchor="lt")[2] <= width
        for word in words:
            proposed = (line + " " + word).strip()
            if fits(proposed):
                line = proposed
                continue
            if line:
                lines.append(line)
                line = ""
            # Long SKU, product or offer tokens must not overflow or vanish.
            for letter in word:
                if line and not fits(line + letter):
                    lines.append(line)
                    line = ""
                line += letter
        if line:
            lines.append(line)
        line_height = max(9, round(px * 1.24))
        if lines and len(lines) * line_height <= height and all(fits(s) for s in lines):
            for index, value in enumerate(lines):
                draw.text((x, y + index * line_height), value, font=font,
                          fill=color, anchor="lt")
            return
    raise DesignError("Authorized poster text cannot fit its layer without clipping")


def _assets(manifest, staged_root, shop_id, asset_id):
    """Reuse the secure Part 1 path, tenant and commercial-rights validator."""
    import importlib.util
    import sys
    name = "retailgrowth_poster_legacy_rights"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("render.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    try:
        return module._asset(manifest, staged_root, asset_id, shop_id)
    except module.PosterError as exc:
        raise DesignError(str(exc)) from exc


def _prepare_authorized_images(design, manifest, staged_root):
    """Resolve each tenant-checked source image ONCE per individual render job.

    This is deliberately private to the engine, never a browser-controlled
    image cache. Rights revocations require a new job/authorization check.
    """
    if not isinstance(manifest, dict) or manifest.get("shop_id") != design["shop_id"]:
        raise DesignError("Cross-tenant manifest")
    images = {}
    for layer in design["layers"]:
        if layer["type"] == "image" and layer["asset_id"] not in images:
            images[layer["asset_id"]] = _assets(
                manifest, staged_root, design["shop_id"], layer["asset_id"]
            )
    return images


def _render_prepared(design, images, output_path, *, scale=1, pulse_offer=False,
                     image_transform_cache=None):
    """Draw one canvas using prepared images; optional tiny job-local transform cache.

    Cache is scoped to a single render job, NEVER shared between shops or
    persisted beyond its private TemporaryDirectory. No external URLs.
    """
    if type(scale) not in (int, float) or not .2 <= scale <= 1:
        raise DesignError("Invalid output scale")
    w0, h0 = FORMATS[design["format"]]
    w, h = round(w0 * scale), round(h0 * scale)
    canvas = Image.new("RGB", (w, h), design["background"])
    d = ImageDraw.Draw(canvas)
    for layer in design["layers"]:
        x, y, width, height = (round(layer[key] * bound)
                               for key, bound in (("x", w), ("y", h), ("w", w), ("h", h)))
        if layer["type"] == "rect":
            d.rectangle((x, y, x + width, y + height), fill=layer["color"])
        elif layer["type"] == "image":
            photo = images[layer["asset_id"]]
            is_logo = layer["id"] == "logo"
            key = (layer["asset_id"], width, height, is_logo)
            transformed = None if image_transform_cache is None else image_transform_cache.get(key)
            if transformed is None:
                if is_logo:
                    transformed = ImageOps.contain(photo.convert("RGBA"), (width, height),
                                                  Image.Resampling.LANCZOS)
                else:
                    # Preserve transparent garment PNGs and exact cover crop.
                    transformed = ImageOps.fit(photo.convert("RGBA"), (width, height),
                                               Image.Resampling.LANCZOS)
                if image_transform_cache is not None:
                    # Keep at most four converted RGBA images in this single
                    # job; no global cache, unbounded RAM or rights staleness.
                    if len(image_transform_cache) >= 4:
                        image_transform_cache.pop(next(iter(image_transform_cache)))
                    image_transform_cache[key] = transformed
            if is_logo:
                ox = x + (width - transformed.width) // 2
                oy = y + (height - transformed.height) // 2
                canvas.paste(transformed.convert("RGB"), (ox, oy),
                             mask=transformed.getchannel("A"))
            else:
                canvas.paste(transformed.convert("RGB"), (x, y),
                             mask=transformed.getchannel("A"))
        else:
            color = layer["color"]
            size = layer["font_size"]
            if pulse_offer and layer["id"] == "offer":
                color = "#FFFFFF" if pulse_offer == "flash" else color
                size = round(size * 1.10)
            _draw_fitted_text(d, layer["text"], x, y, width, height,
                              size, color, layer["bold"], scale)
    path = Path(output_path)
    if path.suffix.lower() != ".png":
        raise DesignError("Only PNG output permitted")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, format="PNG")
    return {"path": str(path), "width": w, "height": h,
            "shop_id": design["shop_id"], "schema": SCHEMA}


def render_design(design, manifest, staged_root, output_path, *, scale=1,
                  pulse_offer=False):
    """Rights-check current media, draw PNG and never fetch arbitrary URLs."""
    checked = validate_design(design)
    images = _prepare_authorized_images(checked, manifest, staged_root)
    return _render_prepared(checked, images, output_path, scale=scale,
                            pulse_offer=pulse_offer)

