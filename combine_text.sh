#!/bin/bash

# Define the directory containing the .txt files
txt_directory="text"
# Define the directory where the combined files will be saved
combined_directory="combined_text"

# Create the combined directory if it doesn't exist
mkdir -p "$combined_directory"

# Collect unique base names
declare -A seen
for file in "$txt_directory"/*.txt; do
    base_name=$(basename "$file" | cut -d '_' -f 1)

    # Skip if we've already processed this base name
    if [ "${seen[$base_name]}" ]; then
        continue
    fi
    seen[$base_name]=1

    output_file="${combined_directory}/${base_name}.txt"

    # Check if combined file exists and is newer than all source parts
    needs_update=false
    if [ ! -f "$output_file" ]; then
        needs_update=true
    else
        # Re-combine if any source file is newer than the combined file
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
