#!/usr/bin/env bash
# READ ONLY: Azure GET/LIST inventory and local validation. No deployment, secrets or writes.
set -euo pipefail
umask 077
if [ "$#" -ne 1 ] || { [ "$1" != "iam" ] && [ "$1" != "runtime" ]; }; then
  echo "Usage: azure-readonly-preflight.sh iam|runtime" >&2
  exit 2
fi
phase="$1"
: "$RETAIL_AZURE_SUBSCRIPTION_ID"
: "$RETAIL_AZURE_DEV_RG"
: "$RETAIL_AZURE_CLIENT_ID"
if [ -z "$RETAIL_AZURE_SUBSCRIPTION_ID" ] || [ -z "$RETAIL_AZURE_DEV_RG" ] || [ -z "$RETAIL_AZURE_CLIENT_ID" ]; then
  echo "Missing expected RetailGrowthAI DEV environment settings" >&2; exit 2
fi
case "$RETAIL_AZURE_DEV_RG" in
  rg-*retailgrowth*dev*|rgai*dev*) ;;
  *) echo "BLOCKED: not a dedicated RetailGrowthAI DEV group" >&2; exit 3 ;;
esac
if [ "$phase" = "runtime" ]; then
  : "$RETAIL_AZURE_FUNCTION_NAME"
  : "$RETAIL_AZURE_STORAGE_ACCOUNT"
  : "$RETAIL_DEV_FRONTEND_ORIGIN"
  : "$RETAIL_DEV_MONTHLY_BUDGET_LIMIT"
fi
command -v az >/dev/null || { echo "Azure CLI required" >&2; exit 2; }
command -v python3 >/dev/null || { echo "Python 3 required" >&2; exit 2; }
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
az account show --query '{id:id,userType:user.type,userName:user.name}' -o json > "$tmp/account.json"
python3 - "$tmp/account.json" "$RETAIL_AZURE_SUBSCRIPTION_ID" "$RETAIL_AZURE_CLIENT_ID" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    a = json.load(f)
if (str(a.get("id", "")).lower() != sys.argv[2].lower()
        or str(a.get("userType", "")).lower() != "serviceprincipal"
        or str(a.get("userName", "")).lower() != sys.argv[3].lower()):
    raise SystemExit("BLOCKED: not authenticated as expected OIDC app/subscription")
PY
principal="$(printenv RETAIL_AZURE_PRINCIPAL_OBJECT_ID 2>/dev/null || true)"
if [ -z "$principal" ]; then
  # May require Entra directory-read permission; fail closed rather than guessing.
  principal="$(az ad sp show --id "$RETAIL_AZURE_CLIENT_ID" --query id -o tsv)"
fi
scope="/subscriptions/$RETAIL_AZURE_SUBSCRIPTION_ID/resourceGroups/$RETAIL_AZURE_DEV_RG"
az group show --name "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" \
  --query '{id:id,name:name,location:location,tags:tags}' -o json > "$tmp/group.json"
az role assignment list --assignee-object-id "$principal" --scope "$scope" \
  --include-inherited --all \
  --query '[].{roleDefinitionName:roleDefinitionName,scope:scope,principalId:principalId}' \
  -o json > "$tmp/roles.json"
if [ "$phase" = "runtime" ]; then
  app_id="$scope/providers/Microsoft.Web/sites/$RETAIL_AZURE_FUNCTION_NAME"
  storage_id="$scope/providers/Microsoft.Storage/storageAccounts/$RETAIL_AZURE_STORAGE_ACCOUNT"
  az resource show --ids "$app_id" --api-version 2024-11-01 \
    --query '{name:name,location:location,tags:tags,properties:{httpsOnly:properties.httpsOnly,functionAppConfig:properties.functionAppConfig,siteConfig:{minTlsVersion:properties.siteConfig.minTlsVersion,ftpsState:properties.siteConfig.ftpsState,cors:properties.siteConfig.cors}}}' \
    -o json > "$tmp/app.json"
  az resource show --ids "$storage_id" --api-version 2023-05-01 \
    --query '{name:name,location:location,tags:tags,kind:kind,sku:sku,properties:{allowBlobPublicAccess:properties.allowBlobPublicAccess,supportsHttpsTrafficOnly:properties.supportsHttpsTrafficOnly,minimumTlsVersion:properties.minimumTlsVersion}}' \
    -o json > "$tmp/storage.json"
  # Query setting NAMES only; never persist service keys or setting values.
  az functionapp config appsettings list --name "$RETAIL_AZURE_FUNCTION_NAME" \
    --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" \
    --query '[].name' -o json > "$tmp/settings.json"
  az functionapp function list --name "$RETAIL_AZURE_FUNCTION_NAME" \
    --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" \
    --query '[].{name:name,config:config}' -o json > "$tmp/functions.json"
  : > "$tmp/queues.ndjson"
  for queue in retail-campaign-planning retail-reel-render retail-campaign-planning-poison retail-reel-render-poison; do
    az resource show --ids "$storage_id/queueServices/default/queues/$queue" \
      --api-version 2023-05-01 --query '{name:name}' -o json >> "$tmp/queues.ndjson"
  done
  # ARM read of RG-scoped Consumption budgets. Missing permissions/budget => blocked.
  az rest --method get --url "https://management.azure.com$scope/providers/Microsoft.Consumption/budgets?api-version=2023-05-01" \
    --query 'value[].{id:id,properties:properties}' -o json > "$tmp/budgets-list.json"
fi
python3 - "$tmp" "$RETAIL_AZURE_SUBSCRIPTION_ID" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
def load(name):
    return json.loads((p / name).read_text())
snapshot = {
    "subscription_id": sys.argv[2],
    "account": load("account.json"),
    "resource_group": load("group.json"),
    "role_assignments": load("roles.json"),
}
if (p / "app.json").exists():
    snapshot.update(
        function_app=load("app.json"), storage=load("storage.json"),
        app_setting_names=load("settings.json"), functions=load("functions.json"),
        queues=[json.loads(x) for x in (p / "queues.ndjson").read_text().splitlines()],
        budgets={"value": load("budgets-list.json")},
    )
(p / "snapshot.json").write_text(json.dumps(snapshot))
PY
if [ "$phase" = "runtime" ]; then
  python3 "$root/scripts/deploy/release_preflight.py" --snapshot "$tmp/snapshot.json" \
    --phase runtime --subscription-id "$RETAIL_AZURE_SUBSCRIPTION_ID" \
    --resource-group "$RETAIL_AZURE_DEV_RG" --principal-id "$principal" \
    --frontend-origin "$RETAIL_DEV_FRONTEND_ORIGIN" \
    --monthly-budget-limit "$RETAIL_DEV_MONTHLY_BUDGET_LIMIT"
else
  python3 "$root/scripts/deploy/release_preflight.py" --snapshot "$tmp/snapshot.json" \
    --phase iam --subscription-id "$RETAIL_AZURE_SUBSCRIPTION_ID" \
    --resource-group "$RETAIL_AZURE_DEV_RG" --principal-id "$principal"
fi
echo "Snapshot deleted on exit. No Azure writes and no deployment approval granted."
