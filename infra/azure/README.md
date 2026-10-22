# RetailGrowthAI Azure DEV infrastructure — PREPARATION ONLY

Nothing has been deployed or provisioned. Never use WineShopPOS resources, secrets or accounts.

## Low-cost proposed pilot

One Python 3.12 Flex Consumption Azure Functions app (2048 MiB, maximum 2 on-demand instances **per independently scaling function group**, no always-ready instances), plus one dedicated Standard_LRS GPv2 storage account with private package container and queues:
- retail-campaign-planning
- retail-reel-render

The merged queue adapter requires a server-only RETAIL_STORAGE connection string. AzureWebJobsStorage is likewise backend-only. Shared-key storage is enabled temporarily for compatibility; identity-based queue access requires a separate backend change. Frontend CORS permits only the exact configured HTTPS origin. Private tenant uploads and rendered MP4s remain in the existing RetailGrowthAI Supabase DEV, **not** public Azure blobs. Storage/Functions execution and logs can still incur charges; set subscription budget alerts before deployment.

## Offline, safe checks

Keep an edited private copy of dev.parameters.example.json OUTSIDE the repository with globally unique new DEV resource names and the HTTPS frontend origin.

~~~bash
bash scripts/deploy/check.sh
python scripts/deploy/package.py --check
~~~

The standard Python Functions host does not guarantee an FFmpeg executable. Obtain and audit approved **Linux x86_64** FFmpeg and ffprobe, with libx264, AAC, drawtext, xfade codecs and THIRD_PARTY_NOTICES.txt covering license compliance. The package builder refuses absent/unverified binaries and checks ELF architecture.

~~~bash
python scripts/deploy/package.py --ffmpeg-dir /approved/linux-amd64-bins --output .artifacts/retailgrowth-functions.zip
~~~

Package preserves the original repo-relative video-engine import depth by generating a root Functions wrapper; copies Python ai_agents module; adjusts generated host.json queue batchSize 1/newBatchThreshold 0/maxDequeueCount 3. It never modifies source code or makes a cloud call.

Optional Azure read-only preview, after setting a correct logged-in subscription and an existing dedicated DEV resource group:

~~~bash
export RETAIL_AZURE_DEV_RG=rg-retailgrowth-dev
export RETAIL_AZURE_SUBSCRIPTION_ID=expected-subscription-uuid
bash scripts/deploy/plan.sh /private/path/dev.parameters.json
~~~

Confirm Python 3.12 Flex Consumption availability in centralindia before provisioning.

## Future approval-gated manual deployment — DO NOT RUN NOW

Only after separate explicit resource/deployment/migration authorization:

~~~bash
export RETAIL_AZURE_DEPLOY_APPROVED=YES
bash scripts/deploy/apply-infra.sh --approve /private/path/dev.parameters.json
export RETAIL_AZURE_FUNCTION_NAME=approved-dev-function-name
bash scripts/deploy/deploy-code.sh --approve .artifacts/retailgrowth-functions.zip
~~~

Both scripts require explicit owner approval flags, matched subscription and a DEV resource group; they never create a resource group themselves. Add RETAIL_SUPABASE_URL, RETAIL_SUPABASE_PUBLISHABLE_KEY, and RETAIL_SUPABASE_SERVICE_ROLE_KEY only as protected backend settings/Key Vault references. Never commit real values or place service secrets in VITE variables. The Bicep siteConfig.appSettings is declarative: **reapplying it after adding secrets may overwrite those settings**. Require review first.

RELEASE BLOCKERS: pending Supabase DEV migrations; actual hosted auth/RLS/uploads/render/download E2E; CORS and secrets; FFmpeg licensing; budget and poison-queue alerting. A pending source-only follow-up aligns the Functions host timeout and planning/render DB leases with the 780-second FFmpeg cap; **do not deploy or apply migrations** until the whole revised budget is approved and measured on DEV. Test realistic 1080x1920 media and choose an approved Container Apps Jobs alternative if Flex is unsuitable. Current RETAIL_ENABLE_MOCK_CAMPAIGNS remains false: no real Azure AI Foundry provider is configured. CI does not prove cloud readiness.

## Worker execution time and lease alignment (source-only; do not deploy)
A coordinator follow-up proposes bounded 20-minute Flex Functions invocation and 25-minute planning/render DB leases in **pending** `20261022205000_p1_worker_execution_budget.sql`. FFmpeg remains capped at 780 seconds, leaving at most seven minutes of configured host time for media staging, output upload and bookkeeping (not a measured guarantee). The lease is five minutes longer than the host cap. Offline packaging fails closed if these specific limits drift; it cannot prove host reliability, Azure Queue retry correctness or actual 1080p performance.

The previous 4-minute lease/host vs 13-minute FFmpeg mismatch must **not** be deployed. Do not apply any pending migration or provision Azure without explicit approval. Before authorizing cloud rendering, complete benchmark, DB attempt-fenced completion, durable poison/recovery and platform-runtime validation.

## Workstream J — Azure Flex DEV readiness (2026-10-22; source only)

- **OIDC:** coordinator PR #30 verified read-only GitHub to Azure federation. That is not deployment approval or authorization for cloud writes.
- **Flex:** Bicep declares the Python 3.12 runtime only via `functionAppConfig.runtime` (not legacy `FUNCTIONS_WORKER_RUNTIME` or `FUNCTIONS_EXTENSION_VERSION` app settings on Flex). The DEV region is restricted to `centralindia`. The storage connection suffix uses `environment().suffixes.storage` rather than hardcoded cloud DNS. Verify Azure Functions host indexing after *separately approved* deployment; offline validation alone cannot prove runtime startup.
- **Cost ceilings:** DEV defaults to one on-demand instance per independently scaling function group, configurable only up to two through reviewed parameters; memory stays at 2048 MiB. No always-ready instances are configured. HTTP and the two queue handlers scale independently, so this is *not* an app-wide limit. Configure Azure budget alerts, queue poison/depth alerts and logging retention before enabling paid workloads. A cap on instances is not a hard monthly bill cap.
- **Queue and host:** packaged `host.json` still enforces a 20-minute worker timeout and queue batch size 1, threshold 0 and max dequeue 3. Planning/render lease is 25 minutes in an unapplied SQL migration. Workstream I owns durable outbox, poison acknowledgements and attempt fencing; without it, a poison event can strand a job.
- **FFmpeg packaging:** only approved static Linux x86_64 FFmpeg and ffprobe ELF binaries with `THIRD_PARTY_NOTICES.txt` are packaged; dynamic ELF interpreters are rejected. Package limit: 300 MiB ZIP and 400 MiB uncompressed. ZIP verification rejects missing executables, missing executable permissions, tampered host/queue limits, corrupt archives and unsafe paths. Use `python scripts/deploy/package.py --verify-zip /private/path/package.zip` before any approved deployment.
- **Unverified dependencies:** these checks cannot guarantee libx264, AAC, drawtext, xfade, DejaVu Sans/fontconfig, binary provenance, or realistic 1080x1920 CPU/RAM/scratch/render duration on Flex. Independently verify on a trusted Linux host; then benchmark licensed assets on a separately approved isolated DEV setup before enabling real rendering.
- **Offline test:** `bash scripts/deploy/check.sh` runs package and infra policy tests; Azure Bicep compilation runs when local Azure CLI is available. Remote Python dependency build and Functions host/trigger startup need later approved live testing.

**No provisioning, deployment, Supabase migration or WineShopPOS changes were performed in Workstream J.**

## Workstream M — read-only release gates

See [RELEASE_READINESS.md](RELEASE_READINESS.md) for scoped OIDC service-principal IAM inspection, hosted Flex/runtime/queue/poison and cost-budget preflight, fail-closed offline security tests, and protected rollback artifacts. Azure CLI checks are **read-only** and not automatically run by PR CI; hosted DEV inventory remains unverified until independently authorized. The code-deployment approval script now also demands an approved first-release designation or a retained, separately validated known-good ZIP for recovery. No deployment or Azure provisioning was performed.
