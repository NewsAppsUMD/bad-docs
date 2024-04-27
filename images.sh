#!/bin/bash

# Define directories
pdf_directory="pdfs"
image_directory="images"

# Create the directory to store the images if it doesn't exist
mkdir -p "$image_directory"

# Loop over PDF files in the pdfs directory
for pdf_file in "$pdf_directory"/*.pdf; do
    # Extract filename without extension
    filename=$(basename "$pdf_file" .pdf)
    
    # Check if there are no images for the current PDF file in the images directory
    if [ ! -f "$image_directory/${filename}_0.png" ] && [ ! -f "$image_directory/${filename}-1.png" ]; then
        # Convert PDF to images (PNG format)
        pdftoppm -png "$pdf_file" "$image_directory/${filename}"
    fi
done