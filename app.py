import os
from peewee import *
from flask import Flask
from flask import render_template
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

class Alert(Model):
    filename = CharField(unique=True)
    text_id = CharField(unique=True)
    url = CharField(unique=True)
    doctor_info_id = IntegerField()
    first_name = CharField()
    middle_name = CharField()
    last_name = CharField()
    suffix = CharField()
    type = CharField()
    year = IntegerField()
    date = DateField()
    case_num = CharField()
    
    class Meta:
        database = db
        table_name = 'clean_alerts'

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
    notices = Alert.select().where(Alert.doctor_info_id==id)
    return render_template("doctor.html", doctor = doctor)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)