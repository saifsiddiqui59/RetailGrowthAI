# Feature #5 — authenticated Azure DEV portal read-only evidence (2026-10-26)

**Status: user Azure sign-in saved; no Hunyuan GPU deployment.** Source: two separate signed-in Azure Portal read-only inspections in the user's saved browser profile on 2026-10-26. The evidence below is an inventory checkpoint, not proof of quota or deployment access.

## Confirmed from first portal inspection

- Saved profile has a Microsoft sign-in and Azure Portal successfully opened **Azure subscription 1**, Default Directory.
- The dedicated existing resource group `rg-retailgrowth-dev` in **Central India** was visible. Azure portal showed `app=RetailGrowthAI` and `environment=dev` tags.
- Observed 8 resources inside DEV RG: private StorageV2 account `rgaid4e5ddbdf0d21d96`, Central India Function App `rgai-dev-functions-d4e5ddbd`, `rgai-dev-flex` plan, SWA `retailgrowthai-dev-preview`, `rgai-dev-appinsights`, `rgai-dev-law`, Azure OpenAI `rgai-dev-openai-d4e5ddbd`, and anomaly detector.
- No existing Azure Container Registry in this DEV group and no existing GPU VM/Container Apps in it.
- Subscription's visible Azure Container Apps environments inventory contained one environment `vobiz-stream-env` in a **separate voice-project RG** in Sweden Central; do not touch. **No existing East US A100 Container Apps environment was visible.**
- **A100 quota was not checked** in the first inspection. Lack of an environment is NOT proof of a zero quota or inability to create one. Published A100 rates are not quota evidence.

## Second targeted quota attempt

- The Azure Portal's generic `Subscriptions` blade reported `Filtered (0 of 0)`, even after filters were cleared, in its displayed directory context. Consequently the `Usage + quotas` page for the above subscription could not be opened during this second inspection.
- Because the first audit DID see the subscription and exact DEV group, this is a **directory-context, portal filtering, session or access ambiguity**. Do NOT state that the user lacks Azure rights or that Azure rejected A100: neither is proven.
- We did NOT submit a quota request, change directories/access roles, touch resource settings, create anything or spend Azure GPU money.

## Direct user action to resolve the portal blade discrepancy

1. In the signed-in Azure Portal open the top-right **Settings (gear) → Directories + subscriptions**, select the directory/subscription where `rg-retailgrowth-dev` is visible, and ensure `Azure subscription 1` is in the subscription filter.
2. In **Subscriptions → Azure subscription 1 → Usage + quotas** or the separate **Quotas** service, select **Container Apps**, **East US**. Read **Managed Environment Consumption NCA100 GPUs** used/limit/available, if listed. Do not request a quota change or create resources yet.
3. If it is not listed, report **not visible** rather than inventing a zero quota; an authenticated Azure CLI/OIDC query for Container Apps GPU workload-profile quota and account eligibility may be needed.
4. For the first demo use the existing fictional **T2V fashion prompt only**, one explicit A100 execution after verifying actual allowed region/Tencent terms/model weights/image and full price cap; zero retries and no PROD/WineShopPOS changes.

## Feature5's existing preparation (NOT deployment)

- `feature5_motion/azure_gpu_readonly_cli.py` can inspect exact DEV subscription/tagged group, supported East US A100 profile, existing A100 environments and quota read-only in an already authenticated Azure CLI/OIDC session. Running it within ChatGPT was not possible because no Azure CLI/credentials are installed in this execution environment; code-tested mocks are not cloud evidence.
- Source-only `demo_fashion.py`, `runner.py`, `artifact_lock.py` and single-mode manual GPU test are present on draft Feature5 PR #323. **No licensed weight shards or genuine Hunyuan-generated MP4 are present.**
- Model-weight size/VRAM/latency, actual region-supported A100 job model and billed dollar limit remain unverified. Do not claim feature completion or deploy speculatively.
