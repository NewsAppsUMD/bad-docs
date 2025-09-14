#!/usr/bin/env python3
"""Populate DocumentJSON table from generated JSON files."""

import json
from pathlib import Path
from datetime import datetime
from app import DocumentJSON, db

def populate_json_data():
    """Read JSON files from json/ directory and populate DocumentJSON table."""
    json_dir = Path("json")
    
    if not json_dir.exists():
        print(f"JSON directory '{json_dir}' does not exist")
        return
    
    # Create table if it doesn't exist
    try:
        db.create_tables([DocumentJSON])
        print("Created DocumentJSON table")
    except Exception as e:
        print(f"Table may already exist: {e}")
    
    processed = 0
    errors = 0
    
    with db.atomic():
        for json_file in json_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate required fields
                required_fields = ['respondent', 'license_number', 'date', 'summary', 'keywords']
                if not all(field in data for field in required_fields):
                    print(f"Missing required fields in {json_file.name}")
                    errors += 1
                    continue
                
                # Convert date string to date object
                try:
                    date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
                except ValueError:
                    print(f"Invalid date format in {json_file.name}: {data['date']}")
                    errors += 1
                    continue
                
                # Check if record already exists
                filename = json_file.stem + '.txt'
                try:
                    existing = DocumentJSON.get(DocumentJSON.filename == filename)
                    print(f"Record already exists for {filename}, skipping")
                    continue
                except DocumentJSON.DoesNotExist:
                    pass
                
                # Create new record
                DocumentJSON.create(
                    filename=filename,
                    respondent=data['respondent'][:255] if len(data['respondent']) > 255 else data['respondent'],
                    license_number=data['license_number'][:255] if len(data['license_number']) > 255 else data['license_number'],
                    date=date_obj,
                    summary=data['summary'],
                    keywords=','.join([kw.lower() for kw in data['keywords']]) if isinstance(data['keywords'], list) else str(data['keywords']).lower()
                )
                processed += 1
                print(f"Processed {json_file.name}")
                
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in {json_file.name}: {e}")
                errors += 1
            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")
                errors += 1
    
    print(f"\nCompleted: {processed} records processed, {errors} errors")

def show_stats():
    """Show statistics about the populated data."""
    try:
        total_docs = DocumentJSON.select().count()
        print(f"Total documents in database: {total_docs}")
        
        if total_docs > 0:
            # Show recent documents
            recent = DocumentJSON.select().order_by(DocumentJSON.date.desc()).limit(5)
            print("\nMost recent documents:")
            for doc in recent:
                print(f"  {doc.filename}: {doc.respondent} ({doc.date})")
            
            # Show keyword statistics
            all_docs = DocumentJSON.select()
            keyword_counts = {}
            for doc in all_docs:
                if doc.keywords:
                    keywords = [k.strip().lower() for k in doc.keywords.split(',')]
                    for keyword in keywords:
                        if keyword:
                            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            if keyword_counts:
                top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                print(f"\nTop keywords:")
                for keyword, count in top_keywords:
                    print(f"  {keyword}: {count}")
    
    except Exception as e:
        print(f"Error showing stats: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate DocumentJSON table from JSON files')
    parser.add_argument('--stats', action='store_true', help='Show statistics after population')
    args = parser.parse_args()
    
    populate_json_data()
    
    if args.stats:
        show_stats()
