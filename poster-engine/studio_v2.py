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
                   template=None, format="square", accent="#C05F43",
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
    layers = [
        {"id": "brand", "type": "text", "x": .07, "y": .055, "w": .86, "h": .07,
         "text": name.upper(), "color": "#23232B", "font_size": 37, "bold": True},
    ]
    if source_asset_id:
        layers.append({"id": "product", "type": "image", "x": .07, "y": .16,
                       "w": .86, "h": .47, "asset_id": source_asset_id})
    else:
        layers.append({"id": "decorative", "type": "rect", "x": .07, "y": .16,
                       "w": .86, "h": .47, "color": accent})
    layers += [
        {"id": "headline", "type": "text", "x": .07, "y": .665, "w": .86, "h": .12,
         "text": title, "color": "#23232B", "font_size": 52, "bold": True},
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


def render_design(design, manifest, staged_root, output_path, *, scale=1,
                  pulse_offer=False):
    """Draw bounded versioned layers as server-side PNG, with no remote fetch."""
    design = validate_design(design)
    if type(scale) not in (int, float) or not .2 <= scale <= 1:
        raise DesignError("Invalid output scale")
    if not isinstance(manifest, dict) or manifest.get("shop_id") != design["shop_id"]:
        raise DesignError("Cross-tenant manifest")
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
            photo = _assets(manifest, staged_root, design["shop_id"], layer["asset_id"])
            image = ImageOps.fit(photo.convert("RGB"), (width, height), Image.Resampling.LANCZOS)
            canvas.paste(image, (x, y))
        else:
            color = layer["color"]
            size = layer["font_size"]
            if pulse_offer and layer["id"] == "offer":
                color = "#FFFFFF" if pulse_offer == "flash" else color
                size = round(size * 1.10)
            font = _font(max(8, round(size * scale)), layer["bold"])
            text = layer["text"]
            # Never draw claims outside the caller-controlled layer rectangle.
            words, lines, current = text.split(), [], ""
            for word in words:
                trial = (current + " " + word).strip()
                if d.textbbox((0, 0), trial, font=font)[2] <= width:
                    current = trial
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
            max_lines = max(1, height // max(1, round(font.size * 1.18)))
            for line in lines[:max_lines]:
                d.text((x, y), line[:140], font=font, fill=color)
                y += round(font.size * 1.18)
    path = Path(output_path)
    if path.suffix.lower() != ".png":
        raise DesignError("Only PNG output permitted")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, format="PNG")
    return {"path": str(path), "width": w, "height": h,
            "shop_id": design["shop_id"], "schema": SCHEMA}
