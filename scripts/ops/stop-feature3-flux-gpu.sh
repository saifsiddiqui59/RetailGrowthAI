#!/usr/bin/env bash
set -euo pipefail
# Stop only a named Feature3 job execution; allowed while new GPU starts disabled.
# Pass: --subscription <DEV-UUID> --job <EXISTING-FEATURE3-JOB> --execution <EXACT-NAME> --execute
exec python3 "$(dirname "${BASH_SOURCE[0]}")/feature3_flux_gpu.py" stop "$@"
