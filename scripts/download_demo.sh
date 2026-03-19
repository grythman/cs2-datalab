#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
OUT="${2:-}"

if [ -z "$URL" ] || [ -z "$OUT" ]; then
  echo "Usage: download_demo.sh <url> <output_path>"
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

curl -fL \
  --retry 2 \
  --connect-timeout 10 \
  --max-time 30 \
  "$URL" -o "$OUT"

FILE_TYPE="$(file -b "$OUT" || true)"
echo "Downloaded: $OUT"
echo "File type: $FILE_TYPE"

case "$FILE_TYPE" in
  *HTML*|*XML*|*text*)
    echo "ERROR: downloaded file is not a real demo file"
    exit 2
    ;;
esac
