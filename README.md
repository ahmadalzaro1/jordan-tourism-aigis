# Jordan Tourism AI-GIS

A working map-based application for exploring tourism demand, accommodation capacity, and investment scenarios across Jordan's 12 governorates.

It combines a Next.js / MapLibre interface, a FastAPI / PostGIS backend, a Python SDK, and optional Superset datasets. The bundled visitor and occupancy series are **generated demo data**, not official MoTA observations. The project is not evidence of a ministry commission or deployment.

## Verified behavior

The November 2026 validation exercised the application against a separate PostGIS database: **61 backend tests**, **30 original functional checks**, **3 frontend export tests**, a clean `npm ci`, type checks, lint, and a production build. Browser checks covered the map, year filters, layer switches, investment rankings, scenarios, research inventory, and CSV downloads. The browser file-upload check was declined; API importer tests passed before that decision.

See [the validation report](docs/validation/2026-11-07-validation.md) for evidence, limitations, reproducible commands, and API improvements.

## Forecast results

The original headline numbers refer to different Prophet settings on the same generated-data holdout. Both reproduce with Prophet 1.1.6 and CmdStanPy 1.2.5:

| 2025 holdout, training through 2024 | MAPE |
|---|---:|
| Prophet, `changepoint_prior_scale=0.05` (application default) | 4.89% |
| Prophet, `changepoint_prior_scale=0.01` (research comparison) | 3.58% |
| Seasonal naive, repeat the preceding year | 5.80% |
| ARIMA `(1,1,1)` | 26.50% |

These measurements do not establish accuracy on real tourism data. API forecast metrics now use an earlier training period and unseen final months, rather than fitted-history errors. A Prophet failure is explicitly reported when ARIMA is used instead.

## Data

| Bundled core dataset | Rows | Kind |
|---|---:|---|
| Monthly visitors, 2020–2025 | 864 | Generated demo |
| Monthly occupancy, 2020–2025 | 864 | Generated demo |
| Hotel inventory | 22 | Demo inventory |
| Tourism sites | 80 | Curated inventory |
| Monthly site visits | 5,760 | Generated demo |
| Cached governorate weather | 864 | Snapshot |
| Cached economic indicators | 11 annual rows | Snapshot with missing values |

`GET /api/sources` reports available core files and their provenance categories. Additional OSM and contextual CSVs are snapshots, estimates, or computed inputs; a file count is not a count of independent live sources. Seven provider classes are registered in the Python SDK.

The map uses attributed geoBoundaries polygons under CC BY 2.5, representing 2006 boundaries. Nine site points and three hotel points require review against their assigned regions; see the report. Older GADM files remain historical inputs and are not used for the new map seeding.

## Local development

Requires Python 3.11, Node 22, and PostgreSQL with PostGIS. Keep this development application on localhost: write actions currently have no authentication or authorization layer.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
# Set DATABASE_URL to your development PostGIS database before seeding.
.venv/bin/python backend/scripts/setup_database.py
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second shell:

```sh
cd frontend
npm ci
npm run dev
```

The default frontend API URL is `http://localhost:8000`; configure `NEXT_PUBLIC_API_URL` and backend `CORS_ORIGINS` together when choosing different ports. `TOURISM_DATA_DIR` can select an explicit shared dataset directory. Setup preserves bundled CSVs by default; `--generate-demo` explicitly regenerates them.

For the Compose environment, review ports for conflicts first:

```sh
docker compose up -d --build
docker compose exec backend python scripts/setup_database.py
```

Compose binds services to loopback. Superset now includes its PostgreSQL driver and runs its initialization script. Its metadata is separate from the tourism tables. Add the tourism database through a read-only role and register the provided SQL views; a fully authored BI dashboard is not bundled. Replace demo credentials and secret configuration before any production deployment.

## Tests and research

```sh
.venv/bin/python -m pip install pytest==9.2.0 httpx==0.28.1
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_forecasting_validation.py backend/tests/test_connectors.py
PYTHONPATH=backend .venv/bin/python backend/scripts/functional_test.py
PYTHONPATH=backend .venv/bin/python backend/scripts/backtest_forecast.py
PYTHONPATH=backend .venv/bin/python backend/scripts/validate_benchmarks.py
cd frontend
npm test
npm run lint
npm run build
```

Integration tests require `GIS_VALIDATION_DATABASE_URL` explicitly targeting the disposable database described in the validation report. They create workflow records; do not target an existing production database.

The module named `mcp/server.py` is a keyword query router over the SDK. It is not a standard MCP transport implementation or a general reasoning agent. Workflow notifications and automated forecast adjustments are planned hooks, not executed external actions.
