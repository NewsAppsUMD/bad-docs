import os
import json
import llm
import numpy as np
from peewee import *
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date
from datetime import datetime
app = Flask(__name__)
db = SqliteDatabase('bad_docs.db')
        
class Doctor(Model):
    id = IntegerField(unique=True)
    clean_name = CharField()
    doctor_type = CharField()
    license_num = CharField()
    
    class Meta:
        database = db
        table_name = 'doctor_info'

class Text(Model):
    id = IntegerField(unique=True)
    filename = CharField()
    text = CharField()

    class Meta:
        database = db
        table_name = 'text'

class Alert(Model):
    id = CharField(unique=True)
    file_id = CharField(unique=True)
    text_id = ForeignKeyField(Text)
    url = CharField(unique=True)
    doctor_info_id = ForeignKeyField(Doctor)
    first_name = CharField()
    middle_name = CharField()
    last_name = CharField()
    suffix = CharField()
    type = CharField()
    year = IntegerField()
    date = DateField()
    date_str = CharField()
    
    class Meta:
        database = db
        table_name = 'clean_alerts'

class Cases(Model):
    id  = IntegerField(unique=True)
    case_num = CharField()
    file_id = CharField()
    alert_id = ForeignKeyField(Alert)

    class Meta:
        database = db
        table_name = 'all_cases'

class DocumentJSON(Model):
    id = AutoField(primary_key=True)
    filename = CharField()  # links to Text.filename
    respondent = CharField()
    license_number = CharField()
    date = DateField()
    summary = TextField()
    keywords = CharField()  # store as comma-separated
    embedding = BlobField(null=True)  # Store embeddings as binary data
    
    class Meta:
        database = db
        table_name = 'document_json'

# Similarity search functions
def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b)

def get_embedding_for_text(text, model_name="nomic-embed-text"):
    """Generate embedding for given text"""
    try:
        model = llm.get_embedding_model(model_name)
        return model.embed(text)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def similarity_search(query_text, limit=5, exclude_filename=None):
    """Find documents similar to the query text"""
    query_embedding = get_embedding_for_text(query_text)
    if query_embedding is None:
        return []
    
    # Get all documents with embeddings
    documents = DocumentJSON.select().where(DocumentJSON.embedding.is_null(False))
    
    # Exclude the original document if specified
    if exclude_filename:
        documents = documents.where(DocumentJSON.filename != exclude_filename)
    
    similarities = []
    
    for doc in documents:
        try:
            # Decode the stored embedding
            doc_embedding = json.loads(doc.embedding.decode('utf-8'))
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))
        except Exception as e:
            print(f"Error processing document {doc.filename}: {e}")
            continue
    
    # Sort by similarity (highest first) and return top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [(doc, sim) for doc, sim in similarities[:limit]]

@app.route("/")
def index():
    notice_count = Doctor.select().count()
    all_docs = Doctor.select()
    template = 'index.html'
    top_five = Alert.select().order_by(Alert.date.desc()).limit(5)
    # Get alert counts by doctor type (join alerts with doctors) ordered by count
    type_table = (Doctor
                  .select(Doctor.doctor_type, fn.COUNT(Alert.id).alias('count'))
                  .join(Alert)
                  .group_by(Doctor.doctor_type)
                  .order_by(fn.COUNT(Alert.id).desc()))
    
    # New JSON-based stats
    recent_docs = []
    top_keywords = []
    
    try:
        # Get recent documents with their corresponding alerts
        recent_json_docs = DocumentJSON.select().order_by(DocumentJSON.date.desc()).limit(4)
        
        for json_doc in recent_json_docs:
            # Find corresponding text document
            try:
                text_doc = Text.get(Text.filename == json_doc.filename)
                # Find corresponding alert
                try:
                    alert = Alert.get(Alert.text_id == text_doc.id)
                    recent_docs.append({
                        'json_doc': json_doc,
                        'alert': alert
                    })
                except Alert.DoesNotExist:
                    # If no alert, just include the JSON doc
                    recent_docs.append({
                        'json_doc': json_doc,
                        'alert': None
                    })
            except Text.DoesNotExist:
                # If no text doc, just include the JSON doc
                recent_docs.append({
                    'json_doc': json_doc,
                    'alert': None
                })
        
        # Top keywords
        all_json_docs = DocumentJSON.select()
        keyword_counts = {}
        for doc in all_json_docs:
            if doc.keywords:
                keywords = [k.strip().lower() for k in doc.keywords.split(',')]
                for keyword in keywords:
                    if keyword:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    except:
        pass  # If DocumentJSON table doesn't exist or has no data
    
    return render_template(template, 
                         top_five=top_five, 
                         type_table=type_table,
                         recent_docs=recent_docs,
                         top_keywords=top_keywords)

@app.route("/similarity_search", methods=['POST'])
def similarity_search_route():
    """Handle similarity search requests"""
    query = request.form.get('query', '').strip()
    if not query:
        return jsonify({'error': 'No query provided'})
    
    try:
        results = similarity_search(query, limit=10)
        search_results = []
        for doc, similarity in results:
            search_results.append({
                'filename': doc.filename,
                'respondent': doc.respondent,
                'date': str(doc.date),
                'summary': doc.summary[:200] + ('...' if len(doc.summary) > 200 else ''),
                'similarity': round(similarity, 3),
                'pdf_url': f"https://www.mbp.state.md.us/BPQAPP/orders/{doc.filename.replace('.txt', '')}.pdf"
            })
        
        return jsonify({
            'query': query,
            'results': search_results,
            'count': len(search_results)
        })
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'})

@app.route("/similarity_search_results", methods=['POST'])
def similarity_search_results():
    """Handle similarity search and return results page"""
    query = request.form.get('query', '').strip()
    if not query:
        return render_template('similarity_results.html', error="No query provided", results=[])
    
    try:
        # Try to find if this query is actually a document summary (to exclude it from results)
        exclude_filename = None
        try:
            # Check if the query matches any document's summary exactly
            matching_doc = DocumentJSON.get(DocumentJSON.summary == query)
            exclude_filename = matching_doc.filename
        except DocumentJSON.DoesNotExist:
            # Query is not an exact document summary, proceed normally
            pass
        
        results = similarity_search(query, limit=10, exclude_filename=exclude_filename)
        search_results = []
        for doc, similarity in results:
            search_results.append({
                'doc': doc,
                'similarity': round(similarity, 3),
                'pdf_url': f"https://www.mbp.state.md.us/BPQAPP/orders/{doc.filename.replace('.txt', '')}.pdf"
            })
        
        return render_template('similarity_results.html', 
                             query=query, 
                             results=search_results,
                             count=len(search_results))
    except Exception as e:
        return render_template('similarity_results.html', 
                             error=f'Search failed: {str(e)}', 
                             results=[],
                             query=query)

'''@app.route("/searchdocs", methods=['POST'])
def searchdocs():
    # Get search term from form
    top_five = Alert.select().order_by(Alert.date.desc()).limit(5)
    type_table = Doctor.select(Doctor.doctor_type, fn.COUNT(Doctor.doctor_type).alias('count')).group_by(Doctor.doctor_type)
    search_term = request.form.get('search_term')
    if search_term == "":
        results = "No doctor results found"
    else:
        results = Doctor.select().where(Doctor.clean_name.contains(search_term) | Doctor.license_num.contains(search_term))
    return render_template('index.html', resultsd=results, search_term=search_term, top_five = top_five, type_table=type_table)

@app.route("/searchtext", methods=['POST'])
def searchtext():
    # Get search term from form
    top_five = Alert.select().order_by(Alert.date.desc()).limit(5)
    type_table = Doctor.select(Doctor.doctor_type, fn.COUNT(Doctor.doctor_type).alias('count')).group_by(Doctor.doctor_type)
    search_term = request.form.get('search_term')
    if search_term == "":
        results = "No text results found"
    else:
        textresults = Text.select().where(Text.text.contains(search_term))
        alerts = Alert.select().where(Alert.text_id.in_(textresults))
    return render_template('index.html', resultst=alerts, search_term=search_term, top_five = top_five, type_table = type_table)'''

@app.route("/search", methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search.html')
    
    search_term = request.form.get('search_term', '').strip()
    search_type = request.form.get('search_type', 'all')  # all, summary, fulltext, keywords
    
    if not search_term:
        return render_template('search.html', error="Please enter a search term")
    
    results = []
    
    if search_type in ['all', 'summary']:
        # Search summaries
        try:
            json_results = DocumentJSON.select().where(
                DocumentJSON.summary.contains(search_term)
            )
            results.extend(list(json_results))
        except:
            pass
    
    if search_type in ['all', 'fulltext']:
        # Search full text
        try:
            text_results = Text.select().where(Text.text.contains(search_term))
            results.extend(list(text_results))
        except:
            pass
    
    if search_type in ['all', 'keywords']:
        # Search keywords
        try:
            keyword_results = DocumentJSON.select().where(
                DocumentJSON.keywords.contains(search_term.lower())
            )
            results.extend(list(keyword_results))
        except:
            pass
    
    return render_template('search_results.html', 
                         results=results, 
                         search_term=search_term,
                         search_type=search_type)

@app.route("/searchdocs")
def searchdocs():
    # Redirect to new search page
    return redirect(url_for('search'))

@app.route("/searchtext")
def searchtext():
    # Redirect to new search page
    return redirect(url_for('search'))

@app.route('/doctor/<slug>')
def detail(slug):
    doctor = Doctor.get(Doctor.clean_name==slug)
    doctor_id = doctor.id
    alerts = Alert.select().where(Alert.doctor_info_id==doctor_id).order_by(Alert.date.desc())
    cases = Cases.select(Cases.case_num).where(Cases.alert_id.in_(alerts)).distinct()
    top_record = alerts[0] if alerts else None
    
    # Get document summaries for this doctor
    summaries = []
    try:
        # Find text documents linked to this doctor's alerts
        for alert in alerts:
            try:
                text_doc = Text.get(Text.id == alert.text_id)
                # Find corresponding JSON document with summary
                try:
                    json_doc = DocumentJSON.get(DocumentJSON.filename == text_doc.filename)
                    summaries.append({
                        'alert': alert,
                        'json_doc': json_doc,
                        'pdf_url': f"https://www.mbp.state.md.us/BPQAPP/orders/{json_doc.filename.replace('.txt', '')}.pdf"
                    })
                except DocumentJSON.DoesNotExist:
                    pass
            except Text.DoesNotExist:
                pass
    except:
        pass
    
    return render_template("doctor.html", doctor = doctor, cases = cases, top_record = top_record, alerts = alerts, summaries = summaries)

@app.route('/document/<filename>')
def document_detail(filename):
    # Get the text content
    try:
        text_doc = Text.get(Text.filename == filename)
    except Text.DoesNotExist:
        return "Document not found", 404
    
    # Get the JSON data
    try:
        json_doc = DocumentJSON.get(DocumentJSON.filename == filename)
    except DocumentJSON.DoesNotExist:
        json_doc = None
    
    # Get related alert if exists
    try:
        alert = Alert.get(Alert.text_id == text_doc.id)
    except Alert.DoesNotExist:
        alert = None
    
    # Build PDF URL
    pdf_url = f"https://www.mbp.state.md.us/BPQAPP/orders/{filename.replace('.txt', '.pdf')}"
    
    return render_template('document_detail.html', 
                         text_doc=text_doc,
                         json_doc=json_doc,
                         alert=alert,
                         pdf_url=pdf_url)

@app.route('/type/<slug>')
def type(slug):
    doctors = Doctor.select().where(Doctor.doctor_type==slug)
    count_doc = doctors.count()
    alerts = Alert.select().where(Alert.doctor_info_id.in_(doctors))
    count_alerts = alerts.count()
    cases = Cases.select().join(Alert).where(Cases.alert_id.in_(alerts)).order_by(Alert.date.desc())
    count_cases = cases.count()
    c1 = cases[0]
    return render_template("type.html", doctors = doctors, alerts = alerts, cases = cases, 
                           countd = count_doc, counta = count_alerts, countc = count_cases, c1 = c1)

@app.route('/keywords')
def browse_keywords():
    # Get all keywords and their frequencies
    try:
        all_docs = DocumentJSON.select()
        keyword_counts = {}
        
        for doc in all_docs:
            if doc.keywords:
                # Keywords are stored as comma-separated
                keywords = [k.strip().lower() for k in doc.keywords.split(',')]
                for keyword in keywords:
                    if keyword:  # Skip empty keywords
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        
        return render_template('keywords.html', keywords=sorted_keywords)
    except:
        return render_template('keywords.html', keywords=[], error="No keyword data available")

@app.route('/keyword/<keyword>')
def keyword_detail(keyword):
    # Find all documents with this keyword
    try:
        docs = DocumentJSON.select().where(DocumentJSON.keywords.contains(keyword.lower()))
        return render_template('keyword_detail.html', keyword=keyword.lower(), documents=docs)
    except:
        return render_template('keyword_detail.html', keyword=keyword.lower(), documents=[], error="No documents found")

# Route for search form submission
@app.route("/dataset")
def dataset():
    cases = Cases.select().join(Alert).order_by(Alert.date.desc())
    return render_template("dataset.html", cases = cases)

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)