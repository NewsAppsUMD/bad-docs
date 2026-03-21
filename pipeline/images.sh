#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"

pdf_directory="$DATA_DIR/pdfs"
image_directory="$DATA_DIR/images"

mkdir -p "$image_directory"

# Loop over PDF files in the pdfs directory
for pdf_file in "$pdf_directory"/*.pdf; do
    filename=$(basename "$pdf_file" .pdf)

    # Check if there are no images for the current PDF file
    if [ ! -f "$image_directory/${filename}_0.png" ]; then
        uv run pdf2image --output "$image_directory" --image_type png "$pdf_file"
        echo "$filename converted"
    fi
done
