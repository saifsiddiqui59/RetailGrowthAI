# Feature #5 — Azure GPU canary deployment checkpoint (2026-10-26)

**Status: NOT DEPLOYED.** User requested one authentic HunyuanVideo sample on Azure at minimum spend. This is a coordinator-owned Azure DEV infrastructure handoff and a verified **read-only preflight**, not a live GPU job. No customer media, PROD or WineShopPOS changes permitted.

## Why GPU deployment has not happened
- The active ChatGPT execution container has **no `az`, `docker`, NVIDIA driver, CUDA GPU or installed Tencent licensed Hunyuan weights**. GitHub OIDC credentials **are** configured in repository DEV workflows, but the GitHub connector available here has no Azure control-plane write action.
- An Azure Portal browser profile has been offered to the user for authenticated login; **the user must sign in and save it** before an interactive Azure inspection or deployment can be undertaken from that browser. The profile setup link is a short-lived sign-in invitation, not a cloud resource/deployment.
- The existing Azure DEV resource group is `rg-retailgrowth-dev` in **Central India**, with strict `app=retailgrowthai` and `environment=dev` ownership tags. This is from the repository OIDC inventory convention; actual currently existing GPU environments and quota have NOT been inspected through Azure.
- Microsoft officially lists **A100 available in East US, but not Central India** for *serverless Container Apps GPU*. Central India lists T4, which cannot be assumed compatible with this BF16 Hunyuan runner; no retailer/customer data may move overseas. References: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview ; https://learn.microsoft.com/en-us/azure/container-apps/quotas .
- Tencent HunyuanVideo-1.5 official requirements: CUDA GPU, minimum 14GiB VRAM when offloaded, separately downloaded checkpoints, Tencent Community License (hosted terms, territory restrictions, other obligations). References: https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5 and its LICENSE. We have **not** licensed/pinned/staged actual model weights.

## Verified low-risk deployment choice (once access/preflight is ready)

- **Scope**: one manual, ephemeral **East US A100** job for a fictional adult red-kurti fashion model from our *text prompt only*. Never copy actual Indian retailer photos or sensitive tenant data outside consented territory.
- **Resource**: manually triggered Azure Container Apps Job with a single replica, at most **one** execution, **zero automatic retries**, strict execution timeout and no public HTTP ingress. A workload-profiles environment and confirmed positive **Managed Environment Consumption NCA100 GPUs** quota are prerequisites. Confirm API/CLI job GPU support and exact supported workload profile at deployment time; do not guess from A100 price-meter existence.
- **Runtime**: audited, pinned Tencent 1.5 code and full model shard SHA256 lock, build a minimal immutable CUDA image and private Azure model-weight staging with versioned permissions, then run `fashion_motion_spec` in `RETAIL_FEATURE5_ACCEPTANCE_MODE=text`. Keep web/Foundry/vLLM prompt rewriting disabled to avoid extra API cost.
- **Evidence**: real `clip.mp4` with 480p/24FPS/5sec ffprobe, sha256, six actual PNG frames and local/private contact-sheet marked `PENDING_HUMAN_REVIEW`. Match full model manifest, Azure region, observed elapsed/runtime and invoice record. No publishing; user sees **actual MP4** only after verification.
- **Controls**: authenticated signed-in subscription, owner/role and exact tenant, one-time paid spend authorization and region, no automatic restart/retry, privacy-compliant storage, clear teardown plan and post-run Azure Cost Management check. Creating a budget alert is NOT a guaranteed hard cost limit; model weight pulls, storage, network and image build may incur additional charges.

## Read-only probe implementation (committed to isolated Feature5 branch)

```bash
# In a signed-in, authorized Azure CLI session/DEV OIDC runner:
export AZURE_SUBSCRIPTION_ID='<the existing DEV subscription ID from secure secret>'
python -m feature5_motion.azure_gpu_readonly_cli
```

This inspects, without writes: exact account enabled, exact `rg-retailgrowth-dev` and ownership tags, `az containerapp env workload-profile list-supported --location eastus`, current Azure Container Apps DEV environments, A100 workload profiles and **available managed-environment A100 GPU quota**. `INSPECTION_PASS_ONLY` means quota/inventory only; it is **not** a deployment, and it does not verify image/weights/permissions/budget. `BLOCKED` is the expected safe result when no East US A100 DEV environment already exists or quota is unreadable. It intentionally makes no resource create/update/delete calls. Coordinator must do cloud preparation only after actual Azure login and owner-reviewed spending plan.

## Illustrative PAYG estimate, NOT a cap or invoice

Previously checked Azure East US primary meter rates: A100 $0.000529/s, active CPU $0.000024/vCPU-s, active memory $0.000003/GiB-s. At a purely illustrative **4vCPU, 16GiB and 600s** plus $0.05 ancillary, quoted GPU/CPU/memory estimate = **$0.4538**. This does NOT establish that 16GiB RAM is sufficient (Tencent offloading may demand much more), that a real generation finishes in 600s, or that Azure bills only those exact seconds. A **1,800s** example on the same insufficiently validated allocation would be $1.2614 before any unmodeled costs. Query model runtime/image/CPU/RAM requirements and actual subscription/region/usage immediately before approval. Account has no hard-coded spend approval in repository.

## Remaining to execute, in order

1. User saves signed-in Azure Portal browser profile or makes an authenticated Azure management workflow available. Determine actual subscription, isolated DEV RG, A100 environment/quota, permission and supported regions **read-only**.
2. Obtain official Tencent model weights/checkpoints from licensed source, pin source+weights SHA256, legal provider/territory verification, pre-stage on allowed private storage, and containerize/test CUDA dependencies. (Weights and image not currently present.)
3. Approve exact one-run real total budget after testing packaging and workload profile size, then deploy **one** manual A100 job; no auto scaling >1, scheduled polling, PROD resources or retailer media.
4. Record real, human-reviewable MP4 evidence, stop/remove temporary GPU resources, inspect Azure actual charges, hand off accepted media for Feature4 coordinator integration. Do not close PR #323 until then.

**Do not claim a real GPU deployment, paid test, model sample or live Part3/Feature4 integration at this checkpoint.**
