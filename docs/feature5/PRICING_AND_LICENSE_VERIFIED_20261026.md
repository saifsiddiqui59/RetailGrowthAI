# Feature #5 — Verified Azure pricing and permitted roll-out snapshot
Date: 2026-10-26 (official Microsoft Retail Prices API, USD, PAYG primary meters)

## Official source and rates (not a deployment record)

Microsoft Azure Retail Prices API:
- https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName%20eq%20%27Azure%20Container%20Apps%27%20and%20armRegionName%20eq%20%27eastus%27
- https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName%20eq%20%27Azure%20Container%20Apps%27%20and%20armRegionName%20eq%20%27centralindia%27

| PAYG meter | East US, USD | Central India, USD | Billing unit |
|---|---:|---:|---|
| Standard NC A100 v4 GPU Usage | 0.000529 | 0.000741 | 1 second |
| Standard NC T4 v3 GPU Usage | 0.000073 | 0.000102 | 1 second |
| Standard vCPU Active Usage | 0.000024 | 0.000024 | 1 second per vCPU |
| Standard Memory Active Usage | 0.000003 | 0.000003 | 1 GiB second |

A100 listed pricing in Central India DOES NOT mean it can be deployed there: Azure Container Apps' *GPU serverless overview* lists Central India as T4 **only**, East US as A100/T4. Serverless GPU quota is per-subscription/environment and MUST be verified. The primary A100 East US retail meter became effective 2026-04-01; pricing may change.

PAYG East US A100 example assuming 4 vCPU, 16 GiB active RAM, no free grant:
- GPU rate 0.000529 + 4 × 0.000024 + 16 × 0.000003 = **$0.000673/sec** for the assumed active compute configuration.
- 300s including load + inference + teardown ≈ $0.201900
- 600s ≈ $0.403800
- 900s ≈ $0.605700
- 1800s ≈ $1.211400

These are metered *duration scenarios*, not measured HunyuanVideo 1.5 clip generation times. Six completely separate 600-second jobs might cost 6 × 0.4038 = $2.4228 in this assumed profile; a shared bounded model-load session could differ materially. EXCLUDES storage, internet egress, image/weight transfer, extra memory/vCPU, licenses, GST/taxes, currency conversion, provider and media costs, and idle/management overhead where applicable. GPU meter and resource allocation must be rechecked with the Azure account before scheduling even one actual paid test.

## Real test gate despite owner approval

The owner authorized development and real GPU testing in chat, but provided no maximum aggregate spend, no connected Azure subscription credentials/quota, no reviewed outbound media region transfer and no checked Tencent license-use statement. Therefore:
1. Do NOT deploy an always-on GPU or leave an app with min replicas >0.
2. When operator access is available, run a single explicitly configured bounded TEST with job concurrency=1, max attempts=1, timeout <=1800s, consumption workload profiles and target regional availability check; record START/STOP, observed GPU+CPU+RAM charges.
3. Make the pilot's hard spending cap smaller than the approved maximum and reconcile uncertain cloud acknowledgments before any replay.
4. Use non-customer licensed/approved test imagery while India->US regional transfer and user consent are evaluated. No real customer imagery must be transferred without explicit consent.
5. Commercial release requires Tencent hosted-service terms, third-party notices, use limitation, origin/recipient territory controls, and MAU threshold confirmation. India-only is a reasonable proposed pilot scope, not a substitute for legal review.

## License finding
HunyuanVideo 1.5 weights are under **Tencent Hunyuan Community License**, not an unrestricted Apache or MIT license. Territory excludes EU, UK and South Korea, including output distribution; >100-million MAU threshold triggers separate licensing; requirements for notices, acceptable uses, hosted distribution, generated material rights and third-party content remain binding. Acceptance of user-provided approval in chat is NOT Tencent approval or legal clearance.

Sources:
- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE
- https://huggingface.co/tencent/HunyuanVideo-1.5/blob/main/LICENSE
- https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
- https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
