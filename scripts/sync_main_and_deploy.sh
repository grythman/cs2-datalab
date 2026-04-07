#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGET_BRANCH="${1:-main}"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
  echo "Skipping sync: current branch is '$CURRENT_BRANCH', expected '$TARGET_BRANCH'."
  exit 0
fi

git fetch origin "$TARGET_BRANCH"

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "origin/$TARGET_BRANCH")"

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  echo "No new commits on origin/$TARGET_BRANCH."
  exit 0
fi

git pull --ff-only origin "$TARGET_BRANCH"
"$ROOT_DIR/scripts/deploy_generator.sh" "$TARGET_BRANCH"
