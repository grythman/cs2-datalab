#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

git config core.hooksPath .githooks

chmod +x .githooks/pre-push
chmod +x .githooks/post-merge
chmod +x scripts/deploy_generator.sh
chmod +x scripts/install_git_hooks.sh

echo "Installed git hooks from .githooks"
echo "pre-push will deploy changed services before push, only when pushing to main."
echo "post-merge will rebuild and restart generator on main when generator-related files change."
