import os
from peewee import *
from flask import Flask, render_template, request, redirect, url_for
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
    
    class Meta:
        database = db
        table_name = 'clean_alerts'

class Cases(Model):
    id  = IntegerField(unique=True)
    case_num = CharField()
    filename = CharField()

    class Meta:
        database = db
        table_name = 'all_cases'


@app.errorhandler(404)
def _404(e):
    render_template("not_found.html")

@app.route("/")
def index():
    notice_count = Doctor.select().count()
    all_docs = Doctor.select()
    template = 'index.html'
    top_five = Alert.select().order_by(Alert.date.desc()).limit(5)
    return render_template(template, top_five = top_five)

'''# Route for search form submission
@app.route("/redirect", methods=['POST'])
def search():
    # Get search term from form
    search_term = request.form.get('search_term')
    # Search for vendors containing the search term in payee name and order by amount
    search_result = Doctor.select().where(Doctor.clean_name.contains(search_term) | Doctor.license_num.contains(search_term))
    slug = search_result[0].clean_name
    # Redirect to jurisdiction page with slug parameter
    return redirect(url_for("detail", slug=slug))'''

@app.route("/searchdocs", methods=['POST'])
def searchdocs():
    # Get search term from form
    top_five = Alert.select().order_by(Alert.date.desc()).limit(5)
    search_term = request.form.get('search_term')
    if search_term == "":
        results = None
    else:
        results = Doctor.select().where(Doctor.clean_name.contains(search_term) | Doctor.license_num.contains(search_term))
    return render_template('index.html', resultsd=results, search_term=search_term, top_five = top_five)

@app.route("/searchtext", methods=['POST'])
def searchtext():
    # Get search term from form
    top_five = Alert.select().order_by(Alert.date.desc()).limit(5)
    search_term = request.form.get('search_term')
    if search_term == "":
        results = None
    else:
        textresults = Text.select().where(Text.text.contains(search_term))
        alerts = Alert.select().where(Alert.text_id.in_(textresults))
    return render_template('index.html', resultst=alerts, search_term=search_term, top_five = top_five)

@app.route('/doctor/<slug>')
def detail(slug):
    doctor = Doctor.get(Doctor.clean_name==slug)
    doctor_id = doctor.id
    alerts = Alert.select().where(Alert.doctor_info_id==doctor_id)
    cases = []
    for alert in alerts:
        alert_id = alert.id
        case_nos = Cases.select().where(Cases.filename==alert_id)
        for case in case_nos:
            cases.append(case)
    top_record = alerts[0]
    return render_template("doctor.html", doctor = doctor, cases = cases, top_record = top_record)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)