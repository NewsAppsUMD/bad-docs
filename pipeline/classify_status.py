#!/usr/bin/env python3
"""Classify the current disciplinary status for each doctor using an LLM.

Reads each doctor's most recent alert type and asks the LLM to classify it
into a standard status label. Results are stored in the Doctor.status column.

Set MODEL constant below to choose the model.
"""
import sys
from pathlib import Path

# Ensure project root is on the path so we can import models
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import llm
from peewee import fn
from models import db, Doctor, Alert

MODEL = "qwen3.5:9b"

VALID_STATUSES = [
    "License Permanently Revoked",
    "License Revoked",
    "License Surrendered",
    "Suspended",
    "On Probation",
    "Reinstated",
    "Suspension Terminated",
    "Reprimanded",
    "Fined",
]

PROMPT_TEMPLATE = """Given this disciplinary action description for a health professional, classify their CURRENT status into exactly one of these labels:

- License Permanently Revoked
- License Revoked
- License Surrendered
- Suspended
- On Probation
- Reinstated
- Suspension Terminated
- Reprimanded
- Fined

Important rules:
- Focus on the CURRENT state after all actions described have taken effect.
- If a suspension was terminated and probation was imposed, the status is "On Probation".
- If a suspension was terminated but a NEW suspension was also imposed in the same order, the status is "Suspended".
- "Upon termination of suspension, probation will be imposed" means the person is CURRENTLY suspended (probation hasn't started yet).
- If the license was revoked or surrendered (even if a suspension was also terminated), the status is "License Revoked" or "License Surrendered".
- "Permanent revocation" is "License Permanently Revoked".
- If only a reprimand was issued (no active suspension), the status is "Reprimanded".
- If only a fine was issued, the status is "Fined".

Action description:
{alert_type}

Respond with ONLY the status label from the list above, nothing else."""


def classify_doctor(model, doctor, alert_type):
    """Classify a single doctor's status using the LLM."""
    prompt = PROMPT_TEMPLATE.format(alert_type=alert_type)
    try:
        response = model.prompt(prompt)
        status = response.text().strip()
        # Validate the response is one of the valid statuses
        if status in VALID_STATUSES:
            return status
        # Try case-insensitive match
        for valid in VALID_STATUSES:
            if status.lower() == valid.lower():
                return valid
        print(f"  WARNING: Invalid status '{status}' for {doctor.clean_name}, retrying...")
        # Retry once
        response = model.prompt(prompt)
        status = response.text().strip()
        for valid in VALID_STATUSES:
            if status.lower() == valid.lower():
                return valid
        print(f"  ERROR: Still invalid status '{status}' for {doctor.clean_name}")
        return None
    except Exception as e:
        print(f"  ERROR: LLM call failed for {doctor.clean_name}: {e}")
        return None


def main():
    model = llm.get_model(MODEL)

    # Get all doctors
    doctors = Doctor.select()
    total = doctors.count()
    classified = 0
    skipped = 0
    errors = 0

    print(f"Classifying status for {total} doctors...")

    for doctor in doctors:
        # Skip if already classified
        if doctor.status:
            skipped += 1
            continue

        # Get most recent alert
        latest_alert = (Alert
                        .select()
                        .where(Alert.doctor_info_id == doctor.id)
                        .order_by(Alert.date.desc())
                        .first())

        if not latest_alert:
            print(f"  No alerts for {doctor.clean_name}, skipping")
            skipped += 1
            continue

        status = classify_doctor(model, doctor, latest_alert.type)
        if status:
            doctor.status = status
            doctor.save()
            classified += 1
            print(f"  {doctor.clean_name}: {status}")
        else:
            errors += 1

    print(f"\nDone: {classified} classified, {skipped} skipped, {errors} errors (out of {total})")


if __name__ == "__main__":
    main()
