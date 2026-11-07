# Official tourism data reconciliation — 7 November 2026

## Scope

Replaced the default generated-count dashboard with official MoTA observations, preserving the earlier demonstration fixtures in explicit demo mode. Added source hashes, cell provenance, reviewed coordinates, and a read-only Syntax data explorer.

## Geography

All 12 reviewed corrections are documented in `data/geo/location-corrections.json`: Tell el-Hammam, Qasr Azraq, Qasr Burqu’, Jawa, Wadi Mujib Siq Trail, Lot’s Cave, Umm ar-Rasas, Gharandal/Arindela, Humayma, Kempinski Ishtar, Hilton Dead Sea, and Movenpick Dead Sea. In some cases the assignment was wrong; in the Dead Sea hotel cases the coordinates were wrong. Gharandal refers to Arindela in Tafilah, not Ayn Gharandal in Aqaba.

PostGIS `ST_Covers` verifies all 80 site points and 22 hotel points against their assigned bundled governorate polygon: **zero mismatches**. Boundary compatibility does not imply survey-grade coordinate precision; approximate trail/reserve markers are identified as such in the correction manifest.

Fresh database `tourism_official_20261107`, isolated inside the local validation PostGIS container on loopback port 5546:

| Check | Result |
|---|---:|
| Governorate polygons | 12 |
| Curated site points | 80 |
| Curated hotel points | 22 |
| Site / hotel assignment mismatches | 0 / 0 |
| Generated visitor / occupancy / site-visit rows | 0 / 0 / 0 |
| Hotels exposing unverified room or bed capacities | 0 |

Existing demonstration database `tourism_validation` was preserved. Seeding updates reviewed place records rather than only inserting new ones. Setup creates the PostGIS extension before geometry tables.

## Source verification

23 ministry workbooks downloaded from the official statistics pages. Full URLs, retrieval dates, byte lengths and SHA-256 hashes are in `data/official/sources.json`. The importer verifies every workbook hash and rejects revised bytes. Source files are ignored locally; normalized observations are checked in.

National series: exactly 96 distinct monthly records, January 2018–December 2025, reconciled to eight published annual totals within 0.02 trips of underlying estimate precision. Overnight plus same-day estimates reconcile. Legitimate zero months remain zero. National workbook sheet selection rejects stale 2004 template sheets.

Site series: 60 annual records for 30 sites in 2024–2025 and 214 published monthly records from the imported site tables. No missing month is imputed. 2025 site data is preliminary. The published 2024 Hammamat Ma’in annual total (63,502) differs from its components (63,138), and August total (5,301) differs from its components (4,937). Both reported totals are retained and flagged.

Accommodation: 2024–2025 national indicators, 2025 reporting-location check-ins/nights, and 2025 occupancy fractions converted to percentages. A missing Ma’in Spa occupancy value remains null. Occupied room nights are not room inventory. Reporting locations (e.g. Dead Sea, Petra, Wadi Rum) are not allocated to governorates.

## Runtime and tests

Official data is the default backend and frontend mode. Legacy demo summary, forecast, research, exports, ETL and action routes are gated with HTTP 410. Geo marker endpoints omit unverified hotel capacities. Python SDK national queries use real published national records; regional demo queries are blocked in official mode.

73 backend tests passed against the explicitly isolated demonstration regression database, including official-data tests that do not need a database. Existing tests retain explicit demo mode. A separate fresh official-mode database was inspected using read-only SQL and HTTP checks.

On 2018–2025 real national arrivals: default Prophet’s 2025 temporal holdout MAPE is 19.82%; seasonal naive is 14.00%. Training ends December 2024. The API shows both, with no claim of improved real-data accuracy. No governorate observations or model performance are fabricated.

Local evidence lives under ignored `output/official-reconciliation/`. Reproduction: README commands and `backend/tests/test_official_data.py`.
