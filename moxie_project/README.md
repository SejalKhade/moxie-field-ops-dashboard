# Moxie Field Ops Intelligence Dashboard

A full-stack analytics tool that connects three data streams Moxie's current stack keeps siloed:
**FieldRoutes job completion data**, **Geotab route efficiency data**, and **HubSpot CRM customer records**.

The result: one unified dashboard that surfaces which ZIPs have high cancellation rates, which technicians are losing revenue to inefficient routing, and where scheduling capacity is being wasted.

---

## The Problem This Solves

Moxie's current stack (FieldRoutes + Geotab + HubSpot) has no cross-tool visibility layer. Ops managers answer questions like "why is ZIP 75001 cancelling 3x more than 75040?" by exporting CSVs from three separate tools and joining them manually in Excel. This project automates that join at the database layer and serves the answer in under 200ms.

---

## Architecture

```
FieldRoutes (jobs) ──┐
                     ├──► DuckDB star schema ──► SQL analytical views ──► Flask API ──► D3.js dashboard
Geotab (routes) ─────┘
                    dim_technician
                    fact_jobs
                    fact_routes
```

**Stack:** Python · Flask · DuckDB · D3.js · GitHub Actions CI

---

## KPIs Surfaced

| KPI | Source tables | SQL technique |
|---|---|---|
| Cancellation rate by ZIP, ranked | `fact_jobs` | CTE + `RANK() OVER` |
| Revenue per mile by technician | `fact_jobs` JOIN `fact_routes` JOIN `dim_technician` | Dimensional join + efficiency rank |
| Daily scheduling gap + 7-day rolling avg | `fact_jobs` | Window function: `AVG() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` |
| Cancellation reason breakdown | `fact_jobs` | `SUM(COUNT(*)) OVER()` for percentage share |

---

## Setup

```bash
# 1. Install
pip install -r requirements.txt

# 2. Generate simulated data (2,000 jobs, 1,792 routes, 20 technicians, 20 DFW ZIPs)
python generate_data.py

# 3. Run
python app.py
# → http://localhost:5050
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard UI |
| `GET /api/summary` | KPI header tiles |
| `GET /api/cancel_by_zip` | Top 20 ZIPs by cancellation rate |
| `GET /api/tech_efficiency` | Revenue/mile by technician with efficiency rank |
| `GET /api/scheduling_gaps` | Daily job trend with 7-day rolling average |
| `GET /api/cancel_reasons` | Cancellation reason breakdown with % share |

---

## Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

26 tests covering endpoint status codes, required fields, business-logic invariants (cancellation rate 0–100%, pct_of_cancels sums to 100, dates ordered, ranks sorted).

CI runs on every push via GitHub Actions (`ci.yml`) with 85% coverage gate.

---

## Data Model

```sql
dim_technician  (tech_id PK, tech_name, region, hire_date, vehicle_type)
fact_jobs       (job_id PK, tech_id FK, zip_code, scheduled_at, is_completed,
                 cancel_reason, job_revenue, service_type)
fact_routes     (route_id PK, job_id FK, tech_id FK, route_date,
                 miles_driven, drive_minutes, fuel_cost)
```

Higher cancellation probability seeded in ZIPs 75001, 75060, 75080 — designed to be detectable by the `vw_cancel_by_zip` view.

---

## What's Next (Production Path)

- Replace simulated data with live FieldRoutes + Geotab API connectors
- Add HubSpot customer lifetime value join to `fact_jobs`
- Deploy to AWS (ECS + RDS or DuckDB on S3 with Motherduck)
- Role-based auth for ops managers vs. executives
