# Issue #249 — isolated Classic Linux Consumption (Y1) HTTP canary

**Current status (2026-11-11): Separate DEV Y1 plan/app provisioned, minimal health + original no-bearer campaign GET deployed; 40/40 synthetic health/unknown and 12/12 unauthorized campaign requests passed after 240s idle. Full signed retailer API/tenant migration NOT complete; original Flex #249 still OPEN.**

*Historical steps and previous failure snapshots follow below.*

## Purpose
The existing Python 3.12 Flex Consumption DEV Function App has repeatedly returned pre-handler HTTP 503 and no-first-byte timeouts. A separate classic Linux Consumption Y1 app gives a genuinely different Functions hosting plan. This is a controlled HTTP *ingress* comparison before migrating any retailer API.

## Strict Azure scope
- Existing, tagged RetailGrowthAI-only DEV RG: `rg-retailgrowth-dev`, Central India.
- Existing private StorageV2 account `rgaid4e5ddbdf0d21d96` for the new canary's own Functions host and Azure Files content share.
- **Only new** Linux Y1 plan `rgai-dev-y1-p0249` and Function App `rgai-dev-y1-p0249-d4e5ddbd`. Their tags include `purpose=p0249-http-ingress-isolation`.
- Original `rgai-dev-functions-d4e5ddbd`, `rgai-dev-flex`, production, WineShopPOS, all Azure queues and current tenant APIs unchanged.
- No customer secrets, Supabase service role, model/GPU activation, timer or queue triggers in the canary. Its only anonymous endpoint is `GET /api/p0249/health`, a fixed no-customer-data JSON response with an `X-Request-ID` marker.

## How the separately reviewed deployment operates
1. The protected GitHub workflow `.github/workflows/p0249-dev-y1-isolated-canary-once.yml` runs on main only after a reviewed squash merge titled **`ops(#249): create isolated DEV classic Y1 HTTP canary`** or a separate owner-confirmed manual dispatch with `YES-P0249-ISOLATED-Y1`. `dev` environment approval remains enforced.
2. Azure OIDC authenticates against the existing DEV subscription, checks exact RG app/environment tags, storage region/private properties and the current original Flex app/plan. It refuses to overwrite an already-existing Y1 canary.
3. ARM `what-if` must show exactly **two Create operations**, one for each new Microsoft.Web resource, with no other mutation. Provisioning uses an incremental deployment of `infra/azure/p0249-classic-y1-dev-canary.bicep`. It stops on unexpected changes.
4. Verify plan SKU `Y1/Dynamic`, Python 3.12, Linux site and tags while original Flex remains `FC1`. ZIP-deploy ONLY the HTTP canary via the supported Linux Python remote build. No existing API code is deployed.
5. Test real cold HTTP readiness and **20 alternating GETs** to the canary's health route and a nonexistent route. Expected: 200 + handler `X-Request-ID` on health, 404 on unknown, under 18 seconds for every measured request. Passing these proves only that this *minimal Y1 canary* is reliable over this sample — not signed JWT/RLS, queue, media or real campaign parity.
6. If the new resource canary passes, separately review an actual authenticated API migration plan. **Never** point the production frontend at the canary.

## Cost, end-of-life and manual cleanup
Classic Linux Consumption is usage-metered and can scale to zero; Azure storage/network charges and free-grant eligibility vary. No dedicated ACR/GPU/Premium/Container App resource is created. The platform remains a **temporary** comparison: Microsoft retires Linux Consumption hosting on **2028-09-30**, so Container Apps Consumption or a reviewed durable replacement is preferable for a long-lived backend.

For cleanup, inspect both resource tags and subscription first. Then delete **only** the new site and **only** the new plan (in that order). Leave the original app, original Flex plan, original Storage account and any existing hosted data unchanged. Cleanup of the new Azure Files content share is a separately reviewed storage operation, not implied by deleting a site.

References: https://azure.microsoft.com/en-us/updates?id=499451 ; https://learn.microsoft.com/en-us/azure/azure-functions/functions-infrastructure-as-code ; https://learn.microsoft.com/en-us/azure/azure-functions/python-build-options .

**Status labels:** SOURCE PREPARED ≠ PR CI PASS ≠ MERGED ≠ DEPLOYED ≠ ACCEPTED. Issue #249 remains OPEN until a proven reliable hosting replacement with signed two-shop E2E acceptance.

## November 11 — First DEV Azure creation completed; code deployment not yet attempted
- Owner-authorized source PR #903 merged to main as `8953917792a1be25c4fb1e6a8d87e5d2e827dd6f` after exact-head 4/4 CI. [Actual protected Azure OIDC run #42911959806](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42911959806) completed exact DEV scope preflight, ARM `what-if` (two new Microsoft.Web resources, no old-resource modification) and **Azure ARM provisioning succeeded**.
- The run then FAILED at `python3 ops/p0249_y1_canary_guard.py verify` (generic error in original guard) before any canary ZIP deployment or real HTTP probing. Azure Bicep warned that Y1 plan property `computeMode` is not part of the API schema; the deployment step itself returned success. The new plan/site are **provisioned but not confirmed healthy**; do not run the original create-only workflow again or claim that #249 is repaired.
- Recovery PR adds sanitized allowlisted Azure ARM field reporting, explicitly verifies Linux site kind, preserves Y1 SKU/region/tags/Python3.12, and provides a protected **resume-only** workflow `.github/workflows/p0249-dev-y1-resume-existing-once.yml`. That workflow can only deploy the anonymous single-route canary to the exact existing isolated Y1 site after strict identity verification. It does not run `az deployment group create` and cannot create or replace other resources.
- Expect actual `20/20` Y1 canary response evidence before considering any real retailer API migration. The original Flex app remains the source of the unresolved #249 pre-handler HTTP errors.

## November 11 — Y1 code ZIP accepted asynchronously, immediate endpoint still 404
- Source recovery PR #913 merged as `25f8f346a30f0ef0b48e22675fbf33a74bff3158` after exact-head 4/4 CI. In [protected run #42913728498](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42913728498), exact Y1 resource and unchanged Flex verification **PASSED**: Y1/Dynamic, Linux Python 3.12, expected tags and region. `az functionapp deployment source config-zip --build-remote true` returned after the platform ZIP endpoint gave **HTTP 202 Accepted**; it is **not proof of completed function indexing**.
- The immediate read-only health endpoint requests after this accepted ZIP returned `404` on all three readiness attempts (approximately 1.95s, 0.79s, 0.79s). **0/20 acceptance probes executed** because the readiness gate failed; this is NOT the original ~61s Flex 503 behavior and NOT a Y1 reliability PASS.
- Before re-deploying again, inspect Azure indexed function names via the separate reviewed read-only workflow `.github/workflows/p0249-dev-y1-post202-readonly-once.yml`, verify exact DEV scope, and retry the original health/unknown path after additional Azure async indexing time. No ARM creation or site configuration write in that diagnostic. If still 404, inspect Kudu deployment and Functions host indexing errors, with secret redaction. Keep #249 OPEN.

## 2026-11-11 — real Y1 post-202 indexing check and explicit Python v1 packaging fallback

The protected read-only [Azure OIDC run #42915478036](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42915478036) verified the created Y1 plan/site and unchanged original Flex again, but confirmed **0 Azure-indexed functions**. All four 20-second bounded HTTP readiness probes of `GET /api/p0249/health` returned prompt **404** (2.8s, then ~0.9s); the separate earlier code ZIP deployment had returned **202 Accepted** and was not proof of Function host indexing. This is distinct from the original Flex ~61s gateway-generated 503. The isolated Y1 canary is **NOT functionally deployed**; do not switch retailer APIs or mark #249 fixed.

Next recovery experiment: replace **only the isolated DEV Y1 canary ZIP** with a tiny Python **v1 explicit `p0249_health/function.json` + `__init__.py`** HTTP trigger and a Linux Python3.12 prebuilt vendored `azure-functions` wheel package, avoiding uncertain remote Oryx indexing. Confirm the existing Y1 tags/SKU/runtime and original Flex via protected DEV OIDC BEFORE write. Poll actual Azure indexed function list (expected exactly one `p0249_health`) and require the original 20/20 true HTTP checks. No new ARM resources, queue/timer workers, retailer credentials, provider/GPU, PROD or WineShopPOS change. Reference: https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python and https://learn.microsoft.com/en-us/azure/azure-functions/python-build-options . This recovery is unverified until hosted deployment and exact output evidence.

## 2026-11-11 — AFTER-IDLE REAL ACCEPTANCE (latest authoritative checkpoint)
- Protected [Azure #42964811296](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42964811296) was **SUCCESS**. The same existing tagged DEV Y1 indexed exactly `p0249_health` and `campaign_read` GET functions; the original Flex FC1 identity/plan remained unchanged. Two genuine synthetic HTTP windows, separated by **240 seconds with no test requests**, each passed **20/20** health/unknown GET statuses/markers and **6/6** original-auth campaign missing-Bearer handler-marked HTTP401 (total **40/40** health/unknown, **12/12** 401; 401 latencies roughly 0.91–0.93 seconds). No code deployment, ARM write or appsetting change in this run.
- The independent local signed RSA two-user/two-shop fixture PR #934 passed exact-head 4/4 and integrated with postmerge main 4/4. It exercises original JWT, API and TenantStore, but mocks JWKS and database transport and **does not validate hosted positive JWT or real RLS**. The next checkpoint requires isolated disposable DEV test identities and tenant fixtures, a reviewed temporary public-settings-only Y1 shadow configuration with rollback, and genuine signed own-/foreign-shop GETs. Original issue #249 is still OPEN. No frontend routing switch or queue/timer duplication.
