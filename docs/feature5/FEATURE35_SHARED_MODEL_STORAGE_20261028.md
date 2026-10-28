# RetailGrowthAI Feature #3 + #5 — Shared Azure Files Model Staging
Date: 2026-10-28. Scope: **RetailGrowthAI DEV only**. No GPU operation.

## Desired configuration
- Existing subscription and `rg-retailgrowth-dev`, exact dev ownership tags.
- New East US **StorageV2 / Standard_LRS** account `rgaimodelseastus26` to match Feature5 Azure A100 environment region, not the existing Central India production/function storage.
- One classic SMB pay-as-you-go **Azure Files Cool LRS** share `retailgrowth-models`, **64 GiB quota**. Under PAYG billed bytes are ~34 GB (six model files), not full 64 GiB, plus operations and taxes. Quota is not a hard financial cap.
- Model structure:
  - `feature3/diffusion_models/flux-2-klein-4b.safetensors`
  - `feature3/text_encoders/qwen_3_4b.safetensors`
  - `feature3/vae/flux2-vae.safetensors`
  - `feature5/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors`
  - `feature5/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors`
  - `feature5/vae/wan2.2_vae.safetensors`
- Source: official Comfy-Org Hugging Face repos, with pinned commit resolved and verified published SHA-256; download streams over HTTPS and upload 4 MiB ranges. A completion manifest in the private share is written only after all six files are successful. No model bytes in repository or CI artifacts.

## Execution and safety
- Coordinator-owned workflow: `.github/workflows/retail-dev-feature35-stage-models-once.yml`.
- One-time `push` to **main** of the reviewed workflow, explicit `environment: dev`, existing GitHub Azure DEV OIDC; do not run on feature branches/PR or change branch protection.
- Fail closed if wrong subscription, tenant RG tags, region, StorageV2/LRS, Cool SMB share, size/digests, 64 GiB share quota or prior mismatched files.
- Creates neither A100, T4, Azure Container App nor model-serving endpoint. Existing dedicated model storage is recurring billable even with GPU OFF.
- The owner specifically requested **both Feature #3 and #5 in the same share**. No shared customer uploads; do not copy WineShopPOS assets.
- Owner's first portal execution verified `rg-retailgrowth-dev` and existing Central India account `rgaid4e5ddbdf0d21d96` with the East US GPU environment; read-only.
- Second portal create attempt stopped before Review/Create, leaving **no new storage account or share**. The first branch-triggered GitHub OIDC job was rejected before any step (environment branch gate), with no Azure changes. Coordinator main-only workflow is the tested access route. Do not claim provisioning or upload until a successful main workflow and storage readback.
- Azure Container Apps only supports directly mounting **classic** file shares (`Microsoft.Storage`), not new `Microsoft.FileShares`. See https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts and https://learn.microsoft.com/en-us/azure/storage/files/understanding-billing .

## Actual evidence needed after main merge
Workflow main run URL and actual success/failure; `az storage account show` regional/sku/tags; ARM share Cool/64GiB details; each `feature3/` and `feature5/` file size/SHA256 and `models-sha256-manifest.json`. No inference/quality claims from model-file readiness.
