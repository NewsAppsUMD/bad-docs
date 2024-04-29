#!/bin/bash

sqlite-utils drop-table bad_docs.db clean_alerts
sqlite-utils drop-table bad_docs.db text
sqlite-utils drop-table bad_docs.db doctor_info
sqlite-utils drop-table bad_docs.db all_cases

# Database file
DB_FILE="bad_docs.db"

# SQL command to create a table
SQL="CREATE TABLE IF NOT EXISTS clean_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    text TEXT,
    license_num TEXT
);"

SQL="CREATE TABLE IF NOT EXISTS all_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_num TEXT,
    filename TEXT
);"

# Execute the command
sqlite3 "$DB_FILE" "$SQL"

echo "Table created successfully."

python3 repop_db.py

echo "Table populated successfully."

sqlite-utils extract bad_docs.db clean_alerts text --table text

#sqlite-utils extract 
#sqlite-utils transform bad_docs.db text --rename id text_id

echo "Text table created"

sqlite-utils extract bad_docs.db clean_alerts clean_name first_name middle_name last_name suffix doctor_type license_num --table doctor_info

echo "Doctor table created"

