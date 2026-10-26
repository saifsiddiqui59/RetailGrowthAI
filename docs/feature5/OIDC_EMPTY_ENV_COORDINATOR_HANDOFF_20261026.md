# Feature5 — coordinator Azure OIDC execution handoff (2026-10-26)

**STATUS: SOURCE READY, NOT EXECUTED.** Owner asked to proceed, avoid support
tickets, minimize cost and produce one genuine HunyuanVideo sample. Actual
connected Azure Portal inspections confirm `rg-retailgrowth-dev` exists. Both
Quota portal views lacked a managed-environment A100 row because the required
East US workload-profiles environment is not yet created.

## Official Azure blocker decoded

Microsoft's [serverless GPUs documentation](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview) states:

> You must create a workload profiles environment in a supported region before
> you can request the required managed environment GPU quota.

The existing subscription's *subscription-level dedicated GPU quota* is NOT
the per-environment serverless NCA100 quota. Checking Quotas without a managed
environment was the wrong first step; do not infer the latter is zero. Official
[Container Apps quotas](https://learn.microsoft.com/en-us/azure/container-apps/quotas)
are scoped per environment and read via `az containerapp env list-usages`.

## Tools attempted (do not repeat browser route)

1. Saved Microsoft Azure Portal login succeeded and exposed dedicated DEV RG,
   but Quotas had no NCA100 data.
2. Portal's Container Apps Environment list/Marketplace repeatedly navigated
   to VM results, never exposed a standalone environment create wizard; no write.
3. An **ephemeral, no-storage** Azure Cloud Shell Bash session did start, but
   the browser automation could not focus the xterm prompt to type commands.
   No shell commands ran, and no resource was created.

The reliable next route is the repository's existing Azure DEV GitHub OIDC
identity, *not* more portal clicks. **Only the coordinator owns and may edit
`.github/workflows/**`, main, shared contracts and actual Azure deployment.**
Feature5 PR #323 intentionally contains no workflows or live migrations.

## Single new-resource proposal

The pinned, fully test-validated ARM JSON is
`feature5_motion/infra/empty_gpu_env.json`. It creates **one** resource only:

- Subscription: exact existing DEV subscription from GitHub environment secret
  `AZURE_SUBSCRIPTION_ID`, not copied into code.
- Resource group: `rg-retailgrowth-dev` (existing tagged Central India group).
- Container Apps managed environment: `rgai-f5-gpu-canary-eastus`,
  resource region `eastus`, tags app=RetailGrowthAI, environment=dev,
  feature=feature5.
- Workload profiles type v2 with **default Consumption only**.
- `appLogsConfiguration.destination = none` — no new Log Analytics bill.
- NO A100 workload profile, Container App, Job, VM, image registry,
  private networking or active replica. No GPU charge can originate from
  a non-existent GPU replica. Any other Azure dependent charges must still be
  reviewed in ARM what-if before deploying.

## Gated coordinator execution procedure

From a reviewed, manually dispatched GitHub DEV OIDC workflow using
`azure/login@v3` and existing `environment: dev`, or another securely
authenticated Azure terminal authorized for the exact DEV RG only:

```bash
set -euo pipefail
umask 077
RG=rg-retailgrowth-dev
ENV=rgai-f5-gpu-canary-eastus
# Secret inherited from existing RetailGrowthAI GitHub environment DEV,
# not printed in logs:
test -n "${AZURE_SUBSCRIPTION_ID:-}"
test "$(az account show --query id -o tsv)" = "$AZURE_SUBSCRIPTION_ID"
test "$(az account show --query state -o tsv)" = Enabled
test "$(az group show -n "$RG" --query location -o tsv)" = centralindia
test "$(az group show -n "$RG" --query tags.app -o tsv)" = RetailGrowthAI
test "$(az group show -n "$RG" --query tags.environment -o tsv)" = dev
test "$(az provider show -n Microsoft.App --query registrationState -o tsv)" = Registered
if az containerapp env show -g "$RG" -n "$ENV" -o json >/dev/null 2>&1; then
  echo 'BLOCKED: target exists; reconcile instead of overwrite'; exit 4
fi
python - <<'PY'
from feature5_motion.empty_env_template import validate_template
validate_template()
print('Exact one-resource zero-compute template validated')
PY
az deployment group what-if --resource-group "$RG" --template-file \
  feature5_motion/infra/empty_gpu_env.json --output json > "$RUNNER_TEMP/feature5_whatif.json"
python - "$RUNNER_TEMP/feature5_whatif.json" "$AZURE_SUBSCRIPTION_ID" <<'PY'
import json,sys
from feature5_motion.empty_env_template import validate_what_if
validate_what_if(json.load(open(sys.argv[1])), sys.argv[2])
print("Azure what-if: exactly one new empty RetailGrowthAI DEV managed environment")
PY
# STOP HERE ON INITIAL COORDINATOR REVIEW.
# Separate explicitly approved manual job may then execute exactly:
# az deployment group create -g "$RG" \
#   --template-file feature5_motion/infra/empty_gpu_env.json \
#   --name rgai-feature5-empty-env-quota-inspection
```

After an approved empty environment creation and ARM `Succeeded`:

```bash
az containerapp env show -g "$RG" -n "$ENV" \
  --query '{name:name,region:location,state:properties.provisioningState,profiles:properties.workloadProfiles}' -o json
az containerapp env list-usages -g "$RG" -n "$ENV" -o json
```

Read specifically `Managed Environment Consumption NCA100 GPUs`
limit/currentValue. Missing row = **not visible or ineligible**, not zero.
No quota request or GPU job should start without that evidence. Do not
automatically retry a potentially created resource after timeouts.

## Before genuine model run

Only after an available quota **and** separately reviewed Tencent community
license, complete Tencent model shards+immutable SHA256, approved synthetic
text-only region, actual 24vCPU/220GiB-style A100 profile (verify Azure
meter/resource shape), private media receipts and explicit full-job USD ceiling
may the coordinator propose one manual, zero-retry, bounded-time GPU Job.
Feature5's sample prompt is `fashion_motion_spec` (red embroidered kurti
in boutique, 5s portrait), with real ffprobe/sha256/contact-sheet acceptance.
No real Tencent model MP4 exists today.

## Cost correction

The older hypothetical 4-vCPU/16-GiB example is NOT a verified allocation
for A100 serverless GPU. Microsoft lists A100 serverless workload profiles
with **up to 24 vCPU and 220 GiB**; Azure publishes per-second GPU/CPU/GiB
meters. At the previously verified public East US meter snapshot:

- A100 $0.000529 per second
- 24 vCPU × $0.000024 per second = $0.000576 per second
- 220 GiB × $0.000003 per second = $0.000660 per second
- Combined **$0.001765 per second**, or **$1.059 for 600 billed seconds**
  before VAT/egress/storage/image startup, model load, retries and other costs.

This is an **illustrative estimate**, not guaranteed quota, price, runtime,
capacity reservation or hard billing cap. GPU is still NOT running.
