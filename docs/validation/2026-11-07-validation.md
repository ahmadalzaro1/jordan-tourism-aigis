# Jordan Tourism AI-GIS — reconciliation and validation

Validation began November 6 and continued November 7, 2026. Baseline: GitHub `main` at `c32514d5fe76c3f3d8815858f0145440c6ec3321`. Changes are in the separate checkout on branch `codex/gis-validation-20261107`. The original Desktop checkout was preserved. It has a different local HEAD, `ccbaddb`, including later planning documents; those were not overwritten or merged into this validation checkout.

## Result

The application runs locally with real PostGIS geometry, working analytics routes, scenarios, exports, source inventory, and a map interface. The numerical and runtime faults below were corrected. It is suitable for demonstrating the software. Its generated tourism observations, incomplete source provenance, unauthenticated write routes, and unreviewed geospatial assignments prevent a claim of production or policy readiness.

The Syntax website was not deployed or changed by this work.

## Checks completed

| Area | Outcome and scope |
|---|---|
| Backend integration and regressions | 61 passed against disposable PostGIS; JUnit and console logs saved |
| Original functional script | 30/30 passed; checks include repeated deterministic indicators, not universal forecast reproducibility |
| Frontend unit tests | 3 passed: CSV escaping, heterogeneous fields, formula neutralization |
| Dependency installation | Clean locked `npm ci` succeeds after React peer conflict repair |
| Frontend quality | TypeScript, ESLint, production build pass; one existing external-font lint warning |
| Production dependency audit | Zero npm production advisories after compatible patches and MapLibre upgrade; this is not a full security audit |
| Map | Browser rendering, 12 valid nonempty MultiPolygons, hotel/site markers, capacity fills, accommodation-density layer |
| Browser interactions | Year change updates summaries; layer checkboxes change rendering; map selection opens scenario; scenario and investment results render; Research reflects actual core files |
| Browser CSV export | Downloaded `national_summary.csv` and parsed nine exported fields |
| Browser map export | Downloaded a real map PNG after repairing data-URL export to use a Blob; artifact saved locally |
| PDF export | HTTP response is a nonempty PDF; example saved locally |
| Upload pipeline | Initial database imports 864 visitor, 864 occupancy, and 5,760 site-visit rows; API tests cover duplicates and malformed periods, totals, and codes |
| Browser upload | Not completed: the user declined browser file-upload permission. No alternative upload was attempted after the refusal |
| Responsive layout | Tested at 390 × 844: page width 390, sidebar 390 × 464, map 390 × 380; desktop viewport restored |
| Superset | Health endpoint passes; PostgreSQL driver installed; read-only queries return 864 monthly rows and 1,155,634 demo visitors for 2025; three views registered as datasets |
| Container configuration | Repaired Superset Dockerfile builds; Compose configuration renders; full Compose startup was not run over the user's occupied ports |

The containerized backend/frontend images were not independently built in this run. Backend validation used Python 3.11.16; the existing backend Dockerfile targets Python 3.12. Superset was tested in its own container. Test scope is broad application coverage, not an assertion that every input or deployment environment has been proven correct.

## Forecast reconciliation

The archived JSON contains actual and predicted arrays that independently recompute to MAPE **4.89%**, MAE **3936.17**, RMSE **4884.09**. Rerunning the bundled sample-data backtest reproduces the result, with mean governorate MAPE **8.10%**.

The **3.58%** README claim is reproducible with `changepoint_prior_scale=0.01`; the live application defaults to `0.05`. The forecast function previously ignored supplied keyword options. It now forwards them. Neither number validates performance against official tourism counts.

| Holdout year | Seasonal naive | Prophet 0.05 | Prophet 0.01 | ARIMA 1,1,1 |
|---|---:|---:|---:|---:|
| 2023 | 4.68% | 5.27% | 4.45% | 41.61% |
| 2024 | 5.70% | 5.67% | 5.15% | 53.12% |
| 2025 | 5.80% | 4.89% | 3.58% | 26.50% |

Each fold trains on earlier years only. All rows are generated demo observations. Comparing configurations on these folds is model development; a final accuracy claim needs fresh, unseen real observations. The earlier exponential-smoothing claim was not reproduced in this run and was removed from the active README performance table.

Exact benchmark environment: Prophet 1.1.6, CmdStanPy 1.2.5, pandas 2.2.3, NumPy 1.26.4, statsmodels 0.14.4. CmdStanPy 1.3.2 rejects the older Prophet wheel's incomplete packaged CmdStan directory; it caused silent ARIMA fallback until the compatible dependency was pinned. This failure matches the [upstream issue](https://github.com/facebook/prophet/issues/2697).

API metrics previously measured predictions from a model already fitted on evaluation rows. They now fit only the earlier training subset, report explicit holdout dates, and reject gapped, duplicated, nonfinite, or negative monthly inputs. All-zero percentage errors are undefined, not perfect accuracy. Prediction intervals can vary; universal 100% forecast reproducibility is not established.

## Faults corrected

- React 19 had a React-18-only testing-library peer dependency. Installation now succeeds without ignoring peer dependencies or discarding the lockfile.
- Annual room/bed stocks were summed across months. They now use average monthly stock; country totals aggregate across governorates. PostgreSQL Decimal results are converted through floating SQL expressions where required.
- Two SQL views multiplied visitor totals through hotel/site joins. Inputs are aggregated before joining, and sums are checked against the raw CSVs.
- Bootstrap skipped SQL statements beginning with comments and used an absent schema path. It now executes all seven views transactionally, preserving bundled data unless regeneration is explicitly requested.
- Governorate geometries were empty after seeding. Seeding now imports explicitly ISO-matched, attributed geoBoundaries polygons.
- Research referenced NumPy without importing it and ignored its requested year. Both are corrected. Empty destination filters no longer return national totals.
- CSV imports accepted invalid dates, negative or fractional counts, inconsistent visitor totals, and unknown references. Validation now runs before mutation, and failure logging rolls back the session correctly.
- CSV export used JSON escaping instead of CSV escaping. It now quotes cells correctly and neutralizes spreadsheet formulas in text fields.
- The map PNG export did not produce a browser download from its data URL. It now uses a Blob URL, verified by an actual PNG download.
- The PDF export used the computer's current year rather than the selected data year. It now uses the selected year.
- Map switches were disconnected from rendered layers. Capacity fills now use actual computed classifications, and the density layer is correctly described as accommodation supply, not measured tourist demand.
- MapLibre's worker failed after bundling. Its matching worker is now copied from the installed package and served locally. Map framing includes the country's full extent; a narrow-screen layout keeps both panel and map available.
- The weather API call used an unsupported monthly response. It now requests daily observations and aggregates temperature, rainfall, and sunshine explicitly, preserving missing measurements.
- Providers and ETL modules disagreed on root versus backend data directories. A shared configurable path now resolves canonical datasets.
- Monthly scenarios used a full year's bed nights. They now use the target month's day count; ratios used with annual classification thresholds are annualized consistently. The 2.5-night stay is still an assumption, not a measured statistic.
- Superset lacked its PostgreSQL driver and never invoked the mounted initialization script. The image, idempotent administrator bootstrap, startup command, and separate metadata configuration were repaired.
- Workflow responses advertised notifications/forecast adjustments without executing them. They now distinguish planned hooks from executed actions.
- Static dashboard claims were replaced by the source inventory. Primary README claims distinguish functioning code, sample observations, and verified measurements.

## Spatial data review still needed

All 12 imported polygons are valid. Membership checks flag nine site points and three hotel points outside their assigned governorate polygon. This is a review list, not proof that the 2006 boundary file is current or authoritative.

| Point | Assigned | Matching 2006 polygon |
|---|---|---|
| Tell el-Hammam | Irbid | Balqa |
| Qasr Azraq | Mafraq | Zarqa |
| Qasr Burqu', Jawa | Mafraq | Outside the imported polygons |
| Wadi Mujib Siq Trail | Balqa | Madaba |
| Lot's Cave | Balqa | Karak |
| Umm ar-Rasas | Madaba | Amman |
| Gharandal | Tafilah | Ma'an |
| Humayma | Ma'an | Aqaba |
| Kempinski Ishtar, Hilton, Movenpick Dead Sea | Balqa | Madaba |

Do not silently reassign these from an old boundary snapshot. Verify current official administrative boundaries, coordinates, facility identity, and tourism reporting regions first. Existing GADM files were preserved but are not used by the repaired seed path; [GADM's terms](https://gadm.org/license.html) differ from the new boundary source's license.

## APIs researched and tested

No paid service was purchased or new API credential created. Treg is installed but signed out, so its private account-specific catalog was not available for verification. This inventory concerns the project's existing sources and public endpoints that were actually tested.

| Source | Observed result | Useful improvement |
|---|---|---|
| [MoTA statistics](https://www.mota.gov.jo/AR/List/ar_statisiics) | Official 2025/2026 tables located, including monthly overnight/day visitors, site visits, accommodation. Direct file discovery from this environment received HTTP 451; no official series imported | Highest priority: versioned official ingestion, definitions, source publication date, checksum, and human review of normalized tables |
| [Jordan Open Government Data API](https://opendata.gov.jo/en/api-guide/) | HTTP 500 for English/Arabic catalog searches, including documented GET-body format | Add bounded retries and cached catalog snapshots; never silently substitute demo observations |
| [Open-Meteo historical API](https://open-meteo.com/en/docs/historical-weather-api) | January 2025 Amman daily request succeeds; repaired connector produces one monthly row | Historical weather covariates, missingness and full-month coverage, location aggregation, source/model timestamps. Free hosted use is noncommercial; [commercial usage terms](https://open-meteo.com/en/terms) must be satisfied before a business deployment |
| [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation) | Existing connector works. GDP, growth, inflation, unemployment, exchange rate return 2023–2025; recent tourism arrivals/receipts are absent | Refresh annual context with explicit nulls and release lags. It cannot replace monthly governorate arrivals |
| [geoBoundaries](https://www.geoboundaries.org/api.html) | Metadata and all 12 polygons retrieved; CC BY 2.5, boundary year 2006 | Working map geometry with attribution and ISO identifiers; replace or cross-check against a newer authoritative boundary source |
| OpenStreetMap / Overpass | Existing POI snapshot files available; one bounded live query timed out after 20 seconds | Scheduled small-area refreshes with OSM IDs, deduplication, attribution, dates, and fallback to labeled snapshots |
| [Wikimedia pageviews](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/) | Petra monthly pageviews return three rows for January–March 2025 | Attention covariate with clear coverage bias; pageviews are not visitor counts |
| Routing / accessibility | Current distances and access scores are curated estimates; no authenticated routing integration verified | Add travel-time matrices and isochrones through a selected routing API. [Current provider terms and limits](https://account.heigit.org/) need verification before integration |

## Recommended next implementation

1. **Official data and provenance.** Build a reviewed MoTA import adapter for real monthly arrivals and accommodation, retaining national/site/governorate geographic granularity. Never manufacture governorate values from national totals. Attach units, definitions, reporting region, vintage, license, refresh time, and checksum to each dataset.
2. **Geographic quality.** Resolve the 12 flagged point assignments, reconcile accommodation inventory against occupancy totals, and use versioned official regions. These inputs matter more than adding more model APIs.
3. **Reproducible evaluation.** Retain seasonal naive, multiple temporal folds, model/runtime versions, and an untouched final test period. Evaluate weather, holidays, attention, and economic covariates for genuine out-of-sample improvement before enabling them in ranking logic.
4. **Real accessibility.** Replace fixed 20/50 km assumptions with measured travel times between facilities, attractions, airports, and population centers. Cache results and record provider/date/license.
5. **Agent integration.** Expose validated typed, read-only query and scenario tools through a standard MCP server or a controlled model tool interface. Return source citations and assumptions. The existing keyword router is useful code, but does not implement that protocol. Investment approvals and notifications must remain explicit authenticated human actions.
6. **Production boundary.** Add authentication, per-role authorization, request limits, upload resource limits, durable audit logs, migration strategy, backup/restore checks, secrets management, and deployment-specific security review before public write access. Author BI dashboards separately; registering datasets is not the same as shipping a dashboard.

## Reproduce the local checks

The disposable database is `tourism_validation` at `127.0.0.1:5546`. Frontend: `http://127.0.0.1:4186`; backend: `http://127.0.0.1:8186`; Superset: `http://127.0.0.1:8188`. Credentials are local demo values, not production account credentials.

```sh
# From the repository root, with the disposable database URL in both variables:
export DATABASE_URL="$GIS_VALIDATION_DATABASE_URL"
.venv/bin/python backend/scripts/setup_database.py
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q --junitxml=output/validation/backend-tests.xml
PYTHONPATH=backend .venv/bin/python backend/scripts/functional_test.py
PYTHONPATH=backend .venv/bin/python backend/scripts/backtest_forecast.py
PYTHONPATH=backend .venv/bin/python backend/scripts/validate_benchmarks.py
PYTHONPATH=backend .venv/bin/python backend/scripts/probe_public_apis.py
cd frontend
npm ci
npm test
npm run lint
NEXT_PUBLIC_API_URL=http://127.0.0.1:8186 npm run build
npm audit --omit=dev
```

`output/validation/` contains logs, JUnit, original dataset hashes, archived forecast JSON, model comparison JSON, bounded API responses, SQL/spatial diagnostics, an example PDF, and exact Python versions. It is excluded from Git. The versioned benchmark and test scripts make the checks repeatable; request-dependent API availability and source publication vintages can change.

## Local map export

The browser-generated export is saved in `output/validation/gis-map-export.png`. MapLibre exports the WebGL map canvas; UI controls and HTML attribution are outside that canvas. Retain required attribution when reusing this export externally.
