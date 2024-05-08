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

SQL="CREATE TABLE IF NOT EXISTS all_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_num TEXT,
    file_id TEXT,
    alert_id INTEGER
);"

# Execute the command
sqlite3 "$DB_FILE" "$SQL"

echo "Table created successfully."

python3 repop_db.py

echo "Table populated successfully."

# Update 'file_id' column in 'all_cases' using data from 'clean_alerts'
# Assuming both tables have a common identifier to link rows, e.g., `case_id`
sqlite3 bad_docs.db "UPDATE all_cases SET alert_id = (SELECT id FROM clean_alerts WHERE clean_alerts.file_id = all_cases.file_id)"

sqlite3 bad_docs.db "PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
CREATE TABLE all_cases_new AS SELECT * FROM all_cases;
DROP TABLE all_cases;
CREATE TABLE all_cases (id INTEGER PRIMARY KEY, case_num TEXT, file_id TEXT, alert_id INTEGER REFERENCES clean_alerts(id));
INSERT INTO all_cases SELECT * FROM all_cases_new;
DROP TABLE all_cases_new;
COMMIT;
PRAGMA foreign_keys = ON;"

sqlite-utils extract bad_docs.db clean_alerts filename text --table text

#sqlite-utils extract 
#sqlite-utils transform bad_docs.db text --rename id text_id

echo "Text table created"

sqlite-utils extract bad_docs.db clean_alerts clean_name doctor_type license_num --table doctor_info

echo "Doctor table created"

