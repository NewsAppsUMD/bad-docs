#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"

txt_directory="$DATA_DIR/text"
combined_directory="$DATA_DIR/combined_text"

mkdir -p "$combined_directory"

# Collect unique base names (compatible with bash 3.2 — no associative arrays)
seen_file=$(mktemp)
trap "rm -f $seen_file" EXIT

for file in "$txt_directory"/*.txt; do
    [ -f "$file" ] || continue
    base_name=$(basename "$file" | cut -d '_' -f 1)

    # Skip if we've already processed this base name
    if grep -qx "$base_name" "$seen_file" 2>/dev/null; then
        continue
    fi
    echo "$base_name" >> "$seen_file"

    output_file="${combined_directory}/${base_name}.txt"

    # Check if combined file exists and is newer than all source parts
    needs_update=false
    if [ ! -f "$output_file" ]; then
        needs_update=true
    else
        for part in "${txt_directory}/${base_name}"_*.txt; do
            if [ "$part" -nt "$output_file" ]; then
                needs_update=true
                break
            fi
        done
    fi

    if [ "$needs_update" = true ]; then
        cat "${txt_directory}/${base_name}"_*.txt > "$output_file"
        echo "Combined files into $output_file"
    fi
done

echo "All files combined."
