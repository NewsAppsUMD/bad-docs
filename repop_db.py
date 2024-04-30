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
            case_dict = {}
            # Read the content of the .txt file
            row['text'] = read_text_file(txt_file_path)
            text_file = read_text_file(txt_file_path).upper()
            if re.search(r'CASE N', text_file):
                pattern = r'\b\d{4}-\d{4} ?[A-Z]?\b'
                alt_patt = r'\b\d{4}-\d{5} ?[A-Z]?\b'
                if re.search(pattern, text_file):
                    matches = re.findall(pattern, text_file)
                    result = list(set(matches))
                elif re.search(alt_patt, text_file):
                    result = list(set(matches))
                else:
                    result = ["None"]
            else:
                result = ["None"]
            for case in result:
                case = case.replace(" ", "")
            result = list(set(result))
            for case in result:
                case_dict['case_num'] = case
                filename = row['filename'].replace(".txt", "")
                case_dict['filename'] = filename
                db["all_cases"].insert(case_dict, pk="id", replace=True)
        else:
            # If the file does not exist, set the text to None or an empty string
            row['text'] = "Document Not Found"
            row['license_num'] = "Document Not Found"
        # Upsert the row into the SQLite database
        db["clean_alerts"].insert(row, pk="id", replace=True)

db["clean_alerts"].enable_fts(["text"], tokenize="porter", replace=True)