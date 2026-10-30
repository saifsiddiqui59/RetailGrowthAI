#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m feature5_motion.gpu_job_control stop "$@"
