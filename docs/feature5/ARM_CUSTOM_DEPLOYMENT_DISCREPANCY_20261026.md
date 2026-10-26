# Feature #5 — Azure Portal ARM deployment discrepancy

Date: 2026-10-26. **Production GPU: NOT DEPLOYED. Actual Hunyuan MP4: NONE.**

## Observed live cloud state

Using the owner's saved Microsoft Azure Portal login, a tightly scoped ARM
custom-template deployment was submitted against the EXISTING
`Azure subscription 1` and existing `rg-retailgrowth-dev`.

- ARM deployment name reported by the portal:
  `CustomDeployment-20261026093554`.
- Target resource: `Microsoft.App/managedEnvironments`,
  `rgai-f5-gpu-canary-eastus`, in `eastus`.
- Template requested only the default v2 `Consumption` workload profile,
  `appLogsConfiguration.destination=none`, and ownership tags. No container,
  job, GPU instance, ACR, networking or Log Analytics new resource.
- Azure portal briefly showed **Deployment succeeded**.
- **However:** later the same resource group resource list showed only the
  original eight resources; searching for the target name returned none.
- The follow-up read-only portal audit could not open the deployment's
  operations/template details because browser automation exhausted its
  usage budget. Thus the success notification **is NOT proof** of a created
  managed environment. No evidence of a GPU job/model inference exists.

Do not submit the template a second time or assert that Azure's A100 quota
is zero until the precise ARM deployment record is examined. An ARM
deployment can report Succeeded with an empty `resources` array, or a
portal's resource-list view can lag; neither is established without a read.

## Exact coordinator-only OIDC read-only reconciliation

Use existing GitHub `environment: dev` federation; **no credential values,
access tokens, subscription IDs or tenant keys in logs**. Only the project
coordinator may edit `.github/workflows/**` or apply shared deployment.

```bash
set -euo pipefail
RG=rg-retailgrowth-dev
ENV=rgai-f5-gpu-canary-eastus
DEPLOYMENT=CustomDeployment-20261026093554
test "$(az account show --query state -o tsv)" = Enabled
test "$(az account show --query id -o tsv)" = "$AZURE_SUBSCRIPTION_ID"
test "$(az group show -n "$RG" --query tags.app -o tsv)" = RetailGrowthAI
test "$(az group show -n "$RG" --query tags.environment -o tsv)" = dev

# Read-only: reconcile whether succeeded deployment had any resource changes.
az deployment group show -g "$RG" -n "$DEPLOYMENT" \
  --query '{name:name,state:properties.provisioningState,mode:properties.mode,template:properties.template.resources}' -o json
az deployment operation group list -g "$RG" -n "$DEPLOYMENT" \
  --query "[].{state:properties.provisioningState,target:properties.targetResource.id,status:properties.statusCode}" -o json
az resource list -g "$RG" --resource-type Microsoft.App/managedEnvironments \
  --query "[].{name:name,location:location,state:properties.provisioningState,tags:tags}" -o json
az provider show -n Microsoft.App --query registrationState -o tsv
```

**Decision path:**

- If target environment is present, verify it is exactly East US, tagged DEV,
  `appLogsConfiguration.destination=none`, v2 with Consumption profile only,
  no GPU/app/job/dedicated nodes. Then, and only then, run:
  `az containerapp env list-usages -g "$RG" -n "$ENV" -o json`.
- If the deployment's `template.resources` is empty, its successful status
  created nothing. Use the version-controlled strict
  `feature5_motion/infra/empty_gpu_env.json`, perform ARM what-if and
  `validate_template`/`validate_what_if`, and *only coordinator-approved*
  create of ONE empty environment.
- If the deployment contains target resource but operations show Failed or a
  partial state, do not retry until the exact ARM error and residual resource
  state are reconciled. Do not silently change providers, billing, roles or
  PROD resources.
- If the provider cannot be read due to RBAC or Microsoft.App registration,
  record the precise error; don't invent a zero quota.

Azure official docs:
https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview
(An East US workload-profiles environment must exist before environment GPU
quota is visible/requestable.)
https://learn.microsoft.com/en-us/azure/container-apps/quotas
(Quota for Managed Environment Consumption NCA100 GPUs is per-environment.)

## Local Feature5 source committed and tested

`feature5_motion/empty_env_template.py` validates one fixed zero-active-
compute environment and fails closed on extra GPU, paid profiles or logging.
`feature5_motion/azure_gpu_preflight.py` now returns
`ENVIRONMENT_REQUIRED` on no existing owned East US environment instead of
pretending the quota is zero. `azure_gpu_readonly_cli.py` reads usage for
the exact owned empty environment, not an already provisioned A100 profile.

Previous 4vCPU/16GiB illustrative pricing is NOT sufficient as a verified
A100 profile allocation. Microsoft describes up to 24vCPU/220GiB for the
A100 Consumption GPU type. Even after quota is known, official full
vCPU+memory+GPU billable time and model weights must be checked before
a single zero-retry synthetic Hunyuan sample. **No actual CUDA model generation
or real MP4 has happened.**
