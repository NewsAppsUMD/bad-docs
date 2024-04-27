#!/bin/bash

sqlite-utils drop-table bad_docs.db clean_alerts
sqlite-utils drop-table bad_docs.db text

# Database file
DB_FILE="bad_docs.db"

# SQL command to create a table
SQL="CREATE TABLE IF NOT EXISTS clean_alerts (
    id TEXT,
    url TEXT,
    clean_name TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    suffix TEXT,
    doctor_type TEXT,
    type TEXT,
    year INTEGER,
    filename TEXT PRIMARY KEY,
    date TEXT,
    text TEXT,
    license_num TEXT,
    case_num TEXT
);"

# Execute the command
sqlite3 "$DB_FILE" "$SQL"

echo "Table created successfully."

python3 repop_db.py

echo "Table populated successfully."

sqlite-utils extract bad_docs.db clean_alerts text id --table text
sqlite-utils transform bad_docs.db text --rename id text_id