#!/bin/bash
set -e

# Usage:
#   bash full_pipeline.sh           # Incremental update (only process new documents)
#   bash full_pipeline.sh --full    # Full rebuild from scratch

FULL_FLAG=""
for arg in "$@"; do
    case $arg in
        --full) FULL_FLAG="--full" ;;
    esac
done

if [ -n "$FULL_FLAG" ]; then
    echo "=== FULL REBUILD MODE ==="
else
    echo "=== INCREMENTAL UPDATE MODE ==="
    echo "    (use --full to rebuild everything from scratch)"
fi

# Ensure dependencies are installed
uv sync

# 1. Scrape alerts from Maryland Board of Physicians
#    Always re-scrapes to pick up new alerts (fast, ~10 seconds)
echo ""
echo "=== Step 1/10: Scraping alerts ==="
uv run python scrape.py

# 2. Fix file_id inconsistencies
echo ""
echo "=== Step 2/10: Applying license mutations ==="
uv run python license_mutations.py

# 3. Download PDFs (skips already-downloaded files)
echo ""
echo "=== Step 3/10: Downloading PDFs ==="
bash get_pdfs.sh

# 4. Convert PDFs to images for OCR (skips already-converted files)
echo ""
echo "=== Step 4/10: Converting PDFs to images ==="
bash images.sh

# 5. Run OCR on images (skips already-processed images)
echo ""
echo "=== Step 5/10: Running OCR ==="
bash ocr.sh

# 6. Combine multi-page OCR output (skips already-combined files)
echo ""
echo "=== Step 6/10: Combining text files ==="
bash combine_text.sh

# 7. Clean and reformat alerts
#    Always re-runs (fast CSV transforms)
echo ""
echo "=== Step 7/10: Cleaning alert data ==="
uv run python mod_alerts.py
uv run python data_cleaning.py

# 8. Create and populate database
#    Core tables rebuilt; document_json preserved unless --full
echo ""
echo "=== Step 8/10: Building database ==="
bash database_creation.sh $FULL_FLAG

# 9. Generate AI summaries from documents (skips existing JSON files)
echo ""
echo "=== Step 9/10: Generating JSON summaries (requires Gemini API key) ==="
uv run python generate_json_from_combined.py

# 10. Generate embeddings for similarity search (skips docs with embeddings)
echo ""
echo "=== Step 10/10: Generating embeddings (requires Ollama with nomic-embed-text) ==="
uv run python add_embeddings.py

echo ""
echo "=== Pipeline complete ==="
echo "Start the app with: uv run python app.py"
