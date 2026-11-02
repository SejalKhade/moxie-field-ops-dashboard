# Moxie Field Ops Intelligence Dashboard

> **Full-stack analytics tool** built to eliminate manual Excel joins across three enterprise SaaS platforms — surfacing field operations KPIs in under 200ms through a live, interactive dashboard.

**Stack:** Python · Flask · DuckDB · D3.js · SQL (window functions) · GitHub Actions CI · pytest

---

## What This Project Demonstrates

| Skill Area | What You'll See |
|---|---|
| **Backend / API design** | RESTful Flask API with 5 endpoints, clean separation of DB and route logic |
| **Analytical SQL** | CTEs, `RANK() OVER`, rolling window averages, dimensional joins across a star schema |
| **Data engineering** | DuckDB star schema: `fact_jobs`, `fact_routes`, `dim_technician` |
| **Testing** | 28 pytest tests covering status codes, field contracts, and business-logic invariants |
| **CI/CD** | GitHub Actions pipeline with 85% coverage gate on every push |
| **Frontend** | D3.js dashboard consuming live API data |

---

## The Problem It Solves

Moxie's ops stack (FieldRoutes + Geotab) has no unified visibility layer. Ops managers manually export CSVs from two tools and join them in Excel to answer questions like:

> *"Why is ZIP 75001 cancelling 3× more than ZIP 75040?"*
> *"Which technician is driving the most miles for the least revenue?"*

This project automates those joins at the database layer and serves answers through a REST API in **under 200ms**.

---

## Live Demo

```bash
git clone https://github.com/SejalKhade/moxie-field-ops-dashboard.git
cd moxie-field-ops-dashboard/moxie_project
pip install -r requirements.txt
python generate_data.py   # builds DuckDB with 2,000 jobs · 1,792 routes · 20 techs
python app.py             # → http://localhost:5050
```

---

## Architecture

```
FieldRoutes (jobs) ──┐
                     ├──► DuckDB star schema ──► SQL analytical views ──► Flask REST API ──► D3.js dashboard
Geotab (routes) ─────┘

Tables:  dim_technician · fact_jobs · fact_routes
Views:   vw_cancel_by_zip · vw_tech_efficiency · vw_scheduling_gaps · vw_cancel_reasons
```

---

## KPIs & SQL Techniques

| KPI | SQL Technique Used |
|---|---|
| Cancellation rate by ZIP (ranked) | CTE + `RANK() OVER (ORDER BY cancel_rate DESC)` |
| Revenue per mile by technician | 3-table dimensional join + efficiency rank |
| Daily scheduling gap + 7-day rolling avg | `AVG() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` |
| Cancellation reason % share | `SUM(COUNT(*)) OVER()` for percentage of total |

---

## API Endpoints

| Endpoint | Returns |
|---|---|
| `GET /api/summary` | KPI tiles: total jobs, completion rate, revenue, active techs |
| `GET /api/cancel_by_zip` | Top 20 ZIPs ranked by cancellation rate |
| `GET /api/tech_efficiency` | Revenue-per-mile rank for all technicians |
| `GET /api/scheduling_gaps` | Daily completed vs. capacity with 7-day rolling average |
| `GET /api/cancel_reasons` | Cancellation reason breakdown with % share |

---

## Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

**28 tests** across all 5 endpoints — covering:
- HTTP status codes and response shape
- Required field contracts on every response object
- Business-logic invariants: cancel rate stays 0–100%, `pct_of_cancels` sums to 100, dates are ordered, ranks are sorted

CI enforces **85% coverage** on every push via GitHub Actions.

---

## Data Model

```sql
dim_technician  (tech_id PK, tech_name, region, hire_date)
fact_jobs       (job_id PK, tech_id FK, zip_code, scheduled_at, is_completed,
                 cancel_reason, job_revenue, service_type)
fact_routes     (job_id FK, tech_id FK, date, miles_driven, drive_minutes, fuel_cost)
```

Higher cancellation probability is seeded into ZIPs 75001, 75060, 75080 — a deliberate signal detectable by `vw_cancel_by_zip`, validating the analytical layer works correctly.

---

## Production Roadmap

- Replace simulated data with live FieldRoutes + Geotab API connectors
- Add HubSpot customer lifetime value join to `fact_jobs`
- Deploy to AWS (ECS + DuckDB on S3 / MotherDuck)
- Role-based auth for ops managers vs. executives

---

*Built by Sejal Khade — [sejalkhade2310@gmail.com](mailto:sejalkhade2310@gmail.com)*
