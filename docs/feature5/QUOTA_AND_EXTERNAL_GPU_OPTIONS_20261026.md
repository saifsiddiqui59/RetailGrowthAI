# Feature #5 — GPU quota escalation and economical one-shot alternatives

Date: 2026-10-26. Scope: **DEV synthetic red-kurti T2V only**. This document is an evidence-based decision/operation aid, not a cloud execution receipt or a license grant.

## Independently verified existing state

- Azure DEV resource group: `rg-retailgrowth-dev`; East US existing empty workload-profiles environment: `rgai-f5-gpu-canary-eastus`. It has default Consumption only, not a GPU job or application. Actual GitHub OIDC creation/readback: [run #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764).
- Exact environment usage entry `ManagedEnvironmentConsumptionNCA100Gpus`: **limit 0 / used 0 / available 0**. Do not recreate the environment.
- Follow-on existing coordinator OIDC [run #40355181214](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40355181214): Central India and East US regional VM-vCPU quota 10 each; no usable A100 VM capacity in tested account, full A10 24 GiB profile requires more regional vCPU than currently allocated. A public SKU catalog is not account quota.
- No evidence of a successfully submitted quota request, approved quota=1, installed pinned licensed Tencent weights, paid CUDA call or generated real MP4.

## Correct Microsoft quota process (validated against updated documentation)

Official Microsoft [Container Apps quota guide](https://learn.microsoft.com/en-us/azure/container-apps/quotas) and [quota request guide](https://learn.microsoft.com/en-us/azure/container-apps/quota-requests) distinguish **managed-environment serverless GPU quota** from **regional subscription dedicated NCA100 GPU quota**.

1. On the authorized RetailGrowthAI DEV subscription open Azure Portal → Container Apps **environment** `rgai-f5-gpu-canary-eastus`, under `rg-retailgrowth-dev`.
2. Open **Settings → Quota**, choose `Managed Environment Consumption NCA100 GPUs`, request **new limit 1**. The existing row was observed via OIDC CLI, so the environment and quota key are not guesses.
3. Record Azure's actual submission/approval state and new `az containerapp env list-usages --resource-group rg-retailgrowth-dev --name rgai-f5-gpu-canary-eastus` response. A submitted request is NOT an approved quota; approval also is NOT real deployment capacity.
4. If Azure routes the request to quota review/support, follow Microsoft's resulting flow. Do not create a technical incident for this ordinary quota limitation; do not attempt a fallback by requesting unrelated dedicated regional GPU quota.
5. Once limit >= 1 and used < limit are verified, **do not deploy immediately**: licensed weight lock, actual CUDA image, Tencent rights, synthetic-only region, total bill quote, one-job no-retry with external termination assurance, and private evidence remain mandatory.

**CLI/REST finding:** Official docs show `az containerapp env list-usages` to **read** usage, but provide the managed-environment **Quota page** to submit that specific increase. No supported documented Azure CLI/REST quota-increase submission API was confirmed for this scope. Do not post guessed ARM mutations through OIDC. The existing GitHub connector also has no workflow-dispatch action, and Feature5 workers do not own `.github/workflows/**`.

Serverless A100 region support in [Microsoft GPU overview](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview) includes East US and excludes Central India. Catalog availability does not imply subscription GPU allotment or temporary capacity.

## Price-screened fallback for the *same* official Tencent HunyuanVideo 1.5

Tencent's [HunyuanVideo 1.5 README](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) documents NVIDIA CUDA, **minimum 14 GB VRAM only with offloading**, and default **50 inference steps for 480p T2V**; it reports 8–12-step acceleration specifically for its 480p **I2V step-distilled** variant. Do not promise eight-step red-kurti **text-to-video** or substitute a generic video model.

Price discovery 2026-10-26, USD headline/on-demand examples only:

| Candidate | Published reference | Raw 30-minute GPU cost, excluding all other charges | Feasibility and operational caveat |
|---|---|---:|---|
| Existing Azure East US serverless A100 | Existing official Retail Prices snapshot: GPU $0.000529/s, plus CPU/RAM | $0.9522 GPU alone; ~$1.2114 with illustrative 4 vCPU/16 GiB for 1800s | Quota is **0**; must secure environment quota 1. Actual allocation might differ from 4/16 assumption |
| Runpod A40 48 GB Pod | [Official Runpod price list](https://www.runpod.io/pricing): $0.59/hr advertised | $0.295 | BF16 capable and larger VRAM than 24GB cards, but exact instance RAM/location/availability, paid idle, storage and image pulls must be checked; no model run benchmark |
| Runpod RTX 4090 24 GB Pod | [Official Runpod price list](https://www.runpod.io/pricing): $0.89/hr advertised | $0.445 | BF16 capable, only 24 GB VRAM; 50-step T2V with offload may exceed 30-minute timeout |
| Runpod A100 80 GB Serverless | [Official Runpod price list](https://www.runpod.io/pricing): $2.72/hr listed | $1.36 | Cold starts/downloads can dominate; actual worker billing modes differ from Pods |
| Vast.ai marketplace 4090 / A100 | [Vast's changing live prices](https://vast.ai/pricing) | **No reliable fixed amount** | Host-specific price, trust, storage, geography, interruption and availability must be individually inspected, not assumed from advertised minimum |

All headline prices **exclude** storage, transfer, failed attempts, persistent volumes, setup and taxes. They are neither a commitment nor measured Hunyuan runtime. A 30-minute quote does not establish completion within 30 minutes. A job timeout in Python does **not** stop an external GPU pod; require a provider-side termination/stop control and spending/prepaid ceiling **before** creating one. Limit 1 GPU, no retries, no auto scale, isolated throwaway synthetic inputs and delete disks after private evidence is secured.

**Recommendation:** First seek the existing Azure managed-environment quota=1 (no GPU provision needed for the request). For an urgent independent genuine sample, evaluate an on-demand **Runpod A40 48 GB**, *after* account-specific price, country, actual 40+ GiB system RAM, CUDA BF16, model license and termination controls are verified. Avoid automatically using a lower-priced, less trusted community host for customer data. Feature5's current official `HunyuanLocalRunner` is local-GPU portable but the manual acceptance harness is Azure-price-gated; an external quote review does not silently activate paid inference.

## New safe CPU-only provider comparison code

`feature5_motion/external_gpu_budget.py` accepts an *operator-provided* small quote with exact reviewed SHA256. It rejects unknown provider/GPU, preemptible mode, fewer than 40 GiB host RAM or 24 GiB GPU family, multiple GPUs, non-USD prices, stale/future/over-one-day quote validity, unexpected keys, duplicate JSON keys, symlinked/tampered file and over-ceiling worst-case rental quote. It calculates quoted maximum exposure including storage/hour, billing minimum and ancillary reserve, and reports **QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION**. It performs **zero cloud/network/CUDA operations**.

A quote is not a payment limit or price verification; account billing may persist beyond the Python process. Code intentionally does not automate Runpod/Vast provisioning or falsely claim provider termination controls. If using an external provider, coordinator must approve a separate teardown-verified, paid-cap-aware operator execution procedure before allowing a genuine Hunyuan sample.

Example (illustrative quote, **not** operator approval):

```json
{
  "provider": "runpod", "sku": "RTX_4090_24GB",
  "gpu_count": 1, "system_ram_gib": 48,
  "region": "us-east-1", "country": "US",
  "billing_mode": "on_demand", "currency": "USD",
  "compute_usd_per_hour": "0.89", "storage_usd_per_hour": "0.02",
  "minimum_billable_seconds": 60,
  "quoted_at": "2026-10-26T12:00:00Z",
  "expires_at": "2026-10-26T23:00:00Z"
}
```

Quote SHA256 must be kept *outside* the quote file and confirmed against the chosen vendor account. Never pass real retailer media or credentials in GitHub source, job logs, CI attachments or community Cloud. Tencent's conditional Community License, output territories, model weight provenance and hosted notice requirements apply on any provider.

## Acceptance needed before real sample can be claimed

For **one** red-and-gold kurti T2V: licensed pinned Tencent runtime+model shards, independently reviewed `ArtifactLock`, provider-specific CUDA BF16 result, true 5s/480p portrait/24fps H264 MP4, `ffprobe` and SHA256, six-frame contact sheet, private review packet, actual wall-clock and account invoice, confirmed stop/deletion, and human garment/face/hands review. There is **no MP4 from this work**, and a synthetic FFmpeg clip does not satisfy this gate.

## Provider-side termination guard (required for actual rental)

Runpod's [official Pod CLI reference](https://docs.runpod.io/runpodctl/reference/runpodctl-remove-pods) documents `--terminate-after 1h` on Pod creation and states it **permanently deletes the Pod**, unlike `--stop-after`. For a one-shot demo, provisioned Pod settings must confirm one GPU, Secure Cloud where available, explicit permitted country, image digest, no public inference port, **automatic termination within one hour**, and later API readback that the Pod is actually terminated. Persistent separately purchased network volumes may remain billable even after a Pod is deleted; avoid them for the pilot or independently delete and reconcile. This is **research, not executed**.

The new quote checker requires `provider_termination_after_seconds` at least 60 seconds beyond the process timeout and at most 3600. Its estimate is based on the **whole provider auto-termination window**, including minimum billing, not only CUDA subprocess time. Example: the illustrative Runpod RTX 4090 quote at $0.89/hour + $0.02/hour disk and $0.05 ancillary reserve with a 1-hour auto-termination bound is **$0.9600**, versus just $0.2017 if one naively counted a 10-minute Python timeout. It is still not a guaranteed upper limit on a malfunctioning provider, currency conversion, taxes or retained network storage. A real rental needs an approved prepaid/account cap and verified stop/delete readback.

`runpodctl` is **not installed or connected** here, and no Runpod account, GPU region/stock, credit balance or provider API credential was inspected. A safe illustrative command is deliberately not executable without operator-supplied vetted values:

```sh
# OPERATOR REVIEW ONLY — DO NOT EXECUTE BEFORE LICENSE, COST, REGION & CREDIT GATES
runpodctl pod create --image '<PINNED_APPROVED_IMAGE>' \
  --gpu-id '<EXACT_ACCOUNT_AVAILABLE_48GB_A40>' --gpu-count 1 \
  --cloud-type SECURE --country-code US --terminate-after 1h
```

A provider-side teardown option does not replace on-instance CUDA 1800s maximum timeout or independent verification of actual post-job termination. Operator must copy the genuine local MP4 and private evidence **before** deletion, avoiding public URLs and GitHub CI artifacts.
