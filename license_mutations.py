#!/usr/bin/env python3
"""Transform alerts.csv similarly to license_mutations.R.

Usage:
  python license_mutations.py [--in alerts.csv] [--out alerts.csv]

Reads CSV, applies specific file_id fixes, rebuilds url, trims year to first 4 chars, and writes output.
"""
import csv
import argparse
from pathlib import Path


FIXES = [
    ("J00031312.239", "J0003112.239"),
    ("d1042801.237", "D1042801.257"),
    ("d1362907.256", "D1362907.286"),
    ("d2792511.096", "D2792511.146"),
]


def apply_fixes(file_id: str) -> str:
    if not file_id:
        return file_id
    for pattern, replacement in FIXES:
        if pattern in file_id:
            return replacement
    return file_id


def process_rows(rows):
    out = []
    for r in rows:
        file_id = r.get("file_id", "")
        file_id = apply_fixes(file_id)
        r["file_id"] = file_id
        # rebuild url if file_id present
        if file_id:
            r["url"] = f"https://www.mbp.state.md.us/BPQAPP/orders/{file_id}.pdf"
        # ensure year is first 4 characters
        if "year" in r and r["year"] is not None:
            r["year"] = str(r["year"])[:4]
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="alerts.csv")
    ap.add_argument("--out", dest="outfile", default="alerts.csv")
    args = ap.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)

    with infile.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames

    new_rows = process_rows(rows)

    # Ensure we write the same fieldnames (or include newly added fields)
    if fieldnames is None:
        fieldnames = []
    # ensure url and file_id and year present
    for col in ("file_id", "url", "year"):
        if col not in fieldnames:
            fieldnames.append(col)

    with outfile.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)


if __name__ == "__main__":
    main()
