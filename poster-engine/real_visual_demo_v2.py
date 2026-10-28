"""Feature #3 real FLUX.2 Klein 4B local GPU sample harness.

This is NOT a hosted retailer API, cloud GPU deployment or real virtual try-on.
It makes exactly two actual model calls using approved, PREINSTALLED local
weights: (1) synthetic adult fashion campaign model, (2) product concept.
The resulting generated model image is composited into an actual CPU poster.

Default usage, on a machine with CUDA and reviewed FLUX.2 klein-4B weights:
  python poster-engine/real_visual_demo_v2.py --weights /private/flux2-klein-4b \
      --out /private/retailgrowth-feature3-demo

No runtime downloads, HTTP requests, service-role tokens, third-party uploads,
Azure resources, paid endpoints or new SaaS API paths. All outputs are unreviewed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
from uuid import UUID, uuid5

from PIL import Image, UnidentifiedImageError

from ai_providers_v2 import InferenceJob, ProviderBlocked, _verified_png
from gpu_worker_v2 import OfflineFluxKlein4B
from gpu_preflight_v2 import verify_local_flux_snapshot
from studio_v2 import compose_poster, render_design


DEMO_SHOP = "00000000-0000-4000-8000-000000000a33"
MODEL_ASSET = "00000000-0000-4000-8000-000000000a76"
MAX_FILE = 25 * 1024 * 1024
MODEL_BRIEF = (
    "Photorealistic synthetic adult Indian fashion model, wearing an elegant "
    "festive deep emerald green kurti with gold thread embroidery, standing "
    "inside a premium boutique with natural cinematic lighting, professional "
    "retail campaign photography, believable fabric folds, natural proportions, "
    "no logos, no labels, no watermarks, no letters or promotional text"
)
PRODUCT_BRIEF = (
    "Premium e-commerce product photography of a single deep emerald green "
    "festive women's kurti with delicate gold embroidery, presented on a "
    "simple neutral display with soft studio lighting, beautiful fabric detail, "
    "centered garment, no person, no logos, no words or watermarks"
)


def _directory(output_root):
    root = Path(output_root).expanduser()
    if root.is_symlink() or (root.exists() and
                             (not root.is_dir() or any(root.iterdir()))):
        raise ProviderBlocked("Sample output must be a new or empty private directory")
    # The caller controls this path; no external URLs or temp-directory reuse.
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root.resolve(strict=True)


def _write_png(root, name, payload):
    clean = _verified_png(payload)
    target = root / name
    if target.exists():
        raise ProviderBlocked("Existing output cannot be overwritten")
    target.write_bytes(clean)
    return target, sha256(clean).hexdigest()


def create_real_visual_sample(*, runner, output_root, shop_id=DEMO_SHOP,
                              business_name="Sample Fashion House",
                              approved_offer=None, approved_reference=None):
    """Invoke the injected REAL model runner, or a clearly marked test fake.

    runner(job, inputs) emits model-generated PNG bytes; this helper is also
    unit tested with deterministic synthetic bytes, which are not AI evidence.
    The approved_reference, if present, is operator-supplied local bytes:
    it is never fetched from a URL, and only conditions the product image
    edit. It does not certify perfect preservation of the garment.
    """
    if not callable(runner) or not isinstance(business_name, str) or not business_name.strip():
        raise ProviderBlocked("Approved inference runner and business name required")
    if not isinstance(shop_id, str) or str(UUID(shop_id)) != shop_id:
        raise ProviderBlocked("Canonical shop UUID required")
    if approved_offer is not None and (not isinstance(approved_offer, str)
                                      or not approved_offer.strip()
                                      or len(approved_offer) > 85):
        raise ProviderBlocked("Unapproved or malformed promotional offer")
    if approved_reference is not None:
        if not isinstance(approved_reference, bytes) or not 0 < len(approved_reference) <= MAX_FILE:
            raise ProviderBlocked("Only authorized local product bytes accepted")
        try:
            with Image.open(BytesIO(approved_reference)) as photo:
                if photo.width * photo.height > 24_000_000 or getattr(photo, "n_frames", 1) != 1:
                    raise ProviderBlocked("Unsafe garment reference")
                photo.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ProviderBlocked("Garment reference cannot be decoded") from exc
    root = _directory(output_root)
    # Deterministic job IDs for reproducible sample composition. No durable
    # usage ledger here: this is an isolated local QA command, never SaaS.
    model = InferenceJob(
        shop_id=shop_id, job_id=str(uuid5(UUID(shop_id), "feature3-local-model-v1")),
        capability="human_model", prompt=MODEL_BRIEF,
    )
    product = InferenceJob(
        shop_id=shop_id, job_id=str(uuid5(UUID(shop_id), "feature3-local-product-v1")),
        capability="image_edit" if approved_reference is not None else "text_to_image",
        prompt=PRODUCT_BRIEF,
        source_asset_ids=(str(uuid5(UUID(shop_id), "feature3-demo-product-input")),)
            if approved_reference is not None else (),
    )
    inputs = ({product.source_asset_ids[0]: approved_reference}
              if approved_reference is not None else {})
    try:
        fashion_path, fashion_hash = _write_png(
            root, "fashion-model-flux-generated.png", runner(model, {}))
        product_path, product_hash = _write_png(
            root, "product-visual-flux-generated.png", runner(product, inputs))
        manifest = {"shop_id": shop_id, "assets": {
            MODEL_ASSET: {
                "kind": "image", "shop_id": shop_id,
                "path": fashion_path.name,
                "rights": {
                    "license": "owned", "commercial_use": True,
                    "source": "FLUX.2 Klein 4B synthetic local QA output",
                    "evidence": "Review required; synthetic model, not product-authenticity proof",
                },
            },
        }}
        design = compose_poster(
            shop_id=shop_id, mode="image", prompt="Premium festive boutique clothing",
            business_name=business_name, headline="Discover festive style",
            cta="Visit our boutique", approved_offer=approved_offer,
            source_asset_id=MODEL_ASSET, template="luxury", format="portrait",
        )
        poster_path = root / "fashion-poster-cpu-composed.png"
        render_design(design, manifest, root, poster_path)
        hashes = {
            "fashion_model_png": fashion_hash,
            "product_visual_png": product_hash,
            "poster_png": sha256(poster_path.read_bytes()).hexdigest(),
        }
        real_flux = isinstance(runner, OfflineFluxKlein4B) and runner.pipeline is not None
        receipt = {
            "provider": ("FLUX.2 Klein 4B via locally preinstalled Diffusers"
                         if real_flux else "UNVERIFIED_INJECTED_TEST_RUNNER"),
            "shop_id": shop_id, "assets": [
                fashion_path.name, product_path.name, poster_path.name,
            ], "hashes": hashes,
            "model_inference_verified": real_flux,
            "model_inference_executed_by_runner": real_flux,
            "inference_claim_requires_real_cuda_run": True,
            "model_output_reviewed": False, "actual_try_on": False,
            "reference_product_fidelity_verified": False,
            "commercial_model_release_gate": "requires operator review",
            "server_cloud_deployed": False,
            "external_paid_api_calls": 0,
            "flights": 2,
            "source_reference_supplied": approved_reference is not None,
        }
        (root / "local-run-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2), encoding="utf-8")
        return receipt
    except BaseException:
        # Avoid displaying a half-created three-image demo as complete.
        for name in ("fashion-model-flux-generated.png",
                     "product-visual-flux-generated.png",
                     "fashion-poster-cpu-composed.png", "local-run-receipt.json"):
            (root / name).unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run REAL locally installed FLUX.2 Klein 4B; no cloud API")
    parser.add_argument("--weights", type=Path, required=True,
                        help="Already downloaded, reviewed 4B model directory")
    parser.add_argument("--out", type=Path, required=True,
                        help="Empty private local output directory")
    parser.add_argument("--approval-manifest", type=Path, required=True,
                        help="Operator-verified 4B repo/revision/license and model index SHA-256")
    parser.add_argument("--business-name", default="Sample Fashion House")
    parser.add_argument("--licensed-garment", type=Path,
                        help="Locally owned/approved reference; not guaranteed try-on")
    parser.add_argument("--confirm-commercial-rights", action="store_true",
                        help="Explicit confirmation for the reference image")
    args = parser.parse_args(argv)
    if args.licensed_garment and not args.confirm_commercial_rights:
        parser.error("Owned garment needs --confirm-commercial-rights")
    preflight = verify_local_flux_snapshot(args.weights, args.approval_manifest)
    # Diffusers/HF must not download or auto-upgrade models during execution.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["DIFFUSERS_OFFLINE"] = "1"
    runner = OfflineFluxKlein4B(args.weights, steps=4, height=768, width=768)
    source = args.licensed_garment.read_bytes() if args.licensed_garment else None
    receipt = create_real_visual_sample(
        runner=runner, output_root=args.out,
        business_name=args.business_name, approved_reference=source,
    )
    print(json.dumps({**receipt, "model_snapshot_preflight": preflight}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
