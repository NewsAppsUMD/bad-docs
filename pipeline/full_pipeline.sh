#!/bin/bash
set -e

# Usage:
#   bash pipeline/full_pipeline.sh           # Incremental update
#   bash pipeline/full_pipeline.sh --full    # Full rebuild from scratch

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

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

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Ensure dependencies are installed (including pipeline extras)
cd "$PROJECT_ROOT"
uv sync --extra pipeline

# 1. Scrape alerts from Maryland Board of Physicians
echo ""
echo "=== Step 1/10: Scraping alerts ==="
uv run python "$SCRIPT_DIR/scrape.py"

# 2. Fix file_id inconsistencies
echo ""
echo "=== Step 2/10: Applying license mutations ==="
uv run python "$SCRIPT_DIR/license_mutations.py"

# 3. Download PDFs (skips already-downloaded files)
echo ""
echo "=== Step 3/10: Downloading PDFs ==="
bash "$SCRIPT_DIR/get_pdfs.sh"

# 4. Convert PDFs to images for OCR (skips already-converted files)
echo ""
echo "=== Step 4/10: Converting PDFs to images ==="
bash "$SCRIPT_DIR/images.sh"

# 5. Run OCR on images (skips already-processed images)
echo ""
echo "=== Step 5/10: Running OCR ==="
bash "$SCRIPT_DIR/ocr.sh"

# 6. Combine multi-page OCR output (skips already-combined files)
echo ""
echo "=== Step 6/10: Combining text files ==="
bash "$SCRIPT_DIR/combine_text.sh"

# 7. Clean and reformat alerts
echo ""
echo "=== Step 7/10: Cleaning alert data ==="
uv run python "$SCRIPT_DIR/mod_alerts.py"
uv run python "$SCRIPT_DIR/data_cleaning.py"

# 8. Create and populate database
echo ""
echo "=== Step 8/10: Building database ==="
bash "$SCRIPT_DIR/database_creation.sh" $FULL_FLAG

# 9. Classify doctor statuses using LLM (skips already-classified doctors)
echo ""
echo "=== Step 9/11: Classifying doctor statuses (requires Ollama with qwen3.5:9b) ==="
uv run python "$SCRIPT_DIR/classify_status.py"

# 10. Generate AI summaries from documents (skips existing JSON files)
echo ""
echo "=== Step 10/11: Generating JSON summaries (requires Ollama with qwen3.5:9b) ==="
uv run python "$SCRIPT_DIR/generate_json_from_combined.py"

# 11. Generate embeddings for similarity search (skips docs with embeddings)
echo ""
echo "=== Step 11/11: Generating embeddings (requires Ollama with nomic-embed-text) ==="
uv run python "$SCRIPT_DIR/add_embeddings.py"

echo ""
echo "=== Pipeline complete ==="
echo "Start the app with: uv run python app.py"
