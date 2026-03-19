#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"

if [ -z "$URL" ]; then
  echo '{"ok":false,"error":"missing url"}'
  exit 1
fi

/home/linuxuser/cs2-datalab/scripts/run_pipeline.sh "$URL"
