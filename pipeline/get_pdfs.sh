#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"

csv_file="$DATA_DIR/alerts.csv"

mkdir -p "$DATA_DIR/pdfs"

# Extract URLs from the CSV file and download each PDF if it doesn't already exist
csvcut -c url "$csv_file" | tail -n +2 | while IFS= read -r url; do
    filename=$(basename "$url")
    if [ ! -f "$DATA_DIR/pdfs/$filename" ]; then
        wget -P "$DATA_DIR/pdfs" "$url"
        echo "$filename downloaded successfully"
    fi
done
