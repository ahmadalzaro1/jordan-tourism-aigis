# Jordan Tourism AI-GIS — Module Reference

**Purpose:** Complete reference for agentic development. Any agent or developer can understand the full codebase from this document.

## Project Overview

AI-Enabled Geo-Analytics platform for Jordan's Ministry of Tourism and Antiquities. Integrates national tourism statistics with spatial data for demand-capacity analysis, forecasting, and investment prioritization.

**RFP:** PoC Program 5 — JICA/MoDEE (deadline April 19, 2026)
**Tech Stack:** FastAPI + PostgreSQL/PostGIS + Apache Superset + Next.js + MapLibre

## Directory Structure

```
jordan-tourism-aigis/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Settings (DB URL, CORS)
│   │   ├── api/routes/        # REST endpoints (5 files)
│   │   ├── db/                # Database models + connection
│   │   ├── analytics/         # 5 analytics modules
│   │   ├── etl/               # Data pipeline (3 files)
│   │   └── schemas/           # Pydantic models (empty)
│   ├── scripts/               # Data generation + seeding (4 files)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Pages (layout, page, globals.css)
│   │   ├── components/
│   │   │   ├── map/           # MapViewer.tsx
│   │   │   └── dashboard/     # DashboardPanel, SimulationPanel, InvestmentExplorer
│   │   └── lib/               # api.ts, types.ts, constants.ts
│   └── package.json
├── superset/                   # Apache Superset config
│   ├── superset_config.py
│   └── init.sh
├── data/
│   ├── schema/                # init.sql, views.sql
│   ├── sample/                # 5 sample CSVs
│   ├── geo/                   # (empty, for GeoJSON)
│   └── osm/                   # 28 OSM data files
├── docs/                      # Documentation (4 files)
├── docker-compose.yml         # 5 services
└── .planning/                 # GSD project tracking
    ├── PROJECT.md
    ├── ROADMAP.md
    ├── REQUIREMENTS.md
    ├── STATE.md
    ├── research/              # Market research
    └── phases/                # 4 phases with plans+summaries
```

## Backend Modules

### main.py
FastAPI application entry point. Registers 5 routers, configures CORS, creates tables on startup.

### config.py
Settings via pydantic-settings. Key vars: `database_url`, `cors_origins`, `etl_upload_dir`.

### db/database.py
SQLAlchemy engine + session factory. `get_db()` dependency for FastAPI routes.

### db/models.py — 8 Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| Governorate | 12 Jordan governorates | name_en, name_ar, code, geometry (MULTIPOLYGON), area_km2, population |
| TourismSite | Tourist attractions | name_en, name_ar, site_type, era, description, lat, lng, geometry (POINT) |
| Hotel | Accommodation | name, hotel_class, rooms, beds, lat, lng, geometry (POINT) |
| VisitorData | Monthly visitors | governorate_id, year, month, total_visitors, international, domestic |
| SiteVisitData | Monthly site visits | site_id, year, month, total_visits |
| OccupancyData | Monthly occupancy | governorate_id, year, month, occupancy_rate, rooms, beds |
| CapacityIndicator | Computed indicators | governorate_id, year, month, rooms_per_1000, beds_per_1000, opi, gpi, cai, classification, priority_score |
| ETLLog | Import tracking | filename, dataset_type, counts, status, errors |

### analytics/indicators.py
5 indicator formulas:
- `rooms_per_1000_visitors(rooms, visitors)` → float
- `beds_per_1000_visitors(beds, visitors)` → float
- `occupancy_pressure_index(avg_occ, peak_occ)` → float (0-100)
- `growth_pressure_index(current, prev, prev2)` → float (%)
- `capacity_adequacy_index(beds, visitors)` → float (>1=surplus)
- `compute_indicators_for_period(...)` → dict of all 5

### analytics/classification.py
- `classify_capacity(indicators, thresholds)` → "under"|"balanced"|"over"
- Majority voting across 4 indicators
- Configurable thresholds via DEFAULT_THRESHOLDS

### analytics/forecasting.py
- `prepare_monthly_series(data)` → DataFrame with ds,y columns
- `forecast_prophet(df, horizon)` → dict with forecast[], history[], metrics
- `forecast_arima(df, horizon)` → dict (fallback)
- `forecast_best(df, horizon)` → tries Prophet, falls back to ARIMA
- Metrics: MAPE, MAE, RMSE via back-testing

### analytics/simulation.py
- `accommodation_scenario(baseline, name, added_beds)` → dict with baseline/scenario/difference
- `demand_scenario(baseline, name, visitor_change_pct)` → dict
- Both compare against forecasted baseline (not current data)

### analytics/scoring.py
- `compute_priority_score(visitors, beds, pressure, growth, airport, highway)` → dict
- 5 component scores (0-100), weighted total
- Rule-based investment type recommendation
- `compute_priority_batch(governorates)` → ranked list

### api/routes/data.py
GET /api/tourism/visitors, /occupancy, /site-visits, /rooms-beds — filtered by governorate_id, year, month

### api/routes/geo.py
GET /api/geo/governorates, /hotels, /sites — returns GeoJSON FeatureCollections

### api/routes/etl.py
POST /api/etl/upload — CSV upload with dataset_type
GET /api/etl/logs — import history

### api/routes/summary.py
GET /api/summary/national — aggregated national indicators
GET /api/summary/governorate/{id} — governorate detail with time series

### api/routes/analytics.py
POST /api/analytics/indicators/{id} — compute indicators
POST /api/analytics/forecast/{id} — Prophet/ARIMA forecast
POST /api/analytics/simulate — forecast-based what-if simulation
GET /api/analytics/investment-ranker — priority rankings
POST /api/analytics/compute-all — bulk compute

### etl/pipeline.py
`run_etl(filepath, dataset_type, db)` → dict with processed/inserted/skipped/errored
Handles: visitors, occupancy, site_visits, hotels, sites
Idempotent: skips duplicates, reports errors

### etl/osm_import.py
Downloads HDX OSM GeoJSON, parses into categories, exports CSVs.

### etl/overpass_import.py
Queries Overpass API for historic/heritage/nature features in Jordan.

### scripts/generate_sample_data.py
Generates 5 sample CSVs: visitors (864), occupancy (864), hotels (22), sites (16), site_visits (1152).

### scripts/jordan_tourism_comprehensive.py
80 curated tourism sites across 12 governorates with names, Arabic names, types, eras, descriptions.

### scripts/seed_database.py
Seeds DB: governorates, sites, hotels, visitor data, occupancy data.

### scripts/setup_database.py
One-command setup: generate data + seed + create SQL views.

## Frontend Components

### MapViewer.tsx
MapLibre GL map centered on Jordan. CartoDB dark basemap. Governorate boundaries (gold), hotel markers, tourism site markers (colored by type). Layer toggles. Navigation control.

### DashboardPanel.tsx
National overview with indicator cards. Year selector. Governorate drill-down with SVG mini charts. Capacity classification display.

### SimulationPanel.tsx
Scenario type selector (accommodation/demand). Slider controls. Run simulation button. Comparison table (baseline vs scenario vs difference). Classification change alert.

### InvestmentExplorer.tsx
Ranked zone cards. Priority score badges (red/amber/green). Score component progress bars. Investment type recommendation. Justification text.

### page.tsx
3-tab layout (Overview, Simulation, Investment). Dashboard on left (420px), map on right (flex). Dynamic imports for all panels.

### api.ts
`fetchJSON(path, method)` — generic fetch wrapper
`fetchNationalSummary(year)`, `fetchGovernorateSummary(id, year)`, `fetchGovernorates()`, `fetchHotels()`, `fetchSites()`
`fetchForecast(id, horizon)`, `fetchIndicators(id, year)`, `fetchInvestmentRanker()`, `runSimulation(params)`

### types.ts
TypeScript interfaces: Governorate, NationalSummary, GovernorateSummary, GeoJSONFeature, GeoJSONCollection

### constants.ts
JORDAN_CENTER, JORDAN_BOUNDS, GOVERNORATE_CODES, CAPACITY_COLORS, THEME, API_URL

## Superset

### Configuration
- Connects directly to PostgreSQL (not through FastAPI)
- Feature flags: template processing, native filters, cross-filters
- Redis caching
- Port 8088, login admin/admin

### SQL Views (data/schema/views.sql)
7 views pre-joining tables for easy chart building:
- v_monthly_tourism (visitors + occupancy by governorate/month)
- v_site_visits (site data with governorate info)
- v_hotels (hotels with governorate info)
- v_tourism_sites (sites with governorate info)
- v_capacity_indicators (computed indicators)
- v_national_summary (national totals by year)
- v_governorate_comparison (side-by-side comparison)

## Docker Services

| Service | Port | Image |
|---------|------|-------|
| db | 5433 | postgis/postgis:16-3.4 |
| redis | 6379 | redis:7-alpine |
| superset | 8088 | apache/superset:4.1.2 |
| backend | 8000 | python:3.12-slim (custom) |
| frontend | 3000 | node:20-alpine (custom) |

## How to Run

```bash
cd jordan-tourism-aigis
docker-compose up -d
cd backend && python3 scripts/setup_database.py
# Superset: http://localhost:8088 (admin/admin)
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

## RFP Requirements Mapping

| RFP Requirement | Module | Status |
|----------------|--------|--------|
| ETL-01 to ETL-08 | etl/pipeline.py | ✅ |
| DB-01 to DB-04 | db/models.py | ✅ |
| ANALYTICS-01 to ANALYTICS-09 | analytics/indicators.py + classification.py | ✅ |
| FORECAST-01 to FORECAST-03 | analytics/forecasting.py | ✅ |
| SIM-01 to SIM-04 | analytics/simulation.py | ✅ |
| SCORE-01 to SCORE-03 | analytics/scoring.py | ✅ |
| DASH-01 to DASH-08 | Superset + frontend components | ✅ |
| EXPORT-01 to EXPORT-03 | Superset built-in | ✅ |
| UI-01 to UI-04 | MapLibre + Superset | ✅ |
| DEPLOY-01 to DEPLOY-05 | docker-compose + docs | ✅ (docs) |
| TEST-01 to TEST-04 | (needs running system) | ⏳ |
| HANDOVER-01 to HANDOVER-03 | docs/ | ✅ |
