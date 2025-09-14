#!/usr/bin/env python3
"""
Python version of data_cleaning.R
Cleans up alerts data by extracting doctor types, cleaning names, and generating license numbers.
"""

import pandas as pd
import re
import numpy as np

def clean_alerts_data():
    """
    Clean up alerts data following the same logic as data_cleaning.R
    """
    print("Reading modified_alerts.csv...")
    
    # Read the CSV file
    alert_textfiles = pd.read_csv("modified_alerts.csv")
    
    print(f"Loaded {len(alert_textfiles)} rows")
    
    # Step 1: Extract doctor type from name (last word after space)
    print("Extracting doctor types from names...")
    
    def extract_doctor_type(name):
        """Extract the last word from name as potential doctor type"""
        if pd.isna(name):
            return ""
        # Extract last word after space, remove periods
        match = re.search(r'\s(\S+)$', str(name))
        if match:
            return re.sub(r'\.', '', match.group(1))
        return ""
    
    alert_textfiles['doctor_type'] = alert_textfiles['name'].apply(extract_doctor_type)
    
    # Clean the name by removing the last comma and everything after it
    alert_textfiles['doc_nameclean'] = alert_textfiles['name'].apply(
        lambda x: re.sub(r',[^,]*$', '', str(x)) if pd.notna(x) else ""
    )
    
    # Step 2: Handle special cases for doctor_type based on type column
    print("Applying special cases for doctor types...")
    
    def apply_doctor_type_cases(row):
        """Apply case_when logic for doctor_type"""
        if "ithout a License" in str(row['type']):
            return "Unlicensed"
        elif "Cease and Desist Order" in str(row['type']):
            return "Doctor of Osteopathic Medicine"
        elif "Cease and Desist" in str(row['type']):
            return "Unlicensed"
        elif row['doctor_type'] in str(row['doc_nameclean']):
            return np.nan
        else:
            return row['doctor_type']
    
    alert_textfiles['doctor_type'] = alert_textfiles.apply(apply_doctor_type_cases, axis=1)
    
    # Step 3: Separate names into components
    print("Separating names into components...")
    
    def separate_name(doc_nameclean):
        """Separate name into first, middle, last, suffix"""
        if pd.isna(doc_nameclean) or doc_nameclean == "":
            return ["", "", "", ""]
        
        # Split by whitespace, limit to 4 parts
        parts = str(doc_nameclean).split()
        
        # Pad with empty strings if needed
        while len(parts) < 4:
            parts.append("")
        
        # If more than 4 parts, merge extras into suffix
        if len(parts) > 4:
            suffix = " ".join(parts[3:])
            parts = parts[:3] + [suffix]
        
        return parts
    
    name_parts = alert_textfiles['doc_nameclean'].apply(separate_name)
    alert_textfiles[['first_name', 'middle_name', 'last_name', 'suffix']] = pd.DataFrame(
        name_parts.tolist(), index=alert_textfiles.index
    )
    
    # Step 4: Clean punctuation from name parts
    print("Cleaning punctuation from names...")
    
    for col in ['first_name', 'middle_name', 'last_name', 'suffix']:
        alert_textfiles[col] = alert_textfiles[col].apply(
            lambda x: re.sub(r'[,.]', '', str(x)) if pd.notna(x) else ""
        )
    
    # Step 5: Handle special cases for last_name
    def fix_last_name(row):
        """Apply special logic for last_name"""
        if row['last_name'] in ["Jr", ""] or pd.isna(row['last_name']):
            return row['middle_name']
        return row['last_name']
    
    alert_textfiles['last_name'] = alert_textfiles.apply(fix_last_name, axis=1)
    
    # Fix middle_name when it becomes last_name
    def fix_middle_name(row):
        """Clear middle_name if it's now the last_name"""
        if row['last_name'] == row['middle_name']:
            return ""
        return row['middle_name']
    
    alert_textfiles['middle_name'] = alert_textfiles.apply(fix_middle_name, axis=1)
    
    # Special case for Jeffery Dormu
    alert_textfiles.loc[alert_textfiles['last_name'] == 'Dormu', 'first_name'] = 'Jeffery'
    
    # Create clean_name
    alert_textfiles['clean_name'] = alert_textfiles['first_name'] + " " + alert_textfiles['last_name']
    alert_textfiles['clean_name'] = alert_textfiles['clean_name'].str.strip()
    
    # Step 6: Create doctor type mapping for unique names
    print("Creating doctor type mappings...")
    
    # Sort by doctor_type and keep only distinct clean_name entries
    doc_typecw = (alert_textfiles
                  .sort_values('doctor_type')
                  .drop_duplicates('clean_name', keep='first')
                  [['clean_name', 'doctor_type']]
                  .copy())
    
    # Apply standardized doctor type mappings
    def standardize_doctor_type(row):
        """Standardize doctor types with specific mappings"""
        doctor_type = str(row['doctor_type'])
        clean_name = str(row['clean_name'])
        
        if "RCP" in doctor_type:
            return "Respiratory Care Practitioner"
        elif any(name in clean_name for name in ["Poroj", "Gig", "Shawyer", "Wyrick"]):
            return "Radiographer"
        elif doctor_type == "PA":
            return "Physician Assistant"
        elif doctor_type == "PA-C":
            return "Certified Physician Assistant"
        elif doctor_type == "DO":
            return "Doctor of Osteopathic Medicine"
        elif doctor_type == "NMT":
            return "Nuclear Medicine Technologist"
        elif "RT" in doctor_type or "Therapist" in doctor_type:
            return "Respiratory Therapist"
        elif doctor_type == "ATC":
            return "Certified Athletic Trainer"
        elif doctor_type == "ND":
            return "Neuropathic Doctor"
        elif doctor_type == "MD":
            return "Doctor of Medicine"
        elif "Polysom" in doctor_type or "RPSGT" in doctor_type:
            return "Polysomnographic Technologist"
        else:
            return doctor_type
    
    doc_typecw['doctor_type'] = doc_typecw.apply(standardize_doctor_type, axis=1)
    
    # Step 7: Join back the cleaned doctor types
    print("Joining cleaned doctor types...")
    
    # Remove old doctor_type and join with cleaned version
    alert_textfiles = alert_textfiles.drop('doctor_type', axis=1)
    alert_textfiles = alert_textfiles.merge(doc_typecw, on='clean_name', how='left')
    
    # Step 8: Generate license numbers
    print("Generating license numbers...")
    
    def generate_license_number(row):
        """Generate license number from file_id"""
        if row['doctor_type'] == "Unlicensed":
            return "Unlicensed"
        
        file_id = str(row['file_id'])
        if len(file_id) < 6:
            return "Unlicensed"
        
        # Extract license number (remove last 6 characters)
        license_num = file_id[:-6]
        
        if not license_num:
            return "Unlicensed"
        
        # Extract letter and digits
        license_let = license_num[0].upper() if license_num else ""
        license_digits = re.sub(r'\D', '', license_num)
        
        if not license_digits:
            return "Unlicensed"
        
        # Format digits to 7 characters with leading zeros
        try:
            license_dig = f"{int(license_digits):07d}"
            return f"{license_let}{license_dig}"
        except ValueError:
            return "Unlicensed"
    
    alert_textfiles['license_num'] = alert_textfiles.apply(generate_license_number, axis=1)
    
    # Step 9: Select final columns and save
    print("Selecting final columns...")
    
    final_columns = [
        'file_id', 'url', 'clean_name', 'first_name', 'middle_name', 
        'last_name', 'suffix', 'doctor_type', 'type', 'year', 'filename', 'date', 'license_num'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in final_columns if col in alert_textfiles.columns]
    anti_clean = alert_textfiles[available_columns].copy()
    
    # Save to CSV
    print("Saving to clean_nametype.csv...")
    anti_clean.to_csv("clean_nametype.csv", index=False)
    
    print(f"✓ Successfully created clean_nametype.csv with {len(anti_clean)} rows")
    
    # Print some statistics
    print(f"\nStatistics:")
    print(f"  Total records: {len(anti_clean)}")
    print(f"  Unique doctors: {anti_clean['clean_name'].nunique()}")
    print(f"  Doctor types: {anti_clean['doctor_type'].nunique()}")
    print(f"  Licensed doctors: {(anti_clean['license_num'] != 'Unlicensed').sum()}")
    
    print(f"\nTop doctor types:")
    print(anti_clean['doctor_type'].value_counts().head())
    
    return anti_clean

if __name__ == "__main__":
    try:
        clean_alerts_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure modified_alerts.csv exists in the current directory")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
