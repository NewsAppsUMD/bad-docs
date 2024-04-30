import os
from peewee import *
from flask import Flask
from flask import render_template
app = Flask(__name__)
db = SqliteDatabase('bad_docs.db')
        
class Doctor(Model):
    id = IntegerField(unique=True)
    clean_name = CharField()
    first_name = CharField()
    middle_name = CharField()
    last_name = CharField()
    suffix = CharField()
    doctor_type = CharField()
    license_num = CharField()
    
    class Meta:
        database = db
        table_name = 'doctor_info'

class Alert(Model):
    id = CharField(unique=True)
    text_id = CharField(unique=True)
    url = CharField(unique=True)
    doctor_info_id = IntegerField()
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

@app.route("/")
def index():
    notice_count = Doctor.select().count()
    all_docs = Doctor.select()
    template = 'index.html'
    return render_template(template, count = notice_count, all_docs = all_docs)

@app.route('/doctor/<slug>')
def detail(slug):
    doctor = Doctor.get(Doctor.clean_name==slug)
    doctor_id = doctor.id
    alerts = Alert.select().where(Alert.doctor_info_id==doctor_id)
    cases = []
    for alert in alerts:
        alert_id = alert.id
        case_nos = Cases.select().where(Cases.filename==alert_id)
        cases.append(case_nos)
    return render_template("doctor.html", doctor = doctor, cases = cases)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)