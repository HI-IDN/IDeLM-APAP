"""
Export the APAP results from the legacy SQLite database to CSV files for the paper.

The database is built by `make import` from the solved weekly schedules. The default is the
February 2024 build (data/weekly_assigned_data/database-2024-02-26.sqlite); use --db for another. Doctors are identified by their initials, as in the schedules the doctors
provided for research. For publication, --pseudonymise replaces them with codes D01, D02, ...
assigned in random order. The key is kept in data/doctor_key.csv (gitignored) and reused on
later runs, so codes stay stable.

Writes to data/results/ (gitignored):
    weeks.csv        one row per solved week: dates, target, objective values, model size
    doctors.csv      one row per doctor: id, cardiac/charge qualification, start and end dates
    points.csv       one row per week and doctor: points, role counts, days worked
    assignments.csv  one row per doctor and day: peel-off position (points), shift, roles, day type
    holidays.csv     holiday dates and names

Run from code/:  python -m data.apap_export [--db PATH] [--pseudonymise]
"""
import argparse
import csv
import os
import random
import sqlite3
from datetime import date

DB = '../data/weekly_assigned_data/database-2024-02-26.sqlite'
STAFF = '../data/staff.csv'
KEY = '../data/doctor_key.csv'
OUT = '../data/results'


def load_key(doctors):
    """Pseudonym key {initials: code}; new doctors get unused codes in random order."""
    key = {}
    if os.path.exists(KEY):
        with open(KEY, newline='', encoding='utf-8') as f:
            key = {row['anst']: row['code'] for row in csv.DictReader(f)}
    new = [d for d in doctors if d not in key]
    width = max(2, len(str(len(key) + len(new))))
    free = [f'D{i:0{width}d}' for i in range(1, len(key) + len(new) + 1)
            if f'D{i:0{width}d}' not in key.values()]
    random.SystemRandom().shuffle(free)
    key.update(zip(new, free))
    with open(KEY, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['anst', 'code'])
        writer.writerows(sorted(key.items(), key=lambda kv: kv[1]))
    return key


def write(name, header, rows):
    with open(os.path.join(OUT, name), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f'{name}: {len(rows)} rows')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', default=DB, help=f'SQLite database (default {DB})')
    parser.add_argument('--pseudonymise', action='store_true', help='replace initials with random codes')
    args = parser.parse_args()

    os.makedirs(OUT, exist_ok=True)
    con = sqlite3.connect(args.db)
    doctors = [row[0] for row in con.execute('SELECT id FROM doctors ORDER BY id')]
    key = load_key(doctors) if args.pseudonymise else {d: d for d in doctors}

    with open(STAFF, newline='', encoding='utf-8') as f:
        staff = {row['anst']: row for row in csv.DictReader(f)}
    write('doctors.csv', ['doctor', 'cardiac', 'charge', 'started', 'retired'], sorted(
        [key[d], int(bool(c)), int(bool(h)), staff.get(d, {}).get('started', ''),
         staff.get(d, {}).get('retired', '')]
        for d, c, h in con.execute('SELECT id, cardiac, charge FROM doctors')))

    week_of = {}
    rows = []
    for row in con.execute('''SELECT id, file_name, period_start, period_end, workdays, target_value,
                                     objective_total, objective_equity, objective_cardiac_charge,
                                     objective_priority_charge, num_constraints, num_variables, optimal
                              FROM schedule ORDER BY period_start'''):
        week = row[1].removesuffix('.json')
        week_of[row[0]] = week
        rows.append([week, *row[2:]])
    write('weeks.csv', ['week', 'start', 'end', 'workdays', 'target', 'objective_total',
                        'objective_equity', 'objective_cardiac_charge', 'objective_priority_charge',
                        'constraints', 'variables', 'optimal'], rows)

    write('points.csv', ['week', 'doctor', 'fixed_points', 'total_points', 'cardiac', 'charge',
                         'days_working'],
          [[week_of[s], key[d], *rest] for s, d, *rest in con.execute(
              '''SELECT schedule_id, doctor_id, fixed_points, total_points, cardiac, charge, days_working
                 FROM points ORDER BY schedule_id, doctor_id''')])

    holidays = dict(con.execute('SELECT date, description FROM holidays ORDER BY date'))
    write('holidays.csv', ['date', 'holiday'], sorted(holidays.items()))

    def day_type(day):
        if day in holidays:
            return 'holiday'
        return 'weekend' if date.fromisoformat(day).weekday() >= 5 else 'weekday'

    write('assignments.csv', ['week', 'date', 'doctor', 'points', 'shift', 'charge', 'cardiac', 'day_type'],
          [[week_of[s], d, key[doc], p, shift, ch, ca, day_type(d)] for s, d, doc, p, shift, ch, ca in con.execute(
              '''SELECT schedule_id, date, doctor_id, points, role, is_charge, is_cardiac
                 FROM assignments ORDER BY date, points''')])
    con.close()


if __name__ == '__main__':
    main()
