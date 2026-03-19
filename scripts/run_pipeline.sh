#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"

if [ -z "$URL" ]; then
  echo '{"ok":false,"error":"missing url"}'
  exit 1
fi

SAFE_NAME="$(date +%Y%m%d_%H%M%S)"
RAW_ZIP="/data/raw/${SAFE_NAME}.zip"
RAW_DEM="/data/raw/${SAFE_NAME}.dem"

cleanup() {
  true
}
trap cleanup EXIT

if /app/scripts/download_demo.sh "$URL" "$RAW_ZIP"; then
  INPUT_PATH="/data/raw/${SAFE_NAME}.zip"
elif /app/scripts/download_demo.sh "$URL" "$RAW_DEM"; then
  INPUT_PATH="/data/raw/${SAFE_NAME}.dem"
else
  echo '{"ok":false,"error":"download failed"}'
  exit 2
fi

bash /app/scripts/auto_extract_and_parse.sh "$INPUT_PATH"

SUMMARY_FILE="/data/parsed/${SAFE_NAME}_summary.json"
CSV_FILE="/data/parsed/${SAFE_NAME}_kills.csv"

python3 - <<PY
import json
from pathlib import Path

summary_path = Path("$SUMMARY_FILE")
csv_path = Path("$CSV_FILE")

if not summary_path.exists():
    print(json.dumps({"ok": False, "error": "summary not found"}))
    raise SystemExit(3)

data = json.loads(summary_path.read_text(encoding="utf-8"))
data["ok"] = True
data["csv_file"] = str(csv_path)
print(json.dumps(data))
PY
