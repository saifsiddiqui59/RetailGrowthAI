#!/usr/bin/env bash
# Azure what-if is read-only preview; NEVER applies a deployment.
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: plan.sh /private/path/dev.parameters.json" >&2; exit 2
fi
: "$RETAIL_AZURE_DEV_RG"
: "$RETAIL_AZURE_SUBSCRIPTION_ID"
if [ ! -f "$1" ]; then echo "Parameter file missing" >&2; exit 2; fi
actual="$(az account show --query id --output tsv)"
if [ "$actual" != "$RETAIL_AZURE_SUBSCRIPTION_ID" ]; then
  echo "Subscription mismatch; refusing preview" >&2; exit 3
fi
root="$(cd "$(dirname "$0")/../.." && pwd)"
az deployment group what-if --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" --template-file "$root/infra/azure/main.bicep" --parameters "@$1"
echo "What-if only: NO resource creation and NO code deployment"
