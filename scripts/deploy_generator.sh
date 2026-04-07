#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGET_BRANCH="${1:-main}"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
  echo "Skipping generator deploy: current branch is '$CURRENT_BRANCH', expected '$TARGET_BRANCH'."
  exit 0
fi

echo "Deploying generator on branch '$CURRENT_BRANCH'..."
docker compose build generator
docker compose up -d generator
echo "Generator deploy complete."
