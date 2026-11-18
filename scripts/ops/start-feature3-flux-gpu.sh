#!/usr/bin/env bash
set -euo pipefail
# GPU remains OFF by default; require --execute plus two explicit operator flags.
# Pass: --subscription <DEV-UUID> --job <EXISTING-FEATURE3-JOB> --rate-usd-per-sec <VERIFIED> --max-usd <CAPPED>
exec python3 "$(dirname "${BASH_SOURCE[0]}")/feature3_flux_gpu.py" start "$@"
