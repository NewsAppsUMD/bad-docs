import csv
import sqlite_utils
from pathlib import Path
from datetime import datetime
import re

# Path to the original alerts.csv
csv_file_path = 'alerts.csv'
# Path for the modified alerts.csv (can be the same as csv_file_path to overwrite)
modified_csv_file_path = 'modified_alerts.csv'

# Function to convert date format from MM/DD/YYYY to YYYY-MM-DD
def convert_date_format(date_str):
    # Convert the string to datetime object
    date_obj = datetime.strptime(date_str, "%m/%d/%Y")
    # Format the datetime object to the desired string format
    return date_obj.strftime("%Y-%m-%d")

# Read the original CSV and add the 'filename' column
rows = []
with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    # Add 'filename' to the fieldnames if it's not already included
    fieldnames = reader.fieldnames + ['filename'] if 'filename' not in reader.fieldnames else reader.fieldnames
    # Assume 'date' is the name of the date column to be transformed
    fieldnames = [fn for fn in fieldnames if fn != 'date'] + ['date'] # Ensure 'date' is in the last position for reordering if needed
    for row in reader:
        # Extract filename from URL, change extension to .txt
        filename = row['url'].split('/')[-1].replace('.pdf', '.txt')
        row['filename'] = filename
        # Convert and replace the date format
        if 'date' in row:
            row['date'] = convert_date_format(row['date'])
        rows.append(row)


# Write the modified data to a new CSV
with open(modified_csv_file_path, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)