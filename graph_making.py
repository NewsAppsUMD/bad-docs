from datawrapper import Datawrapper
import pandas as pd
import os
from sqlite_utils import *

db = Database('bad_docs.db')

dw=Datawrapper(os.environ.get('DATAWRAPPER_API'))

type_data = db.table("doctor_info")

all_types = ["Doctor of Medicine", "Radiographer", "Respiratory Care Practitioner", "Physician Assistant", "Doctor of Osteopathic Medicine",
             "Unlicensed", "Nuclear Medicine Technologist", "Respiratory Therapist", "Perfusionist", "Polysomnographic Technologist", "Certified Athletic Trainer", 
             "Neuropathic Doctor"]

type_count = []

for type in all_types:
    count = type_data.count_where("doctor_type = ?", (type,))
    type_count.append((type, count))

type_df = pd.DataFrame(type_count, columns=("Physician Type", "Count"))

chart_config = dw.create_chart(
    title="Physicians by Type",
    chart_type="column-chart",
    data=type_df
)

chart_id = chart_config["id"]
dw.publish_chart(chart_id)

dw.display_chart(chart_id)
