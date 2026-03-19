#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-}"

if [ -z "$INPUT" ]; then
  echo "Usage: auto_extract_and_parse.sh <zip_or_dem_path>"
  exit 1
fi

BASENAME=$(basename "$INPUT")
NAME="${BASENAME%.*}"

WORKDIR="/data/raw/$NAME"
mkdir -p "$WORKDIR"

FILE_TYPE=$(file -b "$INPUT" || true)

if [[ "$FILE_TYPE" == *Zip* ]]; then
  echo "ZIP detected, extracting..."
  unzip -o "$INPUT" -d "$WORKDIR"
elif [[ "$FILE_TYPE" == *data* ]]; then
  echo "Raw demo detected, copying..."
  cp "$INPUT" "$WORKDIR/"
else
  echo "Unknown file type: $FILE_TYPE"
  exit 2
fi

DEMO_FILE=$(find "$WORKDIR" -type f -name "*.dem" | head -n 1)

if [ -z "$DEMO_FILE" ]; then
  echo "No .dem file found"
  exit 3
fi

echo "Found demo: $DEMO_FILE"

OUT_CSV="/data/parsed/${NAME}_kills.csv"
OUT_JSON="/data/parsed/${NAME}_summary.json"

python /app/scripts/extract_cli.py \
  "$DEMO_FILE" \
  "$OUT_CSV" \
  --summary-json "$OUT_JSON"

echo "Done:"
echo "$OUT_CSV"
echo "$OUT_JSON"
