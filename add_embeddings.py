#!/usr/bin/env python3
"""
Script to generate and store embeddings for document summaries using the llm library.
"""

import llm
import json
import argparse
from peewee import *
from playhouse.sqlite_ext import *

# Database setup
db = SqliteExtDatabase('bad_docs.db')

class DocumentJSON(Model):
    id = AutoField(primary_key=True)
    filename = CharField()
    respondent = CharField()
    license_number = CharField()
    date = DateField()
    summary = TextField()
    keywords = CharField()
    embedding = BlobField(null=True)  # Store embeddings as binary data
    
    class Meta:
        database = db
        table_name = 'document_json'

def add_embedding_column():
    """Add embedding column if it doesn't exist"""
    try:
        # Try to add the column
        db.execute_sql('ALTER TABLE document_json ADD COLUMN embedding BLOB')
        print("Added embedding column to document_json table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("Embedding column already exists")
        else:
            print(f"Error adding embedding column: {e}")

def generate_embeddings(model_name="nomic-embed-text", force_regenerate=False):
    """
    Generate embeddings for all document summaries.
    
    Args:
        model_name: The embedding model to use
        force_regenerate: If True, regenerate embeddings even if they exist
    """
    
    # Connect to database
    db.connect()
    
    # Add embedding column if needed
    add_embedding_column()
    
    # Get the embedding model
    try:
        # Try to get embedding model specifically
        model = llm.get_embedding_model(model_name)
        print(f"Using embedding model: {model_name}")
    except Exception as e:
        print(f"Error loading embedding model {model_name}: {e}")
        try:
            # Fallback to regular model if it supports embeddings
            model = llm.get_model(model_name)
            if not hasattr(model, 'embed'):
                raise Exception(f"Model {model_name} does not support embeddings")
            print(f"Using model with embedding support: {model_name}")
        except Exception as e2:
            print(f"Error loading model {model_name}: {e2}")
            print("Available embedding models:")
            import subprocess
            try:
                result = subprocess.run(['uv', 'run', 'llm', 'embed-models'], 
                                      capture_output=True, text=True, check=True)
                print(result.stdout)
            except:
                pass
            return
    
    # Get documents that need embeddings
    if force_regenerate:
        documents = DocumentJSON.select().where(DocumentJSON.summary.is_null(False))
        print(f"Regenerating embeddings for all {documents.count()} documents")
    else:
        documents = DocumentJSON.select().where(
            (DocumentJSON.summary.is_null(False)) & 
            (DocumentJSON.embedding.is_null(True))
        )
        print(f"Generating embeddings for {documents.count()} documents without embeddings")
    
    success_count = 0
    error_count = 0
    
    for doc in documents:
        try:
            # Generate embedding for the summary
            embedding = model.embed(doc.summary)
            
            # Convert embedding to JSON and then to bytes for storage
            embedding_json = json.dumps(embedding).encode('utf-8')
            
            # Update the document with the embedding
            doc.embedding = embedding_json
            doc.save()
            
            success_count += 1
            print(f"✓ Generated embedding for {doc.filename} ({doc.respondent})")
            
        except Exception as e:
            error_count += 1
            print(f"✗ Error generating embedding for {doc.filename}: {e}")
    
    print(f"\nCompleted: {success_count} successful, {error_count} errors")
    
    # Close database connection
    db.close()

def list_embedding_models():
    """List available embedding models"""
    import subprocess
    try:
        result = subprocess.run(['uv', 'run', 'llm', 'embed-models'], 
                              capture_output=True, text=True, check=True)
        print("Available embedding models:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing models: {e}")
        print("Fallback - checking llm models:")
        for model in llm.get_models():
            print(f"  - {model.model_id}")

def show_stats():
    """Show statistics about embeddings in the database"""
    db.connect()
    
    total_docs = DocumentJSON.select().count()
    docs_with_embeddings = DocumentJSON.select().where(DocumentJSON.embedding.is_null(False)).count()
    docs_without_embeddings = total_docs - docs_with_embeddings
    
    print(f"Embedding Statistics:")
    print(f"  Total documents: {total_docs}")
    print(f"  Documents with embeddings: {docs_with_embeddings}")
    print(f"  Documents without embeddings: {docs_without_embeddings}")
    
    if docs_with_embeddings > 0:
        # Show a sample embedding info
        sample_doc = DocumentJSON.select().where(DocumentJSON.embedding.is_null(False)).first()
        if sample_doc:
            embedding_data = json.loads(sample_doc.embedding.decode('utf-8'))
            print(f"  Embedding dimensions: {len(embedding_data)}")
    
    db.close()

def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for document summaries")
    parser.add_argument("--model", default="text-embedding-004", 
                       help="Embedding model to use (default: text-embedding-004)")
    parser.add_argument("--force", action="store_true", 
                       help="Regenerate embeddings even if they exist")
    parser.add_argument("--list-models", action="store_true", 
                       help="List available embedding models")
    parser.add_argument("--stats", action="store_true", 
                       help="Show embedding statistics")
    
    args = parser.parse_args()
    
    if args.list_models:
        list_embedding_models()
    elif args.stats:
        show_stats()
    else:
        generate_embeddings(args.model, args.force)

if __name__ == "__main__":
    main()
