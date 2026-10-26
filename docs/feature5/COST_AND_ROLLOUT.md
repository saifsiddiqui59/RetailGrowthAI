# Feature #5 GPU & licensing decision (2026-10-26)

**Status: decision proposal only, no provisioning / no paid test.**

## Model options and constraints

| Option | Text / Image | Estimated GPU requirement | Commercial and activation gate |
| --- | --- | --- | --- |
| HunyuanVideo 1.5 official CLI | T2V + I2V, 480p/720p variants | Official **minimum 14 GB VRAM with offload**; actual viable SKU/latency unmeasured | Tencent Community License (NOT Apache). Territory EXCLUDES EU, UK, South Korea; hosted-service disclosures, MAU and acceptable use terms need legal review. |
| HunyuanVideo 1.5 Diffusers | Separate documented HunyuanVideo15 pipelines | Similar model weights; memory and compatibility per configuration, benchmark required | Same weight/model terms; Diffusers Apache licensing does not replace Tencent model license |
| Existing Alibaba Wan 2.7 Model Studio (Part3) | T2V / I2V, 2–15s at 720p/1080p | GPU managed by vendor | Part3 already implements gated provider; vendor cloud pricing/region/data transfer require commercial approval |
| Wan self-hosted family | Depends on exact model/weights | Unknown for chosen variant; requires separate benchmark | Research only; no added production provider |

## Azure DEV region
Microsoft currently lists Azure Container Apps serverless **T4 in Central India**, not A100 there. T4 nominal 16 GB VRAM is **not proof** that a 14-GB-offload Hunyuan model can run sustainably (CUDA, activations, torch overhead, cold start/latency). Do not provision before actual per-subscription quota, driver/CUDA/model compatibility and reservation caps are checked. Serverless GPU is supported on *Consumption workload profiles*, not Consumption-only environments, and can scale to zero. An alternative for future evaluation is an explicitly approved dedicated GPU VM/AKS batch job, with shutdown cost control. Existing Azure Functions remains CPU orchestrator only.

## Cost formula, before provisioning
Compute (USD) = (measured load/warmup seconds + measured GPU generation seconds) × **approved GPU+memory+CPU rate/second**, plus CPU Feature4 composition, output storage, transferred input weights, and egress. For multiple clips, add per-clip generation; reuse a loaded model only when it is cheaper than repeated cold starts without incurring unwanted idle GPU charges. Model weights transfer/caching, compliance and support may dominate short clips.

**Illustrative math only**, NOT Azure quote or performance benchmark: assume an all-in GPU rate of **$1.00/hour**, 120 seconds warm inference, 60 seconds cold start, 60 seconds CPU at $0.20/hour, 0.1 GB stored at $0.02/GB, and 0.05 GB egress at $0.10/GB: **$0.0604 per 5-second clip** (including illustrative cold start and ancillary line items). Six separate 5s clips cost **~$0.3624** under identical assumptions; one shared load across six sequential clips could be lower. If real inference takes 600s or incurs failed retries, cost rises sharply. No assertion 120-second Hunyuan inference is feasible on T4. The price web page does not currently render numeric regional GPU prices, so the real rate is **unverified**.

**Existing Part3 vendor comparator** (from `docs/part3/PROVIDERS_AND_COSTS.md`, not a fresh quote): Wan 2.7 Singapore 720p at $0.10/video-second -> 5s $0.50, six 5s clips composing 30s $3.00, excluding storage/egress/GST. This is not comparable quality/resolution (480p self-hosted vs 720p Wan) or a guaranteed savings calculation. CPU-only Feature4 alternative uses existing FFmpeg and stock/approved stills, avoiding generative GPU/model spend.

## Before allowing even one real GPU DEV test
1. Legal and geographic license sign-off and end-user provider disclosures; only authorized clothing/likeness media.
2. Verify exact model/weights checksum + pinned official runtime commit and 480p output settings.
3. Validate real Central India GPU SKU, per-subscription quota, explicit capped spend, trial limit and egress residency approval.
4. Run isolated DEV once with no public HTTP, GPU job max one concurrent, bounded timeout, no automatic paid retries; use original source + real output side-by-side for garment/face/temporal review.
5. Require coordinator's existing atomic subscription reservation, idempotency, optimistic claim fencing, private import and usage reconciliation before any customer launch.
6. Publish actual per-clip runtime/cost measurements and only then decide whether Hunyuan vs existing Wan is the default option.

Sources:
- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5
- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE
- https://huggingface.co/docs/diffusers/api/pipelines/hunyuan_video15
- https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
- https://azure.microsoft.com/en-in/pricing/details/container-apps/
- Existing RetailGrowthAI Part3 docs `docs/part3/PROVIDERS_AND_COSTS.md`

## 2026-10-26 additional hardware qualification
**Default BF16 restriction matters more than nominal VRAM.** Tencent official `generate.py` defaults to BF16 or FP32 (not an unrestricted FP16 selector). NVIDIA lists T4 as CUDA capability 7.5, versus A100 at 8.0, and BF16 hardware capability is not generally available on T4. Feature5's default local runner now rejects GPUs for which `torch.cuda.is_bf16_supported()` is false, including typical T4 configurations. An explicit FP32/T4 experiment requires a new reviewed memory/performance/quality profile; do **not** silently assume it fits.

Azure documents A100 serverless in East US and T4-only in Central India, but **no automatic cross-region forwarding** is authorized. Check residency, contractual permissions, provider licensing and subscription quota before proposing a real East US A100 trial; the original DEV platform remains Central India. No fabricated all-in A100/T4 price is provided until Azure's actual GPU + vCPU + RAM rate and cold load times are measured.

- Official CLI: https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/generate.py
- GPU architecture: https://developer.nvidia.com/cuda/gpus
- Regional inventory: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
