# Feature #5 — Azure GPU quota fallback investigation (2026-10-26)

**Source-verified cloud status:**
- Existing GitHub DEV OIDC successfully created the isolated East US Container Apps managed environment `rgai-f5-gpu-canary-eastus` with default **Consumption only**, no GPU workload, application, job, or log sink. [Real successful workflow #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764).
- The live provider returned `ManagedEnvironmentConsumptionNCA100Gpus`: **limit 0; used 0**. This is not a cost limit; it prevents any A100 serverless GPU from being allocated until approved. The environment is not a GPU deployment, and no real HunyuanVideo sample has run.
- Official [Container Apps quota docs](https://learn.microsoft.com/en-us/azure/container-apps/quota-requests) direct managed-environment NCA100 quota requests to the environment **Quota** page, where requests may route to Azure Support. We are not creating a support case or automatically requesting quota here.
- Tencent's [HunyuanVideo-1.5](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) documents minimum 14 GB CUDA VRAM **with model offloading**; performance and stability are *not validated* on our Azure alternative VMs. The currently integrated Feature5 runner requires CUDA BF16; NVIDIA A10 Ampere may be a **candidate** while Tesla T4 is not assumed compatible with native BF16. Actual Azure VM families, quota, region availability, and billable rate require verification first.

## Alternative no-cost diagnostic

The coordinator-installed, main-only `.github/workflows/retail-dev-feature5-gpu-vm-inventory.yml` reuses the existing `dev` OIDC secret identity. It performs **read-only** `az vm list-usage` and `az vm list-skus --all` for `centralindia` and `eastus` to identify VM-family vCPU quota limits/usage and A10/A100 SKU restrictions. No VM/GPU/disk/network is provisioned; negative CI guard in `tests/ai/test_feature5_gpu_vm_inventory_ci.py`.

Running this workflow on first merge to main can determine whether any in-subscription Azure GPU option exists **without requesting another quota**. A published SKU alone does not prove quota, allocation capacity or a running compatible Hunyuan inference stack.

## Further action

1. Read exact post-merge OIDC inventory logs and assess whether a relevant Ampere GPU VM SKU is regionally offered, un-restricted and has **positive remaining family and regional vCPU quota**. If missing, don't launch.
2. For A100 serverless, request only **1 managed-environment Consumption NCA100 GPU** via Azure's existing environment Quota page (subject to Microsoft approval); quota request itself does not start a GPU or create recurring compute costs. User previously rejected support tickets for other Azure issues; no case created here.
3. Actual inference further requires verified licensed official Tencent weight shards and manifest, BF16 driver/CUDA, strict synthetic-only region approval and **explicit full single-run price ceiling**. Do not claim a real Hunyuan-generated MP4 before running CUDA and checking ffprobe+video evidence.
4. Protect WineShopPOS, separate voice project, RetailGrowthAI PROD and other coordinators' active branches. No TinyFish browser automation used.

**Status:** This workflow is source-only until its merge and actual cloud run; do not infer quota from planned or mocked tests.
