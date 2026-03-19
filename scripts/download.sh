#!/bin/sh
URL=$1
FILENAME=$2
RAW_DIR="/home/linuxuser/cs2-datalab/raw"

echo "Татаж байна: $URL"
# n8n дотроос curl ашиглан татах (User-Agent нэмсэн)
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "$URL" -o "$RAW_DIR/$FILENAME.dem.bz2"

echo "Задалж байна..."
bzip2 -d -f "$RAW_DIR/$FILENAME.dem.bz2"

echo "Амжилттай: $RAW_DIR/$FILENAME.dem"
