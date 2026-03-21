import os
import re
import json
import logging
import llm
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, jsonify
from peewee import fn, OperationalError
from models import db, Doctor, Text, Alert, Cases, DocumentJSON

app = Flask(__name__)

def doctor_slug(doctor):
    """Generate a URL slug from doctor name + license number."""
    name = re.sub(r'[^a-z0-9]+', '-', doctor.clean_name.lower()).strip('-')
    return f"{name}-{doctor.license_num.lower()}"

def doctor_slug_for_license(license_num):
    """Look up a doctor by license number and return their URL slug, or None."""
    try:
        doctor = Doctor.get(Doctor.license_num == license_num)
        return doctor_slug(doctor)
    except Doctor.DoesNotExist:
        # Try zero-padding numeric part (e.g. D90487 -> D0090487)
        match = re.match(r'^([A-Za-z])(\d+)$', license_num)
        if match:
            padded = f"{match.group(1)}{match.group(2).zfill(7)}"
            try:
                doctor = Doctor.get(Doctor.license_num == padded)
                return doctor_slug(doctor)
            except Doctor.DoesNotExist:
                pass
        return None

def keyword_slug(keyword):
    """Generate a URL slug from a keyword (e.g. 'prescription fraud' -> 'prescription-fraud')."""
    return re.sub(r'[^a-z0-9]+', '-', keyword.strip().lower()).strip('-')

def keyword_unslug(slug):
    """Convert a keyword slug back to a keyword (e.g. 'prescription-fraud' -> 'prescription fraud')."""
    return slug.replace('-', ' ')

def type_slug(doctor_type):
    """Generate a URL slug from a doctor type (e.g. 'Doctor of Medicine' -> 'doctor-of-medicine')."""
    return re.sub(r'[^a-z0-9]+', '-', doctor_type.strip().lower()).strip('-')

app.jinja_env.globals['doctor_slug'] = doctor_slug
app.jinja_env.globals['doctor_slug_for_license'] = doctor_slug_for_license
app.jinja_env.globals['keyword_slug'] = keyword_slug
app.jinja_env.globals['type_slug'] = type_slug
logger = logging.getLogger(__name__)

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
        logger.error(f"Error generating embedding: {e}")
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
            logger.error(f"Error processing document {doc.filename}: {e}")
            continue

    # Sort by similarity (highest first) and return top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [(doc, sim) for doc, sim in similarities[:limit]]

TOPIC_CATEGORIES = {
    'Prescribing & Drugs': ['opioids', 'controlled substances', 'prescription fraud', 'substance abuse', 'prescribing', 'drug diversion', 'controlled dangerous substances', 'medications', 'prescription'],
    'Patient Harm': ['negligence', 'malpractice', 'patient death', 'sexual misconduct', 'incompetence', 'patient safety', 'standard of care', 'boundary violations', 'sexual abuse'],
    'Licensing & Fraud': ['unlicensed practice', 'false credentials', 'insurance fraud', 'fraud', 'misrepresentation', 'unauthorized practice', 'false statements'],
    'Impairment': ['alcohol', 'drug use', 'mental health', 'impairment', 'rehabilitation', 'substance use disorder'],
}

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

    # Dashboard stats
    doctor_count = Doctor.select().count()
    alert_count = Alert.select().count()

    most_common_action_row = (Alert
                              .select(Alert.type, fn.COUNT(Alert.id).alias('cnt'))
                              .group_by(Alert.type)
                              .order_by(fn.COUNT(Alert.id).desc())
                              .limit(1)
                              .first())
    most_common_action = most_common_action_row.type if most_common_action_row else None

    most_common_type_row = (Doctor
                            .select(Doctor.doctor_type, fn.COUNT(Doctor.id).alias('cnt'))
                            .group_by(Doctor.doctor_type)
                            .order_by(fn.COUNT(Doctor.id).desc())
                            .limit(1)
                            .first())
    most_common_type = most_common_type_row.doctor_type if most_common_type_row else None

    # Recent activity feed - use Alert as primary source (most up-to-date)
    recent_alerts = (Alert
                     .select(Alert, Doctor)
                     .join(Doctor, on=(Alert.doctor_info_id == Doctor.id))
                     .order_by(Alert.date.desc())
                     .limit(5))

    recent_docs = []
    for alert in recent_alerts:
        # Try to find a DocumentJSON summary for this alert
        json_doc = None
        try:
            text_doc = Text.get(Text.id == alert.text_id)
            try:
                json_doc = DocumentJSON.get(DocumentJSON.filename == text_doc.filename)
            except DocumentJSON.DoesNotExist:
                pass
        except Text.DoesNotExist:
            pass
        recent_docs.append({
            'alert': alert,
            'doctor': alert.doctor_info_id,
            'json_doc': json_doc,
        })

    top_keywords = []

    try:

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
    except OperationalError:
        keyword_counts = {}
        logger.warning("DocumentJSON table not available")

    # Build topic categories from keyword_counts
    topic_categories = {}
    for category, cat_keywords in TOPIC_CATEGORIES.items():
        matched = []
        for kw in cat_keywords:
            count = keyword_counts.get(kw, 0)
            if count > 0:
                matched.append((kw, count))
        if matched:
            matched.sort(key=lambda x: x[1], reverse=True)
            topic_categories[category] = matched

    return render_template(template,
                         top_five=top_five,
                         type_table=type_table,
                         recent_docs=recent_docs,
                         top_keywords=top_keywords,
                         doctor_count=doctor_count,
                         alert_count=alert_count,
                         most_common_action=most_common_action,
                         most_common_type=most_common_type,
                         topic_categories=topic_categories)

@app.route("/api/doctor_search")
def doctor_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    doctors = (Doctor
               .select(Doctor.clean_name, Doctor.doctor_type, Doctor.license_num)
               .where(Doctor.clean_name.contains(q))
               .limit(10))
    results = [{'clean_name': d.clean_name, 'doctor_type': d.doctor_type, 'license_num': d.license_num, 'slug': doctor_slug(d)} for d in doctors]
    return jsonify(results)

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
        logger.error(f"Similarity search failed: {e}")
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
            matching_doc = DocumentJSON.get(DocumentJSON.summary == query)
            exclude_filename = matching_doc.filename
        except DocumentJSON.DoesNotExist:
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
        logger.error(f"Similarity search results failed: {e}")
        return render_template('similarity_results.html',
                             error=f'Search failed: {str(e)}',
                             results=[],
                             query=query)

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
        try:
            json_results = DocumentJSON.select().where(
                DocumentJSON.summary.contains(search_term)
            )
            results.extend(list(json_results))
        except OperationalError:
            logger.warning("DocumentJSON table not available for summary search")

    if search_type in ['all', 'fulltext']:
        try:
            text_results = Text.select().where(Text.text.contains(search_term))
            results.extend(list(text_results))
        except OperationalError:
            logger.warning("Text table not available for fulltext search")

    if search_type in ['all', 'keywords']:
        try:
            keyword_results = DocumentJSON.select().where(
                DocumentJSON.keywords.contains(search_term.lower())
            )
            results.extend(list(keyword_results))
        except OperationalError:
            logger.warning("DocumentJSON table not available for keyword search")

    return render_template('search_results.html',
                         results=results,
                         search_term=search_term,
                         search_type=search_type)

@app.route("/searchdocs")
def searchdocs():
    return redirect(url_for('search'))

@app.route("/searchtext")
def searchtext():
    return redirect(url_for('search'))

STATUS_COLORS = {
    'License Permanently Revoked': 'danger',
    'License Revoked': 'danger',
    'License Surrendered': 'danger',
    'Suspended': 'warning',
    'On Probation': 'warning',
    'Reinstated': 'success',
    'Suspension Terminated': 'success',
    'Reprimanded': 'info',
    'Fined': 'info',
}

@app.route('/doctor/<slug>')
def detail(slug):
    # Extract license number from end of slug (e.g. "joan-smith-h0048286" or "foo-unlicensed")
    license_match = re.search(r'-([a-z]\d{7})$', slug, re.IGNORECASE)
    if license_match:
        license_num = license_match.group(1).upper()
        doctor = Doctor.get(Doctor.license_num == license_num)
    elif slug.endswith('-unlicensed'):
        # Derive name from slug prefix
        name_part = slug.rsplit('-unlicensed', 1)[0].replace('-', ' ').title()
        doctor = Doctor.get((Doctor.clean_name == name_part) & (Doctor.license_num == 'Unlicensed'))
    else:
        # Fallback: try matching by clean_name for old-style URLs
        doctor = Doctor.get(Doctor.clean_name == slug)
    doctor_id = doctor.id
    alerts = Alert.select().where(Alert.doctor_info_id==doctor_id).order_by(Alert.date.desc())
    cases = Cases.select(Cases.case_num).where(Cases.alert_id.in_(alerts)).distinct()
    top_record = alerts[0] if alerts else None

    # Get document summaries for this doctor
    summaries = []
    for alert in alerts:
        try:
            text_doc = Text.get(Text.id == alert.text_id)
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

    # Status badge from pre-computed doctor.status
    status_color = STATUS_COLORS.get(doctor.status, 'secondary') if doctor.status else None

    return render_template("doctor.html", doctor=doctor, cases=cases, top_record=top_record, alerts=alerts, summaries=summaries, status_color=status_color)

@app.route('/document/<filename>')
def document_detail(filename):
    try:
        text_doc = Text.get(Text.filename == filename)
    except Text.DoesNotExist:
        return "Document not found", 404

    try:
        json_doc = DocumentJSON.get(DocumentJSON.filename == filename)
    except DocumentJSON.DoesNotExist:
        json_doc = None

    try:
        alert = Alert.get(Alert.text_id == text_doc.id)
    except Alert.DoesNotExist:
        alert = None

    pdf_url = f"https://www.mbp.state.md.us/BPQAPP/orders/{filename.replace('.txt', '.pdf')}"

    return render_template('document_detail.html',
                         text_doc=text_doc,
                         json_doc=json_doc,
                         alert=alert,
                         pdf_url=pdf_url)

@app.route('/type/<slug>')
def type(slug):
    # Find the doctor_type whose slug matches
    all_types = Doctor.select(Doctor.doctor_type).distinct()
    doctor_type = None
    for t in all_types:
        if type_slug(t.doctor_type) == slug:
            doctor_type = t.doctor_type
            break
    if doctor_type is None:
        return "Type not found", 404
    doctors = Doctor.select().where(Doctor.doctor_type == doctor_type)
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
    try:
        all_docs = DocumentJSON.select()
        keyword_counts = {}

        for doc in all_docs:
            if doc.keywords:
                keywords = [k.strip().lower() for k in doc.keywords.split(',')]
                for keyword in keywords:
                    if keyword:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)

        return render_template('keywords.html', keywords=sorted_keywords)
    except OperationalError:
        return render_template('keywords.html', keywords=[], error="No keyword data available")

@app.route('/keyword/<slug>')
def keyword_detail(slug):
    keyword = keyword_unslug(slug)
    try:
        docs = DocumentJSON.select().where(DocumentJSON.keywords.contains(keyword)).order_by(DocumentJSON.date.desc())
        return render_template('keyword_detail.html', keyword=keyword, documents=docs)
    except OperationalError:
        return render_template('keyword_detail.html', keyword=keyword, documents=[], error="No documents found")

@app.route("/dataset")
def dataset():
    cases = Cases.select().join(Alert).order_by(Alert.date.desc())
    return render_template("dataset.html", cases = cases)

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
