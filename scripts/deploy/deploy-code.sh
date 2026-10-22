#!/usr/bin/env bash
# Future manual code deploy ONLY after separate explicit owner approval.
set -euo pipefail
if [ "$#" -ne 2 ] || [ "$1" != "--approve" ]; then
  echo "BLOCKED: owner-approved --approve package.zip required" >&2; exit 3
fi
if ! env | grep -Fxq 'RETAIL_AZURE_DEPLOY_APPROVED=YES'; then
  echo "BLOCKED: explicit owner deployment approval required" >&2; exit 3
fi
: "$RETAIL_AZURE_DEV_RG"
: "$RETAIL_AZURE_SUBSCRIPTION_ID"
: "$RETAIL_AZURE_FUNCTION_NAME"
case "$RETAIL_AZURE_DEV_RG" in
  *retailgrowth*dev*|*rgai*dev*) ;;
  *) echo "Not RetailGrowthAI DEV" >&2; exit 3 ;;
esac
if [ ! -f "$2" ]; then echo "Package not found" >&2; exit 2; fi
if [ "$(az account show --query id --output tsv)" != "$RETAIL_AZURE_SUBSCRIPTION_ID" ]; then
  echo "Wrong subscription; no cloud write" >&2; exit 3
fi
# Query only config NAMES; never log service secrets.
keys="$(az functionapp config appsettings list --name "$RETAIL_AZURE_FUNCTION_NAME" --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" --query '[].name' --output tsv)"
for needed in AzureWebJobsStorage RETAIL_STORAGE RETAIL_SUPABASE_URL RETAIL_SUPABASE_PUBLISHABLE_KEY RETAIL_SUPABASE_SERVICE_ROLE_KEY; do
  if ! printf '%s\n' "$keys" | grep -Fxq "$needed"; then
    echo "Missing backend secret/config key: $needed" >&2; exit 3
  fi
done
# Avoid accidentally publishing a ZIP without the approved FFmpeg distribution.
if command -v python3 >/dev/null 2>&1; then py=python3; else py=python; fi
"$py" - "$2" <<'PY'
from sys import argv
from zipfile import ZipFile
with ZipFile(argv[1]) as z:
    names = set(z.namelist())
    needed = {
        "function_app.py", "requirements.txt", "host.json",
        "ai_agents/schemas.py", "azure-functions/campaign-api/render_worker.py",
        "video-engine/render.py", "bin/ffmpeg", "bin/ffprobe",
        "bin/THIRD_PARTY_NOTICES.txt",
    }
    if not needed.issubset(names):
        raise SystemExit("Incomplete package: refuse publish")
    for name in ("bin/ffmpeg", "bin/ffprobe"):
        if z.read(name)[:4] != b"\x7fELF":
            raise SystemExit("Invalid Linux binary: " + name)
PY
# Do not use until approved Supabase DEV migrations, timeout/retry,
# licensing, billing alerts and function app configuration are verified.
az functionapp deployment source config-zip --name "$RETAIL_AZURE_FUNCTION_NAME" --resource-group "$RETAIL_AZURE_DEV_RG" --subscription "$RETAIL_AZURE_SUBSCRIPTION_ID" --src "$2" --build-remote true
