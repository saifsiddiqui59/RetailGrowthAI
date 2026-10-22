#!/usr/bin/env bash
# Offline only. No Azure mutations, migrations or cloud secrets.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
if command -v python3 >/dev/null 2>&1; then
  py=python3
elif command -v python >/dev/null 2>&1; then
  py=python
else
  echo "Missing Python 3; install with uv python install 3.12" >&2
  exit 2
fi
"$py" scripts/deploy/package.py --check
"$py" -m unittest discover -s scripts/deploy -p 'test_*.py' -v
"$py" -m unittest discover -s tests/infra -p 'test_*.py' -v
if command -v az >/dev/null 2>&1; then
  target="$(mktemp -t retailgrowth-azure-XXXXXX.json)"
  trap 'rm -f "$target"' EXIT
  az bicep build --file infra/azure/main.bicep --outfile "$target" >/dev/null
  echo "PASS: local Azure Bicep compile, no cloud resource writes"
else
  echo "NOTE: Azure CLI missing; Bicep compilation NOT verified"
fi
