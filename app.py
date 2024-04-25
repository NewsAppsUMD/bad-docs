import os
from peewee import *
from flask import Flask
from flask import render_template
app = Flask(__name__)
db = SqliteDatabase('bad_docs.db')

class Notice(Model):
    

    class Meta:
        

class Doctor(Model):
    

    class Meta:

@app.route("/")
def index():
    notice_count = Notice.select().count()
    all_zips = Doctor.select()
    template = 'index.html'
    return render_template(template, count = notice_count, all_zips = all_zips)

@app.route('/doctor/<slug>')
def detail(slug):
    zipcode = Doctor.get(Doctor.clean_name==slug)
    notices = Notice.select().where(Notice.zip==slug)
    total_notices = Notice.select(fn.SUM(Notice.notices).alias('sum')).where(Notice.zip==slug).scalar()
    notice_json = []
    for notice in notices:
        notice_json.append({'x': str(notice.month.year) + ' ' + str(notice.month.month), 'y': notice.zip, 'heat': notice.notices})
    return render_template("detail.html", zipcode=zipcode, notices=notices, notices_count=len(notices), notice_json = notice_json, total_notices = total_notices)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)