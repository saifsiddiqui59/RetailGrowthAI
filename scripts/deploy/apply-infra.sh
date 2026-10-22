#!/usr/bin/env bash
# Future manual use ONLY after separate explicit owner approval.
set -euo pipefail
if [ "$#" -ne 2 ] || [ "$1" != "--approve" ]; then
  echo "BLOCKED: use --approve private-dev-parameters.json only with owner approval" >&2
  exit 3
fi
if ! env | grep -Fxq 'RETAIL_AZURE_DEPLOY_APPROVED=YES'; then
  echo "BLOCKED: missing RETAIL_AZURE_DEPLOY_APPROVED=YES" >&2
  exit 3
fi
: "$RETAIL_AZURE_DEV_RG"
: "$RETAIL_AZURE_SUBSCRIPTION_ID"
case "$RETAIL_AZURE_DEV_RG" in
  *retailgrowth*dev*|*rgai*dev*) ;;
  *) echo "Blocked: must be isolated RetailGrowthAI DEV group" >&2; exit 3 ;;
esac
if [ ! -f "$2" ]; then echo "Private parameter file missing" >&2; exit 2; fi
actual="$(az account show --query id --output tsv)"
if [ "$actual" != "$RETAIL_AZURE_SUBSCRIPTION_ID" ]; then
  echo "Wrong subscription; no cloud write" >&2; exit 3
fi
root="$(cd "$(dirname "$0")/../.." && pwd)"
python3 "$root/scripts/deploy/release_package.py" --parameters "$2" --check-parameters
# Do not reapply declarative Bicep appSettings to an existing site: it can erase protected keys.
app_name="$(python3 "$root/scripts/deploy/release_package.py" --parameters "$2" --get-function-name)"
existing="$(az resource list --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" --resource-type Microsoft.Web/sites --query "[?name=='$app_name'].id" -o tsv)"
if [ -n "$existing" ]; then
  echo "BLOCKED: existing Function App; protected settings might be overwritten" >&2
  exit 3
fi
# Fail closed if this OIDC identity is not an exact-RG scoped Contributor.
bash "$root/scripts/deploy/azure-readonly-preflight.sh" iam
az deployment group create --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" --template-file "$root/infra/azure/main.bicep" --parameters "@$2"
