# F5 historical parent #323 original patch hunks — part 1 of 2

- Source head: `ffc464c09f719a0bfb6b15b5c34608f89d76234b`; original PR https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323
- This file preserves 33 original GitHub changed-file patch hunks *exactly*. This is non-executing archive data, not recovered F5 runtime integration.
- Current-main recovery already merged: #1011 GPU-OFF manifest/contract subset with exact-head + postmerge 4/4; #1013 human QA source is a separate active cross-feature review PR. Do not overwrite newer current main with historical worker, pricing or Azure GPU deployment code.
- Original Feature5 22 task IDs and #125/#724 review/rights remain open; no weights, model execution, GPU, remote Azure Files readback, paid services, PROD or WineShopPOS are authorized by this archive.

## docs/feature5/ARM_CUSTOM_DEPLOYMENT_DISCREPANCY_20261026.md

~~~~diff
@@ -0,0 +1,96 @@
+# Feature #5 — Azure Portal ARM deployment discrepancy
+
+Date: 2026-10-26. **Production GPU: NOT DEPLOYED. Actual Hunyuan MP4: NONE.**
+
+## Observed live cloud state
+
+Using the owner's saved Microsoft Azure Portal login, a tightly scoped ARM
+custom-template deployment was submitted against the EXISTING
+`Azure subscription 1` and existing `rg-retailgrowth-dev`.
+
+- ARM deployment name reported by the portal:
+  `CustomDeployment-20261026093554`.
+- Target resource: `Microsoft.App/managedEnvironments`,
+  `rgai-f5-gpu-canary-eastus`, in `eastus`.
+- Template requested only the default v2 `Consumption` workload profile,
+  `appLogsConfiguration.destination=none`, and ownership tags. No container,
+  job, GPU instance, ACR, networking or Log Analytics new resource.
+- Azure portal briefly showed **Deployment succeeded**.
+- **However:** later the same resource group resource list showed only the
+  original eight resources; searching for the target name returned none.
+- The follow-up read-only portal audit could not open the deployment's
+  operations/template details because browser automation exhausted its
+  usage budget. Thus the success notification **is NOT proof** of a created
+  managed environment. No evidence of a GPU job/model inference exists.
+
+Do not submit the template a second time or assert that Azure's A100 quota
+is zero until the precise ARM deployment record is examined. An ARM
+deployment can report Succeeded with an empty `resources` array, or a
+portal's resource-list view can lag; neither is established without a read.
+
+## Exact coordinator-only OIDC read-only reconciliation
+
+Use existing GitHub `environment: dev` federation; **no credential values,
+access tokens, subscription IDs or tenant keys in logs**. Only the project
+coordinator may edit `.github/workflows/**` or apply shared deployment.
+
+```bash
+set -euo pipefail
+RG=rg-retailgrowth-dev
+ENV=rgai-f5-gpu-canary-eastus
+DEPLOYMENT=CustomDeployment-20261026093554
+test "$(az account show --query state -o tsv)" = Enabled
+test "$(az account show --query id -o tsv)" = "$AZURE_SUBSCRIPTION_ID"
+test "$(az group show -n "$RG" --query tags.app -o tsv)" = RetailGrowthAI
+test "$(az group show -n "$RG" --query tags.environment -o tsv)" = dev
+
+# Read-only: reconcile whether succeeded deployment had any resource changes.
+az deployment group show -g "$RG" -n "$DEPLOYMENT" \
+  --query '{name:name,state:properties.provisioningState,mode:properties.mode,template:properties.template.resources}' -o json
+az deployment operation group list -g "$RG" -n "$DEPLOYMENT" \
+  --query "[].{state:properties.provisioningState,target:properties.targetResource.id,status:properties.statusCode}" -o json
+az resource list -g "$RG" --resource-type Microsoft.App/managedEnvironments \
+  --query "[].{name:name,location:location,state:properties.provisioningState,tags:tags}" -o json
+az provider show -n Microsoft.App --query registrationState -o tsv
+```
+
+**Decision path:**
+
+- If target environment is present, verify it is exactly East US, tagged DEV,
+  `appLogsConfiguration.destination=none`, v2 with Consumption profile only,
+  no GPU/app/job/dedicated nodes. Then, and only then, run:
+  `az containerapp env list-usages -g "$RG" -n "$ENV" -o json`.
+- If the deployment's `template.resources` is empty, its successful status
+  created nothing. Use the version-controlled strict
+  `feature5_motion/infra/empty_gpu_env.json`, perform ARM what-if and
+  `validate_template`/`validate_what_if`, and *only coordinator-approved*
+  create of ONE empty environment.
+- If the deployment contains target resource but operations show Failed or a
+  partial state, do not retry until the exact ARM error and residual resource
+  state are reconciled. Do not silently change providers, billing, roles or
+  PROD resources.
+- If the provider cannot be read due to RBAC or Microsoft.App registration,
+  record the precise error; don't invent a zero quota.
+
+Azure official docs:
+https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
+(An East US workload-profiles environment must exist before environment GPU
+quota is visible/requestable.)
+https://learn.microsoft.com/en-us/azure/container-apps/quotas
+(Quota for Managed Environment Consumption NCA100 GPUs is per-environment.)
+
+## Local Feature5 source committed and tested
+
+`feature5_motion/empty_env_template.py` validates one fixed zero-active-
+compute environment and fails closed on extra GPU, paid profiles or logging.
+`feature5_motion/azure_gpu_preflight.py` now returns
+`ENVIRONMENT_REQUIRED` on no existing owned East US environment instead of
+pretending the quota is zero. `azure_gpu_readonly_cli.py` reads usage for
+the exact owned empty environment, not an already provisioned A100 profile.
+
+Previous 4vCPU/16GiB illustrative pricing is NOT sufficient as a verified
+A100 profile allocation. Microsoft describes up to 24vCPU/220GiB for the
+A100 Consumption GPU type. Even after quota is known, official full
+vCPU+memory+GPU billable time and model weights must be checked before
+a single zero-retry synthetic Hunyuan sample. **No actual CUDA model generation
+or real MP4 has happened.**
~~~~

## docs/feature5/AZURE_GPU_CANARY_DEPLOYMENT_20261026.md

~~~~diff
@@ -0,0 +1,41 @@
+# Feature #5 — Azure GPU canary deployment checkpoint (2026-10-26)
+
+**Status: NOT DEPLOYED.** User requested one authentic HunyuanVideo sample on Azure at minimum spend. This is a coordinator-owned Azure DEV infrastructure handoff and a verified **read-only preflight**, not a live GPU job. No customer media, PROD or WineShopPOS changes permitted.
+
+## Why GPU deployment has not happened
+- The active ChatGPT execution container has **no `az`, `docker`, NVIDIA driver, CUDA GPU or installed Tencent licensed Hunyuan weights**. GitHub OIDC credentials **are** configured in repository DEV workflows, but the GitHub connector available here has no Azure control-plane write action.
+- An Azure Portal browser profile has been offered to the user for authenticated login; **the user must sign in and save it** before an interactive Azure inspection or deployment can be undertaken from that browser. The profile setup link is a short-lived sign-in invitation, not a cloud resource/deployment.
+- The existing Azure DEV resource group is `rg-retailgrowth-dev` in **Central India**, with strict `app=retailgrowthai` and `environment=dev` ownership tags. This is from the repository OIDC inventory convention; actual currently existing GPU environments and quota have NOT been inspected through Azure.
+- Microsoft officially lists **A100 available in East US, but not Central India** for *serverless Container Apps GPU*. Central India lists T4, which cannot be assumed compatible with this BF16 Hunyuan runner; no retailer/customer data may move overseas. References: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview ; https://learn.microsoft.com/en-us/azure/container-apps/quotas .
+- Tencent HunyuanVideo-1.5 official requirements: CUDA GPU, minimum 14GiB VRAM when offloaded, separately downloaded checkpoints, Tencent Community License (hosted terms, territory restrictions, other obligations). References: https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5 and its LICENSE. We have **not** licensed/pinned/staged actual model weights.
+
+## Verified low-risk deployment choice (once access/preflight is ready)
+
+- **Scope**: one manual, ephemeral **East US A100** job for a fictional adult red-kurti fashion model from our *text prompt only*. Never copy actual Indian retailer photos or sensitive tenant data outside consented territory.
+- **Resource**: manually triggered Azure Container Apps Job with a single replica, at most **one** execution, **zero automatic retries**, strict execution timeout and no public HTTP ingress. A workload-profiles environment and confirmed positive **Managed Environment Consumption NCA100 GPUs** quota are prerequisites. Confirm API/CLI job GPU support and exact supported workload profile at deployment time; do not guess from A100 price-meter existence.
+- **Runtime**: audited, pinned Tencent 1.5 code and full model shard SHA256 lock, build a minimal immutable CUDA image and private Azure model-weight staging with versioned permissions, then run `fashion_motion_spec` in `RETAIL_FEATURE5_ACCEPTANCE_MODE=text`. Keep web/Foundry/vLLM prompt rewriting disabled to avoid extra API cost.
+- **Evidence**: real `clip.mp4` with 480p/24FPS/5sec ffprobe, sha256, six actual PNG frames and local/private contact-sheet marked `PENDING_HUMAN_REVIEW`. Match full model manifest, Azure region, observed elapsed/runtime and invoice record. No publishing; user sees **actual MP4** only after verification.
+- **Controls**: authenticated signed-in subscription, owner/role and exact tenant, one-time paid spend authorization and region, no automatic restart/retry, privacy-compliant storage, clear teardown plan and post-run Azure Cost Management check. Creating a budget alert is NOT a guaranteed hard cost limit; model weight pulls, storage, network and image build may incur additional charges.
+
+## Read-only probe implementation (committed to isolated Feature5 branch)
+
+```bash
+# In a signed-in, authorized Azure CLI session/DEV OIDC runner:
+export AZURE_SUBSCRIPTION_ID='<the existing DEV subscription ID from secure secret>'
+python -m feature5_motion.azure_gpu_readonly_cli
+```
+
+This inspects, without writes: exact account enabled, exact `rg-retailgrowth-dev` and ownership tags, `az containerapp env workload-profile list-supported --location eastus`, current Azure Container Apps DEV environments, A100 workload profiles and **available managed-environment A100 GPU quota**. `INSPECTION_PASS_ONLY` means quota/inventory only; it is **not** a deployment, and it does not verify image/weights/permissions/budget. `BLOCKED` is the expected safe result when no East US A100 DEV environment already exists or quota is unreadable. It intentionally makes no resource create/update/delete calls. Coordinator must do cloud preparation only after actual Azure login and owner-reviewed spending plan.
+
+## Illustrative PAYG estimate, NOT a cap or invoice
+
+Previously checked Azure East US primary meter rates: A100 $0.000529/s, active CPU $0.000024/vCPU-s, active memory $0.000003/GiB-s. At a purely illustrative **4vCPU, 16GiB and 600s** plus $0.05 ancillary, quoted GPU/CPU/memory estimate = **$0.4538**. This does NOT establish that 16GiB RAM is sufficient (Tencent offloading may demand much more), that a real generation finishes in 600s, or that Azure bills only those exact seconds. A **1,800s** example on the same insufficiently validated allocation would be $1.2614 before any unmodeled costs. Query model runtime/image/CPU/RAM requirements and actual subscription/region/usage immediately before approval. Account has no hard-coded spend approval in repository.
+
+## Remaining to execute, in order
+
+1. User saves signed-in Azure Portal browser profile or makes an authenticated Azure management workflow available. Determine actual subscription, isolated DEV RG, A100 environment/quota, permission and supported regions **read-only**.
+2. Obtain official Tencent model weights/checkpoints from licensed source, pin source+weights SHA256, legal provider/territory verification, pre-stage on allowed private storage, and containerize/test CUDA dependencies. (Weights and image not currently present.)
+3. Approve exact one-run real total budget after testing packaging and workload profile size, then deploy **one** manual A100 job; no auto scaling >1, scheduled polling, PROD resources or retailer media.
+4. Record real, human-reviewable MP4 evidence, stop/remove temporary GPU resources, inspect Azure actual charges, hand off accepted media for Feature4 coordinator integration. Do not close PR #323 until then.
+
+**Do not claim a real GPU deployment, paid test, model sample or live Part3/Feature4 integration at this checkpoint.**
~~~~

## docs/feature5/AZURE_SIGNEDIN_INVENTORY_20261026.md

~~~~diff
@@ -0,0 +1,31 @@
+# Feature #5 — authenticated Azure DEV portal read-only evidence (2026-10-26)
+
+**Status: user Azure sign-in saved; no Hunyuan GPU deployment.** Source: two separate signed-in Azure Portal read-only inspections in the user's saved browser profile on 2026-10-26. The evidence below is an inventory checkpoint, not proof of quota or deployment access.
+
+## Confirmed from first portal inspection
+
+- Saved profile has a Microsoft sign-in and Azure Portal successfully opened **Azure subscription 1**, Default Directory.
+- The dedicated existing resource group `rg-retailgrowth-dev` in **Central India** was visible. Azure portal showed `app=RetailGrowthAI` and `environment=dev` tags.
+- Observed 8 resources inside DEV RG: private StorageV2 account `rgaid4e5ddbdf0d21d96`, Central India Function App `rgai-dev-functions-d4e5ddbd`, `rgai-dev-flex` plan, SWA `retailgrowthai-dev-preview`, `rgai-dev-appinsights`, `rgai-dev-law`, Azure OpenAI `rgai-dev-openai-d4e5ddbd`, and anomaly detector.
+- No existing Azure Container Registry in this DEV group and no existing GPU VM/Container Apps in it.
+- Subscription's visible Azure Container Apps environments inventory contained one environment `vobiz-stream-env` in a **separate voice-project RG** in Sweden Central; do not touch. **No existing East US A100 Container Apps environment was visible.**
+- **A100 quota was not checked** in the first inspection. Lack of an environment is NOT proof of a zero quota or inability to create one. Published A100 rates are not quota evidence.
+
+## Second targeted quota attempt
+
+- The Azure Portal's generic `Subscriptions` blade reported `Filtered (0 of 0)`, even after filters were cleared, in its displayed directory context. Consequently the `Usage + quotas` page for the above subscription could not be opened during this second inspection.
+- Because the first audit DID see the subscription and exact DEV group, this is a **directory-context, portal filtering, session or access ambiguity**. Do NOT state that the user lacks Azure rights or that Azure rejected A100: neither is proven.
+- We did NOT submit a quota request, change directories/access roles, touch resource settings, create anything or spend Azure GPU money.
+
+## Direct user action to resolve the portal blade discrepancy
+
+1. In the signed-in Azure Portal open the top-right **Settings (gear) → Directories + subscriptions**, select the directory/subscription where `rg-retailgrowth-dev` is visible, and ensure `Azure subscription 1` is in the subscription filter.
+2. In **Subscriptions → Azure subscription 1 → Usage + quotas** or the separate **Quotas** service, select **Container Apps**, **East US**. Read **Managed Environment Consumption NCA100 GPUs** used/limit/available, if listed. Do not request a quota change or create resources yet.
+3. If it is not listed, report **not visible** rather than inventing a zero quota; an authenticated Azure CLI/OIDC query for Container Apps GPU workload-profile quota and account eligibility may be needed.
+4. For the first demo use the existing fictional **T2V fashion prompt only**, one explicit A100 execution after verifying actual allowed region/Tencent terms/model weights/image and full price cap; zero retries and no PROD/WineShopPOS changes.
+
+## Feature5's existing preparation (NOT deployment)
+
+- `feature5_motion/azure_gpu_readonly_cli.py` can inspect exact DEV subscription/tagged group, supported East US A100 profile, existing A100 environments and quota read-only in an already authenticated Azure CLI/OIDC session. Running it within ChatGPT was not possible because no Azure CLI/credentials are installed in this execution environment; code-tested mocks are not cloud evidence.
+- Source-only `demo_fashion.py`, `runner.py`, `artifact_lock.py` and single-mode manual GPU test are present on draft Feature5 PR #323. **No licensed weight shards or genuine Hunyuan-generated MP4 are present.**
+- Model-weight size/VRAM/latency, actual region-supported A100 job model and billed dollar limit remain unverified. Do not claim feature completion or deploy speculatively.
~~~~

## docs/feature5/COST_AND_ROLLOUT.md

~~~~diff
@@ -0,0 +1,52 @@
+# Feature #5 GPU & licensing decision (2026-10-26)
+
+**Status: decision proposal only, no provisioning / no paid test.**
+
+## Model options and constraints
+
+| Option | Text / Image | Estimated GPU requirement | Commercial and activation gate |
+| --- | --- | --- | --- |
+| HunyuanVideo 1.5 official CLI | T2V + I2V, 480p/720p variants | Official **minimum 14 GB VRAM with offload**; actual viable SKU/latency unmeasured | Tencent Community License (NOT Apache). Territory EXCLUDES EU, UK, South Korea; hosted-service disclosures, MAU and acceptable use terms need legal review. |
+| HunyuanVideo 1.5 Diffusers | Separate documented HunyuanVideo15 pipelines | Similar model weights; memory and compatibility per configuration, benchmark required | Same weight/model terms; Diffusers Apache licensing does not replace Tencent model license |
+| Existing Alibaba Wan 2.7 Model Studio (Part3) | T2V / I2V, 2–15s at 720p/1080p | GPU managed by vendor | Part3 already implements gated provider; vendor cloud pricing/region/data transfer require commercial approval |
+| Wan self-hosted family | Depends on exact model/weights | Unknown for chosen variant; requires separate benchmark | Research only; no added production provider |
+
+## Azure DEV region
+Microsoft currently lists Azure Container Apps serverless **T4 in Central India**, not A100 there. T4 nominal 16 GB VRAM is **not proof** that a 14-GB-offload Hunyuan model can run sustainably (CUDA, activations, torch overhead, cold start/latency). Do not provision before actual per-subscription quota, driver/CUDA/model compatibility and reservation caps are checked. Serverless GPU is supported on *Consumption workload profiles*, not Consumption-only environments, and can scale to zero. An alternative for future evaluation is an explicitly approved dedicated GPU VM/AKS batch job, with shutdown cost control. Existing Azure Functions remains CPU orchestrator only.
+
+## Cost formula, before provisioning
+Compute (USD) = (measured load/warmup seconds + measured GPU generation seconds) × **approved GPU+memory+CPU rate/second**, plus CPU Feature4 composition, output storage, transferred input weights, and egress. For multiple clips, add per-clip generation; reuse a loaded model only when it is cheaper than repeated cold starts without incurring unwanted idle GPU charges. Model weights transfer/caching, compliance and support may dominate short clips.
+
+**Illustrative math only**, NOT Azure quote or performance benchmark: assume an all-in GPU rate of **$1.00/hour**, 120 seconds warm inference, 60 seconds cold start, 60 seconds CPU at $0.20/hour, 0.1 GB stored at $0.02/GB, and 0.05 GB egress at $0.10/GB: **$0.0604 per 5-second clip** (including illustrative cold start and ancillary line items). Six separate 5s clips cost **~$0.3624** under identical assumptions; one shared load across six sequential clips could be lower. If real inference takes 600s or incurs failed retries, cost rises sharply. No assertion 120-second Hunyuan inference is feasible on T4. The price web page does not currently render numeric regional GPU prices, so the real rate is **unverified**.
+
+**Existing Part3 vendor comparator** (from `docs/part3/PROVIDERS_AND_COSTS.md`, not a fresh quote): Wan 2.7 Singapore 720p at $0.10/video-second -> 5s $0.50, six 5s clips composing 30s $3.00, excluding storage/egress/GST. This is not comparable quality/resolution (480p self-hosted vs 720p Wan) or a guaranteed savings calculation. CPU-only Feature4 alternative uses existing FFmpeg and stock/approved stills, avoiding generative GPU/model spend.
+
+## Before allowing even one real GPU DEV test
+1. Legal and geographic license sign-off and end-user provider disclosures; only authorized clothing/likeness media.
+2. Verify exact model/weights checksum + pinned official runtime commit and 480p output settings.
+3. Validate real Central India GPU SKU, per-subscription quota, explicit capped spend, trial limit and egress residency approval.
+4. Run isolated DEV once with no public HTTP, GPU job max one concurrent, bounded timeout, no automatic paid retries; use original source + real output side-by-side for garment/face/temporal review.
+5. Require coordinator's existing atomic subscription reservation, idempotency, optimistic claim fencing, private import and usage reconciliation before any customer launch.
+6. Publish actual per-clip runtime/cost measurements and only then decide whether Hunyuan vs existing Wan is the default option.
+
+Sources:
+- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5
+- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE
+- https://huggingface.co/docs/diffusers/api/pipelines/hunyuan_video15
+- https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
+- https://azure.microsoft.com/en-in/pricing/details/container-apps/
+- Existing RetailGrowthAI Part3 docs `docs/part3/PROVIDERS_AND_COSTS.md`
+
+## 2026-10-26 additional hardware qualification
+**Default BF16 restriction matters more than nominal VRAM.** Tencent official `generate.py` defaults to BF16 or FP32 (not an unrestricted FP16 selector). NVIDIA lists T4 as CUDA capability 7.5, versus A100 at 8.0, and BF16 hardware capability is not generally available on T4. Feature5's default local runner now rejects GPUs for which `torch.cuda.is_bf16_supported()` is false, including typical T4 configurations. An explicit FP32/T4 experiment requires a new reviewed memory/performance/quality profile; do **not** silently assume it fits.
+
+Azure documents A100 serverless in East US and T4-only in Central India, but **no automatic cross-region forwarding** is authorized. Check residency, contractual permissions, provider licensing and subscription quota before proposing a real East US A100 trial; the original DEV platform remains Central India. No fabricated all-in A100/T4 price is provided until Azure's actual GPU + vCPU + RAM rate and cold load times are measured.
+
+- Official CLI: https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/generate.py
+- GPU architecture: https://developer.nvidia.com/cuda/gpus
+- Regional inventory: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
+
+## Important reservation-bound design update
+- `MotionSpendGuard` now **requires** pricing/resource profile for every enabled Feature5 worker run (source code). At the verified East US Retail Prices snapshot: A100 $0.000529/s + 4 vCPUs × $0.000024/s + 16 GiB × $0.000003/GiB-s = $0.000673/s active model job assumption.
+- Worst-case 600s costs about **$0.4038** active compute. With a separately reviewed $0.05 storage/network overhead reserve, require **at least $0.4538** existing shop premium credit for that one job. A 30s mocked test maximum is $0.02019 + $0.005 = $0.0252.
+- This is a **budget estimate**, not an Azure itemized invoice or Hunyuan benchmark. Startup, GPU model pull/load, other platform meters, network and actual runtime might exceed the assumptions. Any case beyond approved duration stays UNKNOWN for reconciliation rather than automatic retry.
~~~~

## docs/feature5/DECISIONS.md

~~~~diff
@@ -0,0 +1,100 @@
+# Feature #5 isolated decisions
+
+- Primary research/adapter candidate: Tencent **HunyuanVideo 1.5**, local official CLI with optional future Diffusers backend; never dynamically fetch unreviewed weights.
+- Do not activate Tencent under the community license without commercial/legal and territory review; hosted Indian SaaS does **not** automatically imply unrestricted worldwide access.
+- Keep previously implemented Alibaba Wan on Part3 integration branch as an alternative provider behind the coordinator's contract. No second live paid provider.
+- 480p, 5-second, 24-fps bounded output profile is a conservative **proposed** profile; not asserted verified by actual inference. Dimensions/probe acceptance require real pinned-model test.
+- Premium disabled at three gates: worker flag, license approval, GPU budget approval. Existing approval + quota reservation required in DB before claim. No browser/provider key exposure, no public inference endpoint, no LangGraph or new DB schema.
+- Feature4 alone handles reliable offer text, brand logo, music, transitions and final export. Feature5 preserves original assets and indicates human quality review required.
+
+## 2026-10-26 safety/interop addendum
+- Tencent official CLI uses `--image_path` *only* for I2V; text mode must omit the parameter. `--video_length 121` at 24 fps targets five seconds, but exact output requires real inference validation.
+- Default BF16 runner requires `torch.cuda.is_bf16_supported()`, at least 14 GiB of GPU memory, and a pinned local install. Do not assume the Central India T4 is sufficient merely because it offers 16 GB nominal VRAM; no silent fall back to FP32 (substantially different cost/memory).
+- Treat unknown/late private Storage upload acknowledgments and completion fencing as `UNKNOWN`, never as refundable FAILED or a reason to repeat GPU inference.
+- Exact existing private object convention `{shop}/renders/{job}/{lease}.mp4` in `retailgrowth-media`; invalid bucket, path, lease or private flag are not success. Never create a duplicate public media bucket.
+- No new Azure Functions ingestion path, payment ledger, or final renderer: Part3 and coordinating Feature4 own those integrations.
+
+## 2026-10-26 continued decisions
+- Part3 draft Wan reservation SQL is incompatible with the Hunyuan profile. Stop at an injected adapter; coordinator must reconcile ONE premium ledger and versioned provider/model/cost schema before hosted activation.
+- A Feature4-ready clip must have a matching audited VisualReview object bound to the exact stored media hash and reviewer tenant write permissions. A `quality_status=APPROVED` string alone is insufficient.
+- Generation idempotency version `feature5-lease-v2` includes approved prompt SHA-256 and model seed to prevent stale campaign output reuse or accidental duplicate GPU spend.
+- Tencent Hunyuan Community License is conditional and territory-limited. Runner now fails closed when explicit operator licensing, regions, hosted notices, rights and MAU context is absent. This does not replace licensed jurisdiction/terms review or authorize use in EU/UK/Korea.
+- Initial paid GPU pilot remains gated on real account access, quota, approved geography/consent and bounded spend. Never claim mock video is Hunyuan output.
+
+## Runtime budget hardening decision
+- An enabled GPU job requires a `MotionSpendGuard` and existing service-only DB credit reservation covering **worst case** allowed GPU wall time, active A100/vCPU/RAM rates plus ancillary allowance, not merely a nonzero reserved value. Runner timeout must not exceed quote. If no guard/rates or insufficient allowance, fail before leasing/launch.
+- Measured subprocess wall-time is included in output metadata only as an **estimate of model-related compute**, not as an Azure invoice. Worker must reconcile Azure startup, image pulls, network, storage and full bill before settling charge.
+- On out-of-budget runtime or unclear DB write, enter `UNKNOWN` (or raise reconciliation-only status when persistence fails). Never transform unrecorded uncertain paid work into a refundable `FAILED`.
+
+## 2026-10-26 source pin + visual evidence decision
+- Pin official Tencent HunyuanVideo-1.5 `generate.py` from upstream commit `60783e704160023913bee78f0b47036d393d4dfa` by Git-object SHA1 blob `ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d`. SHA1 is Git's blob identity and cannot substitute for SHA256 checks of model weights/dependency provenance; pin still needs actual tested runtime and licensed source evidence.
+- A cheap real FFmpeg-encoded 5-second MP4 fixture is appropriate to verify Feature5 machine media validation without pretending a text/image-to-video model ran. Do not treat it as cinematographic acceptance.
+- Human visual QA will examine private PNG samples and contact sheet tied to the exact MP4 SHA256. Only tenant-authorized reviewer state stored in the existing service backend can later authorize Feature4; generated review sheets alone confer no right to publish.
+
+## Hosted DB reality check — 2026-10-26
+- Read-only inspection of dedicated RetailGrowthAI DEV subscription/usage/outbox catalog confirms the provider-aware premium ledger is **not deployed**. Existing quotas and outbox cannot store premium jobs in their present CHECKs. Never claim Part3/Feature5 live subscription ledger integration until coordinator migration and E2E prove it. Source-only adapter design remains intentionally backward-compatible and default-disabled.
+
+## 2026-10-26 — Weight code integrity and retained real inference evidence
+- A pinned `generate.py` Git blob is insufficient to approve GPU spend. **Require a complete enumerated SHA256 manifest of materialized clean source files and licensed model weight shards**, with independently reviewed top-level SHA256 passed into the runner. Reject extra/missing/modified files and symlinks before CUDA. Keep lock generation local/offline and exclusive so no silently overwritten prior candidate.
+- A manifest file in the same download folder is not an independent trust root. The reviewed `approved_manifest_sha256` must be protected in separate operator configuration, and origin/model-license/dependency checks still require human/operator diligence.
+- A manual GPU test that deletes the generated video cannot provide real human visual sign-off. Require a separately protected `RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT` and preserve the original MP4, side-by-side source reference for I2V, review frames and clip SHA256 with **PENDING_HUMAN_REVIEW** status only. Actual quality must be approved by a reviewer, never inferred from video codec/duration checks.
+
+## 2026-10-26 — Cost-minimizing policy
+- Default to **zero premium spend**. Prefer already deployed CPU FFmpeg for retailer-approved stock/images when no photorealistic model motion is required; stills must never be misrepresented as bespoke walking-model footage. A separate reviewed `MotionSpendGuard` full wall-time quote and explicit paid operator flag are required even to mark a premium job GPU-budget-eligible. Feature5-only selector is a **planning boundary**; Part3/Feature4 coordinator owns actual execution.
+- Start of `HunyuanLocalRunner.run` constitutes **possibly billable** attempt even if code/model initialization fails before producing valid MP4. Any subsequent exception, time-limit failure or rejected output must be `UNKNOWN` rather than refundable FAILED; safe pre-inference invalid source may be FAILED. Existing DB reconciler must prove amount/credit disposition; never blindly retry.
+- Do not acquire a paid A100 GPU in East US or transfer Indian retailer private media simply because Central India has only T4 in official serverless GPU support. Geographic consent, hardware compatibility, actual quota, licensing and capped commercial inference remain gates.
+
+## 2026-10-26 — Authenticity and one-shot-only cost gate
+- Do not present assistant-generated stills as Hunyuan video output. The sole acceptable Feature5 sample is a **real MP4 from pinned Tencent code and weight shards on CUDA**, with provenance, cost and ffprobe/visual evidence. User can choose theme freely; selected free-to-design red festive kurti luxury-boutique T2V to avoid sharing any retailer photos.
+- Manual GPU harness must select **exactly one of text/image** per invocation and require a verified Azure pricing snapshot and operator dollar cap covering all allowed billable GPU/vCPU/RAM/ancillary time before launch. No budget config or GPU means no sample launch. Actual billing is separately reconciled; manual harness is not a subscription integration.
+- A free community Hugging Face Space can illustrate what original Tencent weights do, but is **not our connected Feature5 runner or customer tenant media flow**. Keep exact provenance labels and third-party retention/usage distinctions.
+
+## 2026-10-26 — Azure demo must be real, capped and explicitly authenticated
+- Owner intent authorizes pursuing an Azure GPU canary, but does not itself supply an Azure login, GPU quota, Tencent licensed weights, or an exact enforceable bill cap. Fail closed before creating a paid resource; no false deployment claims.
+- Use a single manual East US A100 candidate **for synthetic T2V only**, subject to permission/territory/weights/price approval; Central India serverless T4 should not be assumed to support this BF16 Hunyuan runner. Existing verified dedicated Central India DEV RG must remain isolated and ownership-tagged; do not touch PROD or WineShopPOS.
+- Separate read-only Azure subscription/profile/quota inspection from paid provisioning. No code in Feature5 may mutate Azure without a reviewed coordinator deployment path. Capture real mp4, exact sha, visual review evidence and charged USD before claiming task completion.
+
+## 2026-10-26 — Azure sign-in does not imply GPU quota
+- Actual signed-in browser profile makes the dedicated DEV subscription and resource group visible, but East US A100 managed-environment quota has not been surfaced; a different portal blade showed no subscription rows in its current directory/filter context. Do not mislabel this as an Azure denial or user failure. Keep paid GPU creation disabled until exact quota, supplier model weights, accepted licensing and maximum bill are verified. Do not reuse the separate voice-project Container Apps environment.
+
+## 2026-10-26 — Azure ARM notification is not a verified GPU deployment
+- `CustomDeployment-20261026093554` showed **Deployment succeeded** in Azure Portal, but exact managed environment was not visible and operation/template details were not retrievable. Therefore mark **UNVERIFIED**, never retry automatically; use coordinator OIDC read-only ARM show/operations before creating anything.
+- Azure **environment-level** Consumption NCA100 GPU quota is only observable after a supported v2 managed environment exists; subscription Quotas empty pre-environment is NOT a proof of zero quota. Allow a single empty Consumption/logging-none DEV environment via strict one-resource what-if, but not an actual GPU profile or job until confirmed availability and real capped spend.
+- Azure Cloud Shell ephemeral browser input failed, and the portal browser tool exhausted its metered budget. Prefer existing repository DEV OIDC to execute coordinator-controlled audited ARM path instead of repeating unreliable GUI steps. User's desire for minimum cost remains controlling; no GPU execution or paid deployment was verified.
+
+## 2026-10-26 — OIDC is a runner credential, not direct chat cloud access
+Keep Azure authentication within reviewed GitHub Actions using existing `dev` federation, without access keys or TinyFish browser wallet usage. The current GitHub app supports source commits and Actions logs but **does not expose arbitrary `workflow_dispatch`**; do not claim direct session Azure control. Only the coordinator installs .github workflows and approves any actual ARM create. Feature5 can publish a read-only proposed YAML under its own docs and pass reviewed handoff. Owner does not need to re-enter Azure login credentials for normal OIDC workflows.
+
+## 2026-10-26 — Actual Azure per-environment quota zero; no GPU spend before one-GPU allocation
+- Azure's actual list-usages output on the newly provisioned tagged East US v2 managed environment is `ManagedEnvironmentConsumptionNCA100Gpus limit=0 used=0`. Earlier blank portal quota pages were due to the missing environment and are superseded by this live result. We will **not** misinterpret an empty Consumption environment as a deployed/operational A100 GPU, nor claim a genuine Hunyuan MP4.
+- Use the **managed environment Quota** request path for **1** serverless NCA100 GPU (not a subscription NCA 100 dedicated quota). The official Microsoft documented path may auto approve or require Azure Support review; do not file a separate case without owner approval. Paying for a GPU remains explicitly gated by quota, real licensed weights, approved geography/data handling and exact cost ceiling. Existing empty environment must stay isolated; no WineShopPOS/voice/PROD changes.
+
+## 2026-10-26 — Do not use fractional A10 below model minimum or over-vCPU quota
+- For authentic HunyuanVideo 1.5, follow Tencent official >=14GB VRAM with offloading. Azure NVadsA10 v5 SKU sizes offer 4/8/12GB fractional GPU at 6/12/18 vCPU and first 24GB full GPU at 36vCPU. DEV subscription regional cap is 10 vCPUs in both Central India/East US (live OIDC), so neither the insufficient-memory low-tier options nor first memory-sufficient 36vCPU SKU should be deployed. A100 VM SKUs restricted. No speculative paid VM, no auto quota request; favor one serverless A100 managed-environment quota request to the already existing DEV environment. Retain zero-active-compute settings until approved.
+
+## 2026-10-26 — Managed-environment quota submission and outside-GPU fallback
+- Microsoft now documents environment-level serverless A100 quota increases through **existing Container Apps environment → Settings → Quota**; neither public GPU SKU listing nor the unrelated subscription dedicated GPU quota satisfies it. The exact environment already exists (OIDC #40347841764) and limit=0; no request was submitted or approved. No undocumented REST/write mutation through OIDC.
+- A lower-priced third-party on-demand GPU is **evaluation-only** until account-specific provider geography, isolation, model licensing, upload policies, host RAM, real cost/termination and source/weight provenance are approved. Use synthetic T2V before any retailer media. Model 480p T2V requires the official 50-step configuration by default; its faster distilled I2V mode is not a substitute.
+- External price quotes are separately SHA256-pinned and checked with a strict, read-only CPU module; the result deliberately says QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION. Python wall-time cannot terminate a rental provider instance or hard-cap the invoice. Never activate external GPU spending on quote-only output.
+
+## 2026-10-26 — A40 exact screening support
+- A40 is included only as one BF16-capable, 48GB VRAM **provisional** candidate in SHA-locked price screening. Its $0.59/hr Runpod published Pod price is not guaranteed account capacity or a true provider-enforced ceiling. A 1-hour rental at $0.59/hr plus illustrative $0.02/hr storage and $0.05 reserve screens at $0.66, explicitly including provider termination, not just inference time.
+
+## 2026-10-26 — Do not equate complete open-source engine with a deployed SaaS
+- Reassess Feature5 with **official, runnable GitHub upstreams** rather than another paid video API: prioritize LTX-Video 13B v0.9.8 as **conditional** long-form/60s extension candidate, Part3 Wan2.2 as Apache-2.0 baseline, existing Hunyuan code preserved. ComfyUI offers an internal authoring/runtime engine but its GPL-3.0 and model licenses are separately reviewed. Azure-Samples ComfyUI H100 Terraform is a hardware-expensive example, not an approved deployment plan.
+- No false claim that 60 seconds is generated in one cheap pass: recommended model operating windows are smaller, require continued model inference and continuity evaluation. Code and checkpoints have distinct licensing; LTX's 0.X weights have USD 10m revenue threshold and AI-disclosure/use restrictions.
+- No change to final approved model/provider, paid GPU authorization, quota limit or cross-feature contracts without coordinator approval and verified CUDA quality/cost pilot.
+
+## 2026-10-26 — Full upstream, not handwritten renderer
+- Official whole-project GitHub path: Microsoft `Azure-Samples/comfyui-on-azure` launches full upstream ComfyUI plus models on a **single H100, 40-vCPU Azure VM**. Full A100 serverless alternative is a **new container deployment packaging** of upstream code, not a claim the unmodified H100 Terraform can run on ACA.
+- Cost reference East US H100 $6.98/hr allocated versus A100 serverless GPU $0.000529/sec plus variable CPU/RAM ($2.4228/hr **illustrative** 4/16). Both account quota requests are blockers at the last verified Azure state; no cost-per-60s-video claim absent benchmarking.
+- Preserve real upstream workflows/model quality; RetailGrowthAI code should be an auth, ledger, asset and review adapter, not a substitute video generator. Do not install/rent GPUs under undocumented billing or quota assumptions.
+
+## 2026-10-28 — GPU provider procurement recommendation, not a paid activation
+- For first original Wan2.2 proof under Indian domestic card billing, recommend **JarvisLabs India on-demand A100 80GB at published ₹140.94/hr**, rather than an unverified ₹32/hr community RTX 4090 listing or blocked Azure A100 quota 0. The A100 is not the cheapest hourly GPU, but verified 80GB capacity permits the full non-offload profile and avoids pre-approval Azure GPU capacity constraints.
+- Official vendor: https://jarvislabs.ai/in (INR payment, Indian debit/credit via Stripe, GST; UPI support not confirmed). 100GB persistent storage adds published ₹1.30/hr even while paused; do not leave persistent instance indefinitely. A100 price and stock are estimates for planning until authenticated checkout.
+- **This is a recommendation only**: No payment, VM, vendor access or GPU inferencing occurred. Use operator hard spend cap and no retries. Preserve original upstream generator, existing Feature5 Hunyuan branch, Part3 Wan owner and Azure/Supabase DEV PROD separation.
+
+## 2026-10-28 — Capacity grant does not start paid GPU usage
+- User-supplied Azure Portal environment Quota screenshot shows **A100 limit 2 used 0** in existing `rgai-f5-gpu-canary-eastus`. This supersedes previous capacity limit=0 noted in documentation, pending independent CLI readback. Quota is permission, not a paid reservation.
+- Prefer actual original Wan2.2 model proof on **existing Azure serverless A100** now that capacity appears available, rather than buying external GPU access by default. Provision nothing billable until reviewed cost cap, private upstream image, model integrity/licensing, min replicas 0/max 1 and no-retry controls. No GPU charges at zero replicas; ancillary Azure services can bill separately.
~~~~

## docs/feature5/NEXT_TASK.md

~~~~diff
@@ -0,0 +1,126 @@
+# Feature #5 — Next tasks / gates
+
+1. **Coordinator interface gate (P0):** map `MotionSpec`/AssetGrant to existing signed Feature3 media/Part3 source rights, existing subscription reservation, persisted lease claims, outbox, private Storage importer, without an independent schema or queue. Design review before any shared file change.
+2. **Model exactness gate (P0):** pin upstream Tencent generate.py commit + downloaded weight/checksum and allowed inference mode/version. Current runner supports 480p T2V/I2V via official CLI shape but has never executed GPU inference. Validate output dimension, FPS, 5s actual generation and expected VRAM on a real licensed GPU.
+3. **GPU cost and legal gate (P0):** review Tencent territory exclusions (EU, UK, South Korea), hosted-service notices/disclosure, 100m MAU clause, third-party rights, India data residency; confirm Azure Central India T4 quota and $/GPU-second. Obtain explicit paid approval before provisioning/inference.
+4. **Media integration (P0):** verify existing claim attempt-token DB generation and replay fencing, input byte-signature/pixel/decompression checking via existing Feature3 importer, exact private output media path, DB-fenced registration, and media quality approval. Do not treat machine codec check as garment QA.
+5. **Operational gates (P1):** secure job image staging cleanup, GPU subprocess/child-group timeout, workload profile idle scale-zero, GPU OOM telemetry and retry policy, amount-spent reconciliation and non-billable fallback to Feature4 static animations.
+6. **Cross-feature acceptance (P1):** Coordinator Feature4 assembles a branded fashion Reel; Feature6 ensures human approval before publishing.
+7. **CI:** inspect exact PR-head GitHub Actions after push; no mock implies real GPU output.
+
+## Updated 2026-10-26 progress
+- **Completed offline:** official CLI T2V omission of `--image_path`; I2V source flag, bounded model args, preflight image decode, timeout and CUDA gate, immutable lease-scoped private output receipt, nonfinite quota rejection and post-upload unknown-state handling. Corresponding automated mocked tests added to the standard Python CI.
+- **Still blocked:** verified licensed GPU/device and actual Hunyuan output, pinned weights+runtime digest, real 480p/frame aspect/FPS verification, actual garment quality, managed/private media adapters, transactional reservation and claim RPC wiring, Azure service and real preview.
+- **Hardware:** Central India T4 has native BF16 compatibility risk (CUDA compute capability 7.5); default Hunyuan BF16 runner rejects unsuitable GPU. Coordinator should review whether a consented A100 region is permissible or keep dormant Wan vendor choice. No cross-region transfer without approval.
+
+## Real GPU acceptance harness prepared, not executed
+- Optional `tests/gpu/test_feature5_local_acceptance.py` provides real T2V and I2V paths only after three explicit environment approvals (real test, GPU spend, and reviewed license) plus pinned local checkout and weights. The separate I2V test requires a rights-approved source image.
+- The standard GitHub CI does not discover or run `tests/gpu/`; local manual execution must never be described as a successful test until real GPU output, ffprobe, side-by-side garment review and captured measured costs exist.
+
+## 2026-10-26 integration gates after owner approval
+1. **Coordinator schema + service adapter:** Part3 PR #125 remains draft. Its `PROPOSED_20261023180000_premium_video_reservations.sql` explicitly restricts `model_id` to two Wan 2.7 names and resolution to 720P/1080P. Feature5 `hunyuanvideo-1.5-480p` cannot use that database safely until coordinator reviews a compatible, versioned extension to EXISTING premium jobs/quotas/leases/rights/ledger/outbox. Our `Part3MotionStoreAdapter` is injected interface code and is NOT connected to a real DB RPC. Do NOT create another ledger, apply schema or claim hosted integration.
+2. **Feature4 handoff:** PR #322 `creative_reel_v1` expects genuine approved `source_feature=feature5` video in a backend-signed/staged tenant manifest. Feature5 now provides matching shape, strict rights metadata and a separate immutable human review gate. Coordinator mounts only after merging relevant PR and verifying real signed-in E2E; we did not touch Feature4 branch.
+3. **Real inference:** No Azure/NVIDIA GPU and no licensed model weights in current tool environment. Real pilot needs an Azure connection with exact subscription/project, quota and region, reviewed model commit/weights, licensed approved test image and a cost-capped one-shot GPU job. Existing Central India T4 does not satisfy the default BF16 profile; A100 documented in East US but data-region transfer needs owner consent. Do not silently route Indian customer private media to US.
+4. **Visual signoff:** Before promotion, reviewer compares REAL output side-by-side with original clothing; check face/body, garment color/pattern/sleeves, background continuity, camera, motion, temporal artifacts, honest product representation and mandatory disclosure; bind to exact SHA256 and published-asset version. Synthetic/mocked test checklists never count.
+5. **License:** Review and document Tencent territory limitations (EU/UK/South Korea), hosted use disclosure of actual provider, Tencent no-endorsement, terms/AUP notice, 100m MAU release-date exception, rights. Operator-approved policy booleans are defense in depth, NOT legal clearance or verified geo-blocking.
+6. **CI:** inspect final PR HEAD four required jobs and record SHA/result. Do not self-merge; main integration belongs to coordinator. Preserve WineShopPOS and production isolation.
+
+## Follow-up: quote/actual billing and launch order
+- Implemented SOURCE ONLY: `MotionSpendGuard` bound to approved full-job timeout, Azure GPU+vCPU+RAM price and ancillary allowance; tests run on mocked GPU. A paid runtime must have an existing DB reservation >= quoted worst-case cost, with one charge ledger reconciliation of observed subprocess time and actual cloud bill. No provider charge was incurred.
+- Coordinator must first merge/reconcile Part3 schema and private claim/outbox, Feature4 canonical asset contract and reviewed VisualReview audit persistence. Feature5's code is **not yet connected to those live resources**. Owner consent does not supply cloud credentials, quota, consent for transferring retailer images to East US, licensed weights or a formal legal agreement.
+- Real inference remains a separate acceptance gate: one actual A100 call in authorized region on licensed model/staged noncustomer media, record true elapsed and Azure charges, ffprobe, inspect sampled frames side by side, then attempt authorized clothing I2V. Only after that may Feature5 be described as operational.
+
+## 2026-10-26 follow-up gates after pinned-source implementation
+- **DONE in owned Feature5 source:** pin exact `generate.py` Git blob from audited Tencent upstream revision and reject tampering before GPU, CPU-real FFmpeg 5-second MP4 validator tests, bounded local human-review frame/contact-sheet exporter with clip+frame digests. CI must be inspected on final HEAD; test artifacts are synthetic, not AI-generated.
+- **P0 real model authenticity remains:** obtain explicitly licensed *actual* `HunyuanVideo-1.5` weights and record their immutable release revision/complete shard SHA-256 checksums, runtime dependencies, and GPU execution environment; no model weights were downloaded or attested here.
+- **P0 real human visual acceptance remains:** make a real 5s I2V clothing/retailer demonstration on an approved GPU and reviewed geography, generate review evidence, then require human approval of motion, faces, exact outfit colors/prints, temporal smoothness and disclosure before Feature4 assembly.
+- **P0 coordinator remains:** Part3's current Wan-only reservations SQL/queue/ledger needs additive provider-aware versioning and real service-role adapters; Feature4's `creative_reel_v1` must be integrated by coordinator. Never merge or deploy behind another team.
+
+## Actual hosted DEV evidence and coordinator acceptance (2026-10-26)
+- DONE: read-only catalog verification of RetailGrowthAI DEV confirms **no** `premium_video_jobs`, no premium shop allowance/budget columns, and only `campaign|render` usage / `planning|render` outbox kinds. Feature5 is **not production/billing integrated**, regardless of green offline CI.
+- Coordinator must first reconcile Part3's Wan-only draft and Feature5 480p/A100 total wall-time tariff in a **single existing ledger/outbox**; use `PART3_DEV_SCHEMA_RECONCILIATION_20261026.md` for additive contract and DB-negative acceptance plan. Do not apply migrations independently in Feature5 branch.
+
+## 2026-10-26 — Next activation prerequisites after artifact-lock implementation
+1. **Model release**: Obtain complete legitimate model weights from their licensed source, verify upstream model revision, manufacturer/third-party notices, legal region/commercial eligibility and immutable per-shard SHA256. Stage a **clean, non-symlinked** runtime/weight snapshot without `.git` or transient download cache. Create candidate lock with `python -m feature5_motion.seal_artifacts`, independently review manifest and configure *its* SHA256 in operator-side deployment settings. A self-declared manifest is NOT approval.
+2. **GPU preflight**: On approved BF16-capable GPU and permitted region, run **one cost-capped manual GPU** T2V first, then I2V with approved noncustomer clothing reference, using expected lock SHA, explicit Tencent context, one licensed CUDA environment and isolated private evidence output. Do not deploy an always-on GPU or post media automatically.
+3. **Visual acceptance**: Inspect persisted `clip.mp4`, comparison `reference.png` (I2V), `review/contact-sheet.png`, six frames and hashes; obtain actual tenant/rights/QA reviewer signoff with exact media hash before passing to Feature4. Runtime source tests/CPU mp4 fixtures cannot certify garment fidelity or a model's provenance.
+4. **Hosted billing/composition**: Coordinator must implement and test single Part3 ledger/outbox schema for Hunyuan 480p and Wan, and reconcile Feature4 creative_reel_v1; read-only DEV inventory confirms premium tables/units not applied. No Feature5-owned production/DEV schema change permitted.
+
+## 2026-10-26 — Next tasks after $0-first route and paid-failure fencing
+1. **Coordinator integration gate (unchanged P0):** Part3 must implement existing ledger/reservation/outbox support for Hunyuan 5s/480p with service-owned worst-case bill cap and UNKNOWN-safe reconciliation. This source-only worker's state transitions require an atomic persisted SQL adapter before any live test.
+2. **No-cost delivery (now designed):** coordinator may wire `plan_lowest_cost_delivery` to existing approved-media FFmpeg route; route is source-only and does not itself render/publish. If actual creative intent requires model motion, **defer** until an approved GPU provider is affordable instead of falsifying a real walking video.
+3. **Actual GPU acceptance:** only with independently verified licensed weights, full artifact SHA lock, reviewed Tencent license/territories, budget approval, region/data consent, cloud quota, one-shot capped A100 GPU and human visual review. Do not use T4 merely because it appears as available Central India.
+4. **Cost reconciliation:** if any GPU run times out/fails/produces invalid MP4, worker marks UNKNOWN, requiring existing ledger+Azure bill reconciliation before deciding retry/refund. Actual cloud invoices/FFmpeg v. model quality remain unverified.
+
+## 2026-10-26 — User demands actual model video (NOT another ChatGPT image)
+- **P0 blocked by model execution access:** obtain supported BF16 NVIDIA GPU and licensed pinned Tencent 1.5 weights (complete SHA256 manifest); choose an authorized India-residency solution or separately approve a non-India DEV synthetic-only GPU region. Current chat runtime has **no CUDA**, and the separate public HF ZeroGPU demo cannot be treated as proof of our runner.
+- **One exact chosen creative:** `feature5_motion/demo_fashion.py`: adult fashion model, red/gold kurti, walking in boutique, 5s/480p/24fps/9:16. Launch `RETAIL_FEATURE5_ACCEPTANCE_MODE=text` only after cost snapshot/approved cap, Tencent license, official runtime pinned+weights, zero public personal imagery and recording path in 0700 directory. Do NOT schedule image mode in the same paid pilot.
+- **Proof, not promise:** after real GPU execution, save actual `clip.mp4`, `acceptance-pending.json`, six PNG frames and contact sheet, check ffprobe, clip SHA256 and true Azure billed seconds. Show the real MP4 to user labeled *actual Hunyuan*, never show previous ChatGPT still/FFmpeg animation as generated model motion.
+- **External free model eval:** if user wishes to test Tencent weights independently before connecting GPU, visit `https://huggingface.co/spaces/multimodalart/Hunyuan-Video-1-5` and manually upload an authorized local still + describe motion. This is external, optional, with its own terms/privacy; not a RetailGrowthAI SaaS hosted sample.
+
+## 2026-10-26 — Actual GPU deployment next action (blocked on sign-in)
+1. **User action:** save authenticated Azure Portal browser session from this conversation's secure setup link. No passwords in chat. Or provision a reviewed coordinator-owned Azure management/CI workflow capable of the same read-only checks. Existing GitHub OIDC identity in `dev` can authenticate but is not an executable Azure management tool here.
+2. **Read-only inspection:** verify exact DEV subscription, tags/role in `rg-retailgrowth-dev`, `eastus` A100 workload profile/available quota. `python -m feature5_motion.azure_gpu_readonly_cli` is now implemented. Current cloud GPU quota and image/weights are **unknown**, do not assume green.
+3. **Verified manual deployment prerequisites:** licensed pinned real Tencent weight shards and container image, supported GPU quota, allowed East US synthetic-only deployment, exact agreed max USD, model CPU+RAM sizing and disposable storage. An Azure Cost Management budget alert is not a hard stop; require single manual execution, one replica, no automatic retries, bounded timeout and teardown.
+4. **One real Hunyuan MP4 and audit**: genuine fashion T2V, verify model revision, H264 5-sec 480p/24fps, review frame sheet/sha256 and actual Azure charges; show video to user; later Part3/Feature4 integration remains separate. See `AZURE_GPU_CANARY_DEPLOYMENT_20261026.md`.
+
+## 2026-10-26 — Actual Azure sign-in now available; quota screen currently blocked
+1. **READ-ONLY portal fix:** user selects correct directory/subscription in Portal Settings → Directories + subscriptions, where existing `rg-retailgrowth-dev` is visible. In Azure subscription 1 → Usage + quotas (or Quotas) inspect **Container Apps East US Managed Environment Consumption NCA100 GPUs**. First portal inventory showed the subscription, second generic Subscriptions blade 0/0 after clearing filters, so actual quota is **UNKNOWN**. This is the immediate blocker, not lack of login.
+2. **Do not infer quota from lack of managed environment**: no A100 environment exists yet, but its creation eligibility/limit was not checked. Do not request quota changes, create paid GPU or use voice-project environment as a workaround.
+3. Once quota is verified, operator reviews actual approved region, Tencent license+official pinned weights, supported A100 Container Apps Job profile, image size/pull/CPU/RAM cost and **specific full USD maximum** for one fictional text-only sample. Only then create one ephemeral zero-retry job and capture a genuine MP4. See `AZURE_SIGNEDIN_INVENTORY_20261026.md`.
+
+## 2026-10-26 — Quota blocker after full Azure browser inspection
+- **DONE** signed-in portal resource-group/subscription inventory. **DONE** both Subscription → Usage + quotas and separate Azure Quotas → Container Apps → East US attempt. Both failed to display **Managed Environment Consumption NCA100 GPUs** limit/usage; do not ask owner to redo those same steps without a different diagnostic path.
+- **NEXT diagnostic, read-only:** use dedicated GitHub DEV OIDC identity in a coordinator-reviewed manually dispatched read-only workflow or authenticated local Azure CLI to query **Microsoft.App resource provider registration** and the Container Apps managed-environment A100 GPU quota API/CLI for exact subscription/region. Record returned status codes + precise quota values; don't treat zero results as denial. Feature5-owned `feature5_motion/azure_gpu_readonly_cli.py` offers a no-write inventory helper but does not create an A100 environment and cannot show environment quota when no environment exists.
+- **REMAINING blocking inputs** before actual Hunyuan test: real licensed model shards/checksum trust, supported CUDA GPU/capacity, one-job concrete maximum dollar approval and synthetic-only regional processing, and verified container image profile. No live GPU/MP4 exists.
+
+## 2026-10-26 — Next action after ARM success notification, missing resource
+1. **P0 read-only reconciliation by GitHub DEV OIDC coordinator:** inspect `az deployment group show` and `az deployment operation group list` for `CustomDeployment-20261026093554`; enumerate `Microsoft.App/managedEnvironments` in exact `rg-retailgrowth-dev`; query `Microsoft.App` provider registration. The browser cannot reliably inspect deployment details and must not be retried blindly.
+2. If deployment successfully created target but RG list was stale: verify exact DEV tags, East US, Consumption only and no paid profiles; run `az containerapp env list-usages` for environment and read **Managed Environment Consumption NCA100 GPUs** limit/currentValue. Missing row = UNKNOWN/absent, not zero.
+3. If succeeded deployment is **empty**, coordinator may perform reviewed `what-if` with `feature5_motion/infra/empty_gpu_env.json`, require precisely one Create and no other changes, and explicitly deploy **only the empty environment**; no GPU/app/job/registry/logging.
+4. Still blocked for genuine video: official licensed Tencent weight shards, compatible A100 quota, synthetic-only geography/terms, realistic 24vCPU/220GiB + GPU worst-case capped USD, private output receipt, one no-retry CUDA job and human garment-motion QA. Detailed reconciliation instructions in `ARM_CUSTOM_DEPLOYMENT_DISCREPANCY_20261026.md`.
+
+## 2026-10-26 — Exact next step with existing federated Azure identity
+- Coordinator copies/reviews `docs/feature5/proposed-workflows/azure-feature5-oidc-reconcile.yml` into `.github/workflows/` on a coordinator-owned change and merges after security/CI review. It uses existing `dev` environment secrets, `azure/login@v3`, manual `workflow_dispatch`, and **read-only** Azure CLI; it is intentionally ineligible on feature branches. The current GitHub plugin does not expose a dispatch method, so the initial run must be started via GitHub Actions **Run workflow → main** (or a coordinator-native workflow trigger), not TinyFish.
+- Read logs and record the actual ARM result/managed environment quota. **Do not automatically create** the same environment again after Azure's earlier success notice without knowing whether ARM `CustomDeployment-20261026093554` had an empty template. No actual CUDA/Hunyuan job until licensed weights, A100 available quota and strictly approved full price cap.
+
+## 2026-10-26 — Live deployment succeeded, next gate is quota 0→1
+- **DONE, independently verified in Azure:** East US empty `rgai-f5-gpu-canary-eastus` in isolated `rg-retailgrowth-dev`, default Consumption only; [OIDC #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764) green. **ManagedEnvironmentConsumptionNCA100Gpus: limit=0, used=0**. Do NOT create another managed environment or redeploy the confirmed resource; no GPU/app/job has been launched.
+- **P0 owner/service quota approval:** select that exact environment in Azure Portal → **Settings → Quota**, request **new limit = 1** for **Managed Environment Consumption NCA100 GPUs**, and verify Azure's approval/status. This is an *environment* quota; do not request the unrelated subscription dedicated A100 meter. Microsoft may automatically approve or route to review. Do not create support cases if owner does not authorize them. No quota request submitted so far.
+- **P0 genuine user-requested video after quota:** licensed verified Tencent 1.5 weights + pinned SHA256 lock, working BF16 A100 CUDA image, synthetic no-customer photo processing in East US subject to territory/license review, explicit full-cost one-job hard stop, exact one run/zero retries. Record a real 5-second portrait kurti-boutique MP4, ffprobe, hash, frame sheet and human quality review; only then claim Hunyuan sample produced. Part3/Feature4 hosted integrations separately pending.
+
+## 2026-10-26 — Azure GPU alternate path eliminated under current quota
+- Live read-only GitHub OIDC run #40355181214 confirmed Central India and East US **regional VM vCPU quota 10** and no user-subscription A100 VM eligibility. Azure A10 appears in SKU catalog without restriction, but only a **full 24GB A10** with 36vCPU satisfies Tencent >=14GB with offloading; current region quota is insufficient. Do **not** deploy a 6-vCPU, 4GB fractional A10 expecting model inference, and do not increase other quotas without reviewing costs. No Azure GPU is yet suitable within quota.
+- Cheapest approved short-run path remains an **owner-submitted request for ONE per-environment `Managed Environment Consumption NCA100 GPU`** on existing `rgai-f5-gpu-canary-eastus` (limit 0); Microsoft may automatically approve or route for manual review. Request alone has no GPU compute usage fee. No request has been made. Only after quota 1, source/weight license checksum, territory/privacy, full budget + bounded GPU job, and actual MP4 QA can Feature5 claim genuine generation. Keep job scheduling disabled.
+
+## 2026-10-26 — Prioritized action after verified quota=0 and provider comparison
+1. **External Microsoft prerequisite (UNSUBMITTED):** on existing `rgai-f5-gpu-canary-eastus` → Settings → Quota request `Managed Environment Consumption NCA100 GPUs` new limit **1**; log actual request response/status. OIDC usage read confirms zero, but no supported CLI/REST submission path was verified for this *environment* quota.
+2. **Development source follow-up:** Review/merge the feature-owned `external_gpu_budget.py` quote screening only after CPU test and PR CI; it does not enable new runtime or spend. Existing 5s red-kurti `demo_fashion.py`, pinned Tencent runtime and manual GPU harness remain the ONLY acceptable genuine-video flow.
+3. **Fallback only if provider controls approved:** independently verify current Runpod A40 48GB or RTX 4090 quote, host RAM, location/terms, signed-in account capacity, all-in provider cap and automatic termination/disk delete. Do not treat offline quote screening as an actual provider reservation or hard billing cap; avoid retailer/customer media.
+4. **Paid one-shot still BLOCKED:** verified GPU quota or approved bounded external rental, independently licensed official model/weights digest, BF16 CUDA image, proper region rights/consent, full-dollar cost allowance, one attempt/no retry, private original `clip.mp4` + ffprobe/hash/contact sheet + human QA and invoice/teardown. None has been executed.
+
+## 2026-10-26 — A40 source bug fixed; external action still outstanding
+- DONE: A40 48GB BF16 quote screening and CPU tests under Feature5-owned PR #323; NVIDIA/Runpod public specs support the *hardware candidate*, not a real Hunyuan model benchmark. Provider-side teardown bound in cost screen remains mandatory.
+- NOT DONE: Azure **managed-environment** NCA100 quota new limit=1 request (submit under existing environment Settings→Quota), account-specific cloud GPU capacity/rates, prepaid hard cap, approved Tencent weights, real CUDA, true five-second H264 MP4.
+
+## 2026-10-26 — Next after evaluated full GitHub solutions
+- **Coordinator decision required:** evaluate retaining Hunyuan 1.5 vs adding separate Feature5 **LTX-Video v0.9.8 13B distilled** long-shot candidate, and use Part3-owned Wan2.2 as permissive short-format baseline; no duplicated Part3 implementation.
+- **Before paid deployment:** independently review LTX 0.X checkpoint commercial license and AI disclosure/hosted SaaS constraints, pin exact code/weights/ComfyUI legacy workflow version plus checksums, ensure DEV Azure `ManagedEnvironmentConsumptionNCA100Gpus` limit >= 1, then operator cost ceiling.
+- **Acceptance:** genuine private synthetic 5s pilot and controlled 60s model-extension clip at target portrait FPS, original SHA/FFprobe, garment/face visual reviewer and actual measured Azure GPU billing; until then neither performance nor cost is proven.
+- Source/architecture comparison: `docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md`. No H100 Terraform apply, no new worker deployment and no PR merge independently.
+
+## 2026-10-26 — Full upstream deployment priority
+- User wants **real complete upstream project**, not replacement Feature5 generator code. When Azure quota supports it, use pinned, full ComfyUI plus official LTX-Video engine/models and their genuine long-shot workflow in private serverless A100; H100 Microsoft sample only if the owner accepts its ~3x active cost and separate 40-vCPU VM quota.
+- Gate all paid deployment on operator-approved total budget, exact committed source/weight manifest, license acceptance, secured ComfyUI API, private Azure networking, one-run/no-retry and real visual quality benchmark. Stop/deallocate H100 VM when inactive; serverless A100 scale-to-zero.
+- Detailed Azure USD/INR comparisons and blockers in `docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md`. No switch to paid hosted APIs or mock output as proof.
+
+## 2026-10-28 — External GPU proof first, no automatic purchase
+1. Operator may purchase prepaid credits on https://jarvislabs.ai/in and select **1× A100 80 GB on-demand** in an available India region (published **₹140.94/h**, separate storage + 18% GST; **no spot**). Minimum top-up/availability must be checked in checkout, not inferred.
+2. Before booting/renting, approve a hard spending ceiling, plan minimum 100GB scratch/model disk, verify secure SSH/private endpoint, project checkpoint weight size/terms and output transfer path. Do not expose ComfyUI or customer media; use synthetic image/garment brief.
+3. Install/clone **complete official Wan-Video/Wan2.2** pinned release+TI2V-5B model weights; execute its official 5s portrait inference CLI; preserve original MP4/ffprobe/frames/SHA and real billed minutes. No imitation generator and no unfounded 60s estimate.
+4. Pause immediately when GPU work finishes and **delete disk/instance after downloading private evidence** to avoid continued storage charges. Then compare genuine visual results before any 15s/60s proposal. All code and ledger integration remains Part3/coordinator-owned; Feature5 supplies quality/cost evidence only.
+
+## 2026-10-28 — Azure A100 quota now visible as 2 (operator screenshot)
+- **Previously pending blocker changed:** Azure Portal environment GPU quota **0 used of 2 limit** for A100; owner may use existing East US environment instead of renting third-party GPU. Retain image/screenshot evidence in issue #400; independently confirm with `az containerapp env list-usages --resource-group rg-retailgrowth-dev --name rgai-f5-gpu-canary-eastus` before making any GPU deployment.
+- NEXT: choose original Wan2.2 TI2V-5B upstream for one genuine portrait 5s GPU benchmark, after source+weights integrity and license review. Submit a coordinator-approved one-shot, cap-controlled private GPU worker (1 GPU max, min replicas 0, no automatic retries, private output only) using existing Azure OIDC. **No paid GPU provisioning until the cost ceiling and resource configuration are reviewed.**
+- Cost model: quota alone ₹0 in GPU compute, running Azure serverless GPU replicas billed by GPU/CPU/RAM seconds, scaled-to-zero no replica resource charge. Storage/logging/network may have independent charges. No measured per-video estimate yet.
~~~~

## docs/feature5/OIDC_EMPTY_ENV_COORDINATOR_HANDOFF_20261026.md

~~~~diff
@@ -0,0 +1,136 @@
+# Feature5 — coordinator Azure OIDC execution handoff (2026-10-26)
+
+**STATUS: SOURCE READY, NOT EXECUTED.** Owner asked to proceed, avoid support
+tickets, minimize cost and produce one genuine HunyuanVideo sample. Actual
+connected Azure Portal inspections confirm `rg-retailgrowth-dev` exists. Both
+Quota portal views lacked a managed-environment A100 row because the required
+East US workload-profiles environment is not yet created.
+
+## Official Azure blocker decoded
+
+Microsoft's [serverless GPUs documentation](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview) states:
+
+> You must create a workload profiles environment in a supported region before
+> you can request the required managed environment GPU quota.
+
+The existing subscription's *subscription-level dedicated GPU quota* is NOT
+the per-environment serverless NCA100 quota. Checking Quotas without a managed
+environment was the wrong first step; do not infer the latter is zero. Official
+[Container Apps quotas](https://learn.microsoft.com/en-us/azure/container-apps/quotas)
+are scoped per environment and read via `az containerapp env list-usages`.
+
+## Tools attempted (do not repeat browser route)
+
+1. Saved Microsoft Azure Portal login succeeded and exposed dedicated DEV RG,
+   but Quotas had no NCA100 data.
+2. Portal's Container Apps Environment list/Marketplace repeatedly navigated
+   to VM results, never exposed a standalone environment create wizard; no write.
+3. An **ephemeral, no-storage** Azure Cloud Shell Bash session did start, but
+   the browser automation could not focus the xterm prompt to type commands.
+   No shell commands ran, and no resource was created.
+
+The reliable next route is the repository's existing Azure DEV GitHub OIDC
+identity, *not* more portal clicks. **Only the coordinator owns and may edit
+`.github/workflows/**`, main, shared contracts and actual Azure deployment.**
+Feature5 PR #323 intentionally contains no workflows or live migrations.
+
+## Single new-resource proposal
+
+The pinned, fully test-validated ARM JSON is
+`feature5_motion/infra/empty_gpu_env.json`. It creates **one** resource only:
+
+- Subscription: exact existing DEV subscription from GitHub environment secret
+  `AZURE_SUBSCRIPTION_ID`, not copied into code.
+- Resource group: `rg-retailgrowth-dev` (existing tagged Central India group).
+- Container Apps managed environment: `rgai-f5-gpu-canary-eastus`,
+  resource region `eastus`, tags app=RetailGrowthAI, environment=dev,
+  feature=feature5.
+- Workload profiles type v2 with **default Consumption only**.
+- `appLogsConfiguration.destination = none` — no new Log Analytics bill.
+- NO A100 workload profile, Container App, Job, VM, image registry,
+  private networking or active replica. No GPU charge can originate from
+  a non-existent GPU replica. Any other Azure dependent charges must still be
+  reviewed in ARM what-if before deploying.
+
+## Gated coordinator execution procedure
+
+From a reviewed, manually dispatched GitHub DEV OIDC workflow using
+`azure/login@v3` and existing `environment: dev`, or another securely
+authenticated Azure terminal authorized for the exact DEV RG only:
+
+```bash
+set -euo pipefail
+umask 077
+RG=rg-retailgrowth-dev
+ENV=rgai-f5-gpu-canary-eastus
+# Secret inherited from existing RetailGrowthAI GitHub environment DEV,
+# not printed in logs:
+test -n "${AZURE_SUBSCRIPTION_ID:-}"
+test "$(az account show --query id -o tsv)" = "$AZURE_SUBSCRIPTION_ID"
+test "$(az account show --query state -o tsv)" = Enabled
+test "$(az group show -n "$RG" --query location -o tsv)" = centralindia
+test "$(az group show -n "$RG" --query tags.app -o tsv)" = RetailGrowthAI
+test "$(az group show -n "$RG" --query tags.environment -o tsv)" = dev
+test "$(az provider show -n Microsoft.App --query registrationState -o tsv)" = Registered
+if az containerapp env show -g "$RG" -n "$ENV" -o json >/dev/null 2>&1; then
+  echo 'BLOCKED: target exists; reconcile instead of overwrite'; exit 4
+fi
+python - <<'PY'
+from feature5_motion.empty_env_template import validate_template
+validate_template()
+print('Exact one-resource zero-compute template validated')
+PY
+az deployment group what-if --resource-group "$RG" --template-file \
+  feature5_motion/infra/empty_gpu_env.json --output json > "$RUNNER_TEMP/feature5_whatif.json"
+python - "$RUNNER_TEMP/feature5_whatif.json" "$AZURE_SUBSCRIPTION_ID" <<'PY'
+import json,sys
+from feature5_motion.empty_env_template import validate_what_if
+validate_what_if(json.load(open(sys.argv[1])), sys.argv[2])
+print("Azure what-if: exactly one new empty RetailGrowthAI DEV managed environment")
+PY
+# STOP HERE ON INITIAL COORDINATOR REVIEW.
+# Separate explicitly approved manual job may then execute exactly:
+# az deployment group create -g "$RG" \
+#   --template-file feature5_motion/infra/empty_gpu_env.json \
+#   --name rgai-feature5-empty-env-quota-inspection
+```
+
+After an approved empty environment creation and ARM `Succeeded`:
+
+```bash
+az containerapp env show -g "$RG" -n "$ENV" \
+  --query '{name:name,region:location,state:properties.provisioningState,profiles:properties.workloadProfiles}' -o json
+az containerapp env list-usages -g "$RG" -n "$ENV" -o json
+```
+
+Read specifically `Managed Environment Consumption NCA100 GPUs`
+limit/currentValue. Missing row = **not visible or ineligible**, not zero.
+No quota request or GPU job should start without that evidence. Do not
+automatically retry a potentially created resource after timeouts.
+
+## Before genuine model run
+
+Only after an available quota **and** separately reviewed Tencent community
+license, complete Tencent model shards+immutable SHA256, approved synthetic
+text-only region, actual 24vCPU/220GiB-style A100 profile (verify Azure
+meter/resource shape), private media receipts and explicit full-job USD ceiling
+may the coordinator propose one manual, zero-retry, bounded-time GPU Job.
+Feature5's sample prompt is `fashion_motion_spec` (red embroidered kurti
+in boutique, 5s portrait), with real ffprobe/sha256/contact-sheet acceptance.
+No real Tencent model MP4 exists today.
+
+## Cost correction
+
+The older hypothetical 4-vCPU/16-GiB example is NOT a verified allocation
+for A100 serverless GPU. Microsoft lists A100 serverless workload profiles
+with **up to 24 vCPU and 220 GiB**; Azure publishes per-second GPU/CPU/GiB
+meters. At the previously verified public East US meter snapshot:
+
+- A100 $0.000529 per second
+- 24 vCPU × $0.000024 per second = $0.000576 per second
+- 220 GiB × $0.000003 per second = $0.000660 per second
+- Combined **$0.001765 per second**, or **$1.059 for 600 billed seconds**
+  before VAT/egress/storage/image startup, model load, retries and other costs.
+
+This is an **illustrative estimate**, not guaranteed quota, price, runtime,
+capacity reservation or hard billing cap. GPU is still NOT running.
~~~~

## docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md

~~~~diff
@@ -0,0 +1,74 @@
+# Feature #5 — Open-source video-engine architecture review (2026-10-26)
+
+**Scope:** RetailGrowthAI Azure-only DEV, genuine commercial AI-motion, Indian fashion/product reels, text-to-video and image-to-video, human/garment consistency, private tenant outputs, target up to **60 seconds with 100% AI-generated footage**. Existing self-hosted Hunyuan 1.5 Feature5 PR #323 is preserved; no PROD/WineShopPOS changes.
+
+**Decision status: evaluation, NOT a switched/deployed provider, CUDA benchmark, legal clearance or acceptance of a 60s reel.** Coordinator must explicitly approve any cross-feature Part3 contracts/migration/frontend change. No extra Azure resources or billable GPU were provisioned in this review.
+
+## Complete upstream GitHub candidates (official sources)
+
+| Project | Actual available capability | Code and checkpoint terms | Fit / gap |
+| --- | --- | --- | --- |
+| **Lightricks/LTX-Video** https://github.com/Lightricks/LTX-Video | Official Python inference, T2V/I2V, reference frames, condition/edit/extend; v0.9.8 13B distilled and FP8. Official changelog explicitly offers **up to 60-second extended long shots**, using ComfyUI workflow. Source: https://github.com/Lightricks/LTX-Video; weights: https://huggingface.co/Lightricks/LTX-Video | GitHub code **Apache-2.0**, but v0.9.8 **weights are separately licensed, not Apache**: https://huggingface.co/Lightricks/LTX-Video/blob/main/LTX-Video-Open-Weights-License-0.X.txt. License grants royalty-free use subject to restrictions; businesses with revenue **>= US $10 million** require paid commercial licensing; hosted SaaS, AI-content disclosure and permitted-use requirements apply. Must review legal entity's actual revenue/terms. | **Best long-form candidate for conditional Feature5 R&D.** Not a ready tenant/billing/queue SaaS, and not 60s proof on this subscription. 60s is a *model-extension workflow*, NOT 1 cheap single-pass inference. |
+| **Wan-Video/Wan2.2 TI2V-5B** https://github.com/Wan-Video/Wan2.2 | Real runnable T2V and I2V, official weights, 720p 24fps, at least 24 GB VRAM with offloading on a single card. Source: https://github.com/Wan-Video/Wan2.2 | Official repository says Apache-2.0 code AND model weights; preserve notices and downstream-use obligations. | **Best clean permissive commercial baseline.** Short-clip generator; achieving 60s requires genuine model-generated extension/shot planning and quality gates; no one-shot 60s claim. **Already belongs to Part3 provider ownership**. Do not duplicate Part3 code. |
+| **Tencent-Hunyuan/HunyuanVideo-1.5** https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5 | Official 480p/720p T2V/I2V, 14GB VRAM minimum with offload; existing Feature5 SHA-locked runner/testing under PR #323. | Tencent community model license with territory/notice and service conditions; separate from code and review required before activation. | Best reuse of completed Feature5 work; standard 121-frame 24FPS (~5 s) generation; does not have a demonstrated 60s single-pass solution. |
+| **Comfy-Org/ComfyUI** https://github.com/Comfy-Org/ComfyUI | Runnable visual workflow engine, GPU inference UI and HTTP queue/API. Supports third-party Wan and LTX models/workflows; can be placed behind RetailGrowthAI job API. | **GPL-3.0** engine; separate from weights. Preserve notices and review licensing/interface/distribution strategy; DO NOT expose raw ComfyUI unprotected to users. | **Practical worker/authoring engine**, not a tenant-secure SaaS or a model by itself. Recommended for *internal GPU worker*, or use upstream Python headless directly to avoid GPL integration complexity. |
+| **Azure-Samples/comfyui-on-azure** https://github.com/Azure-Samples/comfyui-on-azure | Working Azure reference with Terraform GPU VM, CUDA, ComfyUI and Wan2.2/LTX-2 models. | Each included model and dependency has its own terms. | **Cloud reference only. Uses H100 GPU VM**, not our already deployed East US scale-to-zero ACA. DO NOT terraform apply as-is: expensive H100 and VM quota 10 vCPU in DEV disallow this template. |
+
+## Findings most material to this retailer SaaS
+
+1. **Strict open-source commercial licensing priority:** Wan2.2 is the permissive model baseline; LTX-Video code is open-source but **v0.9.8 weights have special commercial terms**. Do not conflate code license and checkpoint rights. Do not buy/run LTX weights in customer workflows until legal/licensing gate accepts exact version and shop/platform disclosures.
+2. **Long-form 60-second output:** LTX v0.9.8 13B announcement says *up to 60 seconds using long-shot/extension*. Model card separately recommends **<257 frames per generated window** and image dimensions under 720x1280; for 24FPS 60s is ~1,440 output frames, thus practical design is overlapping, model-generated continuation windows and audio/clip mux, not magically one 1,440-frame cheap generation. It remains 100% AI model-generated footage; FFmpeg is allowed only to assemble model footage/codec/mux, not insert stock footage.
+3. **Realistic fashion/person consistency:** Use approved synthetic/model-owned still reference from Feature3 library + I2V/conditioned long-shot extension, persistent detailed kurti prompt, seeded runs, reference hashes and role/garment temporal human review. Text-only single-prompt identity consistency across 60s is *not guaranteed*.
+4. **Cloud feasibility:** Azure official serverless GPU guide https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview lists A100 East US, per-second usage, scale-to-zero, with **managed-environment GPU quota** requirement. Our existing `rg-retailgrowth-dev` / `rgai-f5-gpu-canary-eastus` has **NCA100 quota 0** (Azure OIDC run #40347841764). Current H100 and comparable VMs are not available under observed regional VM quota; no GPU platform avoids GPU capacity/billing altogether. Quota tracking: #400. The user opened an Azure portal support form; screenshot is not proof of submission or approval.
+5. **Commercial infrastructure cost:** Do NOT equate output-video seconds to GPU billable seconds, nor present unbenchmarked sample ₹ amounts as measured cost. Model- and workflow-specific compile/model load, each overlap/continuation pass, retries, disk/staging and GPU active duration count. Pilot one 5-second model run with a fixed operator-approved spend/teardown ceiling; only then attempt 15s and 60s with budget gate.
+6. **SaaS integration isn't in upstream repos:** preserve our Supabase tenant/auth isolation, existing Part3 reservations/outbox, Feature4 human review and FFmpeg, Feature3 reference library. All public ComfyUI UIs/HTTP ports MUST stay private behind authenticated worker. Use signed blob outputs and provenance; no direct end-user access to GPU containers.
+7. **Avoid copying old Python commands blindly:** GitHub official LTX repo README contains `inference.py` for v0.9.8 and `configs/ltxv-13b-0.9.8-distilled.yaml`; current ComfyUI-LTXVideo branch has moved toward LTX-2.x. Pin a mutually compatible version/revision of workflow and node dependencies before containerizing; inspect complete license and weight manifests. No claim that today's HEAD ComfyUI plugin necessarily accepts v0.9.8 legacy workflow.
+8. **No GPU spend by research:** no repo cloned and CUDA/video output checked in this isolated agent runtime. GitHub upstream READMEs are upstream implementation evidence, not our deployment or performance evidence.
+
+## Proposed low-cost rollout — coordinator approval required
+
+- **Stage A (zero Azure GPU spend):** retain existing Hunyuan runner; pin external repositories and exact model checkpoints, inspect all licenses, model weight SHA256, downstream notices and container supply-chain; prototype an *offline* capability contract for LTX long-extension with `model_id`, `source_ref_hash`, `target_duration`, `aspect_ratio`, `seed`, `max_gpu_seconds`, and `max_total_cost`. No new shared API/schema without coordinator.
+- **Stage B (after quota and license approval):** deploy one private, max-1 scale-to-zero GPU worker to EXISTING `rgai-f5-gpu-canary-eastus` with Azure OIDC; signed approved image and pinned model weights mounted/staged privately; idle resources zero, manual invocation, **no automatic retry**. Reuse Part3 ledger and Feature4 approvals before enabling SaaS checkout. Start with 5 seconds red kurti synthetic T2V or I2V. Record build and GPU validation; keep smoke-test CPU/mock results separate from real inference.
+- **Stage C:** conditional A/B quality test Hunyuan 1.5 vs LTX 13B distilled and Wan 5B on actual available SKU (validate memory/BF16, package/driver). Measure wall/GPU time including cold start, total bill, original MP4 SHA256, FFprobe duration/fps, six+ review frames, visual human garment/identity continuity.
+- **Stage D:** only on positive pilot, attempt 15s -> 60s **pure model-generated** extension. Fail closed on budget/runtime/disclosures/tenant isolation. Do not promise a single-run 60s 480p commercial-quality video or fixed per-reel price.
+- **Alternative budget mode:** existing Part3 Wan provider stays primary where legal simplicity/short AI motion matters, not duplicate Feature5 implementation. LTX is long-form research candidate subject to commercial license review. 
+
+## Concrete verified entry points
+
+- LTX code and long-form claim: https://github.com/Lightricks/LTX-Video
+- LTX versioned model card and weights: https://huggingface.co/Lightricks/LTX-Video
+- LTX model license restrictions: https://huggingface.co/Lightricks/LTX-Video/blob/main/LTX-Video-Open-Weights-License-0.X.txt
+- WAN Apache-2.0 model & single-GPU instructions: https://github.com/Wan-Video/Wan2.2
+- ComfyUI engine/API: https://github.com/Comfy-Org/ComfyUI
+- Azure end-to-end video template (H100 VM, reference only): https://github.com/Azure-Samples/comfyui-on-azure
+- Azure scale-to-zero A100: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
+- RetailGrowthAI current source-only Feature5 PR #323: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/323
+
+**Acceptance:** only claim production model selection after live licensed CUDA 5s and 60s content is privately generated, FFprobed/hashed, visually reviewed and priced from actual Azure usage. Until then, all three candidates are *evaluated upstream projects*, not deployed RetailGrowthAI workers.
+
+## 2026-10-26 decision aid — costs for FULL original Git repositories on Azure
+
+**Customer instruction:** run the original upstream software (full ComfyUI and its model extensions, with genuine full video-model checkpoints), not a reimplementation or mock generator. Do not replace working upstream workflows with hand-built approximations. Integration to RetailGrowthAI should be a thin authenticated wrapper, not a rewrite of the generator.
+
+### Route 1: the whole Microsoft Azure Samples project, unchanged first
+
+- Official full repository: https://github.com/Azure-Samples/comfyui-on-azure
+- It provisions an **Azure Linux H100 GPU VM**, NVIDIA CUDA, complete ComfyUI and Wan2.2/LTX-2 model installations via its Terraform runbook. Upstream VM example publicly exposes an HTTP :8188 URI; *for RetailGrowthAI*, close/public-restrict that raw UI and restrict it to trusted operators and the private Azure network before using any customer content.
+- The `Standard_NC40ads_H100_v5` is **40 vCPUs, 320 GiB RAM, 1x H100 GPU**. Observed public East US Linux PAYG rate **$6.98/hour** (2026-10; source: https://azurehub.org/tools/vm-pricing/Standard_NC40ads_H100_v5/ and https://cloudprice.net/vm/Standard_NC40ads_H100_v5).
+- Approximate INR at October 26, 2026 spot ~₹95.38/USD: **₹666/hour**, **₹15,980/24h**, **₹486,000 per 730-hour month** in VM compute alone, excluding persistent disks, Azure Blob, IP/network, model licensing and tax.
+- VM compute bills when allocated **even while idle**; **stop/deallocate** the VM between operator sessions to stop VM compute, while disk may keep billing. Do not leave Terraform resources running 24/7 for a one-off proof.
+- **BLOCKER:** actual DEV East US VM quota audited at 10 regional vCPU by OIDC #40355181214, below this exact VM's 40 vCPUs. A VM quota increase and SKU/account stock would be necessary. Azure Samples code does not bypass account quota.
+
+### Route 2: entire ORIGINAL video engine inside existing Azure serverless GPU worker
+
+- Clone/fetch and pin **full official source repositories**, install exact compatible ComfyUI extensions and LTX weights; do not copy a minimal imitation generator. Deploy in an Azure Container Apps GPU-enabled image with private model storage and restricted job invocation. The Azure Samples H100 *Terraform* itself is **not directly deployable** to serverless ACA without different resource/container deployment packaging, networking, model-weight storage and warm-start considerations.
+- Verified official Azure Retail Prices API for **East US on 2026-10-26**: https://prices.azure.com/api/retail/prices?%24filter=serviceName%20eq%20%27Azure%20Container%20Apps%27%20and%20armRegionName%20eq%20%27eastus%27 : A100 NCv4 GPU **$0.000529/active second**, standard active vCPU **$0.000024/vCPU-second**, active RAM **$0.000003/GiB-second**. An explicitly **illustrative** 4 vCPU + 16 GiB allocation totals **$0.000673 per second** = **$2.4228/hour** = **~₹231/hour**. Actual full LTX/ComfyUI worker may require higher CPU/RAM, affecting total cost.
+- Illustrative billable active runtime: 0.5h ₹116; 1h ₹231; 2h ₹462; 4h ₹924; 8h ₹1,849. **These are not per 60s output reel.** Model downloads, cold start, multi-window LTX long-shot generation, failed attempts and retries remain unbenchmarked; quote only once a real licensed private run is profiled.
+- Serverless GPU can scale to **zero** when inactive per https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview; other Azure resources/storage still cost money. Treat UI availability/response to cold start, large disk read and model init as unproven.
+- **BLOCKER:** the already created East US `rgai-f5-gpu-canary-eastus` has **ManagedEnvironmentConsumptionNCA100Gpus limit=0** according to Azure OIDC #40347841764. The user has navigated Azure's support-form submission but no support case receipt or approval readback has been verified. Azure cannot schedule the GPU until that quota is nonzero.
+
+### Real deployment and acceptance approach
+
+1. Prefer route 2 for cost ***after quota approval***, but first test whether full upstream ComfyUI+LTX workflow and its checkpoint/config actually fit and perform on A100, with exact source and weight versions pinned, independent license review, all external ports secured and no public sample portal.
+2. If operator insists on using Microsoft Samples as-is to immediately get the original project with minimal integration engineering, route 1 is the reproducible H100 VM option, **but requires a 40-vCPU quota** and costs roughly 3x per active hour, plus ongoing bills until deallocation. Neither option is free of Azure quota hurdles under the observed DEV limits.
+3. The first billable action must be an explicitly capped synthetic DEV run; record **real measured GPU billable seconds** for a long-shot 60-second output, original model output, hash, ffprobe, visual/garment continuity review and proof that the workload used the upstream engine. *Do not sell cost or output quality guarantees without that benchmark.*
~~~~

## docs/feature5/PART3_DEV_SCHEMA_RECONCILIATION_20261026.md

~~~~diff
@@ -0,0 +1,41 @@
+# Feature #5 / Part 3 — Live DEV ledger reconciliation proposal
+
+**2026-10-26 read-only verification.** Status: **proposed for RetailGrowthAI coordinator, not applied**. Feature #5 branch: `feat/feature5-premium-ai-motion`; draft PR #323. Related unmerged Part 3 draft PR #125 and Feature #4 draft PR #322.
+
+## Source of truth: actual DEV database (read-only query)
+
+Project: dedicated RetailGrowthAI DEV Supabase `jeearzffnjbvghwjjjrf`, not WineShopPOS. Checked `information_schema.columns` and PostgreSQL `pg_constraint` via read-only SQL. **No writes occurred.**
+
+| Existing object | Observed DEV status | Needed for optional Hunyuan |
+|---|---|---|
+| `public.shop_subscriptions` | Columns: `shop_id,plan_code,status,valid_from,valid_until,period_start,period_end,created_at`. No premium budget/seconds. | Add optional, default-zero premium allowance and hard per-period cost ceiling using existing subscription row |
+| `public.shop_usage_reservations` | `shop_id,operation,job_id,period_start,reserved_at`; `operation` CHECK allows **only** `campaign` and `render`; no `units` column. | Add `premium_video` operation and monotonic reserved units within existing ledger, preserve old operations |
+| `public.premium_video_jobs` | **Not present**. | Coordinator reviews Part 3's proposed table and evolves **that same table** for Wan and Hunyuan, not separate competing jobs |
+| `public.job_outbox` | Existing kind check **only** `planning` or `render`; states `PENDING/CLAIMED/SENT`. | Add `premium_video` kind with same durable outbox and delivery/poison/lease rules, not best-effort direct Queue publish |
+| `public.render_jobs` | Existing free FFmpeg rendering job and quota. | Compose after Feature5 clip human review; do not duplicate premium credit reservation when composing an existing premium motion asset |
+
+The Part 3 **staged but unmerged** SQL `azure-functions/campaign-api/part3_sql/PROPOSED_20261023180000_premium_video_reservations.sql` permits only Wan model IDs and `720P/1080P`. Its proposed `reserve_premium_video` trigger prices only those resolutions as `seconds × 0.10/0.15` USD. **It is incompatible with 5s, 480p Hunyuan and GPU wall-clock billing. Do not execute it verbatim then blindly insert Hunyuan jobs.**
+
+## Coordinator-owned staged migration design (no migration files or SQL executed here)
+
+1. Build on existing Part 3 provider-neutral `premium_video_jobs`; add provider/model profile for `hunyuanvideo-1.5-480p`, `480p`, 5s profile and optional `image` input. Existing Wan behavior and all old reservations remain valid. Add source `media_assets` shop+asset composite FK and campaign/day same-tenant join checks before spend.
+2. Preserve one **existing** `shop_subscriptions` row lock and `shop_usage_reservations` table for *all* premium jobs. Add `units` and a premium operation to existing usage ledger; default premium seconds/budget to **zero** for all existing shops. Never auto-upgrade TRIAL plans or modify their subscriptions.
+3. Price Hunyuan from **reviewed server-side tariff/workload profile**, with the operator's selected region, GPU+vCPU+RAM retail rate, max billable wall time and ancillary allowance; compute `reserved_usd` **inside an atomic service-role SQL path**, never accept client-submitted USD or blindly apply Wan's `per output video second` price. Feature5 `MotionSpendGuard` checks the same maximum and that the existing reservation covers it.
+4. Durable `job_outbox.kind='premium_video'` triggered in the same transaction as reservation. Queue payload is canonical UUID only; worker atomically claims a bounded lease token; all state changes and storage receipts must fence `shop_id+job_id+attempt_token`. Handle ambiguous GPU/DB/storage outcomes as `UNKNOWN` without automatic charged replay or refunds.
+5. After private `retailgrowth-media` upload and exact receipt verified, mark machine status `SUCCEEDED` but `quality_review_required=True`; disallow Feature4 and publishing until an independently stored authenticated reviewer grants `VisualReview` with exact immutable clip SHA256 and all commercial/licensing/garment checks. Commit output `media_assets` under correct shop RLS; never issue vendor or private source URLs to public API.
+6. Let Feature4 consume an approved, privately staged `source_feature=feature5` video via proposed `creative_reel_v1` server manifest. Apply the normal separately requested final-composition render quota **only if the product contract requires it**, never a second *premium model inference* reservation.
+7. Keep per-provider feature flags OFF until coordinator migration, RLS, signed-in E2E, per-shop caps, budget/region eligibility, source-license and GPU/legal acceptance pass. Have one vetted DEV release, original 20 migration history intact. Do not touch WineShopPOS or PROD.
+
+## Minimum negative SQL/E2E tests (coordinator to execute)
+
+- Anonymous, unapproved VIEWER and other shop cannot create/fetch source, reserve, claim, view output, or approve final clip.
+- Unapproved campaign day, mismatched media tenant, invalid commercial rights, wrong plan, expired plan, zero cap, suspended plan and over-budget job all fail **before** queue/GPU.
+- Simultaneous job inserts honor same shop subscription row lock; two duplicate idempotency requests produce **one** reserved job, not two charges.
+- Insertion with spoofed `reserved_usd`, changed source prompt hash/seed, invalid 480p profile, unauthorised model or missing durable outbox fail.
+- Replayed queue message, expired/mismatched lease token, private upload timeout, DB commit ambiguity and slow GPU overrun never trigger automatic second inference or false refund.
+- A real authorized clip with wrong shop, media SHA, revoked review role, pending VisualReview or unreviewed AI disclosure cannot enter Feature4.
+- Preserve all current `campaign`/`render` operations, render worker, Supabase isolation, existing DEV shop/user and 4 required CI jobs.
+
+## Strictly deferred until integration is actually verified
+
+A real GPU job, model weights checksums, actual tariff/billing reconciliation, image-to-video retailer consent for regional processing, approval of Tencent's territory/hosted commercial terms, human visual results and Feature4 real end-to-end composition **are not complete**. The branch has only offline CPU and contract-level tests. The coordinator alone owns `supabase/migrations/**`, `docs/INTERFACES_V1.md`, current main, PROD, and live rollout.
~~~~

## docs/feature5/PRICING_AND_LICENSE_VERIFIED_20261026.md

~~~~diff
@@ -0,0 +1,44 @@
+# Feature #5 — Verified Azure pricing and permitted roll-out snapshot
+Date: 2026-10-26 (official Microsoft Retail Prices API, USD, PAYG primary meters)
+
+## Official source and rates (not a deployment record)
+
+Microsoft Azure Retail Prices API:
+- https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName%20eq%20%27Azure%20Container%20Apps%27%20and%20armRegionName%20eq%20%27eastus%27
+- https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&%24filter=serviceName%20eq%20%27Azure%20Container%20Apps%27%20and%20armRegionName%20eq%20%27centralindia%27
+
+| PAYG meter | East US, USD | Central India, USD | Billing unit |
+|---|---:|---:|---|
+| Standard NC A100 v4 GPU Usage | 0.000529 | 0.000741 | 1 second |
+| Standard NC T4 v3 GPU Usage | 0.000073 | 0.000102 | 1 second |
+| Standard vCPU Active Usage | 0.000024 | 0.000024 | 1 second per vCPU |
+| Standard Memory Active Usage | 0.000003 | 0.000003 | 1 GiB second |
+
+A100 listed pricing in Central India DOES NOT mean it can be deployed there: Azure Container Apps' *GPU serverless overview* lists Central India as T4 **only**, East US as A100/T4. Serverless GPU quota is per-subscription/environment and MUST be verified. The primary A100 East US retail meter became effective 2026-04-01; pricing may change.
+
+PAYG East US A100 example assuming 4 vCPU, 16 GiB active RAM, no free grant:
+- GPU rate 0.000529 + 4 × 0.000024 + 16 × 0.000003 = **$0.000673/sec** for the assumed active compute configuration.
+- 300s including load + inference + teardown ≈ $0.201900
+- 600s ≈ $0.403800
+- 900s ≈ $0.605700
+- 1800s ≈ $1.211400
+
+These are metered *duration scenarios*, not measured HunyuanVideo 1.5 clip generation times. Six completely separate 600-second jobs might cost 6 × 0.4038 = $2.4228 in this assumed profile; a shared bounded model-load session could differ materially. EXCLUDES storage, internet egress, image/weight transfer, extra memory/vCPU, licenses, GST/taxes, currency conversion, provider and media costs, and idle/management overhead where applicable. GPU meter and resource allocation must be rechecked with the Azure account before scheduling even one actual paid test.
+
+## Real test gate despite owner approval
+
+The owner authorized development and real GPU testing in chat, but provided no maximum aggregate spend, no connected Azure subscription credentials/quota, no reviewed outbound media region transfer and no checked Tencent license-use statement. Therefore:
+1. Do NOT deploy an always-on GPU or leave an app with min replicas >0.
+2. When operator access is available, run a single explicitly configured bounded TEST with job concurrency=1, max attempts=1, timeout <=1800s, consumption workload profiles and target regional availability check; record START/STOP, observed GPU+CPU+RAM charges.
+3. Make the pilot's hard spending cap smaller than the approved maximum and reconcile uncertain cloud acknowledgments before any replay.
+4. Use non-customer licensed/approved test imagery while India->US regional transfer and user consent are evaluated. No real customer imagery must be transferred without explicit consent.
+5. Commercial release requires Tencent hosted-service terms, third-party notices, use limitation, origin/recipient territory controls, and MAU threshold confirmation. India-only is a reasonable proposed pilot scope, not a substitute for legal review.
+
+## License finding
+HunyuanVideo 1.5 weights are under **Tencent Hunyuan Community License**, not an unrestricted Apache or MIT license. Territory excludes EU, UK and South Korea, including output distribution; >100-million MAU threshold triggers separate licensing; requirements for notices, acceptable uses, hosted distribution, generated material rights and third-party content remain binding. Acceptance of user-provided approval in chat is NOT Tencent approval or legal clearance.
+
+Sources:
+- https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE
+- https://huggingface.co/tencent/HunyuanVideo-1.5/blob/main/LICENSE
+- https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
+- https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
~~~~

## docs/feature5/PROJECT_STATE.md

~~~~diff
@@ -0,0 +1,113 @@
+# Feature #5 — Premium AI Motion State (2026-10-26)
+
+Status: **source-only first integration slice**. Provider and GPU adapter source, source-media validation, worker/injected interfaces and offline tests are on `feat/feature5-premium-ai-motion`. This is NOT a working hosted service, real Hunyuan inference, customer preview or paid GPU. No model weights downloaded. No Azure or Supabase changed.
+
+Coordinator-owned `main` and draft Part3 integration PR #125 must be preserved. The existing Part3 Wan provider, credits reservation proposal, encrypted/private import and FFmpeg composition are not duplicated by Feature5. Feature5 adds a disabled Hunyuan candidate with its own private worker contract, pending integration to Part3's ledger and ownership gates.
+
+Delivery and review boundary: Feature5 may add its provider/worker source and own tests; coordinator must approve all shared API/DB/frontend/queue changes and copy status into the main PROJECT_STATE, NEXT_TASK, DECISIONS and WORK_LOG at merge. Do not edit shared files from this feature branch.
+
+## 2026-10-26 continuation (source-only)
+- Exact pre-continuation Feature5 SHA `57f83743` succeeded in all four standard checks, twice (Actions #40289071677 and #40289078080). Later hardening commits require independent, exact-head CI verification.
+- Fixed genuine upstream CLI mismatch: Tencent `generate.py` uses *presence* of `--image_path` to select I2V, so T2V now omits it completely. Added 121-frame/24-fps 5-second target, disabled rewrite and upscaling, and blocked external model downloads. Command tests use mocks, not real GPU output.
+- Added decoded-image checks (including limits), timeout subprocess termination, CUDA BF16+minimum-VRAM preflight, fail-closed NaN/Infinity quota checks, exact private output path/lease receipt, post-upload UNKNOWN reconciliation, and private scratch cleanup.
+- No real inferences, cloud billing, private media uploads, deployed database tables, or operator authorization occurred.
+
+## 2026-10-26 continuation checkpoint — after PR #323 integration review
+- Verified exact branch `51201dbf93d7e94d2b2889310228f129ab6dcb3c` had two independent **4/4 PASS** GitHub Actions runs: #40293931880 / #40293926883. Main subsequently advanced independently; branch remains unmerged draft.
+- After that checkpoint strengthened cross-feature clip handoff to require an independently loaded `VisualReview` with same shop, job, clip asset, exact bytes SHA-256, all anatomy/garment/temporal/branding checklist passes, actual reviewer write role and AI-disclosure approval. Tests use synthetic review records; this does NOT establish real quality.
+- Billable logical request key now includes approved prompt SHA-256 and seed, not just day/source. Changing creative content cannot accidentally return the previous reserved motion clip. This is a proposed Feature5-only internal contract change, coordinator must version/accept it.
+- Added Tencent Community License territory/notice/AUP/MAU policy, which blocks runner launch by default if reviewed activation context is missing. Test policy is simulated; it does NOT constitute Tencent consent or attorney approval.
+- Real-gpu harness additionally requires actual operator reviewed deployment/publication regions and provider legal name. No GPU, weights or Azure credentials attached to this session; real Hunyuan outputs and fashion QA remain UNVERIFIED.
+
+## 2026-10-26 additional gated cost and usage implementation
+- Added `MotionSpendGuard` with verified Azure A100+CPU+RAM per-second rates, bounded maximum billable wall time and explicit ancillary allowance. Worker refuses all real or mocked enabled invocation without the injected guard, a bounded runner timeout and a sufficient existing reservation. Independent mocked tests cover underfunded credits, missing guard and timeout overrun.
+- Measured per-attempt *model subprocess* elapsed time and Azure-rate *estimate* are added to the private media receipt, subject to the existing coordinator's authoritative usage ledger reconciliation. They are **NOT Azure invoice measurements**, and do not include all container warm-up/cold-load time unless measured separately. Exceeded runtime or ambiguous recording requires `UNKNOWN`; never silently retry/refund.
+- No cloud account, model weights, or licensed real GPU currently accessible; no actual Hunyuan inference or visual garment QA was performed.
+
+## 2026-10-26 continued implementation — pinned upstream and human QA assets
+- Verified current Tencent `HunyuanVideo-1.5` official main at commit `60783e704160023913bee78f0b47036d393d4dfa`; `generate.py` Git blob ID `ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d`. Feature5 runner now verifies the exact script blob and rejects a tampered/symlinked entrypoint before GPU initialization. This pins **code bytes only**, not downloaded weight shards or transitive dependencies; licensed weight checksums and actual GPU testing are still missing.
+- Added an actual FFmpeg/libx264-generated synthetic 480×832, 24 FPS, 5s test feeding Feature5's production MP4 validator, plus negative 30 FPS/4s checks (in `tests/ai`). This is real CPU video encoding, explicitly **not** Hunyuan human motion.
+- Added `feature5_motion/visual_review_artifacts.py`: for a trusted private local clip, samples six PNG frames, creates a private contact sheet, records SHA-256 of source video and each frame, with pending-human-review manifest. Source-only; no web/cross-tenant upload, cloud call, booking, publication or automatic visual acceptance.
+
+## 2026-10-26 actual DEV ledger metadata audit (read-only)
+Verified existing RetailGrowthAI DEV public subscription/usage/outbox table columns and CHECKs against actual database. Premium-video table/credits do NOT exist yet; existing usage operations are campaign/render and outbox kinds planning/render. Part3's staged Wan-only schema cannot be used for Feature5 without coordinator review. Added `docs/feature5/PART3_DEV_SCHEMA_RECONCILIATION_20261026.md` with single-ledger migration/tenant-negative checklist. **Read-only SQL only, no cloud changes.**
+
+## 2026-10-26 — Sealed weight/code runtime and review evidence continuation
+- Added **source-only** `feature5_motion/artifact_lock.py` / `seal_artifacts.py`. A clean, materialized Tencent runtime + separately licensed weight directory can be enumerated and hashed with SHA256; the operator reviews a full-set, deterministic manifest and supplies its expected SHA256 **out of band**. Runner refuses missing, modified, symlinked, partial, extra, unpinned or noncanonical artifacts **before GPU**. This does not mean official weights are installed or licensed.
+- Added CPU fixture tests for mismatched source/weight bytes, added/removed shards, symlinks, forged manifest, path traversal, oversized files, and exclusive non-overwriting candidate output; tests use tiny **synthetic** bytes only.
+- Updated manual real-GPU acceptance harness to require reviewed lock path/digest plus a pre-existing private local evidence folder. On success it preserves the real MP4, optional input clothing still, per-frame hashes, six-frame contact sheet and immutable source/video references as `PENDING_HUMAN_REVIEW`. No automatic visual approval, publication or actual GPU execution occurred.
+- `feature5_motion/acceptance.py` is a CPU-only export helper; existing source/composition/ledger interfaces untouched. Commercial Tencent, image transfer region, cloud GPU access and actual media quality gates remain unresolved.
+
+## 2026-10-26 — Minimum-cost continuation: never repay an uncertain GPU attempt
+- Strengthened `MotionWorker` state fencing: errors before GPU runner launch may be `FAILED` but **any failure after runner invocation** (timeout, subprocess exception, invalid output, validation) is `UNKNOWN` with fenced `mark_unknown`. If unknown persistence fails, raise `ReconciliationRequired`; do not mark refundable FAILED. Added negative offline tests. This closes the previous possible duplicate GPU billing path, but the actual Part3 transaction integration remains coordinator-owned.
+- Added `feature5_motion/cost_routing.py`, a source-only cheapest **honest** delivery selector: already-approved images/stock → existing FFmpeg CPU path; bespoke walking model → defer when paid GPU is unapproved/unquoted or worst-case spend exceeds limit; eligible GPU quote is *only a preflight*, never an actual model launch. Premium spend defaults to **$0**. No automatic user-visible substitution of fake model movement.
+- Verified official Azure Container Apps GPU documentation: **Central India lists T4, not A100**; A100 is supported in East US among other regions, but transferring customer media abroad requires separately authorized data processing. Tencent model minimum VRAM is 14 GiB with offloading; Central India T4 availability does **not** demonstrate BF16 compatibility or production inference acceptance. No paid GPU provisioned. Official docs: https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview and https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5.
+
+## 2026-10-26 — Actual Hunyuan demo request, GPU/environment checkpoint
+- User rejected the previous ChatGPT-generated fashion still as proof of Feature5 (correctly). **No real Hunyuan output has been generated.** The session runtime has CPU-only PyTorch 2.10.0+cpu, `torch.cuda.is_available()=False`, no `nvidia-smi`, no licensed model weights, and cannot run local CUDA Hunyuan 1.5.
+- Checked Hugging Face public `multimodalart/Hunyuan-Video-1-5`: a **separate third-party free ZeroGPU** I2V 480p distilled demo is running. A browser attempt could inspect it without login/paywall, but could not submit a sample because the image widget requires a local file (no preloaded example and no URL upload). No video from it was obtained; **that Space is not our Azure/Part3 runner**.
+- Committed `feature5_motion/demo_fashion.py`: a deterministic, five-second, 480p/9:16/24fps **red embroidered kurti boutique T2V** brief, with no fake 20%-off claims. Improved manual `tests/gpu/test_feature5_local_acceptance.py` gating: explicit **single** `RETAIL_FEATURE5_ACCEPTANCE_MODE=text|image`, authoritative local Azure Retail snapshot, region/A100 full 600s-or-operator-defined job cap, positive max total USD preapproval; refuse all GPU paths otherwise. Previously `unittest discover` could run both T2V and I2V when two sets of sample inputs existed, risking duplicate paid calls; now at most one method is eligible per invocation.
+- Actual GPU, verified licensed weights, Tencent policy, regional consent, Part3 ledger and visual quality review remain unfulfilled. No paid GPU, Azure provisioning, DB mutation, or WineShopPOS change occurred.
+
+## 2026-10-26 — Owner authorized Azure GPU deployment, but authenticated Azure session unavailable
+- Verified existing GitHub OIDC `dev` workflows and their credential secret names, documented isolated Central India `rg-retailgrowth-dev` resource group with owner tags. No active Azure subscription-management tool or signed-in Azure Portal browser profile is connected to this session. Current local sandbox has no `az`, `docker`, NVIDIA GPU or model weights. **Azure GPU is still not deployed.**
+- Offered a secure Azure browser-profile sign-in for user action; login is needed to inspect subscription, actual A100 quota, regional resource permissions and cost before any billable provisioning.
+- Confirmed Microsoft's official Container Apps serverless GPU availability: East US A100 yes, Central India A100 no/T4 yes; Tencent Hunyuan 1.5 requires licensed weights, compatible CUDA GPU, commercial/territory safeguards. User-approved fictional-text-only fashion prompt avoids private customer photo transfer.
+- Added `feature5_motion/azure_gpu_preflight.py` and `azure_gpu_readonly_cli.py` with read-only exact DEV subscription, resource-group tag, A100 workload profile and remaining managed-environment quota checks. Negative CI fixtures cover wrong subscription/PROD, T4, no/ambiguous env, no quota, and write-capable CLI command rejection. This is **read-only source code**, not a cloud probe executed against Azure.
+- Created `docs/feature5/AZURE_GPU_CANARY_DEPLOYMENT_20261026.md` with the one-run manual GPU path, evidence, legal/gpu weights prerequisites and illustrative (not guaranteed) spend. No model/registry/VM/job created; no actual media generated.
+
+## 2026-10-26 — Signed-in Azure Portal inventory (GPU still NOT deployed)
+User saved Microsoft browser sign-in. Actual signed-in Azure Portal first audit confirmed **Azure subscription 1**, tagged isolated `rg-retailgrowth-dev` in Central India, eight familiar DEV resources including Function App, storage, SWA and Azure OpenAI. No East US A100 managed environment or ACR observed; a separate Sweden Central `vobiz-stream-env` belongs to the voice project and must not be reused. **No GPU quota was confirmed**. A second Azure Subscriptions blade showed 0/0 subscription filter in its directory context and could not open Usage + quotas. This is conflicting portal context, not proof of insufficient permissions/zero quota. Read-only findings and exact recovery at `docs/feature5/AZURE_SIGNEDIN_INVENTORY_20261026.md`. No cloud modifications or real Hunyuan MP4.
+
+## 2026-10-26 — Authenticated Azure quota investigation completed, actual quota still unknown
+- Reused user's saved signed-in Azure Portal browser profile, followed the exact existing `rg-retailgrowth-dev` from Resource Groups to **Azure subscription 1** in Default Directory. Confirmed eight existing dedicated DEV resources; no GPU created or modified.
+- Direct **Subscription → Usage + quotas** navigation failed to render and redirected to **Events** without an explicit authorization error; do **not** infer RBAC denial solely from redirect.
+- Separately visited **Azure Portal Quotas** service, filtered to **Azure Container Apps**, **Azure subscription 1**, **East US**, searched `NCA100` / `Managed Environment Consumption NCA100 GPUs` / `GPU`. Portal displayed **"No data to display for the selected filters. Try adjusting your filters."** No A100 limit/usage values retrieved. A provider registration warning appeared only when switching to **Microsoft Fabric**, and does not establish `Microsoft.App` is unregistered.
+- Conclusion: **A100 GPU quota UNKNOWN** (neither proven zero nor approved). No GPU deployment, model inference, request for quota increase, resource registration, spend, production or WineShopPOS changes.
+
+## 2026-10-26 — Azure managed-environment creation investigated; not yet verified
+- Official Microsoft docs establish that the **East US workload-profiles environment must exist BEFORE its per-environment Consumption NCA100 GPU quota can be viewed**. Previous empty Azure Quotas result never proved that quota was zero.
+- Owner-authorized empty environment `rgai-f5-gpu-canary-eastus` (Consumption only, no apps, no GPU, logs none) was attempted through portal standalone wizard, Cloud Shell ephemeral and finally custom ARM deployment. Standalone wizard did not show a create action. Cloud Shell opened but browser couldn't type into terminal.
+- Portal displayed a success notification for **`CustomDeployment-20261026093554`**, but the target resource did **NOT** appear in the same DEV RG's list; subsequent audit could not inspect deployment operations because the remote browser's metered usage budget was exhausted. **Environment creation unverified**; no GPU execution or real Hunyuan MP4.
+- Committed one-resource pinned ARM template `feature5_motion/infra/empty_gpu_env.json`, strict ARM what-if validator and negative tests. Revised preflight to return `ENVIRONMENT_REQUIRED` for an absent DEV East US v2 environment and inspect per-environment quota even before an A100 workload profile is added.
+- Exact coordinator-owned read-only ARM discrepancy diagnostic is at `docs/feature5/ARM_CUSTOM_DEPLOYMENT_DISCREPANCY_20261026.md`. **Do not blindly retry deployment** or bill paid GPU. No WineShopPOS/PROD/voice resources modified.
+
+## 2026-10-26 — GitHub OIDC execution route confirmed
+The existing main repository already has `.github/workflows/azure-dev-oidc-verify.yml` and `dev-azure-oidc-inspection.yml`, both using `azure/login@v3`, GitHub `dev` environment secrets, and `id-token: write`. GitHub OIDC can execute Azure CLI **inside a job**, not from a bare ChatGPT shell. The available GitHub connector does not expose workflow dispatch. To replace expensive TinyFish browser navigation, Feature5 added coordinator-reviewable `docs/feature5/proposed-workflows/azure-feature5-oidc-reconcile.yml`: exact DEV subscription/tag verification, read-only ARM deployment operations and environment/quota inspection, no mutations. This file is a **PROPOSAL** and is not executable as a GitHub workflow until the coordinator installs it in `.github/workflows/` on main; the Feature5 lead did not breach shared ownership or deploy GPU.
+
+## 2026-10-26 — LIVE Azure DEV empty Consumption environment deployed; A100 quota zero
+- Main coordinator OIDC workflow [run #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764) **SUCCEEDED**. Exact Azure scope `rg-retailgrowth-dev` was validated. ARM what-if predicted **one Create** for `Microsoft.App/managedEnvironments/rgai-f5-gpu-canary-eastus` plus eight **Ignore** entries for unchanged DEV resources; strict reviewer matched all nine. It actually created and read back the new **East US** managed environment with `provisioningState: Succeeded`, only the default `Consumption` workload profile and no GPU/dedicated nodes/apps/jobs. No new Log Analytics workspace, ACR or VM was created by this approved ARM template.
+- Crucially `az containerapp env list-usages` returned the real value: **`ManagedEnvironmentConsumptionNCA100Gpus limit=0 currentValue=0`**. This is now a verified **ZERO** per-environment A100 allocation, not the historical pre-environment “quota unknown”. Hunyuan licensed weights are still not installed, **no real Tencent model video generated, no GPU job run**. An empty Consumption profile should incur no GPU compute charges, but independent Azure Cost Management would be needed for a statement about any ancillary billing.
+- Current Microsoft guidance: request **1 Managed Environment Consumption NCA100 GPU** from **Azure Portal → Container Apps environment `rgai-f5-gpu-canary-eastus` → Settings → Quota → Managed Environment Consumption NCA100 GPUs → New limit 1 → Submit**; approval may be automatic or routed to review. That step has **NOT** been submitted or approved by any tool/chat workflow. Existing GitHub OIDC Actions handles ARM resources but does not provide a documented managed-environment quota-change API in our available tooling.
+
+## 2026-10-26 — Direct GitHub OIDC GPU VM inventory after A100 quota 0
+- Coordinator [PR #388](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/388) merged after 4/4 CI. Live [read-only Azure VM GPU inventory run #40355181214](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40355181214) successfully used existing DEV OIDC credentials to query Central India and East US. Both regions currently have **Total Regional vCPUs limit=10, used=0**. Azure `Standard_NV6ads_A10_v5`, `NV12ads_A10_v5`, `NV18ads_A10_v5`, `NV36ads_A10_v5` SKUs have no catalog restrictions in those regions, but the first full **24GB A10** VM requires **36 vCPUs**; smaller 6/12/18-vCPU fractional A10 offers 4/8/12GB GPU RAM, below Tencent's verified 14GB minimum. NCads A100 VM SKUs are `NotAvailableForSubscription` in both regions. Thus **no compatible alternative Azure VM is presently verified deployable** with existing regional quota; catalog presence alone does not establish quota or stock. A100 Container Apps env remains empty with `ManagedEnvironmentConsumptionNCA100Gpus limit=0, used=0`. No GPU, licensed weight, Hunyuan MP4 or new paid resource was started.
+
+## 2026-10-26 — Quota submission mechanism and affordable external GPU research
+- Reconfirmed actual existing successful OIDC empty East US environment #40347841764 with managed-environment serverless A100 quota limit=0/used=0. Do not re-create. Already completed Azure VM inventory #40355181214 rules out immediately suitable VM quota. No new live Azure management actions were performed in this milestone.
+- Independently reviewed Microsoft 2026 quota guides: for **Managed Environment Consumption NCA100 GPUs** an operator requests new limit=1 in the **existing environment → Settings → Quota**; docs show CLI **read** only, not a supported scripted submission of this specific environment quota. No quota request was submitted; no GPU profile or inference.
+- Reviewed official Tencent 1.5 14 GB offload minimum and default 480p T2V 50 steps. Compared Runpod 48GB A40, 24GB 4090, 80GB A100 serverless and changing Vast prices. Created pure Python, offline quote screening `feature5_motion/external_gpu_budget.py` and CPU-negative tests. Neither external provider is connected/provisioned. See `QUOTA_AND_EXTERNAL_GPU_OPTIONS_20261026.md`.
+- Genuine red-kurti MP4, model weights/image, visual review, actual GPU bill, provider hard termination assurance and approved new quota remain **NOT DONE**. Feature #5 draft PR remains unmerged; coordinator owns shared workflows/main.
+
+## 2026-10-26 — Cheap A40 pilot option now supported in quote screening
+- Verified official NVIDIA A40 datasheet: Ampere, **48 GB ECC GPU VRAM and BF16 Tensor Cores**; official Runpod 2026 Pod pricing publishes A40 48GB, 50GB host RAM, 9 vCPU from $0.59/hour. These are product capabilities/list pricing, not an account reservation or inference benchmark.
+- Fixed Feature5's offline provider quote screen to accept the exact `A40_48GB` candidate, previously omitted despite documentation recommending it. Added positive and cap-rejection tests using $0.59 GPU + $0.02 hourly disk and $0.05 ancillary reserve: 1h provider-side teardown bound quotes **$0.66**, not 10 minutes of subprocess usage. Provider stock/billing/liveness/termination unverified; no GPU run or quota request submitted.
+
+## 2026-10-26 — Open-source engine research, no provider switch
+- Investigated directly runnable upstream official repositories: Lightricks/LTX-Video 13B v0.9.8 (model-driven long-shot extension up to 60 seconds), Wan-Video/Wan2.2 TI2V-5B (permissive Apache-2.0 weights, 24GB VRAM T2V/I2V), Comfy-Org/ComfyUI GPL-3.0 workflow engine, and Azure-Samples/comfyui-on-azure (H100 VM Terraform **reference only**).
+- Recorded independent distinction between Apache LTX code and **non-Apache LTX 0.9.8 checkpoints** (USD 10m annual revenue commercial boundary, SaaS/disclosure conditions), and between up-to-60s extension and single-pass 60s inference. See `docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md`.
+- Existing Hunyuan SHA-locked Feature5 PR #323 remains source-only and unchanged; no actual GPU/image/weights/video, quota request approval, outside resource provisioning or commercial license clearance is claimed.
+
+## 2026-10-26 — Full upstream GPU engine cost reality
+- User explicitly prefers **running whole official upstream video projects on Azure**, not a limited handmade generator. Evaluated unmodified `Azure-Samples/comfyui-on-azure` H100/ComfyUI/Wan/LTX VM build versus packing full pinned upstream ComfyUI/LTX workflow as a private Azure Container Apps A100 image.
+- Verified East US H100 VM `Standard_NC40ads_H100_v5` public PAYG $6.98/hour (40 vCPU) and A100 ACA Retail API $0.000529/s GPU + $0.000024/vCPU-s + $0.000003/GiB-s RAM. Illustrative full worker with 4vCPU/16GiB $2.4228/active hour. Neither is a measured cost for a generated 60-second clip.
+- Both Azure routes **remain blocked by previously observed quotas** (VM regional 10 vCPU versus H100 40; managed-environment A100 quota zero). No actual upstream repo deployment, Azure GPU spend, model weight/materialization or 60s output. See open-source engine review for detailed comparison.
+
+## 2026-10-28 — Verified India GPU rental option (purchase not performed)
+- Owner requested a definitive external GPU vendor choice rather than waiting for Azure A100 quota. Official JarvisLabs India prices (2026-10-28 research): A100 80 GB **₹140.94/GPU-hour on-demand**, 112 GB system RAM/16 vCPU, per-minute metering, Indian cards/INR with GST invoice; separately billed storage **₹0.0130/GB/hour**, including while paused (100 GB ≈₹1.30/h). Vendor: https://jarvislabs.ai/in.
+- Recommend **one manually controlled JarvisLabs A100 80GB on-demand instance** as a short genuine benchmark of complete, unmodified Wan2.2 TI2V-5B upstream source with full checkpoints, *conditional on operator purchasing prepaid credit and approving the maximum spend*. Full 80 GB GPU may allow skipping memory offload; not a guaranteed speed/quality increase. No provider account accessed, funds paid, instance/weights downloaded or real video generated; original Part3 Wan ownership persists.
+- Cheaper advertised RTX 4090 at ₹32/h may be viable but seller, full fees, verified specs, performance, India payments and availability were not established; Runpod Community + Vast marketplaces generally bill USD and have variable stock/host terms. Avoid selecting on hourly rate alone.
+
+## 2026-10-28 — Owner's Azure Portal quota screenshot
+- Owner-supplied Azure Portal screenshot for existing `rgai-f5-gpu-canary-eastus` now shows **Managed Environment Consumption NCA100 GPUs = 0 used / 2 limit** (T4 = 0/0). This is portal evidence of approved managed-environment GPU capacity, resolving prior quota=0 blocker; it is not an ARM/CLI readback, deployed GPU, reserved compute, GPU billing or model inference. Logged to GitHub issue #400.
+- No GPU replicas in use on the portal quota screenshot; quota alone does not incur GPU-compute charges (Azure Container Apps Consumption billing). Other preexisting storage/logging/network resources may still bill. No external JarvisLabs purchase occurred.
~~~~

## docs/feature5/QUOTA_AND_EXTERNAL_GPU_OPTIONS_20261026.md

~~~~diff
@@ -0,0 +1,86 @@
+# Feature #5 — GPU quota escalation and economical one-shot alternatives
+
+Date: 2026-10-26. Scope: **DEV synthetic red-kurti T2V only**. This document is an evidence-based decision/operation aid, not a cloud execution receipt or a license grant.
+
+## Independently verified existing state
+
+- Azure DEV resource group: `rg-retailgrowth-dev`; East US existing empty workload-profiles environment: `rgai-f5-gpu-canary-eastus`. It has default Consumption only, not a GPU job or application. Actual GitHub OIDC creation/readback: [run #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764).
+- Exact environment usage entry `ManagedEnvironmentConsumptionNCA100Gpus`: **limit 0 / used 0 / available 0**. Do not recreate the environment.
+- Follow-on existing coordinator OIDC [run #40355181214](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40355181214): Central India and East US regional VM-vCPU quota 10 each; no usable A100 VM capacity in tested account, full A10 24 GiB profile requires more regional vCPU than currently allocated. A public SKU catalog is not account quota.
+- No evidence of a successfully submitted quota request, approved quota=1, installed pinned licensed Tencent weights, paid CUDA call or generated real MP4.
+
+## Correct Microsoft quota process (validated against updated documentation)
+
+Official Microsoft [Container Apps quota guide](https://learn.microsoft.com/en-us/azure/container-apps/quotas) and [quota request guide](https://learn.microsoft.com/en-us/azure/container-apps/quota-requests) distinguish **managed-environment serverless GPU quota** from **regional subscription dedicated NCA100 GPU quota**.
+
+1. On the authorized RetailGrowthAI DEV subscription open Azure Portal → Container Apps **environment** `rgai-f5-gpu-canary-eastus`, under `rg-retailgrowth-dev`.
+2. Open **Settings → Quota**, choose `Managed Environment Consumption NCA100 GPUs`, request **new limit 1**. The existing row was observed via OIDC CLI, so the environment and quota key are not guesses.
+3. Record Azure's actual submission/approval state and new `az containerapp env list-usages --resource-group rg-retailgrowth-dev --name rgai-f5-gpu-canary-eastus` response. A submitted request is NOT an approved quota; approval also is NOT real deployment capacity.
+4. If Azure routes the request to quota review/support, follow Microsoft's resulting flow. Do not create a technical incident for this ordinary quota limitation; do not attempt a fallback by requesting unrelated dedicated regional GPU quota.
+5. Once limit >= 1 and used < limit are verified, **do not deploy immediately**: licensed weight lock, actual CUDA image, Tencent rights, synthetic-only region, total bill quote, one-job no-retry with external termination assurance, and private evidence remain mandatory.
+
+**CLI/REST finding:** Official docs show `az containerapp env list-usages` to **read** usage, but provide the managed-environment **Quota page** to submit that specific increase. No supported documented Azure CLI/REST quota-increase submission API was confirmed for this scope. Do not post guessed ARM mutations through OIDC. The existing GitHub connector also has no workflow-dispatch action, and Feature5 workers do not own `.github/workflows/**`.
+
+Serverless A100 region support in [Microsoft GPU overview](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview) includes East US and excludes Central India. Catalog availability does not imply subscription GPU allotment or temporary capacity.
+
+## Price-screened fallback for the *same* official Tencent HunyuanVideo 1.5
+
+Tencent's [HunyuanVideo 1.5 README](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) documents NVIDIA CUDA, **minimum 14 GB VRAM only with offloading**, and default **50 inference steps for 480p T2V**; it reports 8–12-step acceleration specifically for its 480p **I2V step-distilled** variant. Do not promise eight-step red-kurti **text-to-video** or substitute a generic video model.
+
+Price discovery 2026-10-26, USD headline/on-demand examples only:
+
+| Candidate | Published reference | Raw 30-minute GPU cost, excluding all other charges | Feasibility and operational caveat |
+|---|---|---:|---|
+| Existing Azure East US serverless A100 | Existing official Retail Prices snapshot: GPU $0.000529/s, plus CPU/RAM | $0.9522 GPU alone; ~$1.2114 with illustrative 4 vCPU/16 GiB for 1800s | Quota is **0**; must secure environment quota 1. Actual allocation might differ from 4/16 assumption |
+| Runpod A40 48 GB Pod | [Official Runpod price list](https://www.runpod.io/pricing): $0.59/hr advertised | $0.295 | BF16 capable and larger VRAM than 24GB cards, but exact instance RAM/location/availability, paid idle, storage and image pulls must be checked; no model run benchmark |
+| Runpod RTX 4090 24 GB Pod | [Official Runpod price list](https://www.runpod.io/pricing): $0.89/hr advertised | $0.445 | BF16 capable, only 24 GB VRAM; 50-step T2V with offload may exceed 30-minute timeout |
+| Runpod A100 80 GB Serverless | [Official Runpod price list](https://www.runpod.io/pricing): $2.72/hr listed | $1.36 | Cold starts/downloads can dominate; actual worker billing modes differ from Pods |
+| Vast.ai marketplace 4090 / A100 | [Vast's changing live prices](https://vast.ai/pricing) | **No reliable fixed amount** | Host-specific price, trust, storage, geography, interruption and availability must be individually inspected, not assumed from advertised minimum |
+
+All headline prices **exclude** storage, transfer, failed attempts, persistent volumes, setup and taxes. They are neither a commitment nor measured Hunyuan runtime. A 30-minute quote does not establish completion within 30 minutes. A job timeout in Python does **not** stop an external GPU pod; require a provider-side termination/stop control and spending/prepaid ceiling **before** creating one. Limit 1 GPU, no retries, no auto scale, isolated throwaway synthetic inputs and delete disks after private evidence is secured.
+
+**Recommendation:** First seek the existing Azure managed-environment quota=1 (no GPU provision needed for the request). For an urgent independent genuine sample, evaluate an on-demand **Runpod A40 48 GB**, *after* account-specific price, country, actual 40+ GiB system RAM, CUDA BF16, model license and termination controls are verified. Avoid automatically using a lower-priced, less trusted community host for customer data. Feature5's current official `HunyuanLocalRunner` is local-GPU portable but the manual acceptance harness is Azure-price-gated; an external quote review does not silently activate paid inference.
+
+## New safe CPU-only provider comparison code
+
+`feature5_motion/external_gpu_budget.py` accepts an *operator-provided* small quote with exact reviewed SHA256. It rejects unknown provider/GPU, preemptible mode, fewer than 40 GiB host RAM or 24 GiB GPU family, multiple GPUs, non-USD prices, stale/future/over-one-day quote validity, unexpected keys, duplicate JSON keys, symlinked/tampered file and over-ceiling worst-case rental quote. It calculates quoted maximum exposure including storage/hour, billing minimum and ancillary reserve, and reports **QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION**. It performs **zero cloud/network/CUDA operations**.
+
+A quote is not a payment limit or price verification; account billing may persist beyond the Python process. Code intentionally does not automate Runpod/Vast provisioning or falsely claim provider termination controls. If using an external provider, coordinator must approve a separate teardown-verified, paid-cap-aware operator execution procedure before allowing a genuine Hunyuan sample.
+
+Example (illustrative quote, **not** operator approval):
+
+```json
+{
+  "provider": "runpod", "sku": "RTX_4090_24GB",
+  "gpu_count": 1, "system_ram_gib": 48,
+  "region": "us-east-1", "country": "US",
+  "billing_mode": "on_demand", "currency": "USD",
+  "compute_usd_per_hour": "0.89", "storage_usd_per_hour": "0.02",
+  "minimum_billable_seconds": 60,
+  "quoted_at": "2026-10-26T12:00:00Z",
+  "expires_at": "2026-10-26T23:00:00Z"
+}
+```
+
+Quote SHA256 must be kept *outside* the quote file and confirmed against the chosen vendor account. Never pass real retailer media or credentials in GitHub source, job logs, CI attachments or community Cloud. Tencent's conditional Community License, output territories, model weight provenance and hosted notice requirements apply on any provider.
+
+## Acceptance needed before real sample can be claimed
+
+For **one** red-and-gold kurti T2V: licensed pinned Tencent runtime+model shards, independently reviewed `ArtifactLock`, provider-specific CUDA BF16 result, true 5s/480p portrait/24fps H264 MP4, `ffprobe` and SHA256, six-frame contact sheet, private review packet, actual wall-clock and account invoice, confirmed stop/deletion, and human garment/face/hands review. There is **no MP4 from this work**, and a synthetic FFmpeg clip does not satisfy this gate.
+
+## Provider-side termination guard (required for actual rental)
+
+Runpod's [official Pod CLI reference](https://docs.runpod.io/runpodctl/reference/runpodctl-remove-pods) documents `--terminate-after 1h` on Pod creation and states it **permanently deletes the Pod**, unlike `--stop-after`. For a one-shot demo, provisioned Pod settings must confirm one GPU, Secure Cloud where available, explicit permitted country, image digest, no public inference port, **automatic termination within one hour**, and later API readback that the Pod is actually terminated. Persistent separately purchased network volumes may remain billable even after a Pod is deleted; avoid them for the pilot or independently delete and reconcile. This is **research, not executed**.
+
+The new quote checker requires `provider_termination_after_seconds` at least 60 seconds beyond the process timeout and at most 3600. Its estimate is based on the **whole provider auto-termination window**, including minimum billing, not only CUDA subprocess time. Example: the illustrative Runpod RTX 4090 quote at $0.89/hour + $0.02/hour disk and $0.05 ancillary reserve with a 1-hour auto-termination bound is **$0.9600**, versus just $0.2017 if one naively counted a 10-minute Python timeout. It is still not a guaranteed upper limit on a malfunctioning provider, currency conversion, taxes or retained network storage. A real rental needs an approved prepaid/account cap and verified stop/delete readback.
+
+`runpodctl` is **not installed or connected** here, and no Runpod account, GPU region/stock, credit balance or provider API credential was inspected. A safe illustrative command is deliberately not executable without operator-supplied vetted values:
+
+```sh
+# OPERATOR REVIEW ONLY — DO NOT EXECUTE BEFORE LICENSE, COST, REGION & CREDIT GATES
+runpodctl pod create --image '<PINNED_APPROVED_IMAGE>' \
+  --gpu-id '<EXACT_ACCOUNT_AVAILABLE_48GB_A40>' --gpu-count 1 \
+  --cloud-type SECURE --country-code US --terminate-after 1h
+```
+
+A provider-side teardown option does not replace on-instance CUDA 1800s maximum timeout or independent verification of actual post-job termination. Operator must copy the genuine local MP4 and private evidence **before** deletion, avoiding public URLs and GitHub CI artifacts.
~~~~

## docs/feature5/WORK_LOG.md

~~~~diff
@@ -0,0 +1,100 @@
+# Feature #5 development log
+
+## 2026-10-26 — Additive source implementation
+- Read mandatory root docs; verified current main and Part3 integration branch/source/PR #125; noted Part3's Wan, private importer, staged SQL, queue code and mock CI.
+- Verified Tencent HunyuanVideo-1.5 public official code/requirements and community license; Diffusers has documented pipeline; Azure lists Central India serverless T4 but not A100.
+- Created isolated Feature5 branch from exact verified main SHA `140a9f86170132d7c482a183b843788aa09b3b5a`.
+- Added contract, gated local CLI runner and separate injected worker; added offline tests and cost/rollout proposal.
+- No real GPU test, paid API call, subscription adjustment, Azure resource, migration, production edit or WineShopPOS edit.
+- PR #323 is OPEN/DRAFT for coordinator review. Exact post-fix head `57f83743b1c1fad158c5a3f22fc731c83b350862` passed the four mandatory jobs in [Actions run #40289071677](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40289071677): Python/uv (450 tests, 41 subtests at previous diagnostic pass; exact latest job success), FFmpeg codec/render, frontend build/Playwright, and disposable Supabase RLS/security. This proves offline regression only, **not GPU inference, hosted paid activation, or video visual QA**.
+\n- Strengthened image-byte signature checks (PNG/JPEG/WEBP) and DB claim token canonicalization; ambiguous post-upload DB completion remains UNKNOWN for reconciliation, not a duplicate bill or automatic refund.\n
+## 2026-10-26 continued work
+- Inspected Actions #40289071677 and #40289078080: exact SHA `57f83743`, each **4/4 PASS** (Python, frontend, FFmpeg and Supabase isolation). Subsequent intermediate pushes were cancelled by GitHub CI concurrency; inspect the final PR-head run.
+- Inspected real Tencent `generate.py` CLI docs; corrected `--image_path none` bug that would make T2V wrongly select I2V. Added isolated CLI tests with simulated subprocess, no actual generation.
+- Strengthened source image size/decode, subprocess output/timeout, offline-only model flags, BF16 CUDA/VRAM preflight, prevention of NaN/Infinity budget bypass, private scratch cleanup, exact private blob lease receipt, and UNKNOWN on ambiguous uploads.
+- Fixed a mock-fixture timing defect detected by CI (fixture created output before start). Did not disable tests or modify workflow.
+- Code and docs remain isolated to Feature5-owned folders/tests. Production and paid GPUs are untouched.
+
+- Added separate MANUAL-ONLY real local GPU acceptance harness gated on operator cost/license approval and existing on-disk official weights. No tests executed against GPU or billable APIs.
+
+## 2026-10-26 follow-up — owner requested continuation
+- Rechecked branch/main/PR #323 and verified prior exact-head 4/4 CI passes at `51201dbf9` (#40293931880, #40293926883); no changes to Part3/Feature4/PROD.
+- Read updated mandatory canonical project docs and coordinator ownership rules.
+- Verified Tencent official model CLI and November 2025 Community License terms; source confirms `--image_path none` is accepted/normalized to missing (so omitting optional flag is a stylistic contract hardening, not proof that earlier command would have failed). Kept 121-frame documented model profile.
+- Implemented mandatory VisualReview-bound Feature4 clip handoff and negative tests (review absent, wrong asset/job hash/role, rejected garment).
+- Versioned deterministic idempotency key to include source image, approved prompt digest and seed.
+- Implemented reviewed territory/hosted-commercial license policy and negative tests for EU/UK/Korea, missing notices and >100m release-date MAU threshold. Real GPU test harness requires additional operator fields.
+- No actual real GPU inference, azure deployment, licensed sample outputs or human garment acceptance was possible. Next coordinator integration and real GPU blockers documented without pretending all assigned tasks completed.
+
+## 2026-10-26 follow-up — GPU budget ceiling and measured usage
+- Added `MotionSpendGuard` in `feature5_motion/azure_pricing.py`, integrated into `MotionWorker` before durable claim, and required existing reservation >= total worst-case billable approved CPU/RAM/A100 time and ancillary allowance. Added offline negative tests for missing quote/underfunded reservation/runner timeout.
+- Added monotonic subprocess elapsed-time and Azure-rate estimate to private output metadata for later existing ledger reconciliation. Enforced `UNKNOWN` on over-budget runtime; fixed an edge case where failure persisting UNKNOWN could be incorrectly downgraded to FAILED. No GPU was actually run.
+
+## 2026-10-26 work continuation: runtime source integrity and offline QA
+- Re-read latest canonical AGENTS and coordinator project docs, current main, PR #323, PR #125 Part3 and PR #322 Feature4; preserved their branches.
+- Fetched official Tencent upstream `generate.py` at commit `60783e704160023913bee78f0b47036d393d4dfa`; added exact Git-blob integrity gate and fake/tampered/symlinked script tests. Did not download model weights or start CUDA.
+- Added true FFmpeg/libx264 5s H264/24FPS media validation test with real 30FPS and 4s rejection fixtures, rather than relying only on `ffprobe` mocks. Added private six-frame review contact sheet and clip SHA256 manifest; real garment visual assessment remains unperformed.
+- No Part3/Feature4/shared-main edits, Azure/Supabase/PROD changes, GPU spend or WineShopPOS modification.
+
+## 2026-10-26 live DEV metadata verification
+- Queried read-only PostgreSQL information_schema/pg_constraint of dedicated RetailGrowthAI DEV (existing shop/user data not read or modified): `shop_subscriptions` has no premium budget, `shop_usage_reservations` accepts campaign/render only with no units, `job_outbox` accepts planning/render only, `premium_video_jobs` does not exist. Recorded exact coordinator-owned single-ledger reconciliation proposal and negative test plan in `PART3_DEV_SCHEMA_RECONCILIATION_20261026.md`; no schema changes, no live calls to a GPU.
+
+## 2026-10-26 — Remaining model authenticity and quality evidence work
+- Verified GitHub feature branch/PR #323 and separate Part3 #125/Feature4 #322 still open; read latest AGENTS and canonical project docs; stayed within Feature5-owned paths. Previous PR head `45fc91ed1` had two complete 4/4 CI runs (#40307095552, #40307083961).
+- Implemented deterministic full code+weight SHA256 manifest preflight, operator-only candidate generator, trusted digest passed separately to `HunyuanLocalRunner`, and negative CPU-only tests against synthetic code/shard fixtures. No real weights downloaded or licensed; official source commit still independently pinned by existing code.
+- Reworked manual GPU harness to preserve verified actual MP4/reference imagery + contact-sheet frame hashes in a private operator-owned evidence location instead of destroying temporary test media. Added CPU-real FFmpeg acceptance-export fixture tests; no actual Hunyuan generation or real garment visual acceptance was performed.
+- Kept feature flags OFF, no real model/GPU/queue/cloud/Supabase writes, no new ledger, no PROD or WineShopPOS changes. Final exact-head CI status must be inspected after docs commit.
+
+## 2026-10-26 — Owner requested minimum cost; offline continuation
+- Re-read live coordinator AGENTS/PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG/ARCHITECTURE/INTERFACES/PARALLEL_WORK/CI docs. Verified Feature5 PR #323 remains open/draft, Part3 PR #125 and Feature4 PR #322 separate; starting Feature5 head `77f0b8223f` had successful dual four-job CI.
+- Fixed a genuine potential double-charge defect in source-only `MotionWorker`: exceptions or media validation failures after the model runner starts no longer create refundable `FAILED` jobs; they fence as `UNKNOWN` or require explicit reconciliation. Pre-GPU staging still safely fails; added four negative tests.
+- Added zero-premium default `cost_routing` policy and seven offline tests: rights-approved stock/FFmpeg preference, no fake walking model, hard budget rejection, no implicit paid activation, corrupted cost input blocking, independently priced eligibility only. This policy is not yet hosted or connected to Feature4.
+- Independently checked official Microsoft serverless GPU regions: Central India A100 **No**, T4 **Yes**; Tencent minimum 14 GiB VRAM and BF16 CUDA profile does not imply T4 suitability. No cross-border data movement or GPUs provisioned.
+- No WineShopPOS/PROD, schema, other-feature branches, Azure/Supabase writes or charged inference. Exact final PR-head Actions logs must be inspected before reporting success.
+
+## 2026-10-26 — User requested real Hunyuan sample
+- Inspected Github main, open Feature5 #323, Part3 #125 and Feature4 #322; reread root instructions and Feature5 docs. Rechecked current CPU tool runtime (`torch 2.10.0+cpu`, CUDA false, no NVIDIA driver/weights). A ChatGPT-generated still was previously presented by mistake; explicitly ruled out counting it as Hunyuan.
+- Inspected official Tencent Hunyuan 1.5 weights/model docs and public HF `multimodalart/Hunyuan-Video-1-5` ZeroGPU I2V Space. Attempted one public browser demo; no sign-in/payment gate seen, but a local image is required and browser had no uploadable file. **No actual Hunyuan inference completed; no MP4 exists**.
+- Added deterministic five-second festival fashion T2V demo spec with user-chosen theme and CPU tests. Hardened manual CUDA test to disallow accidental second T2V/I2V inference in same invocation and require a reviewed regional Azure retail rate snapshot and total USD cap before paid work. GPU provisioning, model weights, hosted DB and WineShopPOS unchanged.
+
+## 2026-10-26 — Azure GPU request follow-up
+- Acknowledged that no prior Azure GPU deployment was made. Inspected current project branch, separate draft PRs, root AGENTS and mandatory coordinator docs. Verified GitHub has DEV OIDC workflows and known RG-only credentials but this chat has no Azure control-plane action and local sandbox has no `az`/Docker/CUDA/weights.
+- Started secure browser-profile Azure Portal authentication setup for user sign-in (user credential action still outstanding); did not see or request passwords, did not create any GPU resource.
+- Reverified latest Microsoft region/quota and Tencent 1.5 CUDA/license docs. Implemented fail-closed read-only A100/DEV quota inventory helper + 8 negative tests; verified no deployment verbs are possible from inventory wrapper. Prepared one-shot GPU runbook/cost examples; no registry/model download/VM/GPU/storage bill incurred.
+- Left shared root docs, coordinator-owned workflows, PROD, Supabase schema and WineShopPOS untouched. The main blocker is a signed-in Azure management session plus supported model weights/quota, not missing frontend imagery.
+
+## 2026-10-26 — Azure connected and inspected in real portal
+- Confirmed user's Microsoft portal profile signed in; first *actual* Azure Portal inventory verified Azure subscription 1 and tagged `rg-retailgrowth-dev` Central India, eight existing DEV resources, no A100 environment, no ACR, plus separate Sweden Central voice environment untouched. Second browser audit reached Subscriptions filter displaying 0/0 in its directory and could not inspect A100 quota. Quota/permissions remain **unconfirmed**, not proven denied. Logged exact evidence/recovery in `AZURE_SIGNEDIN_INVENTORY_20261026.md`.
+- No Azure resources created, no quota request, no cloud GPU charges, no model weights, no real Hunyuan MP4; protected PROD, WineShopPOS, Supabase data and voice workloads. Need selected directory/usage quota visibility before safe one-shot GPU deployment.
+
+## 2026-10-26 — User asked to verify A100 quota directly
+- Executed two separate **authenticated read-only Azure Portal** checks from user's saved Microsoft profile. First followed existing dedicated `rg-retailgrowth-dev` to Azure subscription 1; direct subscription Usage + quotas redirected to Events without showing table or explicit access denial. Second used standalone Quotas service → Azure Container Apps → East US and searched NCA100/GPU names; UI returned **no data for filters**. A registration warning under Microsoft Fabric did not prove anything about Container Apps registration.
+- **Result:** actual East US Container Apps A100 limit, usage and availability remain unverified; no invented numbers or assumption that quota is zero. Need subscription-scoped Azure Resource Manager/CLI read-only provider+quota inspection, possibly requiring coordinator-approved GitHub DEV OIDC workflow. No Azure writes or GPU spending, no WineShopPOS/PROD modifications.
+
+## 2026-10-26 — Environment-first GPU quota blocker and real ARM attempt
+- Verified latest Microsoft serverless GPU docs: East US A100 profile available in service catalog; must create workload-profiles env before environment Consumption NCA100 quota can be read/requested. Empty subscription quota rows were not meaningful.
+- Used saved signed-in Azure Portal: standalone environment wizard unavailable; ephemeral no-storage Cloud Shell Bash did open but GUI couldn't focus xterm input, **no shell commands executed**. Next used direct Azure custom ARM template wizard, submitted exactly one proposed empty Consumption environment. Portal reported `CustomDeployment-20261026093554` succeeded, but DEV resource-list search did NOT find the environment. Follow-up audit reached RG resources but browser automation metered budget exhausted before ARM operations were opened. **Created-resource state remains UNKNOWN; no GPU or model generation started.**
+- Implemented pinned Azure one-resource log-free/no-GPU ARM template, strict template + what-if validation, negative tests, and corrected source preflight to wait for owned East US empty environment before reading NCA100 quota. Isolated feature-owned paths only; coordinator to inspect ARM deployments via existing DEV OIDC, not retry until reconciled. Complete runbook at `ARM_CUSTOM_DEPLOYMENT_DISCREPANCY_20261026.md`.
+
+## 2026-10-26 — User requested GitHub OIDC connection for direct Azure commands
+- Verified `main` already contains read-only OIDC login/inventory workflows using `azure/login@v3`, GitHub environment `dev`, and short-lived id-token. Confirmed connected GitHub Actions API exposure here is read-only for workflow dispatch (no dispatch tool), so bare chat cannot execute arbitrary Azure commands even though GitHub runners can authenticate and run `az`.
+- Added feature-owned **proposed** manually triggered, read-only GitHub OIDC ARM reconciliation/quota workflow `docs/feature5/proposed-workflows/azure-feature5-oidc-reconcile.yml` for coordinator review/install. Does NOT edit `.github/workflows/**`, merge main, deploy GPU or incur Azure costs. Replaces repeated TinyFish navigation for diagnosis after coordinator activation.
+
+## 2026-10-26 — Real Azure OIDC environment rollout SUCCESS, GPU quota ZERO
+- Coordinator PRs #367, #368, #369, #370 and #377 introduced the read-only OIDC reconciliation and one-time restricted ARM deployment with corrected logging omission and strict Azure what-if Ignore semantics. Actual main [run #40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764) **SUCCEEDED**. Logs explicitly show `PASS: Azure what-if permits 1 Create and 8 known unchanged DEV resources`, then successful ARM creation/read-back for `rgai-f5-gpu-canary-eastus`, East US, default Consumption only, with no GPU workload profile/app/job, and quota `ManagedEnvironmentConsumptionNCA100Gpus limit=0 used=0`.
+- Reviewed current Microsoft quota docs: now that the environment exists, request one managed-environment NCA100 GPU from its own Quota pane; Azure may process or route for review. Quota increase not submitted. No model weights installed, no Hunyuan inference, no MP4, no Azure GPU charges started. Preserve isolated RetailGrowthAI DEV and do not touch PROD/WineShopPOS/voice projects.
+
+## 2026-10-26 — Checked alternate Azure GPU VM quota without TinyFish
+- Coordinator PR #388 added and merged a main-only OIDC read-only regional VM quota/SKU inventory workflow, tested 4/4, and actual run #40355181214 passed with no Azure mutations. Central India and East US regional VM quota each 10 used 0; NVIDIA A10 SKUs listed without location restriction, A100 VM SKUs restricted. Checked Microsoft NVadsA10v5 official RAM/vCPU table and Tencent 1.5 >=14GB GPU memory requirement; viable full A10 24GB uses 36vCPU, beyond existing cap. Thus no suitable Azure VM quota path without additional approval. Existing East US Consumption env A100 quota 0 unchanged. No CUDA inference/real MP4 or GPU bill; next external dependency is a serverless A100 quota increase to 1, which has NOT been submitted.
+
+- 2026-10-26: Read existing Feature5 PR #323 and coordinator merged Azure work through #388; confirmed full OIDC East US empty environment and NCA100 limit=0/used=0 from #40347841764, plus VM inventory limitations from #40355181214. Verified Microsoft 2026 managed-environment quota request path and lack of documented CLI/REST submission route, Tencent 1.5 14GB/offload + 50-step T2V, and official current Runpod/Vast advertised rental rates. Created `docs/feature5/QUOTA_AND_EXTERNAL_GPU_OPTIONS_20261026.md`, `feature5_motion/external_gpu_budget.py`, `tests/ai/test_feature5_external_gpu_budget.py` with fail-closed quote/price/lease screening; development-only, no cloud or GPU calls. CI evidence is to be checked independently after push. **No quota request, genuine Tencent MP4, model weights, external vendor reservation, Azure resource write, invoice or retailer/private media.** Shared root docs, workflows, Part3/Feature4, WineShopPOS, PROD unchanged.
+
+- 2026-10-26 continuation: checked Microsoft current Container Apps managed-environment quota request documentation (Quota page; no documented Microsoft.App Quota REST submission scope), NVIDIA A40 48GB BF16 official datasheet, Tencent 1.5 official T2V requirements and 2026 Runpod Pod pricing. Fixed `feature5_motion/external_gpu_budget.py` to allow exact provisional A40 48GB SKU (previous omission), added 1h pod rental $0.66 estimated cap acceptance/rejection test. No paid Azure/Runpod capacity acquired; no quota request submitted; no model output yet. PR #323 remains draft.
+
+- 2026-10-26 engine re-evaluation: read current repository instructions and Feature5 state, reviewed official live LTX-Video v0.9.8 model+weights and 60-second long-shot claim, Wan2.2 5B Apache-2.0 and 24GB reference, ComfyUI GPL-3, Azure-Samples/comfyui-on-azure H100 Terraform, and Microsoft East US ACA A100 serverless GPU docs. Created `docs/feature5/OPEN_SOURCE_VIDEO_ENGINE_REVIEW_20261026.md`, explicitly documenting checkpoint-license distinction, no one-pass 60s guarantee, quota=0 unchanged and preservation of current Hunyuan and Part3 ownership. No source runner/provider switch, GPU activation, real MP4, Azure/prod edits or WineShopPOS changes. CI requires exact-head confirmation.
+
+- 2026-10-26 full upstream deployment pricing: compared whole official Microsoft Azure Samples ComfyUI-on-Azure H100 VM (40 vCPU; $6.98/hr East US, allocated billing) and full pinned upstream ComfyUI + LTX as private ACA serverless A100 ($0.000529 GPU/s plus active CPU/RAM; illustrative 4 vCPU+16 GiB total $2.4228/hr). Confirmed Microsoft published API meter readings and existing VM-vCPU 10/A100 quota 0 blockers. Updated open-source engine review with cost and runbook distinction. No paid cloud deployment, license approval, actual 60-second AI model reel or source generator rewrite.
+
+- 2026-10-28 procurement recommendation: read current AGENTS.md, canonical PROJECT_STATE/NEXT_TASK/DECISIONS/WORK_LOG and Feature5 handoff. Compared official Wan 24GB minimum with real vendor offerings: Runpod RTX 4090 ($0.34 community up to $0.89/hr listed types), Vast.ai verified RTX 4090 variable USD marketplace and host/storage charges, and JarvisLabs India A30 ₹38.88/h, L4 ₹41.31/h, A100 40GB ₹84.24/h, A100 80GB ₹140.94/h. Selected JarvisLabs India **A100 80GB on-demand** for initial genuine upstream proof because of 80GB VRAM, dedicated GPU, per-minute billing, INR Indian-card checkout/GST, private deployment option. Storage ₹0.013/GB/h and possible 18% GST are additional. Did NOT make a purchase, access paid GPUs, provision any cloud resource, alter Part3 or WineShopPOS, or generate an MP4; owner approval and exact checkout rate remain gate.
+
+- 2026-10-28: Owner posted Azure Portal managed-environment Quota screenshot showing RetailGrowthAI DEV `rgai-f5-gpu-canary-eastus` **NCA100 0 used/2 limit**, T4 0/0, after prior request. Explained authorization capacity != allocated billed GPU usage, confirmed Azure official Consumption billing says zero replicas have no GPU resource charges; independent storage/logging/network can still bill. Updated issue #400 with screenshot-derived status and ARM verification/paid-GPU safeguards. No live Azure API readback, GPU deployment, paid runtime or video generation happened.
~~~~

## docs/feature5/proposed-workflows/azure-feature5-oidc-reconcile.yml

~~~~diff
@@ -0,0 +1,120 @@
+name: Feature5 Azure OIDC ARM reconcile — read only
+
+# PROPOSAL ONLY: feature-owned handoff file. The main-repo coordinator moves
+# this reviewed YAML into .github/workflows/ under an approved pull request.
+# GitHub Actions cannot load workflows from docs/ paths.
+on:
+  workflow_dispatch:
+
+permissions:
+  contents: read
+
+concurrency:
+  group: rgai-dev-feature5-arm-reconcile
+  cancel-in-progress: false
+
+jobs:
+  feature5-azure-reconcile:
+    if: github.repository == 'saifsiddiqui59/RetailGrowthAI' && github.ref == 'refs/heads/main'
+    name: Verify exact DEV ARM deployment and A100 quota without writes
+    runs-on: ubuntu-24.04
+    timeout-minutes: 12
+    environment: dev
+    permissions:
+      contents: read
+      id-token: write
+    env:
+      EXPECTED_SUB: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
+      RG: rg-retailgrowth-dev
+      ENV_NAME: rgai-f5-gpu-canary-eastus
+      DEPLOYMENT: CustomDeployment-20261026093554
+    steps:
+      - name: Azure OIDC login using existing DEV credentials
+        uses: azure/login@v3
+        with:
+          client-id: ${{ secrets.AZURE_CLIENT_ID }}
+          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
+          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
+
+      - name: Verify exact DEV subscription, tenant RG and read Azure state
+        shell: bash
+        run: |
+          set -euo pipefail
+          umask 077
+          test -n "${EXPECTED_SUB:-}"
+          test "$(az account show --query id -o tsv)" = "$EXPECTED_SUB"
+          test "$(az account show --query state -o tsv)" = "Enabled"
+          test "$(az group show -n "$RG" --query location -o tsv)" = "centralindia"
+          test "$(az group show -n "$RG" --query tags.environment -o tsv)" = "dev"
+          test "$(az group show -n "$RG" --query tags.app -o tsv | tr '[:upper:]' '[:lower:]')" = "retailgrowthai"
+          echo "PASS: the intended RetailGrowthAI DEV identity and RG (IDs withheld)"
+          echo "Microsoft.App registration:"
+          az provider show --namespace Microsoft.App --query registrationState -o tsv
+
+          # Azure may report Deployment Succeeded while actually deploying zero
+          # ARM resources. Never attempt a second create before reconciling.
+          if az deployment group show -g "$RG" -n "$DEPLOYMENT" -o json > "$RUNNER_TEMP/arm.json" 2>/dev/null; then
+            python3 - "$RUNNER_TEMP/arm.json" <<'PY'
+          import json,sys
+          p=json.load(open(sys.argv[1]))
+          x=p.get("properties", {})
+          template=x.get("template") or {}
+          resources=template.get("resources")
+          print("Deployment:", p.get("name"))
+          print("Deployment state:", x.get("provisioningState"))
+          print("Template resource count:", len(resources) if isinstance(resources,list) else "unavailable")
+          if isinstance(resources,list):
+              for obj in resources:
+                  print("ARM resource declaration:",
+                        obj.get("type"), obj.get("name"), obj.get("location"))
+          PY
+            az deployment operation group list -g "$RG" -n "$DEPLOYMENT" \
+              --query "[].{status:properties.provisioningState,type:properties.targetResource.resourceType,name:properties.targetResource.resourceName}" -o json
+          else
+            echo "BLOCKED: prior deployment not readable; do not rerun a creation"
+          fi
+
+          # Read-only scoped inventory does not require a GPU or new registry.
+          az resource list -g "$RG" \
+            --resource-type Microsoft.App/managedEnvironments \
+            --query "[].{name:name,location:location,state:properties.provisioningState}" -o json
+
+          if az containerapp env show -g "$RG" -n "$ENV_NAME" -o json > "$RUNNER_TEMP/env.json" 2>/dev/null; then
+            python3 - "$RUNNER_TEMP/env.json" <<'PY'
+          import json,sys
+          x=json.load(open(sys.argv[1]))
+          p=x.get("properties") or {}
+          tag={k.lower():str(v).lower() for k,v in (x.get("tags") or {}).items()}
+          assert x.get("name")=="rgai-f5-gpu-canary-eastus", "Wrong environment name"
+          assert str(x.get("location","")).lower().replace(" ","")=="eastus", "Wrong region"
+          assert tag.get("app")=="retailgrowthai" and tag.get("environment")=="dev" and tag.get("feature")=="feature5", "Wrong ownership"
+          print("PASS: exact isolated East US DEV canary exists.")
+          print("ENV provisioning:", p.get("provisioningState"))
+          print("ENV workload profiles:",[(y.get("name"),y.get("workloadProfileType")) for y in p.get("workloadProfiles") or []])
+          print("ENV log destination:", (p.get("appLogsConfiguration") or {}).get("destination"))
+          PY
+            echo "A100 quota rows (if API supports existing environment):"
+            if az containerapp env list-usages -g "$RG" -n "$ENV_NAME" -o json > "$RUNNER_TEMP/usage.json" 2>/dev/null; then
+              python3 - "$RUNNER_TEMP/usage.json" <<'PY'
+          import json,sys
+          a=json.load(open(sys.argv[1]))
+          items=a if isinstance(a,list) else a.get("value",[])
+          relevant=[v for v in items if "NCA100" in str(v.get("name","")).upper()]
+          if not relevant:
+              print("A100 QUOTA UNKNOWN: no NCA100 row from existing environment")
+          else:
+              for v in relevant:
+                  print("A100 QUOTA:", v.get("name"), "limit=",v.get("limit"),"used=",v.get("currentValue"))
+          PY
+            else
+              echo "A100 QUOTA UNKNOWN: env list-usages unavailable (not quota=0)"
+            fi
+          else
+            echo "ENVIRONMENT ABSENT OR UNREADABLE; do not infer quota=0 or redeploy automatically"
+          fi
+          echo "READ-ONLY COMPLETE. No resource created, changed or deleted."
+
+      - name: Logout Azure OIDC session
+        if: always()
+        shell: bash
+        run: az logout >/dev/null 2>&1 || true
~~~~

## feature5_motion/README.md

~~~~diff
@@ -0,0 +1,72 @@
+# Feature #5 motion adapter — disabled source-only
+
+`MotionSpec` and `AssetGrant` are authenticated **server-authoritative** contracts. Run only behind the existing Part3 approved subscription reservation / source-media RLS / ledger / outbox / lease fences. Incoming queue messages contain just the canonical job UUID. This module does not create a queue, cloud API or Supabase schema and does not modify Part3.
+
+`HunyuanLocalRunner` is a no-download optional local official 1.5 `generate.py` adapter; requires explicitly configured preinstalled model checkout + weights + licensed GPU, `enabled=True`, `license_approved=True`, and `gpu_budget_approved=True`. Default off. A pinned model/runtime is still required before execution. No user-facing endpoint or keys here.
+
+`MotionWorker` expects injected existing `JobStore` and `TenantMedia` adapters. The downstream collaborator MUST supply transactional atomic claim/finish/failed fencing with existing credit accounting. Generated clip is checked with local-only ffprobe and private output upload; a human must compare garment with source and approve before publishing. Feature4 remains responsible for promotions, logos, music and final Reel assembly.
+
+Tests: `python -m pytest tests/ai/test_feature5_motion.py`. All tests are CPU-only/mocked. They do not generate real AI video.
+
+No production use until the gates in `docs/feature5/NEXT_TASK.md` are closed.
+
+## Security contract (2026-10-26)
+- The offline Tencent CLI must omit `--image_path` for T2V; image/poster mode supplies only a decoded, bounded file inside a private job directory. Zero unapproved network model fetching.
+- BF16-capable CUDA hardware and a reviewed 14 GiB minimum are required before launching; a Central India T4 alone is not verified suitable.
+- `TenantMedia.upload_private` must return a verified exact, private receipt with `shop_id`, `job_id`, `attempt_token`, `bucket=retailgrowth-media`, `path={shop_id}/renders/{job_id}/{attempt_token}.mp4`, `private=True`. Receipt ambiguity remains UNKNOWN; the injected existing DB store must reconcile it without paid retry.
+- Scratch image/video files are deleted after processing. Use encrypted/ephemeral private worker disks; do not log local source content, prompts, provider credentials or private URLs.
+- All CLI subprocess and GPU readiness tests remain simulated. No real garment, face, movement or temporal quality has passed acceptance.
+
+## Explicitly approved real GPU test (not part of Actions)
+Run only on a preprovisioned/licensed GPU already authorized by the owner. Supply `RETAIL_FEATURE5_REAL_GPU_TEST=true`, `RETAIL_FEATURE5_GPU_COST_APPROVED=true`, `RETAIL_FEATURE5_LICENSE_APPROVED=true`, `RETAIL_FEATURE5_PINNED_CHECKOUT`, and `RETAIL_FEATURE5_PINNED_WEIGHTS`. For I2V additionally supply `RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE` after consent/rights review. Run `python -m unittest discover -s tests/gpu -p 'test_feature5_local_acceptance.py'`. The test deletes its temporary assets and never activates a hosted service. Its success only validates machine media, not visual/garment QA.
+
+## Mandatory integration and activation details — 2026-10-26
+- IMPORTANT: Part3 draft SQL only supports Wan 720P/1080P models; current `feature5_motion/interop.py` adapter is a **source contract only** and has not been wired to a live Part3 service-role RPC. Coordinator must reconcile an additive 480p model/profile, atomic subscriptions, rights and outbox first. Existing Wan implementation is untouched.
+- Feature4 `feature4_asset_entry` now requires a tenant-authorized, media-hash-bound `VisualReview` (approved garment/quality/disclosure) as well as true output provenance, codec, lease and rights. Synthetic fixtures only validate code contracts; they do not certify motion.
+- Logical motion reservation key `feature5-lease-v2` includes an SHA-256 of the approved prompt plus the generation seed. The canonical coordinator must persist the matching versioned key; no client-supplied hash can authorize expense.
+- HunyuanLocalRunner fails closed without a reviewed `HunyuanLicensePolicy` covering deployment/retailer/intended publication territories, actual legally named service provider, AUP/notice/rights and Tencent MAU terms. This policy is not real commercial legal signoff, IP geolocation or royalty clearance.
+- Separate real local GPU harness requires explicit spend permission, operator licence review, provider legal name, allowed countries, installed weights, pinned runtime and BF16-capable hardware. No GPU execution has occurred.
+
+## Budget runtime contract (added 2026-10-26)
+Even with `enabled=True`, `MotionWorker` refuses to claim/launch without a `MotionSpendGuard` based on a verified active A100/vCPU/RAM quote, allowed max billed execution seconds and ancillary cost reserve. The existing DB must already reserve at least that full worst-case quote and the runner timeout must fit. No additional ledger/table is created. `compute_seconds_measured` and `estimated_observed_compute_usd` are subprocess estimates, not paid-cloud invoice measurements. A GPU overrun or lost acknowledgment goes to UNKNOWN/reconciliation and MUST NOT automatically retry/credit/refund.
+
+## Official pinned upstream and review-fixture workflow
+The optional runner hard-codes `HunyuanVideo-1.5` upstream `generate.py` Git blob `ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d` at Tencent commit `60783e704160023913bee78f0b47036d393d4dfa` and rejects altered/symlinked code before CUDA. It does **not** verify complete model weight shards or dependencies; operator must separately record immutable licensed weight revision/checksums and pin deployment artifacts. Changing upstream versions requires a reviewed source-and-model change.
+`prepare_visual_review(clip, private_new_output_dir)` provides CPU-generated six-frame PNG sampling, 3×2 contact sheet and SHA256 manifest from an already validated tenant-private H.264 MP4. Existing service must authenticate tenant, provide private staging, dispose of artifacts and obtain an independently persisted human `VisualReview`; this utility never automatically passes quality or publishing approval.
+`tests/ai/test_feature5_real_ffmpeg_media.py` makes **real synthetic FFmpeg clips**, verifies the exact 5s/24FPS/480p bytes and checks negative profiles. This is not AI motion, not an Azure end-to-end test and not evidence of garment fidelity.
+
+## Complete model/weights integrity and real manual acceptance (2026-10-26)
+`HunyuanLocalRunner` requires **both** official `generate.py` Git blob identity and an `ArtifactLock` for every installed runtime code file + every licensed weight file. Source tree must be a **clean materialized** copy, no `.git`, symlinks or temp cache. Reviewer generates a CANDIDATE locally, for example:
+
+```bash
+python -m feature5_motion.seal_artifacts --checkout /private/hunyuan-clean-checkout --weights /private/licensed-hunyuan-model --out /private/operator/feature5-model.lock.json
+```
+
+Operator must verify Tencent license/territories, model supplier, model revision, full shard SHA256 list, dependency versions and exact manifest, then store the candidate's SHA256 in a **separate trusted deployment configuration**. The manifest cannot approve itself. Neither generator nor verification downloads any model or starts CUDA; a model lock merely detects mutations and is not licensing proof.
+
+Manual genuine GPU acceptance `tests/gpu/test_feature5_local_acceptance.py` now ALSO requires `RETAIL_FEATURE5_ARTIFACT_LOCK_PATH`, independently reviewed `RETAIL_FEATURE5_APPROVED_LOCK_SHA256`, and an **existing owner-controlled mode-0700** `RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT`. Preserve all previous legal/region/spend/license/rights environment gates documented above. Once a real GPU succeeds, it retains the original validated clip + source still for I2V and six-frame contact sheet + SHA256 under a new output folder. Evidence stays `PENDING_HUMAN_REVIEW` and must be checked by a real authorized reviewer before Feature4 can compose it. No customer data should be sent to an unapproved region.
+
+## $0-first routing and unknown-billing guard (2026-10-26)
+`plan_lowest_cost_delivery(requires_realistic_ai_motion=..., existing_media_approved=..., allow_paid_gpu=False, max_premium_usd="0", guard=None)` defaults to `EXISTING_FFMPEG` for already licensed still/video assets when suitable, `DEFER` for unapproved/no media/expensive photorealistic motion, and only `GPU_BUDGET_ELIGIBLE` for explicit budget, guard and a sufficient worst-case quote. It **does not invoke FFmpeg/GPU, bypass licensing, or alter Part3 quota**. Feature4 coordinator must wire the cheapest actual composition route; do not present a slideshow as an AI model walking.
+
+`MotionWorker` now records failures prior to runner invocation as `FAILED`, and any post-runner-start exception as **`UNKNOWN`**, preventing accidental charged auto-retry or refund on CUDA timeout, invalid output or encoder failures. An UNKNOWN persistence failure raises `ReconciliationRequired`. This source contract depends on the coordinator's atomic Part3 ledger/lease/RPC to be honored in hosted DEV.
+
+Azure documentation (2026-10-26) currently lists Central India with T4 only, not serverless A100; never silently move Indian customer media to an A100 region outside their approved scope. Tencent's 14 GiB minimum plus BF16 requirement does not validate older T4 GPU. Keep real GPU disabled until legal, rights, region, licensed pinned weights, quota, pricing, explicit budget and actual visual QA gates pass.
+
+## Real fashion sample, authenticity, and exactly-one-GPU-attempt controls
+The canonical example is `feature5_motion/demo_fashion.py` (5s 480p/24fps portrait T2V, adult fashion model in red embroidered kurti). **No MP4 has been generated yet**, because this execution environment is CPU-only and no licensed model weights are installed. The previously shown still image was generated by ChatGPT and is not a Feature5 artifact.
+
+The existing manual CUDA harness `tests/gpu/test_feature5_local_acceptance.py` now demands `RETAIL_FEATURE5_ACCEPTANCE_MODE=text` **or** `image` (never both); `RETAIL_FEATURE5_AZURE_PRICE_SNAPSHOT` (a current reviewed official Azure Container Apps USD JSON price response), `RETAIL_FEATURE5_GPU_REGION=eastus` only with reviewed geography, `RETAIL_FEATURE5_MAX_BILLABLE_SECONDS`, and `RETAIL_FEATURE5_MAX_TOTAL_GPU_USD`. It checks an all-in A100+vCPU+RAM+ancillary worst-case quote before the CUDA/weights gate. All previous licensing/territory/model-lock/0700 evidence flags still apply. Missing or insufficient budgets fail closed. Manual GPU test always writes an independent PENDING_HUMAN_REVIEW packet, not a published Reel.
+
+The external public `multimodalart/Hunyuan-Video-1-5` Space is an optional free **third-party** 480p I2V-distilled demo, requiring a local image upload; it is NOT our worker execution, and the tool-driven public test did NOT generate any MP4. Never substitute Tencent's stock clips, ChatGPT image, or FFmpeg still animation for a genuine Feature5 proof.
+
+## Azure GPU one-shot preflight (2026-10-26)
+Before any *real* HunyuanVideo deployment, use authenticated dedicated **DEV** Azure CLI/OIDC credentials (not available in this ChatGPT sandbox). The one explicit read-only command is `AZURE_SUBSCRIPTION_ID=<existing DEV id> python -m feature5_motion.azure_gpu_readonly_cli`. It reads account, known tagged `rg-retailgrowth-dev`, East US supported A100 workload profiles, existing eligible DEV managed environments and A100 available GPU quota. It **never invokes create/start/update/delete**, creates no image/model/cloud billing, and rejects T4-only/unknown environments and wrong subscriptions.
+
+An `INSPECTION_PASS_ONLY` is NOT a deployment or paid inference authorization; licensed complete model shards, immutable CUDA image, region and owner budget, exact resource size and actual paid GPU credentials are still required. User's Azure browser-profile sign-in is outstanding. Detailed gated path: `docs/feature5/AZURE_GPU_CANARY_DEPLOYMENT_20261026.md`.
+
+## Signed-in Azure browser inventory result (2026-10-26)
+Microsoft Azure login **is now saved and functioning**. Portal verified exact isolated DEV resource group and eight resources but **no existing East US A100 Container Apps environment** and **no Container Registry**; a separate Sweden Central Container Apps environment is unrelated and must remain untouched. GPU **quota remains unknown** because a later generic Subscriptions blade showed 0/0 filtered rows in the active directory. Refer to `docs/feature5/AZURE_SIGNEDIN_INVENTORY_20261026.md` to select the directory and inspect quotas before any billable resource. This is no longer a missing-login blocker; it is an unresolved quota/budget/model-artifact gate. No actual GPU deployed or model media produced.
+
+## Azure authenticated DEV checkpoint, 2026-10-26
+**Real empty managed environment is now deployed** via main GitHub Azure OIDC [#40347841764](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/40347841764): `rgai-f5-gpu-canary-eastus`, `rg-retailgrowth-dev`, East US, default Consumption only, no GPU/app/job. Real `az containerapp env list-usages` returned **`ManagedEnvironmentConsumptionNCA100Gpus limit=0 used=0`**. The next prerequisite to run a genuine Tencent sample is **one approved serverless managed-environment A100 GPU quota**, which is requested in that environment's Azure Portal Settings → Quota (not subscription-wide dedicated GPU quota). It has NOT been requested or approved. Licensed Hunyuan model shards, immutable hashes, BF16 CUDA image, full-cost cap and real MP4 QA also remain pending. The previous “environment missing/unknown quota” sections above are historical checkpoints superseded by this verified rollout.
~~~~

## feature5_motion/__init__.py

~~~~diff
@@ -0,0 +1,5 @@
+"""RetailGrowthAI Feature 5: source-only, gated premium motion adapter."""
+from .contracts import AssetGrant, MotionSpec, MotionError, CostEstimate, estimate_cost
+from .worker import MotionWorker, validate_clip
+
+__all__ = ["AssetGrant", "MotionSpec", "MotionError", "CostEstimate", "estimate_cost", "MotionWorker", "validate_clip"]
~~~~

## feature5_motion/acceptance.py

~~~~diff
@@ -0,0 +1,98 @@
+"""Local-only, reviewable evidence from a successfully generated 5-second clip.
+
+No model execution, tenant lookups, cloud uploads or automatic human approval.
+The caller (manual operator) MUST use an already approved local private source
+and select a protected disk location outside any public/server web root.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from pathlib import Path
+import shutil
+
+from .contracts import MotionError
+from .visual_review_artifacts import prepare_visual_review
+from .worker import validate_clip
+
+
+def _copy_private(source: Path, destination: Path) -> str:
+    if source.is_symlink() or not source.is_file():
+        raise MotionError("Only local ordinary files may be exported")
+    # Exclusive creation, not an unsafe overwrite of an earlier acceptance.
+    with source.open("rb") as inp:
+        fd = os.open(str(destination), os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
+        sha = hashlib.sha256()
+        with os.fdopen(fd, "wb") as out:
+            for chunk in iter(lambda: inp.read(1024 * 1024), b""):
+                sha.update(chunk)
+                out.write(chunk)
+    return sha.hexdigest()
+
+
+def export_pending_review(clip: Path, evidence_dir: Path, *,
+                          mode: str, source_image: Path | None = None,
+                          approved_model_manifest_sha256: str) -> dict:
+    """Export a private MP4 + optional source image + human-review contact sheet.
+
+    Both `mode` and model manifest digest are *operator assertions*, not
+    proof of actual inference provenance. The clip must pass ffprobe's strict
+    5-second H264 profile. All outputs remain PENDING_HUMAN_REVIEW.
+    """
+    if mode not in ("text", "image", "poster"):
+        raise MotionError("Unsupported acceptance mode")
+    if (mode == "text") != (source_image is None):
+        raise MotionError("Source image must match text/image acceptance mode")
+    if (not isinstance(approved_model_manifest_sha256, str) or
+        len(approved_model_manifest_sha256) != 64 or
+        any(x not in "0123456789abcdef" for x in approved_model_manifest_sha256)):
+        raise MotionError("Reviewed model manifest digest required")
+    candidate = Path(clip)
+    if candidate.is_symlink() or not candidate.is_file():
+        raise MotionError("Invalid private GPU clip for export")
+    validate_clip(candidate)   # Never copy unvalidated MP4 bytes.
+    if source_image is not None:
+        source = Path(source_image)
+        if (source.is_symlink() or not source.is_file() or
+            source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp") or
+            not 0 < source.stat().st_size <= 20 * 1024 * 1024):
+            raise MotionError("Invalid approved comparison source image")
+    directory = Path(evidence_dir)
+    if directory.is_symlink() or directory.exists():
+        raise MotionError("Acceptance evidence output must be a new private directory")
+    if not directory.parent.resolve(strict=True).is_dir():
+        raise MotionError("Missing private evidence parent")
+    directory.mkdir(mode=0o700, exist_ok=False)
+    try:
+        copied = directory / "clip.mp4"
+        clip_hash = _copy_private(candidate, copied)
+        evidence = prepare_visual_review(copied, directory / "review")
+        if evidence["clip_sha256"] != clip_hash:
+            raise MotionError("Review frames not bound to copied clip hash")
+        source_hash = None
+        if source_image is not None:
+            original = Path(source_image)
+            destination = directory / ("reference" + original.suffix.lower())
+            source_hash = _copy_private(original, destination)
+        record = {
+            "status": "PENDING_HUMAN_REVIEW",
+            "claimed_model": "hunyuanvideo-1.5-480p",
+            "mode": mode,
+            "clip_sha256": clip_hash,
+            "reference_sha256": source_hash,
+            "model_manifest_sha256": approved_model_manifest_sha256,
+            "machine_profile": {
+                "codec": evidence["codec"], "duration_seconds": evidence["duration_seconds"],
+                "width": evidence["width"], "height": evidence["height"],
+            },
+            "visual_review": "review/review-manifest.json",
+        }
+        out = directory / "acceptance-pending.json"
+        fd = os.open(str(out), os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
+        with os.fdopen(fd, "w", encoding="utf-8") as stream:
+            json.dump(record, stream, sort_keys=True)
+        return record
+    except Exception:
+        shutil.rmtree(directory, ignore_errors=True)
+        raise
~~~~

## feature5_motion/artifact_lock.py

~~~~diff
@@ -0,0 +1,172 @@
+"""Offline, complete-set artifact attestation for a reviewed Hunyuan runtime.
+
+Never download any model, activate CUDA, or trust checksums shipped beside
+model weights. The reviewed expected *manifest* SHA256 is supplied independently
+by the trusted operator/deployment configuration.
+
+Snapshot a CLEAN, materialized code checkout (no .git) and LICENSED weights.
+Review the resulting manifest independently before setting its pinned digest.
+A local self-authored manifest does not authorize license, downloads or spend.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from dataclasses import dataclass
+from pathlib import Path, PurePosixPath
+
+from .contracts import MotionError
+
+MAX_MANIFEST_BYTES = 250_000
+MAX_FILES = 4096
+MAX_FILE_BYTES = 45 * 1024 ** 3
+MAX_TOTAL_BYTES = 180 * 1024 ** 3
+BUFFER_BYTES = 1024 * 1024
+
+
+def _digest(value: object, label: str) -> str:
+    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
+        raise MotionError("Invalid reviewed " + label + " SHA256")
+    return value
+
+
+def _root(root: Path) -> Path:
+    path = Path(root)
+    if path.is_symlink() or not path.exists() or not path.is_dir():
+        raise MotionError("Model artifact root missing or symlinked")
+    return path.resolve(strict=True)
+
+
+def _names(root: Path) -> dict[str, Path]:
+    """Enumerate every entry, including hidden ones. No extra/unreviewed files."""
+    found = {}
+    if not (root / ".git").exists() and not (root / ".git").is_symlink():
+        pass
+    else:
+        raise MotionError("Git metadata is not permitted in sealed runtime")
+    for current, dirs, files in os.walk(root, followlinks=False):
+        here = Path(current)
+        for d in dirs:
+            sub = here / d
+            if sub.is_symlink():
+                raise MotionError("Symlinked model directory not permitted")
+            if not sub.is_dir():
+                raise MotionError("Non-directory artifact entry")
+        for f in files:
+            target = here / f
+            if target.is_symlink() or not target.is_file():
+                raise MotionError("Model artifact must be a regular file")
+            name = target.relative_to(root).as_posix()
+            _valid_name(name)
+            found[name] = target
+            if len(found) > MAX_FILES:
+                raise MotionError("Too many local runtime files")
+    return found
+
+
+def _valid_name(value: object) -> str:
+    if not isinstance(value, str) or not 1 <= len(value) <= 230:
+        raise MotionError("Invalid artifact relative name")
+    if "\\" in value or ":" in value or any(ord(c) < 32 for c in value):
+        raise MotionError("Unsafe artifact relative name")
+    p = PurePosixPath(value)
+    if (p.is_absolute() or any(s in ("", ".", "..") for s in value.split("/")) or
+            len(p.parts) > 12 or value.startswith("-")):
+        raise MotionError("Artifact name escaped reviewed root")
+    return value
+
+
+def _hash_file(path: Path) -> tuple[int, str]:
+    n = path.stat().st_size
+    if n <= 0 or n > MAX_FILE_BYTES:
+        raise MotionError("Artifact file size outside approved limit")
+    sha = hashlib.sha256()
+    with path.open("rb") as stream:
+        for part in iter(lambda: stream.read(BUFFER_BYTES), b""):
+            sha.update(part)
+    if path.stat().st_size != n:
+        raise MotionError("Artifact changed while being hashed")
+    return n, sha.hexdigest()
+
+
+def _bytes(entries: list[dict]) -> bytes:
+    return json.dumps(
+        {"version": "feature5-artifacts-v1", "files": entries},
+        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
+    ).encode("utf-8")
+
+
+def construct_manifest(checkout: Path, weights: Path) -> bytes:
+    """Generate unsigned candidate bytes for offline operator REVIEW ONLY."""
+    roots = {"checkout": _root(checkout), "weights": _root(weights)}
+    if roots["checkout"] == roots["weights"]:
+        raise MotionError("Code checkout and licensed weights must be isolated")
+    result = []
+    total = 0
+    for scope in ("checkout", "weights"):
+        for name, path in sorted(_names(roots[scope]).items()):
+            size, sha = _hash_file(path)
+            total += size
+            if total > MAX_TOTAL_BYTES:
+                raise MotionError("Runtime artifacts exceed approved cap")
+            result.append({"scope": scope, "path": name, "bytes": size, "sha256": sha})
+    if not any(e["scope"] == "checkout" and e["path"] == "generate.py" for e in result):
+        raise MotionError("No pinned official generate.py in model checkout")
+    if not any(e["scope"] == "weights" for e in result):
+        raise MotionError("No installed licensed model weights")
+    result_bytes = _bytes(result)
+    if len(result_bytes) > MAX_MANIFEST_BYTES:
+        raise MotionError("Runtime lock manifest too large")
+    return result_bytes
+
+
+@dataclass(frozen=True)
+class ArtifactLock:
+    """The sha256 MUST come from a separately reviewed deployment config."""
+    manifest_path: Path
+    approved_manifest_sha256: str
+
+    def verify(self, *, checkout: Path, weights: Path) -> str:
+        expected = _digest(self.approved_manifest_sha256, "artifact manifest")
+        path = Path(self.manifest_path)
+        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
+            raise MotionError("Pinned artifact lock is missing or unsafe")
+        raw = path.read_bytes()
+        if hashlib.sha256(raw).hexdigest() != expected:
+            raise MotionError("Model artifact lock differs from reviewed manifest")
+        try:
+            parsed = json.loads(raw)
+        except (ValueError, UnicodeError) as exc:
+            raise MotionError("Model artifact lock is invalid JSON") from exc
+        if (type(parsed) is not dict or set(parsed) != {"version", "files"} or
+            parsed["version"] != "feature5-artifacts-v1" or
+            type(parsed["files"]) is not list or not parsed["files"] or
+            len(parsed["files"]) > MAX_FILES):
+            raise MotionError("Model artifact lock has unsupported format")
+        seen = set()
+        total = 0
+        for entry in parsed["files"]:
+            if type(entry) is not dict or set(entry) != {"scope", "path", "bytes", "sha256"}:
+                raise MotionError("Invalid manifest artifact entry")
+            if entry["scope"] not in ("checkout", "weights"):
+                raise MotionError("Unapproved runtime artifact scope")
+            name = _valid_name(entry["path"])
+            key = (entry["scope"], name)
+            if key in seen:
+                raise MotionError("Duplicate model artifact lock entry")
+            seen.add(key)
+            if type(entry["bytes"]) is not int or not 0 < entry["bytes"] <= MAX_FILE_BYTES:
+                raise MotionError("Unapproved artifact size")
+            _digest(entry["sha256"], "artifact")
+            total += entry["bytes"]
+            if total > MAX_TOTAL_BYTES:
+                raise MotionError("Model artifacts exceed approved limit")
+        # This also rejects non-canonical spellings, duplicate JSON keys,
+        # unsigned metadata or added files that were not reviewed.
+        if _bytes(parsed["files"]) != raw:
+            raise MotionError("Noncanonical model manifest is not trusted")
+        actual = construct_manifest(checkout, weights)
+        if actual != raw:
+            raise MotionError("Installed model files differ from reviewed lock")
+        return expected
~~~~

## feature5_motion/azure_gpu_preflight.py

~~~~diff
@@ -0,0 +1,109 @@
+"""Read-only Azure A100 preflight; not a deployment or quota request.
+
+Parse snapshots captured with signed-in Azure CLI. Do not accept an arbitrary
+region, borrowed PROD subscription, or regional A100 catalog as proof of an
+actual available GPU quota. No cloud calls or access tokens in this module.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import Any
+
+from .contracts import MotionError
+
+DEV_GROUP = "rg-retailgrowth-dev"
+CANARY_ENV = "rgai-f5-gpu-canary-eastus"
+REGION = "eastus"
+PROFILE_MATCH = "NCA100"
+
+
+def _a100_profile(item: Any) -> bool:
+    if not isinstance(item, dict):
+        return False
+    names = [item.get("name"), item.get("workloadProfileType"), item.get("type")]
+    return any(isinstance(v, str) and
+               ("NCA100" in v.upper() or "NC24-A100" in v.upper() or
+                "GPU-A100" in v.upper()) for v in names)
+
+
+def _name(value: Any) -> str:
+    if isinstance(value, dict):
+        return str(value.get("value", ""))
+    return str(value or "")
+
+
+@dataclass(frozen=True)
+class A100Readiness:
+    status: str
+    reasons: tuple[str, ...]
+    eligible_environment: str | None
+
+
+def assess_azure_a100_preflight(*, account: dict, resource_group: dict,
+                                supported_profiles: list, environments: list,
+                                usage_by_environment: dict[str, list],
+                                expected_subscription_id: str) -> A100Readiness:
+    """Fail closed, no resource creation. Quota is needed, not just meter price."""
+    if not isinstance(expected_subscription_id, str) or not expected_subscription_id.strip():
+        raise MotionError("Expected DEV subscription ID missing")
+    if not isinstance(account, dict) or account.get("id") != expected_subscription_id or account.get("state") != "Enabled":
+        raise MotionError("Incorrect/inactive Azure subscription: no GPU deployment")
+    if (not isinstance(resource_group, dict) or
+        resource_group.get("name") != DEV_GROUP or
+        str(resource_group.get("location", "")).lower().replace(" ", "") != "centralindia"):
+        raise MotionError("Not the isolated RetailGrowthAI DEV resource group")
+    tags = resource_group.get("tags") or {}
+    if not isinstance(tags, dict):
+        raise MotionError("Invalid DEV ownership tags")
+    normalized = {str(k).lower(): str(v).lower() for k, v in tags.items()}
+    if normalized.get("app") != "retailgrowthai" or normalized.get("environment") != "dev":
+        raise MotionError("Dedicated DEV ownership tags not verified")
+    if not isinstance(supported_profiles, list) or not isinstance(environments, list):
+        raise MotionError("Malformed Azure GPU inventory response")
+    if not any(_a100_profile(x) for x in supported_profiles):
+        return A100Readiness("BLOCKED", ("No A100 consumption profile verified in East US",), None)
+    # Azure's managed-environment A100 quota can ONLY be read once a v2
+    # workload-profiles environment exists in a supported region. It does
+    # NOT need to contain a billable A100 workload profile yet.
+    matching = [e for e in environments if isinstance(e, dict)
+                and e.get("name") == CANARY_ENV]
+    if not matching:
+        return A100Readiness("ENVIRONMENT_REQUIRED", (
+            "Create reviewed, EMPTY East US workload-profiles DEV environment before quota read",
+            "Missing environment does not mean A100 quota is zero",
+        ), None)
+    if len(matching) != 1:
+        return A100Readiness("BLOCKED", ("Ambiguous dedicated DEV environment",), None)
+    e = matching[0]
+    tags = {str(k).lower(): str(v).lower()
+            for k, v in (e.get("tags") or {}).items()}
+    profiles = (e.get("properties") or {}).get("workloadProfiles") or []
+    if (str(e.get("location", "")).lower().replace(" ", "") != REGION or
+        e.get("provisioningState") != "Succeeded" or
+        tags.get("app") != "retailgrowthai" or tags.get("environment") != "dev" or
+        tags.get("feature") != "feature5" or
+        profiles != [{"name": "Consumption", "workloadProfileType": "Consumption"}]):
+        return A100Readiness("BLOCKED", ("Unexpected environment, tags or paid profile",), CANARY_ENV)
+    target = CANARY_ENV
+    rows = usage_by_environment.get(target)
+    if not isinstance(rows, list):
+        return A100Readiness("BLOCKED", ("GPU quota not readable for selected environment",), target)
+    gpu_rows = [q for q in rows if isinstance(q, dict) and
+                PROFILE_MATCH in _name(q.get("name")).upper() and
+                "GPU" in _name(q.get("name")).upper()]
+    if len(gpu_rows) != 1:
+        return A100Readiness("BLOCKED", ("A100 quota row absent or ambiguous",), target)
+    q = gpu_rows[0]
+    try:
+        limit = float(q["limit"])
+        used = float(q.get("currentValue", q.get("value", 0)))
+    except (ValueError, TypeError, KeyError):
+        return A100Readiness("BLOCKED", ("A100 quota values invalid",), target)
+    if not (0 <= used < limit and limit >= 1):
+        return A100Readiness("BLOCKED", ("No unconsumed A100 environment GPU quota",), target)
+    return A100Readiness(
+        "INSPECTION_PASS_ONLY",
+        ("Quota is available, but image/weights/identity/approved budget not verified",
+         "No GPU has been created or deployed"),
+        target,
+    )
~~~~

## feature5_motion/azure_gpu_readonly_cli.py

~~~~diff
@@ -0,0 +1,99 @@
+"""Azure DEV GPU discovery using READ-ONLY Azure CLI calls.
+
+Run only in an already Azure-authenticated shell with AZURE_SUBSCRIPTION_ID
+set to the exact existing DEV subscription. Nothing is provisioned, pushed,
+started, or billed by these commands. This does NOT approve deployment.
+"""
+from __future__ import annotations
+
+import json
+import os
+import re
+import subprocess
+
+from .azure_gpu_preflight import (
+    DEV_GROUP, REGION, assess_azure_a100_preflight,
+    A100Readiness, CANARY_ENV,
+)
+from .contracts import MotionError
+
+_AZ = "az"
+_AZ_TIMEOUT = 45
+_VALID_ENV = re.compile(r"^[A-Za-z][A-Za-z0-9-]{1,62}$")
+
+
+def _read_az(*args: str):
+    # Command allowlist prevents this inventory from becoming a write-capable
+    # arbitrary Azure CLI wrapper (even with malicious environment names).
+    commands = (
+        ("account", "show"),
+        ("group", "show"),
+        ("containerapp", "env", "list"),
+        ("containerapp", "env", "list-usages"),
+        ("containerapp", "env", "workload-profile", "list-supported"),
+    )
+    if not any(args[:len(p)] == p for p in commands):
+        raise MotionError("Disallowed Azure inventory operation")
+    cmd = [_AZ, *args, "--output", "json"]
+    try:
+        result = subprocess.run(cmd, check=True, capture_output=True,
+                                timeout=_AZ_TIMEOUT, text=True)
+        return json.loads(result.stdout)
+    except (OSError, ValueError, subprocess.SubprocessError) as exc:
+        # Never echo an az command's stderr; it might include tenant data.
+        raise MotionError("Azure GPU read-only inventory unavailable") from exc
+
+
+def inspect_current_dev(*, expected_subscription_id: str) -> A100Readiness:
+    if not isinstance(expected_subscription_id, str) or len(expected_subscription_id) != 36:
+        raise MotionError("Exact pre-approved Azure DEV subscription ID required")
+    account = _read_az("account", "show")
+    if not isinstance(account, dict) or account.get("id") != expected_subscription_id:
+        raise MotionError("Incorrect Azure account; refusing cross-subscription inspection")
+    group = _read_az("group", "show", "--name", DEV_GROUP)
+    supported = _read_az("containerapp", "env", "workload-profile",
+                         "list-supported", "--location", REGION)
+    environments = _read_az("containerapp", "env", "list",
+                            "--resource-group", DEV_GROUP)
+    if not isinstance(environments, list):
+        raise MotionError("Azure DEV environment inventory invalid")
+    usage: dict[str, list] = {}
+    for env in environments:
+        if not isinstance(env, dict):
+            continue
+        name = env.get("name")
+        # Environment-level consumption GPU quota is visible before adding
+        # the first GPU workload profile; only read our exact owned canary.
+        if (str(env.get("location", "")).lower().replace(" ", "") != REGION or
+            name != CANARY_ENV or not _VALID_ENV.fullmatch(name)):
+            continue
+        value = _read_az("containerapp", "env", "list-usages",
+                         "--resource-group", DEV_GROUP, "--name", name)
+        usage[name] = value if isinstance(value, list) else (
+            value.get("value", []) if isinstance(value, dict) else [])
+    return assess_azure_a100_preflight(
+        account=account, resource_group=group,
+        supported_profiles=supported, environments=environments,
+        usage_by_environment=usage,
+        expected_subscription_id=expected_subscription_id,
+    )
+
+
+def main():
+    expected = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
+    try:
+        result = inspect_current_dev(expected_subscription_id=expected)
+    except MotionError as exc:
+        print("BLOCKED:", exc)
+        raise SystemExit(3) from None
+    print("Azure A100 DEV preflight:", result.status)
+    print("Existing matching environment:", result.eligible_environment or "(none)")
+    for reason in result.reasons:
+        print(" -", reason)
+    print("This was a READ-ONLY check. No Azure GPU or model deployed.")
+    if result.status != "INSPECTION_PASS_ONLY":
+        raise SystemExit(3)
+
+
+if __name__ == "__main__":
+    main()
~~~~

## feature5_motion/azure_pricing.py

~~~~diff
@@ -0,0 +1,128 @@
+"""Strict interpretation of official Azure Retail Prices API snapshot.
+
+No network, cloud deployment or billing actions. The operator retrieves the
+public JSON from prices.azure.com and must still verify subscription quota,
+region availability, actual vCPU/RAM allocation, VAT, egress and model latency.
+"""
+from __future__ import annotations
+from dataclasses import dataclass
+from decimal import Decimal, InvalidOperation, ROUND_UP
+from math import ceil, isfinite
+from .contracts import MotionError
+
+METERS = {
+    "A100": "Standard NC A100 v4 GPU Usage",
+    "T4": "Standard NC T4 v3 GPU Usage",
+    "cpu": "Standard vCPU Active Usage",
+    "memory": "Standard Memory Active Usage",
+}
+UNITS = {
+    "A100": "1 Second", "T4": "1 Second",
+    "cpu": "1 Second", "memory": "1 GiB Second",
+}
+
+
+def _positive(value):
+    if type(value) is bool:
+        raise MotionError("Invalid Azure rate")
+    try:
+        d = Decimal(str(value))
+    except (InvalidOperation, ValueError, TypeError) as exc:
+        raise MotionError("Invalid Azure rate") from exc
+    if not d.is_finite() or d <= 0:
+        raise MotionError("Invalid Azure price")
+    return d
+
+
+@dataclass(frozen=True)
+class VerifiedAzureRates:
+    region: str
+    gpu: str
+    gpu_per_second_usd: Decimal
+    cpu_per_second_usd: Decimal
+    gib_per_second_usd: Decimal
+    effective_date: str
+
+
+def extract_rates(snapshot: dict, *, region: str, gpu: str) -> VerifiedAzureRates:
+    if gpu not in ("A100", "T4") or region not in ("eastus", "centralindia"):
+        raise MotionError("Unsupported proposed GPU region")
+    if not isinstance(snapshot, dict) or snapshot.get("BillingCurrency") != "USD":
+        raise MotionError("Official Azure USD price response required")
+    rows = snapshot.get("Items")
+    if not isinstance(rows, list):
+        raise MotionError("Azure price meter data missing")
+    selected = {}
+    for key in (gpu, "cpu", "memory"):
+        matching = [r for r in rows if isinstance(r, dict) and
+                    r.get("serviceName") == "Azure Container Apps" and
+                    r.get("armRegionName") == region and
+                    r.get("meterName") == METERS[key] and
+                    r.get("unitOfMeasure") == UNITS[key] and
+                    r.get("currencyCode") == "USD" and
+                    r.get("type") == "Consumption" and
+                    r.get("isPrimaryMeterRegion") is True]
+        if len(matching) != 1:
+            raise MotionError("Official Azure primary meter missing or ambiguous")
+        item = matching[0]
+        selected[key] = (_positive(item.get("retailPrice")), item.get("effectiveStartDate"))
+    return VerifiedAzureRates(region, gpu, selected[gpu][0], selected["cpu"][0],
+                              selected["memory"][0], selected[gpu][1])
+
+
+def estimate_execution_usd(rates: VerifiedAzureRates, *, billable_seconds: int,
+                           vcpus: int, gib_memory: int) -> Decimal:
+    if any(type(x) is not int for x in (billable_seconds, vcpus, gib_memory)):
+        raise MotionError("Invalid Azure capacity or duration")
+    if not (1 <= billable_seconds <= 3600 and 1 <= vcpus <= 32 and 1 <= gib_memory <= 256):
+        raise MotionError("Proposed GPU job exceeds reviewed limits")
+    sec = Decimal(billable_seconds)
+    return (sec * (rates.gpu_per_second_usd +
+                   rates.cpu_per_second_usd * vcpus +
+                   rates.gib_per_second_usd * gib_memory)).quantize(Decimal("0.000001"))
+
+@dataclass(frozen=True)
+class MotionSpendGuard:
+    """Fail-closed proposed maximum bill for one approved local GPU attempt.
+
+    Include worst-case cold load + timeout; the ledger must reserve at least
+    this amount BEFORE worker claims a job. No retries are automatically paid.
+    """
+    rates: VerifiedAzureRates
+    max_billable_seconds: int
+    vcpus: int
+    gib_memory: int
+    ancillary_allowance_usd: Decimal
+
+    def minimum_reservation_usd(self) -> Decimal:
+        if not isinstance(self.rates, VerifiedAzureRates) or self.rates.gpu != "A100":
+            raise MotionError("Hunyuan default requires reviewed A100 pricing")
+        if type(self.max_billable_seconds) is not int or not 30 <= self.max_billable_seconds <= 1800:
+            raise MotionError("GPU time cap must be 30-1800 seconds")
+        try:
+            allowance = Decimal(str(self.ancillary_allowance_usd))
+        except (InvalidOperation, TypeError, ValueError) as exc:
+            raise MotionError("Invalid ancillary inference cost allowance") from exc
+        if not allowance.is_finite() or allowance < 0:
+            raise MotionError("Invalid ancillary inference cost allowance")
+        base = estimate_execution_usd(
+            self.rates, billable_seconds=self.max_billable_seconds,
+            vcpus=self.vcpus, gib_memory=self.gib_memory)
+        return (base + allowance).quantize(Decimal("0.0001"), rounding=ROUND_UP)
+
+    def estimated_spend_for_observed_inference_usd(self, observed_seconds: float) -> Decimal:
+        """Approximation for claim reconciliation, never a provider invoice.
+
+        Includes configured ancillary allowance; billed Azure container time
+        may additionally include image pull, boot, model load and teardown.
+        """
+        if (type(observed_seconds) not in (int, float) or
+            not isfinite(observed_seconds) or observed_seconds < 0 or
+            observed_seconds > self.max_billable_seconds):
+            raise MotionError("Invalid observed GPU runtime")
+        seconds = max(1, ceil(observed_seconds))
+        return (estimate_execution_usd(
+            self.rates, billable_seconds=seconds,
+            vcpus=self.vcpus, gib_memory=self.gib_memory) +
+            Decimal(str(self.ancillary_allowance_usd))).quantize(
+                Decimal("0.0001"), rounding=ROUND_UP)
~~~~

## feature5_motion/contracts.py

~~~~diff
@@ -0,0 +1,123 @@
+"""Server-only Feature 5 contract; never use client-supplied ownership or URLs."""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from decimal import Decimal, ROUND_UP
+from uuid import UUID
+
+
+class MotionError(ValueError):
+    """Sanitized boundary error; keep provider/private details off user responses."""
+
+
+def canonical_uuid(value: str) -> str:
+    if not isinstance(value, str):
+        raise MotionError("Invalid identifier")
+    try:
+        result = str(UUID(value))
+    except (ValueError, AttributeError, TypeError) as exc:
+        raise MotionError("Invalid identifier") from exc
+    if result != value:
+        raise MotionError("Noncanonical identifier")
+    return result
+
+
+@dataclass(frozen=True)
+class AssetGrant:
+    """Result of a SERVER-SIDE lookup through the existing tenant/RLS media store.
+
+    A caller MUST NOT build this grant from browser-provided fields.
+    """
+    asset_id: str
+    shop_id: str
+    approved: bool
+    private: bool
+    commercial_rights: bool
+    media_type: str
+    clean_layers: bool = False
+
+    def __post_init__(self):
+        canonical_uuid(self.asset_id)
+        canonical_uuid(self.shop_id)
+
+
+@dataclass(frozen=True)
+class MotionSpec:
+    job_id: str
+    shop_id: str
+    prompt: str
+    mode: str  # text, image, poster
+    source_asset_id: str | None = None
+    duration_seconds: int = 5
+    resolution: str = "480p"
+    aspect_ratio: str = "9:16"
+    fps: int = 24
+    seed: int = 1
+    prompt_version: str = "feature5-v1"
+
+    def __post_init__(self):
+        canonical_uuid(self.job_id)
+        canonical_uuid(self.shop_id)
+        if self.mode not in ("text", "image", "poster"):
+            raise MotionError("Unsupported motion mode")
+        if not isinstance(self.prompt, str) or not 1 <= len(self.prompt.strip()) <= 1500 or "\x00" in self.prompt:
+            raise MotionError("Prompt must contain 1–1500 safe characters")
+        if type(self.duration_seconds) is not int or self.duration_seconds != 5:
+            raise MotionError("Only the verified 5-second output profile is configured")
+        if self.resolution != "480p" or self.aspect_ratio not in ("9:16", "16:9") or self.fps != 24:
+            raise MotionError("Unsupported output profile")
+        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
+            raise MotionError("Invalid reproducibility seed")
+        if self.prompt_version != "feature5-v1":
+            raise MotionError("Unapproved prompt version")
+        if self.mode == "text" and self.source_asset_id is not None:
+            raise MotionError("Text mode must not receive source media")
+        if self.mode != "text":
+            canonical_uuid(self.source_asset_id)
+
+
+def validate_source(spec: MotionSpec, grant: AssetGrant | None) -> None:
+    if spec.mode == "text":
+        if grant is not None:
+            raise MotionError("Unexpected source media")
+        return
+    if not isinstance(grant, AssetGrant) or grant.asset_id != spec.source_asset_id or grant.shop_id != spec.shop_id:
+        raise MotionError("Unauthorized source media")
+    if not (grant.approved and grant.private and grant.commercial_rights):
+        raise MotionError("Source media not approved for private commercial use")
+    if grant.media_type not in ("image/png", "image/jpeg", "image/webp"):
+        raise MotionError("Unsupported source media type")
+    if spec.mode == "poster" and not grant.clean_layers:
+        raise MotionError("Poster motion requires approved clean source layers")
+
+
+@dataclass(frozen=True)
+class CostEstimate:
+    """Budget math, NOT a public tariff or proven model benchmark."""
+    gpu_compute_usd: Decimal
+    cpu_compute_usd: Decimal
+    storage_usd: Decimal
+    egress_usd: Decimal
+    total_usd: Decimal
+
+
+def estimate_cost(*, gpu_usd_hour: str, cpu_usd_hour: str, gpu_seconds: int,
+                  cold_start_seconds: int, cpu_seconds: int = 0,
+                  storage_gb: str = "0", storage_usd_gb: str = "0",
+                  egress_gb: str = "0", egress_usd_gb: str = "0") -> CostEstimate:
+    if any(type(v) is not int or v < 0 for v in (gpu_seconds, cold_start_seconds, cpu_seconds)):
+        raise MotionError("Invalid compute duration")
+    try:
+        g, c, s, sp, e, ep = [Decimal(v) for v in (
+            gpu_usd_hour, cpu_usd_hour, storage_gb, storage_usd_gb, egress_gb, egress_usd_gb)]
+    except Exception as exc:
+        raise MotionError("Invalid cost inputs") from exc
+    if not all(v.is_finite() and v >= 0 for v in (g, c, s, sp, e, ep)):
+        raise MotionError("Invalid nonnegative rate")
+    gpu = (g * Decimal(gpu_seconds + cold_start_seconds) / 3600)
+    cpu = (c * Decimal(cpu_seconds) / 3600)
+    storage = s * sp
+    egress = e * ep
+    total = gpu + cpu + storage + egress
+    return CostEstimate(*(v.quantize(Decimal("0.0001"), rounding=ROUND_UP) for v in
+                          (gpu, cpu, storage, egress, total)))
~~~~

## feature5_motion/cost_routing.py

~~~~diff
@@ -0,0 +1,72 @@
+"""Zero-premium-cost default for Feature5 motion workflow planning.
+
+This is a source-only, user-intent-preserving routing policy for the coordinator.
+It does not trigger Feature4 rendering or approve credit usage. A requested
+realistic walking model must NOT be represented by a stitched photo slideshow
+without explicit creative acceptance.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from decimal import Decimal, InvalidOperation
+
+from .azure_pricing import MotionSpendGuard
+from .contracts import MotionError
+
+
+@dataclass(frozen=True)
+class LowCostMotionDecision:
+    route: str   # EXISTING_FFMPEG, GPU_BUDGET_ELIGIBLE, DEFER
+    max_premium_usd: Decimal
+    reserved_quote_usd: Decimal | None
+    reason: str
+
+
+def _budget(amount) -> Decimal:
+    if isinstance(amount, bool):
+        raise MotionError("Invalid customer premium budget")
+    try:
+        budget = Decimal(str(amount))
+    except (ValueError, InvalidOperation, TypeError) as exc:
+        raise MotionError("Invalid customer premium budget") from exc
+    if not budget.is_finite() or budget < 0:
+        raise MotionError("Invalid customer premium budget")
+    return budget
+
+
+def plan_lowest_cost_delivery(*, requires_realistic_ai_motion: bool,
+                              existing_media_approved: bool,
+                              allow_paid_gpu: bool = False,
+                              max_premium_usd: str | Decimal = "0",
+                              guard: MotionSpendGuard | None = None) -> LowCostMotionDecision:
+    """Return cheapest *honest* route without scheduling billable compute.
+
+    Only paid motion-specific prompts require a GPU. Existing, rights-reviewed
+    stills/stock footage can be composed using the already deployed FFmpeg.
+    Real motion requests must DEFER rather than silently fake walking models.
+    An approved GPU quote is required even when a positive budget is passed.
+    """
+    if type(requires_realistic_ai_motion) is not bool or type(existing_media_approved) is not bool:
+        raise MotionError("Invalid creative approval or motion intent")
+    if type(allow_paid_gpu) is not bool:
+        raise MotionError("Invalid GPU authorization flag")
+    ceiling = _budget(max_premium_usd)
+    if not requires_realistic_ai_motion and existing_media_approved:
+        return LowCostMotionDecision(
+            "EXISTING_FFMPEG", ceiling, None, "Rights-approved existing media needs no premium motion inference")
+    if not requires_realistic_ai_motion and not existing_media_approved:
+        return LowCostMotionDecision(
+            "DEFER", ceiling, None, "No approved source media for free CPU composition")
+    if not allow_paid_gpu or ceiling == 0:
+        return LowCostMotionDecision(
+            "DEFER", ceiling, None, "Real AI motion requires separately approved paid inference")
+    if not isinstance(guard, MotionSpendGuard):
+        return LowCostMotionDecision(
+            "DEFER", ceiling, None, "Reviewed priced GPU quote is unavailable")
+    quote = guard.minimum_reservation_usd()
+    if quote > ceiling:
+        return LowCostMotionDecision(
+            "DEFER", ceiling, quote, "Worst-case GPU bill exceeds approved per-job budget")
+    return LowCostMotionDecision(
+        "GPU_BUDGET_ELIGIBLE", ceiling, quote,
+        "Budget preflight only; licence, media rights, tenant reservation, region and actual runner approval still required")
~~~~

## feature5_motion/demo_fashion.py

~~~~diff
@@ -0,0 +1,32 @@
+"""One genuine Hunyuan sample brief, not pre-rendered media.
+
+The 5-second, 480p portrait prompt is intentionally text-to-video so that
+reviewers do not need to transfer customer/product photos across regions.
+A generated clip MUST be produced by the separately licensed Hunyuan runner,
+then ffprobed, hashed, stored privately and HUMAN reviewed.
+"""
+from .contracts import MotionSpec
+
+FASHION_BRIEF_ID = "fashion-kurti-boutique-20261026"
+FASHION_PROMPT = (
+    "Cinematic full-body fashion commercial, one adult Indian female fashion "
+    "model wearing a premium deep-red embroidered festive kurti and matching "
+    "trousers, walking slowly and naturally toward the camera through an "
+    "elegant luxury Indian boutique. The same consistent red fabric, detailed "
+    "gold embroidered pattern and complete sleeves remain accurate throughout "
+    "the shot. Natural human gait, coherent face and hands, realistic fabric "
+    "folds and gentle dupatta movement. Warm chandelier lighting, polished "
+    "beige marble floor, premium clothing displays softly out of focus in "
+    "the background. Stable eye-level camera moving slightly backward, "
+    "photorealistic commercial cinematography, continuous single take, "
+    "no cuts, no subtitles, no watermarks."
+)
+
+
+def fashion_motion_spec(*, shop_id: str, job_id: str) -> MotionSpec:
+    """Create one server-authoritative T2V spec; never user-supplied identity."""
+    return MotionSpec(
+        job_id=job_id, shop_id=shop_id, prompt=FASHION_PROMPT,
+        mode="text", resolution="480p", aspect_ratio="9:16",
+        duration_seconds=5, fps=24, seed=20261026,
+    )
~~~~

## feature5_motion/empty_env_template.py

~~~~diff
@@ -0,0 +1,62 @@
+"""Immutable, narrowly scoped Azure environment-only deployment review.
+
+This module performs LOCAL JSON policy checks only. It cannot authenticate
+to Azure or deploy resources. The only permissible first-step resource is an
+unused, scale-to-zero, East US workload-profiles Container Apps environment.
+An existing DEV OIDC coordinator workflow must preview the ARM what-if and
+separately authorize the create. The Hunyuan GPU remains disabled.
+"""
+from __future__ import annotations
+import json
+from pathlib import Path
+from .contracts import MotionError
+
+TEMPLATE = Path(__file__).resolve().parent / "infra" / "empty_gpu_env.json"
+TARGET_RG = "rg-retailgrowth-dev"
+TARGET_ENV = "rgai-f5-gpu-canary-eastus"
+TARGET_TYPE = "Microsoft.App/managedEnvironments"
+EXPECTED_TAGS = {
+    "app": "RetailGrowthAI", "environment": "dev",
+    "feature": "feature5", "purpose": "zero-compute-gpu-quota-probe",
+}
+EXPECTED_PROPERTIES = {
+    "appLogsConfiguration": {"destination": "none"},
+    "workloadProfiles": [{"name": "Consumption", "workloadProfileType": "Consumption"}],
+}
+EXPECTED_KEYS = {"type", "apiVersion", "name", "location", "tags", "properties"}
+
+
+def validate_template(path: Path = TEMPLATE) -> dict:
+    source = Path(path)
+    if source.is_symlink() or not source.is_file() or source.stat().st_size > 12_000:
+        raise MotionError("Invalid feature5 isolated ARM template")
+    try:
+        obj = json.loads(source.read_text(encoding="utf-8"))
+    except (ValueError, UnicodeError) as exc:
+        raise MotionError("Unparseable ARM deployment plan") from exc
+    if type(obj) is not dict or obj.get("$schema") != (
+        "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"
+    ) or obj.get("parameters") or len(obj.get("resources", [])) != 1:
+        raise MotionError("Only one fixed empty DEV environment may be created")
+    res = obj["resources"][0]
+    if (type(res) is not dict or set(res) != EXPECTED_KEYS or
+        res["type"] != TARGET_TYPE or res["apiVersion"] != "2024-03-01" or
+        res["name"] != TARGET_ENV or res["location"] != "eastus" or
+        res["tags"] != EXPECTED_TAGS or res["properties"] != EXPECTED_PROPERTIES):
+        raise MotionError("Unexpected environment, GPU, log sink, region or paid workload")
+    return obj
+
+
+def validate_what_if(change_set: dict, subscription: str) -> None:
+    """Require exactly one ARM 'Create'; reject modify/delete/uncertain actions."""
+    if not isinstance(change_set, dict) or not isinstance(subscription, str) or len(subscription) != 36:
+        raise MotionError("Azure what-if or subscription is untrusted")
+    rows = change_set.get("changes", (change_set.get("properties") or {}).get("changes"))
+    if not isinstance(rows, list) or len(rows) != 1:
+        raise MotionError("Azure what-if did not show exactly one new resource")
+    target = (
+        "/subscriptions/" + subscription + "/resourcegroups/" + TARGET_RG +
+        "/providers/" + TARGET_TYPE + "/" + TARGET_ENV
+    ).lower()
+    if rows[0].get("changeType") != "Create" or str(rows[0].get("resourceId", "")).lower() != target:
+        raise MotionError("Azure what-if attempted other than isolated DEV environment creation")
~~~~

## feature5_motion/external_gpu_budget.py

~~~~diff
@@ -0,0 +1,180 @@
+"""Offline, read-only price qualification for a *possible* external GPU pilot.
+
+Does NOT provision GPU instances, authorize provider bills, claim verified
+capacity, run CUDA, or replace the existing Tencent source/weights/license gate.
+Operator reviews a provider ACCOUNT quote outside this package, then seals the
+exact bytes with an independently supplied SHA256.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import datetime, timedelta, timezone
+from decimal import Decimal, InvalidOperation, ROUND_UP
+from hashlib import sha256
+import json
+from pathlib import Path
+import re
+
+
+class ExternalQuoteError(ValueError):
+    """A quote cannot be treated as a safe bill estimate."""
+
+
+# Model minimum is 14 GiB *with offloading*. 24 GiB GPU and 40 GiB host
+# RAM are only screening floors, NOT certification that 480p T2V will fit.
+BF16_GPU_FAMILIES = {
+    "A100_80GB": 80,
+    "A40_48GB": 48,
+    "RTX_4090_24GB": 24,
+    "RTX_3090_24GB": 24,
+    "RTX_A5000_24GB": 24,
+    "A40_48GB": 48,
+    "RTX_A6000_48GB": 48,
+    "L4_24GB": 24,
+}
+PROVIDERS = frozenset({"runpod", "vast"})
+SHA256 = re.compile(r"^[0-9a-f]{64}$")
+
+
+def _money(value: object, *, name: str, min_value: Decimal = Decimal("0")) -> Decimal:
+    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
+        raise ExternalQuoteError(f"Invalid {name}")
+    try:
+        result = Decimal(str(value))
+    except (InvalidOperation, ValueError) as exc:
+        raise ExternalQuoteError(f"Invalid {name}") from exc
+    if not result.is_finite() or result < min_value or result > Decimal("1000"):
+        raise ExternalQuoteError(f"Out-of-range {name}")
+    return result
+
+
+def _utc_timestamp(text: object) -> datetime:
+    if not isinstance(text, str) or not text.endswith("Z"):
+        raise ExternalQuoteError("Quote time must be UTC with Z suffix")
+    try:
+        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
+    except ValueError as exc:
+        raise ExternalQuoteError("Invalid quote timestamp") from exc
+    if moment.utcoffset() != timedelta(0):
+        raise ExternalQuoteError("Quote timestamp must be UTC")
+    return moment
+
+
+def _no_duplicate_keys(pairs):
+    result = {}
+    for key, value in pairs:
+        if key in result:
+            raise ExternalQuoteError("Duplicate JSON quote key")
+        result[key] = value
+    return result
+
+
+@dataclass(frozen=True)
+class ExternalGpuQuoteEstimate:
+    provider: str
+    sku: str
+    region: str
+    country: str
+    max_seconds: int
+    provider_termination_after_seconds: int
+    cost_ceiling_usd: Decimal
+    approved_ceiling_usd: Decimal
+    status: str = "QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION"
+
+
+def assess_external_gpu_quote(quote: dict, *,
+                              max_seconds: int,
+                              provider_termination_after_seconds: int,
+                              ancillary_allowance_usd: str,
+                              approved_ceiling_usd: str,
+                              now: datetime | None = None) -> ExternalGpuQuoteEstimate:
+    """Calculate worst-case quote given *operator's* provider price evidence.
+
+    A quote is NOT verified capacity, hard provider-level spending limit,
+    geography/licensing clearance or permission to launch a paid instance.
+    Clock includes image/weights download, model startup, inference and exit.
+    """
+    if not isinstance(quote, dict):
+        raise ExternalQuoteError("Malformed external GPU quote")
+    required = {
+        "provider", "sku", "gpu_count", "system_ram_gib", "region",
+        "country", "billing_mode", "currency", "compute_usd_per_hour",
+        "storage_usd_per_hour", "minimum_billable_seconds",
+        "quoted_at", "expires_at",
+    }
+    if set(quote) != required:
+        raise ExternalQuoteError("Missing or unexpected quote fields")
+    if not isinstance(quote["provider"], str) or quote["provider"] not in PROVIDERS:
+        raise ExternalQuoteError("Unreviewed GPU provider")
+    if not isinstance(quote["sku"], str) or quote["sku"] not in BF16_GPU_FAMILIES:
+        raise ExternalQuoteError("Unreviewed GPU architecture/VRAM")
+    if type(quote["gpu_count"]) is not int or quote["gpu_count"] != 1:
+        raise ExternalQuoteError("Only one GPU is permissible")
+    if type(quote["system_ram_gib"]) is not int or quote["system_ram_gib"] < 40:
+        raise ExternalQuoteError("Insufficient advertised host RAM for screening")
+    if quote["billing_mode"] != "on_demand" or quote["currency"] != "USD":
+        raise ExternalQuoteError("Use USD on-demand non-spot prices only")
+    if (not isinstance(quote["region"], str) or
+        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,49}", quote["region"])):
+        raise ExternalQuoteError("Exact region identifier required")
+    if (not isinstance(quote["country"], str) or
+        not re.fullmatch(r"[A-Z]{2}", quote["country"])):
+        raise ExternalQuoteError("Exact ISO country code required")
+    quoted = _utc_timestamp(quote["quoted_at"])
+    expiry = _utc_timestamp(quote["expires_at"])
+    now = now or datetime.now(timezone.utc)
+    if not (quoted <= now <= expiry and expiry > quoted and expiry - quoted <= timedelta(hours=24)):
+        raise ExternalQuoteError("Price quote expired, future-dated or too long-lived")
+    if type(max_seconds) is not int or not 60 <= max_seconds <= 1800:
+        raise ExternalQuoteError("Single CUDA attempt must be bounded to <=1800 seconds")
+    if (type(provider_termination_after_seconds) is not int or
+        not max_seconds + 60 <= provider_termination_after_seconds <= 3600):
+        raise ExternalQuoteError("Provider must auto-terminate within one hour, after a safe exit margin")
+    minimum = quote["minimum_billable_seconds"]
+    if type(minimum) is not int or not 0 <= minimum <= 1800:
+        raise ExternalQuoteError("Invalid provider minimum billing period")
+    rate = _money(quote["compute_usd_per_hour"], name="GPU rate",
+                  min_value=Decimal("0.01"))
+    storage = _money(quote["storage_usd_per_hour"], name="storage hourly rate")
+    ancillary = _money(ancillary_allowance_usd, name="ancillary allowance")
+    cap = _money(approved_ceiling_usd, name="operator ceiling",
+                 min_value=Decimal("0.01"))
+    # Pod rent can continue AFTER the Python subprocess finishes or fails.
+    # Price the provider-side auto-termination bound, not the script timeout.
+    billed = max(provider_termination_after_seconds, minimum)
+    worst = ((rate + storage) * Decimal(billed) / Decimal(3600) + ancillary)
+    worst = worst.quantize(Decimal("0.0001"), rounding=ROUND_UP)
+    if worst > cap:
+        raise ExternalQuoteError("Estimated all-in rental exposure exceeds approved cap")
+    return ExternalGpuQuoteEstimate(
+        provider=quote["provider"], sku=quote["sku"],
+        region=quote["region"], country=quote["country"],
+        max_seconds=max_seconds,
+        provider_termination_after_seconds=provider_termination_after_seconds,
+        cost_ceiling_usd=worst,
+        approved_ceiling_usd=cap,
+    )
+
+
+def read_approved_external_quote(path: Path, *, approved_sha256: str) -> dict:
+    """Read exact vendor-account quote bytes, SHA pinned out of band.
+
+    A digest prevents accidental file drift; the operator must independently
+    verify quote origin and actual pricing. No network, provider or az calls.
+    """
+    file = Path(path)
+    if not isinstance(approved_sha256, str) or not SHA256.fullmatch(approved_sha256):
+        raise ExternalQuoteError("Independent reviewed price-file SHA256 required")
+    if file.is_symlink() or not file.is_file() or not 0 < file.stat().st_size < 16384:
+        raise ExternalQuoteError("Quote must be a small ordinary local file")
+    raw = file.read_bytes()
+    if sha256(raw).hexdigest() != approved_sha256:
+        raise ExternalQuoteError("Price quote SHA256 differs from approved bytes")
+    try:
+        parsed = json.loads(raw.decode("utf-8"),
+                            object_pairs_hook=_no_duplicate_keys)
+    except (UnicodeError, ValueError) as exc:
+        raise ExternalQuoteError("Quote cannot be decoded safely") from exc
+    if not isinstance(parsed, dict):
+        raise ExternalQuoteError("Price quote root must be an object")
+    return parsed
~~~~

## feature5_motion/infra/empty_gpu_env.json

~~~~diff
@@ -0,0 +1,35 @@
+{
+  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
+  "contentVersion": "1.0.0.0",
+  "resources": [
+    {
+      "type": "Microsoft.App/managedEnvironments",
+      "apiVersion": "2024-03-01",
+      "name": "rgai-f5-gpu-canary-eastus",
+      "location": "eastus",
+      "tags": {
+        "app": "RetailGrowthAI",
+        "environment": "dev",
+        "feature": "feature5",
+        "purpose": "zero-compute-gpu-quota-probe"
+      },
+      "properties": {
+        "appLogsConfiguration": {
+          "destination": "none"
+        },
+        "workloadProfiles": [
+          {
+            "name": "Consumption",
+            "workloadProfileType": "Consumption"
+          }
+        ]
+      }
+    }
+  ],
+  "outputs": {
+    "environmentName": {
+      "type": "string",
+      "value": "rgai-f5-gpu-canary-eastus"
+    }
+  }
+}
~~~~

## feature5_motion/interop.py

~~~~diff
@@ -0,0 +1,221 @@
+"""Feature 5 bridge to the existing Part 3 premium job/ledger semantics.
+
+No independent database, booking, credits or queue. Every value comes from
+an existing *server-side* claim, approved campaign and tenant media resolver.
+Shared DB migrations and live RPC bindings remain coordinator-owned.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from dataclasses import dataclass
+from decimal import Decimal, InvalidOperation
+from typing import Protocol
+from uuid import UUID
+
+from .contracts import MotionError, MotionSpec, canonical_uuid
+from .quality_review import VisualReview
+
+HUNYUAN_MODEL = "hunyuanvideo-1.5-480p"
+FEATURE4_VERSION = "creative_reel_v1"
+
+
+def _money(value) -> Decimal:
+    if type(value) is bool:
+        raise MotionError("Invalid premium reservation")
+    try:
+        amount = Decimal(str(value))
+    except (InvalidOperation, TypeError, ValueError) as exc:
+        raise MotionError("Invalid premium reservation") from exc
+    if not amount.is_finite() or amount <= 0 or amount > 1000:
+        raise MotionError("Invalid premium reservation")
+    return amount
+
+
+def planned_motion_key(shop_id: str, campaign_day_id: str, source_asset_id: str | None,
+                       prompt_version: str, mode: str, model_id: str, *,
+                       approved_prompt_sha256: str, seed: int = 1) -> str:
+    """Deterministic key for coordinator's EXISTING shop-scoped reservation.
+
+    Does not create any reservation, and never contains private media URLs.
+    """
+    canonical_uuid(shop_id)
+    canonical_uuid(campaign_day_id)
+    if source_asset_id is not None:
+        canonical_uuid(source_asset_id)
+    if mode not in ("text", "image", "poster") or model_id != HUNYUAN_MODEL:
+        raise MotionError("Unapproved premium model or mode")
+    if prompt_version != "feature5-v1":
+        raise MotionError("Unreviewed prompt version")
+    if (type(approved_prompt_sha256) is not str or len(approved_prompt_sha256) != 64
+        or any(c not in "0123456789abcdef" for c in approved_prompt_sha256)):
+        raise MotionError("Approved creative prompt hash required for idempotency")
+    if type(seed) is not int or not 0 <= seed < 2 ** 32:
+        raise MotionError("Invalid generation seed")
+    # Changing approved copy, seed or source creates a NEW logical request;
+    # retries of the same approved creative reuse the existing job/reservation.
+    values = ["feature5-lease-v2", shop_id, campaign_day_id, source_asset_id,
+              prompt_version, mode, model_id, approved_prompt_sha256, seed]
+    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()
+
+
+def verified_claim_to_motion(raw: dict) -> tuple[MotionSpec, Decimal]:
+    """Translate a transactionally claimed Part3 row, never a browser payload.
+
+    A real coordinator must atomically lease the row and reserve existing
+    shop_usage_reservations before invoking this function. No client-supplied
+    claim may be accepted.
+    """
+    if type(raw) is not dict:
+        raise MotionError("Missing service-only premium claim")
+    required = {
+        "id", "shop_id", "attempt_token", "model_id", "mode", "prompt",
+        "source_asset_id", "resolution", "seconds", "status", "review_status",
+        "reserved_usd", "reservation_id", "idempotency_key", "prompt_version",
+        "rights_approved", "user_approved", "subscription_active",
+    }
+    if required - raw.keys():
+        raise MotionError("Premium claim missing authoritative fields")
+    if raw["model_id"] != HUNYUAN_MODEL or raw["status"] != "RUNNING":
+        raise MotionError("Wrong model or unclaimed motion job")
+    if raw["review_status"] != "APPROVED" or raw["rights_approved"] is not True or raw["user_approved"] is not True or raw["subscription_active"] is not True:
+        raise MotionError("Motion not approved by tenant or subscription")
+    canonical_uuid(raw["attempt_token"])
+    canonical_uuid(raw["reservation_id"])
+    key = raw["idempotency_key"]
+    if type(key) is not str or len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
+        raise MotionError("Invalid persisted idempotency key")
+    price = _money(raw["reserved_usd"])
+    # Reject WAN's incompatible provider settings rather than silently convert.
+    if raw["resolution"] != "480p" or type(raw["seconds"]) is not int or raw["seconds"] != 5:
+        raise MotionError("Unapproved model quality or duration settings")
+    mode = raw["mode"]
+    spec = MotionSpec(
+        job_id=raw["id"], shop_id=raw["shop_id"], prompt=raw["prompt"],
+        mode=mode, source_asset_id=raw["source_asset_id"],
+        duration_seconds=raw["seconds"], resolution=raw["resolution"],
+        seed=raw.get("seed", 1), prompt_version=raw["prompt_version"],
+    )
+    return spec, price
+
+
+@dataclass(frozen=True)
+class ApprovedMotionClip:
+    """Backend-attested media after actual Hunyuan inference AND human review."""
+    job_id: str
+    shop_id: str
+    clip_asset_id: str
+    attempt_token: str
+    storage_path: str
+    status: str
+    provenance: str
+    quality_status: str
+    output_codec: str
+    rights_approved: bool
+    duration_seconds: float
+
+    def __post_init__(self):
+        for value in (self.job_id, self.shop_id, self.clip_asset_id, self.attempt_token):
+            canonical_uuid(value)
+
+
+def feature4_asset_entry(clip: ApprovedMotionClip, *,
+                         shop_id: str, local_staged_path: str, rights: dict,
+                         review: VisualReview | None = None,
+                         actual_media_sha256: str | None = None,
+                         reviewer_has_write_role: bool = False) -> tuple[str, dict]:
+    """Mint Feature4's SERVER-TRUSTED manifest entry; never accept browser data.
+
+    Feature4 still independently validates staged bytes, rights, signatures,
+    FPS/codec and timeline trim. The signed media URL stays in backend storage.
+    """
+    canonical_uuid(shop_id)
+    expected = f"{shop_id}/renders/{clip.job_id}/{clip.attempt_token}.mp4"
+    if (clip.shop_id != shop_id or clip.storage_path != expected or
+        clip.status != "SUCCEEDED" or clip.provenance != HUNYUAN_MODEL or
+        clip.quality_status != "APPROVED" or clip.rights_approved is not True or
+        clip.output_codec != "h264" or not 4.5 <= clip.duration_seconds <= 5.5):
+        raise MotionError("Premium clip has not passed private and visual approval")
+    # A status bit from a media row alone is insufficient. Require the
+    # coordinator's independently loaded, immutable human review bound
+    # to the exact stored clip hash and an authenticated reviewer role.
+    if (not isinstance(review, VisualReview) or review.job_id != clip.job_id
+        or review.output_asset_id != clip.clip_asset_id):
+        raise MotionError("Matching authoritative visual review is required")
+    review.approved_for_feature4(
+        authoritative_shop_id=shop_id,
+        actual_media_sha256=actual_media_sha256,
+        reviewer_has_write_role=reviewer_has_write_role,
+    )
+    # Matches Feature4's actual render.validate_rights contract exactly.
+    if (not isinstance(rights, dict) or rights.get("commercial_use") is not True or
+        rights.get("license") not in {"owned", "cc0", "royalty_free", "commercial"} or
+        not isinstance(rights.get("evidence"), str) or not rights["evidence"].strip() or
+        not isinstance(rights.get("source"), str) or not rights["source"].strip()):
+        raise MotionError("Motion rights do not permit campaign composition")
+    # A local path is produced only by the existing private, server-side media
+    # importer. Reject absolute paths, traversal, URL schemes, and weird chars.
+    if (type(local_staged_path) is not str or not local_staged_path.endswith(".mp4") or
+        len(local_staged_path) > 200 or local_staged_path.startswith(("/", "\\")) or
+        any(part in ("", ".", "..") for part in local_staged_path.split("/")) or
+        ":" in local_staged_path or "\\" in local_staged_path):
+        raise MotionError("Unsafe Feature4 staged media reference")
+    # Feature4 REF_PATTERN permits UUID strings as media IDs.
+    return clip.clip_asset_id, {
+        "shop_id": shop_id,
+        "kind": "video",
+        "source_feature": "feature5",
+        "approved": True,
+        "path": local_staged_path,
+        "rights": dict(rights),
+    }
+
+
+def feature4_scene(clip_asset_id: str, *, order: int, start_time: int,
+                   headline: str, duration: int = 5) -> dict:
+    canonical_uuid(clip_asset_id)
+    if (type(order) is not int or not 0 <= order <= 11 or
+        type(start_time) is not int or start_time < 0 or
+        type(duration) is not int or not 1 <= duration <= 5 or
+        type(headline) is not str or not 1 <= len(headline) <= 110):
+        raise MotionError("Invalid reviewed Feature4 scene")
+    # Do not invent/promote a discount here: Feature4 checks approved copy.
+    return {"order": order, "start_time": start_time, "duration": duration,
+            "asset_id": clip_asset_id, "asset_type": "video",
+            "source_feature": "feature5", "motion_status": "ready",
+            "headline": headline, "mute_source": True}
+
+
+class ExistingPart3Ledger(Protocol):
+    """Coordinator-owned transactional service-role RPC; NOT implemented here."""
+    def claim_authorized_motion(self, job_id: str) -> dict | None: ...
+    def complete_motion(self, job_id: str, attempt_token: str, receipt: dict) -> bool: ...
+    def fail_motion(self, job_id: str, attempt_token: str, category: str) -> bool: ...
+    def unknown_motion(self, job_id: str, attempt_token: str, category: str) -> bool: ...
+
+
+class Part3MotionStoreAdapter:
+    """Injection-only wrapper around the EXISTING shared Part3 ledger RPCs."""
+    def __init__(self, ledger: ExistingPart3Ledger):
+        self.ledger = ledger
+
+    def claim(self, job_id: str) -> dict | None:
+        jid = canonical_uuid(job_id)
+        row = self.ledger.claim_authorized_motion(jid)
+        if row is None:
+            return None
+        spec, price = verified_claim_to_motion(row)
+        if spec.job_id != jid:
+            raise MotionError("Part3 ledger returned a foreign job")
+        return {"spec": spec, "attempt_token": row["attempt_token"],
+                "reserved_usd": price, "review_status": "APPROVED",
+                "reservation_id": row["reservation_id"]}
+
+    def complete(self, job_id: str, attempt_token: str, media_record: dict) -> bool:
+        return bool(self.ledger.complete_motion(canonical_uuid(job_id), canonical_uuid(attempt_token), media_record))
+
+    def fail(self, job_id: str, attempt_token: str, category: str) -> bool:
+        return bool(self.ledger.fail_motion(canonical_uuid(job_id), canonical_uuid(attempt_token), category))
+
+    def mark_unknown(self, job_id: str, attempt_token: str, category: str) -> bool:
+        return bool(self.ledger.unknown_motion(canonical_uuid(job_id), canonical_uuid(attempt_token), category))
~~~~

## feature5_motion/license_gate.py

~~~~diff
@@ -0,0 +1,62 @@
+"""HunyuanVideo 1.5 license activation policy, defense in depth.
+
+This is NOT legal certification or reliable geoblocking. The deployment
+coordinator must independently verify Tencent's then-current actual terms,
+AUP, all distribution territories, recipients, provider notices and identities.
+"""
+from __future__ import annotations
+from dataclasses import dataclass
+from .contracts import MotionError
+
+# European Union members (ISO 3166-1 alpha-2), UK, South Korea.
+EXCLUDED_COUNTRIES = frozenset({
+    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
+    "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
+    "RO", "SK", "SI", "ES", "SE", "GB", "KR",
+})
+LICENSE_URL = "https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE"
+
+
+@dataclass(frozen=True)
+class HunyuanLicensePolicy:
+    """Values must be loaded from verified operator/backend records.
+
+    Owner approval permits DEV spend but does not issue Tencent license rights.
+    This assertion is a required reviewed gate, not legal certification.
+    """
+    deployment_country: str
+    retailer_country: str
+    intended_publication_countries: tuple[str, ...]
+    actual_provider_legal_name: str
+    tencent_no_endorsement_notice: bool
+    full_license_terms_available_to_users: bool
+    acceptable_use_and_local_law_checked: bool
+    commercial_media_rights_checked: bool
+    operator_terms_reviewed: bool
+    monthly_active_users_at_model_release: int
+    separate_tencent_license_if_required: bool = False
+
+    def assert_allowed(self) -> None:
+        countries = (self.deployment_country, self.retailer_country,
+                     *self.intended_publication_countries)
+        if not countries or not self.intended_publication_countries:
+            raise MotionError("Unreviewed deployment/publication territory")
+        if any(type(c) is not str or len(c) != 2 or not c.isupper()
+               or not c.isalpha() or c in EXCLUDED_COUNTRIES for c in countries):
+            raise MotionError("Unlicensed Hunyuan territory or country")
+        if (type(self.actual_provider_legal_name) is not str or
+            not 3 <= len(self.actual_provider_legal_name.strip()) <= 180):
+            raise MotionError("Actual video service provider disclosure missing")
+        for gate in (self.tencent_no_endorsement_notice,
+                     self.full_license_terms_available_to_users,
+                     self.acceptable_use_and_local_law_checked,
+                     self.commercial_media_rights_checked,
+                     self.operator_terms_reviewed):
+            if gate is not True:
+                raise MotionError("Hunyuan commercial license obligation not reviewed")
+        if (type(self.monthly_active_users_at_model_release) is not int or
+            self.monthly_active_users_at_model_release < 0):
+            raise MotionError("Licensing MAU eligibility unverified")
+        if (self.monthly_active_users_at_model_release > 100_000_000 and
+            self.separate_tencent_license_if_required is not True):
+            raise MotionError("Separate Tencent commercial license required")
~~~~

## feature5_motion/quality_review.py

~~~~diff
@@ -0,0 +1,69 @@
+"""Reviewer-facing Feature5 quality gate; visual assessment is never automated.
+
+The existing coordinator must persist this human decision with user JWT,
+tenant approval permissions, immutable media hash and an audit timestamp.
+Passing machine ffprobe alone NEVER results in approval for Feature4.
+"""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from uuid import UUID
+from .contracts import MotionError, canonical_uuid
+
+CATEGORIES = (
+    "human_anatomy", "smooth_motion", "garment_color", "garment_pattern",
+    "sleeve_and_shape", "face_consistency", "temporal_consistency",
+    "background_continuity", "frame_stability", "camera_motion",
+    "product_claim_accuracy",
+)
+
+
+@dataclass(frozen=True)
+class VisualReview:
+    shop_id: str
+    job_id: str
+    source_asset_id: str | None
+    output_asset_id: str
+    reviewer_user_id: str
+    reviewed_sha256: str
+    checks: dict
+    decision: str
+    notes: str
+    ai_disclosure_approved: bool
+
+    def __post_init__(self):
+        for value in (self.shop_id, self.job_id, self.output_asset_id, self.reviewer_user_id):
+            canonical_uuid(value)
+        if self.source_asset_id is not None:
+            canonical_uuid(self.source_asset_id)
+        if type(self.reviewed_sha256) is not str or len(self.reviewed_sha256) != 64 or any(
+            ch not in "0123456789abcdef" for ch in self.reviewed_sha256
+        ):
+            raise MotionError("Missing immutable clip hash for visual review")
+        if self.decision not in ("APPROVED", "REJECTED"):
+            raise MotionError("Human quality decision required")
+        if type(self.checks) is not dict or set(self.checks) != set(CATEGORIES):
+            raise MotionError("Incomplete visual acceptance checklist")
+        if any(type(v) is not bool for v in self.checks.values()):
+            raise MotionError("Each visual check must be manually assessed")
+        if type(self.notes) is not str or len(self.notes.strip()) < 12 or len(self.notes) > 1000:
+            raise MotionError("Reviewer explanation required")
+        if type(self.ai_disclosure_approved) is not bool:
+            raise MotionError("Disclosure review required")
+
+    def approved_for_feature4(self, *, authoritative_shop_id: str, actual_media_sha256: str,
+                              reviewer_has_write_role: bool) -> bool:
+        canonical_uuid(authoritative_shop_id)
+        if authoritative_shop_id != self.shop_id or reviewer_has_write_role is not True:
+            raise MotionError("Reviewer is not authorized for this tenant")
+        if actual_media_sha256 != self.reviewed_sha256:
+            raise MotionError("Clip changed after the visual review")
+        if (self.decision != "APPROVED" or not all(self.checks.values()) or
+            self.ai_disclosure_approved is not True):
+            raise MotionError("Visual quality or AI disclosure not approved")
+        return True
+
+
+def review_template() -> dict:
+    """Fail-closed checklist; pending reviewer must fill every criterion."""
+    return {name: False for name in CATEGORIES}
~~~~

## feature5_motion/runner.py

~~~~diff
@@ -0,0 +1,166 @@
+"""Optional official HunyuanVideo 1.5 local CLI adapter. No network endpoints.
+
+    Uses an ALREADY installed, already licensed and locally staged official
+    inference implementation. This does not download weights or provision GPUs.
+"""
+from __future__ import annotations
+
+import os
+import hashlib
+from pathlib import Path
+import signal
+import subprocess
+import sys
+
+from .contracts import MotionError, MotionSpec
+from .license_gate import HunyuanLicensePolicy
+from .artifact_lock import ArtifactLock
+
+
+# Independently fetched from Tencent-Hunyuan/HunyuanVideo-1.5 GitHub
+# commit 60783e704160023913bee78f0b47036d393d4dfa, generate.py Git blob:
+# ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d (2026-10-26).
+# This attests script bytes ONLY; model weights still need separately
+# licensed version/checksum evidence before true inference activation.
+OFFICIAL_COMMIT = "60783e704160023913bee78f0b47036d393d4dfa"
+OFFICIAL_GENERATE_BLOB = "ba18ce85661d2cc2ebfe5a7fe4ad80994899d07d"
+
+
+def git_blob_sha1(path: Path) -> str:
+    """Git-object digest of a small local script, no git subprocess/network.
+
+    SHA1 is Git's legacy blob addressing scheme, not model-weight integrity
+    proof. The expected blob is fixed at code review, not read from checkout.
+    """
+    candidate = Path(path)
+    if candidate.is_symlink() or not candidate.is_file():
+        raise MotionError("Untrusted local model script")
+    size = candidate.stat().st_size
+    if not 0 < size <= 200_000:
+        raise MotionError("Unapproved local inference script size")
+    data = candidate.read_bytes()
+    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") +
+                        b"\0" + data).hexdigest()
+
+
+def verify_official_script(path: Path) -> None:
+    if git_blob_sha1(path) != OFFICIAL_GENERATE_BLOB:
+        raise MotionError("Hunyuan inference script is not pinned Tencent source")
+
+
+class HunyuanLocalRunner:
+    def __init__(self, *, checkout: Path, weights: Path, enabled: bool = False,
+                 license_approved: bool = False, gpu_budget_approved: bool = False,
+                 timeout_seconds: int = 1800,
+                 license_policy: HunyuanLicensePolicy | None = None,
+                 artifact_lock: ArtifactLock | None = None):
+        self.license_policy = license_policy
+        self.artifact_lock = artifact_lock
+        self.checkout = Path(checkout)
+        self.weights = Path(weights)
+        self.enabled = enabled
+        self.license_approved = license_approved
+        self.gpu_budget_approved = gpu_budget_approved
+        if type(timeout_seconds) is not int or not 30 <= timeout_seconds <= 3600:
+            raise MotionError("Invalid bounded GPU timeout")
+        self.timeout_seconds = timeout_seconds
+
+    @staticmethod
+    def _require_supported_gpu():
+        """Official default dtype is BF16, not native to older T4 hardware."""
+        try:
+            import torch
+            if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
+                raise MotionError("Approved CUDA BF16 GPU is unavailable")
+            memory = torch.cuda.get_device_properties(0).total_memory
+            if memory < 14 * 1024**3:
+                raise MotionError("Available GPU VRAM below model minimum")
+        except ImportError as exc:
+            raise MotionError("Pinned CUDA PyTorch runtime missing") from exc
+        except (RuntimeError, AttributeError) as exc:
+            raise MotionError("CUDA hardware cannot be verified safely") from exc
+
+    def run(self, spec: MotionSpec, *, source_file: Path | None, workdir: Path) -> Path:
+        if not (self.enabled and self.license_approved and self.gpu_budget_approved):
+            raise MotionError("Premium inference is disabled pending approvals")
+        if not isinstance(self.license_policy, HunyuanLicensePolicy):
+            raise MotionError("Reviewed Hunyuan license activation context missing")
+        self.license_policy.assert_allowed()
+        if spec.mode == "text" and source_file is not None:
+            raise MotionError("Unexpected text-mode source")
+        if spec.mode != "text" and source_file is None:
+            raise MotionError("Missing approved private source")
+        script = (self.checkout / "generate.py").resolve()
+        if not (script.is_file() and self.weights.is_dir()):
+            raise MotionError("Preinstalled licensed Hunyuan runtime/weights missing")
+        verify_official_script(script)  # Before any billable CUDA/model initialization.
+        if not isinstance(self.artifact_lock, ArtifactLock):
+            raise MotionError("Review-locked model and weights manifest required")
+        self.artifact_lock.verify(checkout=self.checkout, weights=self.weights)
+        if Path(workdir).is_symlink():
+            raise MotionError("Symlinked working directory is not permitted")
+        wd = Path(workdir).resolve(strict=True)
+        if not wd.is_dir():
+            raise MotionError("Invalid private working directory")
+        frame = None
+        if source_file is not None:
+            source = Path(source_file).resolve(strict=True)
+            if not source.is_file() or not source.is_relative_to(wd) or source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
+                raise MotionError("Source must be validated and staged inside private job directory")
+            if not 0 < source.stat().st_size <= 20 * 1024 * 1024:
+                raise MotionError("Source media exceeds approved staging size")
+            with source.open("rb") as stream:
+                signature = stream.read(16)
+            is_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
+            is_jpeg = signature.startswith(b"\xff\xd8\xff")
+            is_webp = signature.startswith(b"RIFF") and signature[8:12] == b"WEBP"
+            if not ((source.suffix.lower() == ".png" and is_png) or
+                    (source.suffix.lower() in (".jpg", ".jpeg") and is_jpeg) or
+                    (source.suffix.lower() == ".webp" and is_webp)):
+                raise MotionError("Staged image signature mismatch")
+            # Signatures are insufficient: verify actual image decoding and size
+            # before a potentially billable GPU launch. Do not mutate original.
+            try:
+                from PIL import Image, ImageOps
+                with Image.open(source) as image:
+                    w, h = image.size
+                    if not (128 <= w <= 4096 and 128 <= h <= 4096 and w * h <= 16_000_000):
+                        raise MotionError("Unapproved image dimensions")
+                    ImageOps.exif_transpose(image).load()
+            except (OSError, ValueError, Image.DecompressionBombError) as exc:
+                raise MotionError("Staged source image cannot be decoded safely") from exc
+            frame = str(source)
+        output = wd / "motion.mp4"
+        if output.exists():  # Never overwrite a previous successful/maybe-billable result.
+            raise MotionError("Motion output already exists")
+        # Fail before subprocess launch on older T4/non-BF16/missing CUDA GPUs.
+        self._require_supported_gpu()
+        # Explicitly disable external prompt rewriting and superresolution.
+        # Upstream generate.py must be version-pinned and verified before activation.
+        # Tencent's generate.py selects image mode if --image_path is present.
+        # Never pass the literal string "none" for text-to-video.
+        args = [sys.executable, str(script), "--prompt", spec.prompt.strip(),
+                "--model_path", str(self.weights.resolve()),
+                "--resolution", spec.resolution, "--aspect_ratio", spec.aspect_ratio,
+                "--video_length", "121", "--offloading", "true",
+                "--seed", str(spec.seed), "--rewrite", "false", "--sr", "false",
+                "--output_path", str(output)]
+        if frame is not None:
+            args.extend(["--image_path", frame])
+        # Environment restricts automatic model/code downloads. Never capture
+        # unbounded child stdout/stderr (may contain sensitive prompts).
+        env = {k: v for k, v in os.environ.items()
+               if k not in ("RETAIL_WAN_API_KEY", "SUPABASE_SERVICE_ROLE_KEY")}
+        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
+        proc = subprocess.Popen(args, cwd=str(self.checkout.resolve()),
+                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
+                                stderr=subprocess.DEVNULL, start_new_session=True, env=env)
+        try:
+            proc.communicate(timeout=self.timeout_seconds)
+        except subprocess.TimeoutExpired as exc:
+            os.killpg(proc.pid, signal.SIGKILL)
+            proc.communicate()
+            raise MotionError("GPU job reached approved timeout") from exc
+        if proc.returncode != 0 or not output.is_file() or not 0 < output.stat().st_size <= 80 * 1024 * 1024:
+            raise MotionError("Local Hunyuan inference failed validation")
+        return output
~~~~

## feature5_motion/seal_artifacts.py

~~~~diff
@@ -0,0 +1,55 @@
+"""Offline operator helper to create (NOT approve) a model artifact candidate.
+
+Example:
+  python -m feature5_motion.seal_artifacts \
+    --checkout /sealed/hunyuan-code --weights /licensed/hunyuan-weights \
+    --out /restricted/feature5-v1.lock.json
+
+Review source commit, Tencent license, exact code/files, dependency lock and
+weight provenance. Store the printed manifest SHA256 in independently reviewed
+DEV deployment configuration, not inside the downloadable model directory.
+This script does not fetch code/weights, run CUDA, or grant commercial rights.
+"""
+from __future__ import annotations
+
+import argparse
+import hashlib
+import os
+from pathlib import Path
+
+from .artifact_lock import construct_manifest
+from .contracts import MotionError
+
+
+def create_candidate(*, checkout: Path, weights: Path, destination: Path) -> str:
+    raw = construct_manifest(checkout, weights)
+    output = Path(destination)
+    if output.is_symlink() or not output.parent.resolve(strict=True).is_dir():
+        raise MotionError("Lock output parent must already be a safe directory")
+    # Exclusive create; must not overwrite any already reviewed manifest.
+    fd = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
+    try:
+        with os.fdopen(fd, "wb") as target:
+            target.write(raw)
+            target.flush()
+            os.fsync(target.fileno())
+    except Exception:
+        output.unlink(missing_ok=True)
+        raise
+    return hashlib.sha256(raw).hexdigest()
+
+
+def main() -> None:
+    parser = argparse.ArgumentParser(description="Create offline, UNAPPROVED Hunyuan file lock")
+    parser.add_argument("--checkout", type=Path, required=True)
+    parser.add_argument("--weights", type=Path, required=True)
+    parser.add_argument("--out", type=Path, required=True)
+    options = parser.parse_args()
+    digest = create_candidate(
+        checkout=options.checkout, weights=options.weights, destination=options.out)
+    print("CANDIDATE ONLY — independent model license, supplier and hash review required")
+    print("Reviewed artifact manifest SHA256 (after independent approval):", digest)
+
+
+if __name__ == "__main__":
+    main()
~~~~

## feature5_motion/visual_review_artifacts.py

~~~~diff
@@ -0,0 +1,96 @@
+"""Private, ephemeral human-review contact sheet for real Hunyuan output.
+
+CPU-only evidence gathering. It NEVER auto-approves quality, uploads files,
+touches user-facing URLs, or changes the existing credit ledger. The trusted
+caller authorizes/stages local tenant media and disposes of review scratch.
+"""
+from __future__ import annotations
+
+import hashlib
+import json
+from pathlib import Path
+import shutil
+import subprocess
+
+from .contracts import MotionError
+from .worker import validate_clip
+
+TIMESTAMPS = ("0.20", "1.00", "2.00", "3.00", "4.00", "4.80")
+
+
+def _sha256(path: Path) -> str:
+    sha = hashlib.sha256()
+    with path.open("rb") as f:
+        for part in iter(lambda: f.read(1024 * 1024), b""):
+            sha.update(part)
+    return sha.hexdigest()
+
+
+def prepare_visual_review(clip: Path, output_dir: Path, *, ffmpeg="ffmpeg") -> dict:
+    """Extract representative PNG frames and a side-by-side local sheet.
+
+    Input is already authorized tenant-private local storage. Output is a new
+    empty 0700 private directory, owned/cleaned by the existing job service.
+    Return immutable clip sha256 for *later* independent tenant review.
+    """
+    clip = Path(clip)
+    if clip.is_symlink():
+        raise MotionError("Review input must not be a symlink")
+    clip = clip.resolve(strict=True)
+    info = validate_clip(clip)
+    out = Path(output_dir)
+    if out.exists() or out.is_symlink() or not out.parent.resolve(strict=True).is_dir():
+        raise MotionError("Review directory must be new and private")
+    out.mkdir(mode=0o700, exist_ok=False)
+    try:
+        from PIL import Image, ImageDraw
+        frames = []
+        thumbs = []
+        for i, timestamp in enumerate(TIMESTAMPS):
+            name = f"frame-{i:02d}.png"
+            target = out / name
+            cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
+                   "-threads", "1", "-ss", timestamp, "-protocol_whitelist", "file",
+                   "-i", str(clip), "-frames:v", "1", "-y", str(target)]
+            completed = subprocess.run(cmd, capture_output=True, timeout=25)
+            if completed.returncode or not target.is_file() or not 0 < target.stat().st_size <= 8_000_000:
+                raise MotionError("Unable to prepare a local reviewer frame")
+            with Image.open(target) as image:
+                image.verify()
+            with Image.open(target) as image:
+                if image.size != (info["width"], info["height"]):
+                    raise MotionError("Reviewer image dimensions mismatch validated clip")
+                thumb = image.convert("RGB")
+                thumb.thumbnail((240, 420))
+                thumbs.append(thumb.copy())
+            frames.append({"timestamp_seconds": timestamp, "file": name,
+                           "sha256": _sha256(target)})
+        width, height = 3 * 250, 2 * 455 + 44
+        board = Image.new("RGB", (width, height), (18, 18, 24))
+        draw = ImageDraw.Draw(board)
+        draw.text((12, 9), "HUMAN REVIEW REQUIRED - no automatic approval",
+                  fill=(230, 230, 230))
+        for i, thumb in enumerate(thumbs):
+            x, y = (i % 3) * 250 + 5, (i // 3) * 455 + 48
+            board.paste(thumb, (x, y))
+            draw.text((x + 5, y + thumb.height + 4),
+                      "t=" + TIMESTAMPS[i] + "s", fill=(230, 230, 230))
+        sheet_path = out / "contact-sheet.png"
+        board.save(sheet_path, format="PNG")
+        manifest = {
+            "status": "PENDING_HUMAN_REVIEW",
+            "clip_sha256": _sha256(clip),
+            "codec": info["codec"], "duration_seconds": info["duration_seconds"],
+            "width": info["width"], "height": info["height"],
+            "frames": frames, "contact_sheet": "contact-sheet.png",
+        }
+        (out / "review-manifest.json").write_text(
+            json.dumps(manifest, sort_keys=True, separators=(",", ":")),
+            encoding="utf-8",
+        )
+        return manifest
+    except Exception as exc:
+        shutil.rmtree(out, ignore_errors=True)
+        if isinstance(exc, MotionError):
+            raise
+        raise MotionError("Unable to prepare offline visual-review materials") from exc
~~~~

