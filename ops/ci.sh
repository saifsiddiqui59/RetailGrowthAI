#!/usr/bin/env bash
# Offline, no hosted resources; coordinator can wire this to CI.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m pytest -q tests/reliability
# Benchmark is opt-in because 1080p full rendering may exceed hosted CI limits.
echo "PASS: offline retry, poison, orphan, monitor and cost-model tests"
