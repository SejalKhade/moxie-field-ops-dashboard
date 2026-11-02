import pandas as pd
import numpy as np
import duckdb
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# --- Config ---
N_TECHS = 20
N_JOBS = 2000
START = datetime(2024, 1, 1)
ZIPS = ['75001','75006','75010','75019','75038','75039','75040','75041','75050','75051',
        '75060','75061','75062','75063','75080','75081','75082','75088','75089','76001']
CANCEL_REASONS = ['No show','Rescheduled','Price objection','Already treated','Duplicate booking']
SERVICE_TYPES = ['General Pest','Mosquito','Rodent','Termite Inspection','Bed Bug']

# --- Technicians ---
techs = pd.DataFrame({
    'tech_id': [f'T{i:03d}' for i in range(1, N_TECHS+1)],
    'tech_name': [f'Tech_{i}' for i in range(1, N_TECHS+1)],
    'hire_date': [START - timedelta(days=random.randint(30,900)) for _ in range(N_TECHS)],
    'region': random.choices(['North','South','East','West'], k=N_TECHS)
})

# --- Jobs (FieldRoutes-style) ---
rows = []
for i in range(N_JOBS):
    sched = START + timedelta(days=random.randint(0,364), hours=random.randint(7,17))
    tech = random.choice(techs['tech_id'].tolist())
    zip_code = random.choice(ZIPS)
    svc = random.choice(SERVICE_TYPES)
    price = round(random.uniform(89, 349), 2)
    # Higher cancellation for certain zips
    cancel_prob = 0.18 if zip_code in ['75001','75060','75080'] else 0.08
    completed = random.random() > cancel_prob
    cancel_reason = None if completed else random.choice(CANCEL_REASONS)
    actual_time = sched + timedelta(minutes=random.randint(-15,45)) if completed else None
    rows.append({
        'job_id': f'J{i+1:05d}',
        'tech_id': tech,
        'zip_code': zip_code,
        'service_type': svc,
        'scheduled_at': sched,
        'completed_at': actual_time,
        'is_completed': completed,
        'cancel_reason': cancel_reason,
        'job_revenue': price if completed else 0.0,
        'is_new_customer': random.random() < 0.3
    })
jobs = pd.DataFrame(rows)

# --- Routes (Geotab-style) ---
route_rows = []
for _, job in jobs[jobs['is_completed']].iterrows():
    drive_min = round(random.uniform(8, 55), 1)
    miles = round(drive_min * random.uniform(0.4, 0.9), 1)
    route_rows.append({
        'job_id': job['job_id'],
        'tech_id': job['tech_id'],
        'date': job['scheduled_at'].date(),
        'drive_minutes': drive_min,
        'miles_driven': miles,
        'fuel_cost': round(miles * 0.18, 2)
    })
routes = pd.DataFrame(route_rows)

# --- Save to DuckDB ---
con = duckdb.connect('moxie_ops.db')
con.execute("DROP TABLE IF EXISTS dim_technician")
con.execute("DROP TABLE IF EXISTS fact_jobs")
con.execute("DROP TABLE IF EXISTS fact_routes")

con.execute("""
    CREATE TABLE dim_technician AS SELECT * FROM techs
""")
con.execute("""
    CREATE TABLE fact_jobs AS SELECT * FROM jobs
""")
con.execute("""
    CREATE TABLE fact_routes AS SELECT * FROM routes
""")
con.close()
print(f"DB built: {len(jobs)} jobs, {len(routes)} routes, {N_TECHS} technicians")
