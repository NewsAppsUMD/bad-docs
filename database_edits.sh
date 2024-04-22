#!/bin/bash

# Path to the SQLite database file
DB_PATH="bad_docs.db"

# SQLite commands to remove the column
sqlite3 "$DB_PATH" <<EOF
BEGIN TRANSACTION;
CREATE TABLE new_alerts AS SELECT column1, column2, ..., columnN FROM alerts; -- Specify all other columns except 'doc_type'
DROP TABLE alerts;
ALTER TABLE new_alerts RENAME TO alerts;
COMMIT;
EOF

echo "Column removed successfully."
