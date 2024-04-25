import csv
import sqlite_utils
from pathlib import Path
from datetime import datetime
import re

# Path to the original alerts.csv
csv_file_path = 'clean_nametype.csv'

# Path to the directory containing the .txt files
txt_files_directory = Path('combined_text')
# Path to the SQLite database
db_path = 'bad_docs.db'

# Create or open the SQLite database
db = sqlite_utils.Database(db_path)

# Define a function to read the text from a .txt file
def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Assuming alerts.csv is already modified to include a 'filename' column
with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Generate the path to the .txt file based on the filename column
        txt_file_path = txt_files_directory / row['filename']
        # Check if the .txt file exists
        if txt_file_path.exists():
            # Read the content of the .txt file
            row['text'] = read_text_file(txt_file_path)
            text_file = read_text_file(txt_file_path).upper()
            if re.search("LICENSE NUMBER: (\w+)", text_file):
                license_num = re.search("LICENSE NUMBER: (\w+)", text_file)
                row['license_num'] = str(license_num.group(0)).replace("LICENSE NUMBER:", "").strip()
            elif re.search("LICENSE NO.: (\w+)", text_file):
                license_num = re.search("LICENSE NO.: (\w+)", text_file)
                row['license_num'] = str(license_num.group(0)).replace("LICENSE NO.:", "").strip()
            elif re.search("LICENSE NUMBER (\w+)", text_file):
                license_num = re.search("LICENSE NUMBER (\w+)", text_file)
                row['license_num'] = str(license_num.group(0)).replace("LICENSE NUMBER", "").strip()
            if re.search(r'CASE NUMBER:\s*([\d-]+)', text_file):
                case_num = re.search("CASE NUMBER:\s*([\d-]+)", text_file)
                row['case_num'] = str(case_num.group(1))
            elif re.search("CASE NO.:\s*([\d-]+)", text_file):
                case_num = re.search("CASE NO.:\s*([\d-]+)", text_file)
                row['case_num'] = str(case_num.group(1))
        else:
            # If the file does not exist, set the text to None or an empty string
            row['text'] = None
            row['license_num'] = None
            row['case_num'] = None
        # Upsert the row into the SQLite database
        db["clean_alerts"].insert(row, pk="filename", replace=True)

db["clean_alerts"].enable_fts(["text"], tokenize="porter", replace=True)