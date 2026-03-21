#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"

images_directory="$DATA_DIR/images"
text_directory="$DATA_DIR/text"

mkdir -p "$text_directory"

# Loop through each .png file in the images directory
for image_file in "$images_directory"/*.png; do
    filename=$(basename "$image_file" .png)
    output_base="$text_directory/$filename"
    output_text_file="${output_base}.txt"

    if [ ! -f "$output_text_file" ]; then
        echo "Processing: $filename"
        tesseract "$image_file" "$output_base"
    fi
done
