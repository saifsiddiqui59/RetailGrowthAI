# Workstream M — Azure DEV release preflight

**Source-only work. No Azure resource, role, hosted database or deployment was changed.** Existing GitHub Azure OIDC proves authentication only, not permissions or runtime readiness. The coordinator owns shared docs/workflows and DEV approval.

## Offline / CI

~~~bash
bash scripts/deploy/check.sh
python3 scripts/deploy/package.py --check
~~~

The existing Python CI job runs the new negative infra tests. No credentials are used.

## Read-only IAM scope verification (existing DEV resource group only)

Run with an authenticated RetailGrowthAI-specific Azure CLI **service principal** and correct DEV identifiers:

~~~bash
export RETAIL_AZURE_CLIENT_ID="<DEV app client ID>"
export RETAIL_AZURE_SUBSCRIPTION_ID="<DEV subscription UUID>"
export RETAIL_AZURE_DEV_RG="rg-retailgrowth-dev"
# Optional if Azure directory-read is restricted; verify in Entra first:
export RETAIL_AZURE_PRINCIPAL_OBJECT_ID="<service principal object ID>"
bash scripts/deploy/azure-readonly-preflight.sh iam
~~~

Requires a real Central India group tagged app=RetailGrowthAI and environment=dev; direct Contributor at **that exact resource-group scope**; no unexpected inherited/wider write roles. Reader inheritance is permitted. Checks subscription and service-principal OIDC client identity; no provision, role assignment or modification. If group missing, untagged or not scoped correctly, **BLOCKED** is the intended outcome. Group-based grants, PIM, deny assignments and custom roles still require owner review.

## Read-only hosted runtime verification (requires separately approved deployment)

~~~bash
export RETAIL_AZURE_FUNCTION_NAME="<existing DEV Functions app>"
export RETAIL_AZURE_STORAGE_ACCOUNT="<existing dedicated DEV storage>"
export RETAIL_DEV_FRONTEND_ORIGIN="https://<exact DEV frontend host>"
export RETAIL_DEV_MONTHLY_BUDGET_LIMIT="<approved monetary cap in Azure billing currency>"
bash scripts/deploy/azure-readonly-preflight.sh runtime
~~~

The script performs only Azure ARM GET/LIST and Functions metadata reads, and collects **app-setting names only, not values**. It checks Python 3.12 Flex, Central India, 2048 MiB, 1–2 instances per independently scaling function group, no always-ready, HTTPS/TLS, disabled FTP, exact CORS; private Standard_LRS StorageV2; backend config-key presence; planning/render/poison queue triggers and monitored 2-minute stale-recovery timer; all four ARM queue objects; a resource-group-scoped monthly **Cost** budget with approved amount and enabled 80%/100% email alerts.

**Azure budgets alert; they do not hard-cap costs.** This check does not prove that Azure functions actually process jobs, that app settings are correct, that paid model inference is configured, or that message retry/poison recovery works. Real DEV validation is separately approval-gated. Budget amount is in Azure billing currency, not assumed INR.

Local inventories reside only in a restricted temporary directory and are destroyed at exit. Never upload these raw inventories or secret-bearing app configurations to GitHub Actions logs.

## Rollback readiness and controls

The deploy-code script now blocks unless BOTH explicit deployment approval and one of these are present: an independently approved **first release** flag RETAIL_AZURE_FIRST_RELEASE_APPROVED=YES, or RETAIL_AZURE_ROLLBACK_ZIP pointing to the separately preserved known-good previously deployed ZIP. The rollback guard verifies candidate and previous archive packaging, required FFmpeg binary metadata, license notice, host/queue limits, and reports SHA-256 fingerprints; it rejects identical candidate/rollback bundles.

Local-only examples:

~~~bash
python3 scripts/deploy/rollback_guard.py --candidate /private/candidate.zip --previous /private/last-good.zip
python3 scripts/deploy/rollback_guard.py --candidate /private/candidate.zip --first-release-approved
~~~

Before an approved rollout, retain the last-known-good ZIP, SHA digest, baseline site settings **without printing secrets**, current queue/poison depths and a protected hosted database backup. Do not reapply the Bicep template blindly: its declarative appSettings could erase protected values added later. Coordinate any rollback of API with Workstream L migration compatibility; restoring a ZIP never reverts SQL. On failure, pause dispatch via a reviewed operational decision, preserve durable outbox/poison receipts and fencing, restore a vetted artifact under explicit approval, and retest auth/tenant/queue/render. Never delete poison messages or reverse migrations ad hoc.

## Coordinator handoff / remaining blockers

The workstream **prepared but did not execute** live Azure IAM or runtime verification because the connected GitHub tool cannot execute Azure CLI. Coordinator may add the IAM check to a protected main-only manual OIDC workflow after reviewing required env settings; **do not provide credentials to PR CI**. Hosted DEV migrations, RG IAM enumeration, budget/alerts, Flex indexing, FFmpeg license/runtime benchmark, queue retries/poison and actual authenticated end-to-end flows remain approval-gated. Never modify WineShopPOS or provision PROD.
