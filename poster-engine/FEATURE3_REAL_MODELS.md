# Feature #3: Real model sample path (cost-first and commercially guarded)

This is a reproducible **local-only** route to the actual
[Black Forest Labs FLUX.2 Klein 4B](https://github.com/black-forest-labs/flux2)
model. It is **not** a claim that a GPU was deployed or a generated
fashion-model example exists in hosted RetailGrowthAI.

## What is implemented

`real_visual_demo_v2.py` invokes the actual `OfflineFluxKlein4B`
Diffusers runner **twice** using the *locally present 4B weights*:

1. `fashion-model-flux-generated.png` — synthetic adult model in a
   generic festive kurti outfit; not a customer's real garment.
2. `product-visual-flux-generated.png` — fashion product concept. When
   the operator explicitly supplies an owned reference garment the second
   call uses FLUX single-reference image editing. This is **not**
   FASHN virtual try-on or guarantee of matching embroidery, color,
   pattern or fit.
3. `fashion-poster-cpu-composed.png` — generated model photo composed
   by our real Pillow `studio_v2.py` at 1080×1350. Exact merchant
   words are rasterized deterministically, *not* AI-generated.
4. `local-run-receipt.json` — output hashes and explicit flags
   `model_output_reviewed=false`, `actual_try_on=false`, and
   `server_cloud_deployed=false`.

The CLI imports no GPU model or HF client before its path/license preflight.
Diffusers loads only `local_files_only=True` and all HF online fallback
environment variables are disabled before instantiation.

## Source repositories

| Function | Pinned candidate | Source/license constraint |
| --- | --- | --- |
| Fashion model and product image | `black-forest-labs/FLUX.2-klein-4B` | Apache-2.0 4B weights, **not** noncommercial 9B/dev |
| Local Diffusers inference | `Flux2KleinPipeline` | Review exact dependency snapshot |
| Virtual try-on | `fashn-AI/fashn-vton-1.5` | Third-party `fashn-human-parser` inherits NVIDIA SegFormer license; commercial clearance or replacement needed |
| Lightweight poster/animations | Existing Pillow/FFmpeg | CPU default, no model weights or GPU |

## Local operator runbook (NO automatic download or paid service)

Prerequisites: separately obtain and review the exact licensed 4B snapshot,
its full shard list and dependency licenses. Use an approved NVIDIA CUDA host
with sufficient VRAM (BFL quotes roughly 13 GB), preinstall compatible
`torch`, `diffusers`, `transformers` and `Pillow` **outside**
the Azure HTTP Functions application.

- Select and pin the real 40-character upstream 4B revision hash.
- Manually verify `model_index.json` is a **Flux2KleinPipeline** and
  confirm every checkpoint shard came from the approved source. The current
  no-download preflight hashes `model_index.json` but **does not verify
  all multi-GB shards**, so the manifest does not confer supply-chain
  security or permission to deploy to customer tenants.
- Create an operator-approved JSON manifest *outside the model folder*,
  using the real full commit SHA and actual index SHA-256:

```json
{
  "schema": "retailgrowth.flux2-klein-4b.approval.v1",
  "repository": "black-forest-labs/FLUX.2-klein-4B",
  "revision_sha": "REPLACE_WITH_EXACT_40_CHARACTER_4B_COMMIT",
  "weight_license": "Apache-2.0",
  "model_index_sha256": "REPLACE_WITH_ACTUAL_SHA256_OF_MODEL_INDEX",
  "commercial_operator_approved": true,
  "dependencies_operator_approved": true
}
```

The manifest above is a **template**, intentionally invalid until a
human reviewer fills the exact hashes and approvals. Do not blindly
set approval flags without reviewing the release.

```bash
# Runs 2 actual GPU generations only if pretrained weights,
# license manifest and compatible CUDA/Diffusers already exist:
python poster-engine/real_visual_demo_v2.py \
  --weights /private/models/FLUX.2-klein-4B \
  --approval-manifest /private/reviews/flux2-klein-4b-approved.json \
  --out /private/feature3-flux-qa \
  --business-name "Sample Fashion House"

# Optional source-conditioned product visual: ONLY with legally owned photo.
# Output is not guaranteed to preserve that garment exactly, nor real VTON.
python poster-engine/real_visual_demo_v2.py \
  --weights /private/models/FLUX.2-klein-4B \
  --approval-manifest /private/reviews/flux2-klein-4b-approved.json \
  --out /private/feature3-garment-qa \
  --licensed-garment /private/owned/garment.png \
  --confirm-commercial-rights
```

There is no automatic cloud deployment, idle GPU, data upload, wallet
charge, stock video purchase or external API usage in these commands.
Local hardware power/runtime is not free. **Do not run on DEV cloud
GPU before obtaining an actual region/SKU quote, privacy approval,
monthly budget cap and benchmark.** Existing Azure/Supabase services
are unchanged.

## What can already be verified without GPU

- `python -m unittest discover -s tests/media -p 'test_feature3_real_visual_demo.py'`
  validates the two-call workflow with an **explicitly mocked synthetic**
  image runner (not AI), a genuine Pillow generated poster, exact
  shop/job lineage, private local files, cleanup on model error,
  wrong-model license denial and no model-download behavior.
- The previously merged CI media harness runs
  `poster-engine/sample_feature3.py` to output **seven** synthetic
  brand/garment/promo PNG/GIF/MP4 artifacts using actual project Pillow/
  FFmpeg code. The fashion shape is geometric, not a photorealistic
  human model. Download evidence from current PR Actions, not fabricated
  URLs or assistant-generated images.
- UI local-browser PNG is not equivalent to the authoritative full
  private Pillow export or human approval.

## Remaining acceptance gates

1. Real 4B snapshot pinned and approved, real **CUDA inference**
   successful, and view actual fashion/model/product examples.
2. Human quality review for adult human realism and product fidelity;
   generated reference images may be inaccurate.
3. Tenant JWT/RLS source rights, existing outbox/job ledger, privately
   stored model outputs, cost reservation and licensed media attribution
   connected by the coordinator before any user-facing switch.
4. FASHN parser commercial approval/replacement before enabling actual
   apparel try-on; do not substitute geometry or mock outputs and call it VTON.
5. Safe signed-in browser E2E (owner, VIEWER, foreign shop, expired JWT),
   signed final exports, server-backed persistence and cost benchmark.

No PROD resources or WineShopPOS changes permitted.


## Pre-rental private checkpoint audit helper (2026-10-28)

The source-only `flux_t4_review_candidate.py` computes SHA-256 over **every staged safetensors shard**, the exact `Flux2KleinPipeline` index, all required tokenizer/config files, and `LICENSE.md`. It never downloads models, accesses Azure, runs CUDA or approves a license. Run **only after** you have manually staged the official immutable 4B snapshot into private local storage:

```bash
python poster-engine/flux_t4_review_candidate.py \
  --weights /mnt/private/models/FLUX.2-klein-4B \
  --output /mnt/private/reviews/flux2-klein-4b-candidate.json
```

The candidate is created privately with mode 0600 and `dependencies_operator_approved=false`. It is intentionally rejected by `verify_reviewed_flux_snapshot` until an operator independently verifies the pinned publisher commit, signed provenance where available, actual model weight/license terms, dependency notices and all file digests, then explicitly approves a separately protected copy. **Never blindly change this flag to true.** The tool refuses symlinked components, incomplete shards/configs, unexpected pipeline class, an existing destination or a review manifest stored inside the model mount. Tests use tiny synthetic fake checkpoint bytes and are not real model inference.

The owner-provided **October 28 Azure Portal screenshot** shows the existing Feature5 managed environment's A100 quota now **0 used / 2 limit**, while T4 remains **0 used / 0 limit**. This image is user-provided quota evidence, not a new authenticated Azure OIDC pricing, allocation, active compute or model deployment check. Hold any GPU resource launch until actual A100 price, quota usage, allocation and explicit cost cap are verified separately. Do not touch PROD/WineShopPOS.
