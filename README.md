# Jordan Tourism AI-GIS

An interactive geographic workspace for Jordan tourism, using official Ministry of Tourism and Antiquities (MoTA) observations and a curated place inventory. Built with Next.js / MapLibre, FastAPI / PostGIS, and a Python SDK.

**Official data is the default.** National arrivals are not allocated to governorates. Hotel reporting locations are not treated as administrative regions. Site admissions are not unique visitors. This independent project is not a ministry commission or deployment.

## Published observations

| Dataset | Coverage | Records |
|---|---|---:|
| National monthly inbound visitor trips | 2018–2025 | 96 |
| National annual inbound visitor trips | 2018–2025 | 8 |
| Annual visits to reported sites | 30 sites, 2024–2025 | 60 |
| Monthly site visits in the imported publications | 2024–2025, gaps retained | 214 |
| Annual accommodation indicators | 2024–2025 | 2 |
| Occupancy by reporting location | 2025, includes national total | 14 |
| Guest check-ins and nights by reporting location | 2025, includes national total | 17 |

The pinned [observations](data/official/tourism.json) include workbook, sheet and row references. The [source manifest](data/official/sources.json) identifies 23 public MoTA workbooks with retrieval dates and SHA-256 hashes. Only normalized factual observations and provenance are versioned; source workbooks remain local.

2025 national inbound visitor trips round to **7,041,287**. Petra records **582,550** site visits in the preliminary 2025 table. Accommodation records **3,202,595** guest check-ins and **5,179,961** guest nights. These are different populations and must not be added together.

Missing values remain null. Two inconsistencies in the published 2024 Ma’in annual/monthly site totals are retained and flagged, rather than silently corrected. Underlying fractional national estimates retain their source precision; only display values are rounded.

## Map corrections

All **80 site markers and 22 hotel markers** pass point-in-assigned-governorate checks against the bundled geoBoundaries / gbOpen polygons. The nine previously inconsistent site assignments/coordinates and three Dead Sea hotel coordinates are corrected in seeds, CSVs, and existing-database updates. See the [12 corrections and their sources](data/geo/location-corrections.json).

The map is a curated inventory, not an exhaustive accommodation census. Individual hotel room/bed capacities are unverified and omitted in official mode. Boundary data represents 2006 administrative boundaries, under CC BY 2.5; selected coordinates use GeoNames under CC BY 4.0. Attribution and source URLs are retained.

## Run locally

Requires Python 3.11, Node 22, and PostgreSQL with PostGIS. Use a new development database for official mode; existing demo databases are preserved, not erased.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
# Export DATABASE_URL for your own development PostGIS database.
.venv/bin/python backend/scripts/setup_database.py
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```sh
cd frontend
npm ci
npm run dev
```

The default dashboard reads `/api/official/overview` and the reviewed `/api/geo` inventory. The official endpoints and SDK `sdk.official.overview(2025)` work from the checked-in normalized data. `/api/official/forecast` runs an experimental national forecast. Legacy generated-data analytics and write routes return HTTP 410 in official mode.

Configure `NEXT_PUBLIC_API_URL` and backend `CORS_ORIGINS` together when changing local ports. `TOURISM_DATA_DIR` selects an explicit dataset directory. Compose defaults to official mode and binds services to loopback:

```sh
docker compose up -d --build
docker compose exec backend python scripts/setup_database.py
```

Optional Superset remains a local development service. Its seven legacy SQL views describe **demo-mode** tables, not the new official JSON observations; do not label those views official. Replace development credentials before any production use. The Syntax website exposes a separate read-only explorer, not this unauthenticated development API.

## Rebuild from source publications

```sh
.venv/bin/python backend/scripts/import_official_data.py --download
```

A changed source hash stops the import for review. The importer selects the real national data sheets by their table heading, avoiding stale 2004 template worksheets present in several ministry files. Without `--download`, it verifies and normalizes already downloaded workbooks.

## Forecast verification

On the actual national series, training through December 2024 and testing January–December 2025:

| Method | Holdout MAPE |
|---|---:|
| Prophet 1.1.6, default settings | 19.82% |
| Seasonal naive: repeat the preceding year | 14.00% |

Prophet underperforms this simple baseline on that holdout. The model remains experimental; neither historical error nor its intervals guarantee future performance. There is no governorate forecast inferred from national data. Older 3.58% / 4.89% figures apply only to generated fixtures, not these real observations.

## Tests and demo fixtures

**73 backend checks** pass, including official-data reconciliation, source provenance, geographic corrections, API isolation, and the legacy regression suite. Frontend checks cover CSV escaping, types, lint and production build. See [official-data validation](docs/validation/2026-11-07-official-data.md) and the [earlier demo validation](docs/validation/2026-11-07-validation.md).

```sh
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests
cd frontend
npm test
npm run lint
npm run build
```

Database integration tests require `GIS_VALIDATION_DATABASE_URL` pointing to the isolated disposable database documented in the report. Without it, database-dependent tests skip. For the preserved demonstration application, explicitly set **both** backend `DATA_MODE=demo` and frontend `NEXT_PUBLIC_DATA_MODE=demo` before building/running. `--generate-demo` is rejected unless demo mode is explicit.

The module named `mcp/server.py` is a keyword query router over the SDK, not a standard MCP transport or general reasoning agent. Workflow notifications and automated forecast adjustments remain planned hooks.
