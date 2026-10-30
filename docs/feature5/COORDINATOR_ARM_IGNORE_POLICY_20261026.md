# Azure Feature5 ARM what-if: reviewed Ignore entries — 2026-10-26

## Observed live evidence

Authenticated GitHub DEV OIDC [Actions #40343432219](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40343432219) returned Azure ARM what-if:

- **Create**: `Microsoft.App/managedEnvironments/rgai-f5-gpu-canary-eastus` — exactly one target in the isolated `rg-retailgrowth-dev` group, East US
- **Ignore**: eight existing resource-group members (Smart Detector, Azure OpenAI, Application Insights, Log Analytics, Storage, App Service plan, Functions, Static Web App)
- **No observed Delete/Modify/Deploy/extra Create**. Original one-total-record assertion stopped before creation. The GPU itself is NOT provisioned.

Microsoft's [what-if docs](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-what-if) define `Ignore` as resources not present in the incremental template that **will not be deployed or modified**. An unused Consumption-only managed environment is a prerequisite to reading serverless NCA100 per-environment GPU quotas.

## Reviewed policy change

The coordinator-owned script `scripts/ci/feature5_arm_whatif_policy.py` accepts only:

1. One exact `Create` under the expected Azure subscription and `rg-retailgrowth-dev` to `rgai-f5-gpu-canary-eastus`.
2. Eight explicit, pre-existing `Ignore` items under the SAME subscription and resource group, each appearing exactly once.

It rejects any different resource, duplicate, missing entries, other subscription/RG, Modify, Delete, Deploy, Unsupported, Azure what-if errors or nonempty potential changes. `tests/ai/test_feature5_arm_whatif_policy.py` asserts these negative cases. The template is still pinned to ONE empty default Consumption environment, with no active GPU, log sink, ACR, app, job, VM or other new resource. Workflow is main-only and runs on first push of its YAML path, not on a recurring timer.

## Handoff

- Re-run only after reviewed PR CI and merge of the corrected coordinator workflow.
- Inspect real OIDC job; validate actual environment provisioning state and `Managed Environment Consumption NCA100 GPUs` quota limit/currentValue. Stop without GPU if missing.
- This action **does not authorize paid CUDA generation**: licensed Tencent Hunyuan 1.5 weights, regional terms, exact GPU sizing, approved full job cap, and video QA are still required.
- No WineShopPOS, voice, or RetailGrowthAI PROD mutation.
