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

RELEASE BLOCKERS: pending Supabase DEV migrations; actual hosted auth/RLS/uploads/render/download E2E; CORS and secrets; FFmpeg licensing; budget and poison-queue alerting. The current Functions host timeout and render DB lease are 4 minutes, but render subprocess timeout is 780 seconds. Test realistic 1080x1920 renders before deploying or accepting render messages. If renders exceed the lease or host timeout, use an approved Container Apps Jobs alternative or coordinate an updated lease protocol. Current RETAIL_ENABLE_MOCK_CAMPAIGNS remains false: no real Azure AI Foundry provider is configured. CI does not prove cloud readiness.

## Worker execution time and lease alignment (source-only; do not deploy)
A coordinator follow-up proposes bounded 20-minute Flex Functions invocation and 25-minute planning/render DB leases in **pending** `20261022205000_p1_worker_execution_budget.sql`. FFmpeg remains capped at 780 seconds, leaving at most seven minutes of configured host time for media staging, output upload and bookkeeping (not a measured guarantee). The lease is five minutes longer than the host cap. Offline packaging fails closed if these specific limits drift; it cannot prove host reliability, Azure Queue retry correctness or actual 1080p performance.

The previous 4-minute lease/host vs 13-minute FFmpeg mismatch must **not** be deployed. Do not apply any pending migration or provision Azure without explicit approval. Before authorizing cloud rendering, complete benchmark, DB attempt-fenced completion, durable poison/recovery and platform-runtime validation.
