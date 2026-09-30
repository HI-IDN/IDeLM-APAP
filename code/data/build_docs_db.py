"""Build the compact SQLite snapshot used to render the Quarto paper.

Run from code/ after exporting the result CSVs with data.apap_export.
"""
import csv
import sqlite3
from pathlib import Path


RESULTS = Path("../data/results")
OUTPUT = Path("../docs/data/apap.sqlite")

TABLES = {
    "doctors": {
        "columns": ["doctor", "cardiac", "charge"],
        "types": [str, int, int],
    },
    "weeks": {
        "columns": [
            "week", "start", "end", "target", "objective_equity",
            "objective_cardiac_charge", "objective_priority_charge", "optimal",
        ],
        "types": [str, str, str, float, float, float, float, int],
    },
    "points": {
        "columns": ["week", "doctor", "total_points", "days_working"],
        "types": [str, str, float, int],
    },
    "assignments": {
        "columns": ["date", "doctor", "points", "shift", "day_type"],
        "types": [str, str, int, str, str],
    },
    "holidays": {
        "columns": ["date", "holiday"],
        "types": [str, str],
    },
}


def convert(value, kind):
    if value == "":
        return None
    return kind(value)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    with sqlite3.connect(OUTPUT) as con:
        for table, spec in TABLES.items():
            columns = spec["columns"]
            placeholders = ", ".join("?" for _ in columns)
            names = ", ".join(f'"{name}"' for name in columns)
            with (RESULTS / f"{table}.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = [
                    tuple(convert(row[name], kind) for name, kind in zip(columns, spec["types"]))
                    for row in csv.DictReader(f)
                ]
            con.execute(f'CREATE TABLE "{table}" ({names})')
            con.executemany(f'INSERT INTO "{table}" ({names}) VALUES ({placeholders})', rows)
            print(f"{table}: {len(rows)} rows")

        con.execute("CREATE INDEX points_week_doctor ON points (week, doctor)")
        con.execute("CREATE INDEX assignments_date_doctor ON assignments (date, doctor)")

    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
