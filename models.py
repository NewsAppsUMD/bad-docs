"""Shared Peewee database models for MD Medical Discipline Watch."""

import os
from peewee import *

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bad_docs.db')
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Doctor(BaseModel):
    id = IntegerField(unique=True)
    clean_name = CharField()
    doctor_type = CharField()
    license_num = CharField()

    class Meta:
        table_name = 'doctor_info'


class Text(BaseModel):
    id = IntegerField(unique=True)
    filename = CharField()
    text = CharField()

    class Meta:
        table_name = 'text'


class Alert(BaseModel):
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
        table_name = 'clean_alerts'


class Cases(BaseModel):
    id = IntegerField(unique=True)
    case_num = CharField()
    file_id = CharField()
    alert_id = ForeignKeyField(Alert)

    class Meta:
        table_name = 'all_cases'


class DocumentJSON(BaseModel):
    id = AutoField(primary_key=True)
    filename = CharField()
    respondent = CharField()
    license_number = CharField()
    date = DateField()
    summary = TextField()
    keywords = CharField()
    embedding = BlobField(null=True)

    class Meta:
        table_name = 'document_json'
