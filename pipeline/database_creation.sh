#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$(dirname "$SCRIPT_DIR")/data"
DB_FILE="$DATA_DIR/bad_docs.db"

# Parse arguments
FULL_REBUILD=false
for arg in "$@"; do
    case $arg in
        --full) FULL_REBUILD=true ;;
    esac
done

mkdir -p "$DATA_DIR"

# Core tables are cheap to rebuild (derived from CSVs)
echo "Dropping core tables..."
uv run sqlite-utils drop-table "$DB_FILE" clean_alerts --ignore 2>/dev/null || true
uv run sqlite-utils drop-table "$DB_FILE" text --ignore 2>/dev/null || true
uv run sqlite-utils drop-table "$DB_FILE" doctor_info --ignore 2>/dev/null || true
uv run sqlite-utils drop-table "$DB_FILE" all_cases --ignore 2>/dev/null || true

# Only drop document_json on full rebuild — it contains expensive embeddings
if [ "$FULL_REBUILD" = true ]; then
    echo "Full rebuild: dropping document_json table (embeddings will need regeneration)"
    uv run sqlite-utils drop-table "$DB_FILE" document_json --ignore 2>/dev/null || true
else
    echo "Incremental: preserving document_json table (embeddings retained)"
fi

# Create tables
sqlite3 "$DB_FILE" "CREATE TABLE IF NOT EXISTS clean_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id,
    url TEXT,
    clean_name TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    suffix TEXT,
    doctor_type TEXT,
    type TEXT,
    year INTEGER,
    filename TEXT,
    date TEXT,
    date_str TEXT,
    text TEXT,
    license_num TEXT
);"

sqlite3 "$DB_FILE" "CREATE TABLE IF NOT EXISTS all_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_num TEXT,
    file_id TEXT,
    alert_id INTEGER
);"

echo "Tables created successfully."

# Populate from CSV and text files
uv run python "$SCRIPT_DIR/repop_db.py"
echo "Tables populated successfully."

# Link cases to alerts via file_id
sqlite3 "$DB_FILE" "UPDATE all_cases SET alert_id = (SELECT id FROM clean_alerts WHERE clean_alerts.file_id = all_cases.file_id)"

# Add foreign key constraint to all_cases
sqlite3 "$DB_FILE" "PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
CREATE TABLE all_cases_new AS SELECT * FROM all_cases;
DROP TABLE all_cases;
CREATE TABLE all_cases (id INTEGER PRIMARY KEY, case_num TEXT, file_id TEXT, alert_id INTEGER REFERENCES clean_alerts(id));
INSERT INTO all_cases SELECT * FROM all_cases_new;
DROP TABLE all_cases_new;
COMMIT;
PRAGMA foreign_keys = ON;"

# Extract normalized tables
uv run sqlite-utils extract "$DB_FILE" clean_alerts filename text --table text
echo "Text table created."

uv run sqlite-utils extract "$DB_FILE" clean_alerts clean_name doctor_type license_num --table doctor_info
echo "Doctor table created."

# Populate JSON summaries (skips existing records automatically)
uv run python "$SCRIPT_DIR/populate_json.py" --stats
echo "Database creation complete."
