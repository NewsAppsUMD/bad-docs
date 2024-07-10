from flask_frozen import Freezer
from app import *
freezer = Freezer(app)

@freezer.register_generator
def detail():
    for doctor in Doctor.select():
        yield {'slug': doctor.clean_name}

def type():
    doctors = Doctor.select(Doctor.doctor_type).distinct()
    for doctor in doctors:
        yield {'slug': doctor.doctor_type}

def dataset():
    yield '/dataset.html'

def contact():
    yield '/contact.html'


if __name__ == '__main__':
    freezer.freeze()