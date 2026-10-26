"""Create clearly synthetic, non-AI Feature #3 CI advertising examples.

No stock-image downloads or customer content. The garment silhouette is drawn
with Pillow. Outputs go to caller-provided folder and remain noncommercial demos.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageDraw

from studio_v2 import compose_poster, render_design
from animate_v2 import export_animation
from garment_review_v2 import build_review_sheet
from review_export_v2 import create_review_pair

SHOP = "00000000-0000-4000-8000-000000000a33"
ASSET = "00000000-0000-4000-8000-000000000a34"
MOCKED = "00000000-0000-4000-8000-000000000a35"


def samples(destination):
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    garment = root / "synthetic-garment.png"
    picture = Image.new("RGB", (660, 840), "#ECE5DA")
    draw = ImageDraw.Draw(picture)
    draw.ellipse((220, 92, 440, 285), fill="#DFC9B2")
    draw.polygon([(220, 210), (117, 245), (39, 382), (134, 440),
                  (206, 344), (203, 749), (455, 749), (452, 344),
                  (540, 440), (621, 382), (544, 245), (440, 210),
                  (386, 273), (274, 273)], fill="#3C5C71")
    for x in range(236, 450, 55):
        draw.line((x, 332, x, 720), fill="#719BA6", width=10)
    draw.rectangle((238, 514, 426, 530), fill="#DAB676")
    picture.save(garment)
    manifest = {
        "shop_id": SHOP,
        "assets": {
            ASSET: {
                "kind": "image", "shop_id": SHOP, "path": garment.name,
                "rights": {
                    "license": "owned", "commercial_use": True,
                    "source": "CI_SYNTHETIC_PILLOW",
                    "evidence": "Deterministic geometric synthetic garment fixture",
                },
            },
        },
    }
    # Comparison is a synthetic fixture to demonstrate REQUIRED human review.
    # No fashion model or virtual try-on network/model inference is executed.
    fake = root / "synthetic-unverified-review-image.png"
    Image.new("RGB", (660, 840), "#B29E8E").save(fake)
    manifest["assets"][MOCKED] = {
        "kind": "image", "shop_id": SHOP, "path": fake.name,
        "rights": {
            "license": "owned", "commercial_use": True,
            "source": "CI_SYNTHETIC_PILLOW",
            "evidence": "Deterministic unverified comparison test fixture",
        },
    }
    build_review_sheet(
        shop_id=SHOP, garment_asset_id=ASSET, model_asset_id=MOCKED,
        manifest=manifest, staged_root=root,
        output_path=root / "sample-synthetic-garment-review.png",
        inference_verified=False,
    )
    sale = compose_poster(
        shop_id=SHOP, mode="image", prompt="Diwali premium ethnic clothing",
        business_name="Sample Fashion House", headline="Celebrate in style",
        cta="Discover the festive edit", source_asset_id=ASSET,
        template="festival", approved_offer="20% OFF", format="square",
    )
    plain = compose_poster(
        shop_id=SHOP, mode="text", prompt="Create a seasonal clothing collection poster",
        business_name="Sample Fashion House", headline="New season, new style",
        cta="Visit our boutique", template="fashion", format="portrait",
    )
    render_design(sale, manifest, root, root / "sample-clothing-20-off.png")
    # Pixel-identical full-size authoritative output and a smaller review
    # thumbnail downsampled from THAT exact binary, not rerendered in browser.
    create_review_pair(sale, manifest, root, root, preview_long_edge=432)
    render_design(plain, {"shop_id": SHOP, "assets": {}}, root, root / "sample-text-to-poster.png")
    export_animation(sale, manifest, root, root / "sample-flashing-20-off.gif",
                     fps=4, duration=2, scale=.5)
    export_animation(sale, manifest, root, root / "sample-flashing-20-off.mp4",
                     fps=4, duration=2, scale=.5)
    return [root / name for name in (
        "sample-clothing-20-off.png", "sample-text-to-poster.png",
        "sample-flashing-20-off.gif", "sample-flashing-20-off.mp4",
        "sample-synthetic-garment-review.png",
        "poster-final.png", "poster-review-preview.png",
    )]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for artifact in samples(args.out):
        print(artifact.name, artifact.stat().st_size, "bytes; SYNTHETIC / NO AI INFERENCE")
