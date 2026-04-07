#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="cs2-generator-sync.service"
TIMER_NAME="cs2-generator-sync.timer"

sudo cp "$ROOT_DIR/deploy/$SERVICE_NAME" "/etc/systemd/system/$SERVICE_NAME"
sudo cp "$ROOT_DIR/deploy/$TIMER_NAME" "/etc/systemd/system/$TIMER_NAME"

sudo systemctl daemon-reload
sudo systemctl enable --now "$TIMER_NAME"

echo "Installed $SERVICE_NAME and $TIMER_NAME"
echo "Check status with: systemctl status $TIMER_NAME"
