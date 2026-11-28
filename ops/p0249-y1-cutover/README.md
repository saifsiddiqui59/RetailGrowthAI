# Y1 full backend migration — protected cutover workstream (#249)

**This PR prepares code; it does not deploy Y1 or disable Flex.**

## Existing live evidence (2026-11-22)
Protected Y1 run [#45021333842](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/45021333842) deployed exactly five read-only functions. Indexed **5/5**, public HTTP **20/20 twice** separated by 240 seconds and unauthenticated **8/8 401**. It did not install any write handlers, render/queue consumers, timer recovery, billing parity or frontend cutover. Original Flex remains the worker and write host.

## New HTTP artifact (source only)

`ops/p0249-y1-cutover/prepare_http_only.py --check` audits the existing original Flex `function_app.py` and expects exactly its 37 reviewed original HTTP handler registrations and nine original background registrations (38 HTTP including the added Y1 health route). It refuses new/unreviewed registrations. For a prebuilt, **already-verified** existing Flex release ZIP, `--source-zip ... --output-zip ...` rewrites only the nested `azure-functions/campaign-api/function_app.py`, removing **all nine** `@app.queue_trigger` and `@app.timer_trigger` registrations and preserving HTTP handlers, original JWT/RLS tenant code, `HTTPAPI`, durable outbox/queue writes and exact reviewed packaged dependencies. It re-adds the original Y1 health route with the same response/marker. The **input Flex ZIP** must pass the original builder's independent package/FFmpeg/license verification. The converted Y1 output is independently checked for the exact allowed handler/host changes and byte/metadata identity on all other members; the original builder's Flex-only 20-minute host assertion does not apply to the Consumption output. No Azure writes.

**This is an intermediate stage:** Y1 HTTP requests can in principle enqueue to the existing authorized `RETAIL_STORAGE` queues while *Flex remains the only worker owner*. The artifact does not index a second timer or queue consumer, but HTTP parity is not live until separate protected deployment, configuration and real signed verification. The Y1 artifact preserves unchanged original backend API logic; this does not assert that all optional Feature2/3/4/VoiceStudio routes are ready or enabled.

## Actual connections required before Flex retirement

1. **Authorization/data:** Same dedicated Supabase DEV URL, public JWT verifier and server-only service key. Verify fresh signed JWT, current OWNER/EDITOR/VIEWER RLS, own/foreign/revoked reads, campaign writes, subscription/quotas, private media downloads, no redirects or other-project access.
2. **HTTP API:** Y1 has all required indexed GET/POST/PATCH and feature-specific enabled paths, original response/body/error semantics, exact trusted CORS origin and frontend routing. Exercise original POST/PATCH, jobs, media rights and both successful/failed cases.
3. **Durable jobs:** Reuse only existing DEV `RETAIL_STORAGE` queues (`retail-campaign-planning`, `retail-reel-render`, `retail-poster-render`, poison queues) and one authoritative PostgreSQL outbox/claim/lease/quota ledger. Do not enable Y1 background functions while Flex background functions are active in a way that permits duplicate timer/poison or conflicting reconciliation. Audit backlog, in-flight claims, retries and billing idempotency.
4. **Worker transition:** Deploy and separately verify Y1's **eight short planning/poster/poison/recovery/trends queue/timer consumers** with the reviewed 9-minute classic Consumption host cap and least-privilege credentials. Transfer the original 780-second FFmpeg/video queue renderer to a **separately verified 1380-second CPU Container Apps Job**, never to classic Y1 (maximum 600 seconds). Controlled single-owner handoff with rollback; no dead queue, duplicate consumers or billable double processing.
5. **Traffic and reliability:** After signed Y1 functional E2E, switch *every* Free SWA DEV API source from Flex hostname to Y1 hostname; inspect served deployed JS/config, rather than trusting source flags. Verify 503 cold/warm, p95/p99, media/queue latency, 240s idle, no pending jobs and a functional rollback to original before stopping Flex. Then stop only **the exact original RetailGrowthAI DEV Flex Function App**, monitor, validate after stop, and optionally retire the Flex plan only under a separate guarded owner-authorized Azure change.

## Stop/close decision

Do NOT disable `rgai-dev-functions-d4e5ddbd` or delete `rgai-dev-flex` now. The live Y1 package is GET-only and would cause an outage. Do NOT close #249 until hosted Y1 fully replaces the original connection paths, its workers are proven, old Flex is no longer routing traffic, and independent post-cutover health/rollback/latency acceptance passes. The user's other chat owns campaign test execution: this branch only prepares Y1 host packaging and connection ownership, not duplicate shop fixtures.

No PROD, GPU, paid provider, WineShopPOS or global auth approval mutation.

## Source-only retirement evidence checker

`ops/p0249-y1-cutover/retirement_gate.py --diagnostic-json <path>` checks the exact dedicated Y1/Flex/Free-SWA/Supabase scope, backend appsetting NAMES, protected comparison of secret VALUES in the trusted runner, original HTTP+queue+timer indexing, observed browser routing, single-worker ownership, queue reconciliation, and hosted two-shop RLS/write/private-download/billing/p95/p99/rollback receipts. It emits only missing gate names, never a secret or shop identifier. The existing live five-GET Y1 deployment correctly reports **BLOCKED_DO_NOT_STOP**. Even fully asserted JSON produces **BLOCKED_PENDING_PROTECTED_AZURE_ACCEPTANCE**: real Azure protected runner provenance cannot be established by JSON, and this script has no Azure stop/delete/issue-close operation.

After real Y1 worker transfer, Azure Functions supports per-function disable app settings `AzureWebJobs.<FunctionName>.Disabled=true` (see [Microsoft guidance](https://learn.microsoft.com/azure/azure-functions/disable-function)). The handoff must verify these are effective on the real hosts with index/queue observations, never assume setting-name presence means disabled. Do not apply worker-disable settings, stop Flex, or switch frontend until all independent evidence gates are accepted.

## On-demand CPU reel worker and safe DEV connection inspection — source only

- `cpu_render_job.py` is a one-message, CPU-only adapter for a future **scale-to-zero Azure Container Apps Job**, not an Azure Functions classic Consumption trigger. It uses the existing `retail-reel-render` queue and original authenticated `AdminStore`/`PrivateMedia`/`render_worker.process_render`. The 2100-second message visibility lease and 1380-second job replica budget exceed the existing 780-second FFmpeg process cap. The 1380-second replica is strictly shorter than the original SQL render claim's 1500-second (25-minute) lease; this preserves claim ownership during execution. It uses the same durable Postgres fenced claim/lease, validates canonical UUIDs, and acknowledges the **exact original queue message** only for SUCCEEDED/ALREADY_FINAL/DENIED. Invalid payload, lease conflict, exceptions or unknown result stay unacknowledged. No queue creation, mock result, downloaded customer media, secret logs or cloud mutations are performed by source tests.
- `Dockerfile.cpu-render` is a **candidate** build only: the base image must be supplied as a reviewed immutable SHA256 image reference, ffmpeg/libx264/AAC/drawtext must be present and actual signed 1080x1920 30-second output must be verified. Debian apt FFmpeg archive versions also require independent release pinning before publishing. No image was built or deployed; no GPU/paid model.
- Launch remains **fail closed** until exact dedicated DEV environment, existing queue and Supabase server credentials, an approved 1380-second job cap and a protected `VERIFIED_FLEX_RENDER_CONSUMER_DISABLED` handoff marker are set. That marker is *not* proof of actual Flex disablement: the protected Azure release must separately verify `AzureWebJobs.render_campaign_reel.Disabled=true` on the real Flex host, no in-flight duplicate claims, successful queue/lease/media/codec checks and rollback BEFORE enabling the new job. Other Flex queues/timers still need their own single-owner handoff.
- `inspect_azure_connections_readonly.py` is a **read-only Azure CLI inventory utility** for a trusted GitHub `main` DEV runner using a scoped Azure subscription. It requires exact RetailGrowthAI resource group/tags, exact Y1/Flex names and compares existing Supabase URL, publishable/service-role setting values and `RETAIL_STORAGE` **without printing them**. Host-internal `AzureWebJobsStorage` is deliberately not required to equal Flex host storage, since per-host state/locks may need isolation; it only checks that Y1 has its own valid host setting and Python runtime. It also distinguishes the exact **38 HTTP-only** and **46-function (38 HTTP + 8 short workers)** index inventories, worker registration and app Running status; neither source asserts hosted deployment success. All CLI commands are GET/list/show; no IAM/configuration/stop or issue-close. Results are diagnostic only.
- The checked-in `frontend/.env.production` still routes the DEV SPA to `https://rgai-dev-functions-d4e5ddbd.azurewebsites.net`. Do not change it to Y1 until live hosted full HTTP + worker acceptance; then publish SWA and verify actual served JavaScript from the public site. Issue #249 remains OPEN; Flex remains RUNNING.

## Second Y1 stage: bounded queue/timer workers (source only)

The package converter has two explicit modes: `--mode http-only` (default) keeps **38 HTTP routes and zero background consumers**, while `--mode http-with-short-workers` keeps those same 38 HTTP routes plus **eight original queue/timer functions**; it removes exactly the original `render_campaign_reel` consumer, which has a 780-second FFmpeg budget incompatible with classic Y1's 600-second maximum. The second stage pins `host-short-workers.json`: 9-minute host cap, raw UUID queue messages, batch size 1, zero new-batch threshold and three dequeue attempts. The original workers are not forked or reimplemented; the unchanged original ZIP is the input and all other members are byte/metadata compared before anyone may deploy.

The short-worker package is **NOT safe to deploy while Flex queue/timer triggers remain active**. The protected single-owner cutover must first audit and disable corresponding original Flex worker registrations, confirm queue/lease/outbox/backlog, verify Y1 private credentials, release and observe Y1 short workers, and preserve independent rollback. Separately enable the 1380-second CPU Container Apps render job only after proving Flex's long video queue consumer is disabled; Y1 should never index `render_campaign_reel` in either mode. Merely presenting a successful source test, an environment marker or a diagnostic JSON never permits Flex stop or issue closure.

## Disabled-by-default Container Apps Job IaC (NOT deployed)

`infra/azure/p0249-y1-cpu-render-disabled.bicep` is a DEV-only *candidate* deployment to an **existing** Container Apps environment. It references a reviewed digest-pinned CPU image, passes the dedicated Supabase and Azure queue secrets via secure deployment parameters, fixes the job budget to **1380 seconds**, parallelism **1**, replica retry **0** and leaves `triggerType='Manual'` with **no event queue scaler or activation environment marker**. Consequently no queue message automatically launches this candidate, and even a mistaken manual start fails `cpu_render_job.preflight()` before fetching/rendering any message. The source verifier checks these conditions but has not run Bicep compile or an Azure deployment. Cloud provisioning could incur charges and requires independent review and explicit scoped DEV authorization.

Microsoft documents the Container Apps Job `replicaTimeout`, `triggerType`, Event `scale` rules and secure job secrets at https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2026-01-01/jobs and https://learn.microsoft.com/en-us/azure/container-apps/tutorial-event-driven-jobs. Event-driven activation must be a **separate** protected update only after real queue/worker ownership, private media, billing and rollback acceptance; do not “enable” by simply changing an application environment variable. Preserve the original Flex renderer until that handoff is complete.

## Protected Event scaler CANDIDATE (not deployed)

The disabled-by-default Container Apps Job still has a Manual trigger and no activation marker. A separate source file `infra/azure/p0249-y1-cpu-render-event-guarded.bicep` describes the *future update of the same job*, only after an independently verified Flex long-render consumer shutdown and private queue/claim/rights/rollback acceptance. The event scaler watches the EXISTING `retail-reel-render` queue, `minExecutions=0`, `maxExecutions=1`, 60-second polling and parallelism 1. It requires exact named storage credentials through secrets, a verified immutable image and the protected single-owner activation value, and does not create any queue or environment. The CPU adapter's 2100s message invisibility exceeds its 1380s replica budget; recovered attempts may be delayed after a crash. A source file or handoff string is never independently sufficient proof to change running Azure worker ownership. Protected compilation, exact Azure scope, cost estimate, image/media SHA, true job start/ACK, duplicate safety, queue poison tests and rollback are still pending.


## Protected Y1 DEV core-connection staging (PR #1113; NOT deployed)

Before the already-merged five-to-38 HTTP release, `stage_core_connections.py`
checks the **actual existing** five-GET Y1 and original Flex app in the exact
OIDC-scoped RetailGrowthAI DEV subscription. Default invocation is a read-only
plan: it prints **only names** of absent server settings, not keys or values.
It must reject a foreign subscription/RG/app, existing Y1 setting drift,
non-five Y1 indexes, wildcard/foreign CORS, unresolved cross-identity KeyVault
references and any missing/malformed original service/storage credentials.

An optional separate manual-only GitHub protected `dev` workflow,
`.github/workflows/p0249-dev-y1-core-connections-protected.yml`, may copy
**only previously absent** `RETAIL_SUPABASE_URL`,
`RETAIL_SUPABASE_PUBLISHABLE_KEY`, `RETAIL_SUPABASE_SERVICE_ROLE_KEY` and
`RETAIL_STORAGE` from the **same already authorized original DEV Flex** app
to Y1; it verifies resulting values by protected in-memory readback and
captures no raw credentials in logs. Existing target values are never replaced
and the host-specific `AzureWebJobsStorage` is never copied. Only when\nthe known Free SWA origin is absent (and there are no foreign/wildcard\norigins), it can add that exact CORS origin without credentials. The workflow has\nno push/PR trigger, cannot create identities or grant roles, and leaves all
workers, customer API flags, served frontend routing and original Flex
untouched. Source-only CI never attempts it; a protected release/security gate
is still required. A stage can restart the isolated Y1 host, so revalidate
five-GET indexes/health before the later 38-HTTP release. Do not interpret
staging or source tests as signed two-shop, queue, private media or cutover
acceptance; issue #249 must stay open.

## 2026-11-23 — Prevent secrets in Azure CLI process arguments (PR #1113 amendment)

The missing-only protected DEV stage sends the four approved app settings through
Azure CLI's documented `--settings @file` JSON-array syntax, NOT `KEY=value`
process arguments. The JSON lives only in a random 0700 temporary directory
as a 0600 file, is never printed or uploaded, and is removed on normal or
exceptional exit. Synthetic tests check argv exclusion, file permissions,
correct missing-only settings and cleanup after success/failure; no real
credentials are used in CI. This reduces exposure but does not imply Azure
deployment, live health acceptance or independent release approval.

## 2026-11-27 — Post-stage live health gate

Protected manual staging now requires the existing bounded 20/20 Y1 HTTP health probe after missing-only settings/CORS readback. A restart or failed probe blocks a successful workflow receipt. If failure occurs, retain original Flex and staged values, diagnose and rerun protected readback; never overwrite existing settings. This is health evidence, not signed five/38-route acceptance. PR #1132 diagnostics merged at d5903179e95ebc42106098f1aa768cff09bd4004 with postmerge CI #45945139607 4/4; superseded #1065 closed after source/test equivalence verified. Hosted #249 remains 0/7; no Azure dispatch or Flex shutdown.

## 2026-11-28 — First actual core-stage run and bounded retry

The historical owner-authorized GitHub-only bridge was recovered. PR #1137 and launcher #46119354820 on main 9d89de3bd9d7a5d03308d8a77e2ffc0f722f607a passed exact CI 4/4 and dispatched the existing protected DEV workflow #46119656466. Azure OIDC passed, but the read-only inventory failed with a generic BLOCKED receipt; settings/CORS and HTTP steps were skipped, so no write or live milestone is claimed. Candidate retry adds allowlisted fixed error categories and checkpoint labels, recognizes Python Flex runtime in nested ARM or flattened CLI shape while rejecting conflicting declarations, and requires fresh marked 401 for all four protected GET handlers after the existing health probe. Microsoft documents Flex runtime configuration under functionAppConfig.runtime.name: https://learn.microsoft.com/en-us/azure/azure-functions/functions-infrastructure-as-code. The exact previous failed run is the only authorized retry prerequisite; all target environment, identity, missing-only, CORS, and CI gates remain. #249 remains open 0/7 until real hosted evidence. Original Flex unchanged.
