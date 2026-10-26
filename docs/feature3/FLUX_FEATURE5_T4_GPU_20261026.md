# Feature #3 FLUX 4B — reuse Feature #5 GPU resources (2026-10-26)

## Verified infrastructure (do not call it deployed)

The user has retired Feature #5's proposed GPU usage and authorized reuse for Feature #3. **There is no GPU instance to resize**: previous OIDC #40347841764 created only an EMPTY workload-profiles Container Apps environment `rgai-f5-gpu-canary-eastus` inside `rg-retailgrowth-dev`. Existing A100 quota was 0.

New **real Azure DEV OIDC** #40380327515 on reviewed PR #412 confirms: `ManagedEnvironmentConsumptionT4Gpus limit=0 used=0` on that exact environment. Successful read-only run: **no allocated or running GPU and no actual FLUX image**. Source PR #419 inspects `Standard_NC4as_T4_v3` / `Standard_NV6ads_A10_v5` VM quota independently; listed unrestricted SKUs do not prove GPU-family vCPU quota. Do not create a VM until exact positive family+regional quota, price and safe stop/deallocation protocol are verified.

## Model selection and expected hardware

- Official `black-forest-labs/FLUX.2-klein-4B`, **Apache-2.0** (commercial weights), BFL/Hugging Face exact revision `e7b7dc27f91deacad38e78976d1f2b499d76a294`; **not** noncommercial Klein 9B/FLUX Dev.
- BFL gives approximately 13 GB VRAM and official HF repository reports approximately 23.7GB stored model snapshot. Storage/download/startup is not free.
- NVIDIA T4 = 16 GB VRAM, native FP16 but **not BF16**. The reviewed offline runner now selects FP16 + Accelerate CPU offload below 20 GiB, one inference at 512×512 in four model steps, no online model load; quality and throughput must be benchmarked on the actual GPU before merchant activation. A10 (24GB, BF16 capable) is an alternative only if GPU family quota/price is verified first.

## Isolated source-only packaging

- `infra/azure/feature3-flux-t4/Dockerfile`: pinned PyTorch/CUDA model serving runtime, runs as non-root, no keys or checkpoint bundled in image.
- `poster-engine/flux_t4_snapshot.py`: exact official revision, full manifest equality for every `.safetensors` file, pinned index and reviewed dependency license; blocks replaced/incomplete weights.
- `poster-engine/flux_t4_container_entrypoint.py`: takes ONE private file containing trusted `shop_id`, `job_id`, adult synthetic marketing visual brief; reads already staged private model; runs one actual `OfflineFluxKlein4B` call only when all shard hashes verified; outputs an **UNREVIEWED** private PNG and SHA receipt. No approval, promotion, queue, hidden cloud fetch, tenant authorization, SaaS billing or public image link is implied.
- `tests/media/test_feature3_flux_t4_snapshot.py`: uses tiny **mock files and fake PIL output**, never downloads genuine checkpoints or calls CUDA. A green test is NOT a FLUX-generated Indian-model sample.
- Existing `OptionalGPUProvider` must be used by the real tenant-integrated queue with a **single bounded durable existing-shop subscription reservation**, current RLS, provider retry fencing, private output registration, signed download, rate cap and human approval. Not connected here.

## Real deployment sequence (not yet executed)

1. Azure availability gate: read [real T4 quota run #40380327515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40380327515). Current T4=0; cannot allocate in current environment. Consider positive exact VM GPU-family quota from separate probe, or request **1** managed-environment Consumption T4 GPU quota using Azure Portal → existing Container Apps Environment → Settings → Quota; potential Microsoft review.
2. Pricing gate: retrieve current subscription/region *GPU + vCPU + RAM per-second price*, storage/container registry/network and cold start, with a fixed single-run USD cap before launch. Azure's public pricing page does not give an account-specific numeric ACA GPU price; do not invent one.
3. Copy approved, complete official model snapshot into encrypted, private read-only mount `/mnt/private/models/FLUX.2-klein-4B`; generate `approval-manifest.json` from actual file hashes. Review licenses for all dependencies, exact model revision and stop if shard list doesn't match.
4. Build image from repo at known commit digest, pin **immutable SHA256** of built container; never embed secrets/weights. Verify Docker build / CUDA and offline import on GPU and set a hard execution timeout. Mount private job and output paths. Restrict to one manual execution/replica and zero idle.
5. Generate ONE synthetic adult Indian fashion still from text alone; inspect actual private PNG, CUDA/VRAM/elapsed/charge and checkpoint provenance. **Do not claim real FLUX inference from synthetic unit tests.**
6. Only after full tenant integration and valid commercial source licensing, enable retailer model-library registration. Apparel try-on is separate FASHN parser license issue, *not* FLUX text-to-image.

**Current result:** No Azure GPU quota in existing environment. No profile, VM, container app, model stage or FLUX inference deployed. No new paid charges. No WineShopPOS or PROD changes. Owner deferred genuine imported-model photo inspection, independent third-party image rights research and hosted SaaS browser E2E; these remain release gates.
