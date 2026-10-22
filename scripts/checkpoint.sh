#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ $# -lt 1 ]; then
    echo 'Usage: bash scripts/checkpoint.sh "Task summary"'
    exit 1
fi

MESSAGE="$*"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

echo "- ${TIMESTAMP}: ${MESSAGE}" >> docs/WORK_LOG.md

echo "========== CHANGES =========="
git status --short

git add -A

if ! git diff --cached --quiet; then
    git commit -m "$MESSAGE"
fi

git push -u origin "$(git branch --show-current)"

echo "Checkpoint recorded and pushed."
