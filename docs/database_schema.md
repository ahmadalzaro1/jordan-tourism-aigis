# Database Schema Documentation

**Project:** Jordan Tourism AI-GIS
**Database:** PostgreSQL 16 + PostGIS 3.4
**Last Updated:** 2026-03-29

## Overview

The database stores tourism statistics, accommodation data, geospatial boundaries, computed indicators, and ETL logs. All tables use SQLAlchemy ORM with PostGIS for geospatial columns.

## Tables

### governorates

Jordan's 12 administrative governorates with geometry boundaries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| name_en | VARCHAR(100) | English name (e.g., "Amman") |
| name_ar | VARCHAR(100) | Arabic name (e.g., "عمان") |
| code | VARCHAR(10) | Short code (e.g., "AMM", "AQAB") |
| geometry | MULTIPOLYGON (SRID 4326) | Governorate boundary polygon |
| area_km2 | FLOAT | Area in square kilometers |
| population | INTEGER | Population count |

### tourism_sites

Tourist attractions, archaeological sites, natural features, religious sites.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| name_en | VARCHAR(200) | English name |
| name_ar | VARCHAR(200) | Arabic name |
| site_type | VARCHAR(50) | archaeological, natural, religious, coastal, cultural, museum |
| governorate_id | INTEGER (FK) | References governorates.id |
| latitude | FLOAT | WGS84 latitude |
| longitude | FLOAT | WGS84 longitude |
| geometry | POINT (SRID 4326) | Point geometry |
| era | VARCHAR(100) | Historical era (e.g., "Nabataean", "Roman-Byzantine") |
| description | VARCHAR(500) | Brief site description |

### hotels

Accommodation establishments (hotels, hostels, eco-lodges).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| name | VARCHAR(200) | Hotel name |
| hotel_class | VARCHAR(20) | 3-star, 4-star, 5-star, eco-lodge |
| governorate_id | INTEGER (FK) | References governorates.id |
| latitude | FLOAT | WGS84 latitude |
| longitude | FLOAT | WGS84 longitude |
| geometry | POINT (SRID 4326) | Point geometry |
| total_rooms | INTEGER | Number of rooms |
| total_beds | INTEGER | Number of beds |

### visitor_data

Monthly visitor counts per governorate.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| governorate_id | INTEGER (FK) | References governorates.id |
| year | INTEGER | Year (e.g., 2025) |
| month | INTEGER | Month (1-12) |
| total_visitors | INTEGER | Total visitor count |
| international_visitors | INTEGER | International visitors |
| domestic_visitors | INTEGER | Domestic visitors |

**Unique Constraint:** (governorate_id, year, month)

### site_visit_data

Monthly visit counts per tourism site.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| site_id | INTEGER (FK) | References tourism_sites.id |
| year | INTEGER | Year |
| month | INTEGER | Month (1-12) |
| total_visits | INTEGER | Total visit count |

**Unique Constraint:** (site_id, year, month)

### occupancy_data

Monthly hotel occupancy per governorate.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| governorate_id | INTEGER (FK) | References governorates.id |
| year | INTEGER | Year |
| month | INTEGER | Month (1-12) |
| avg_occupancy_rate | FLOAT | Average occupancy rate (0-100%) |
| total_rooms | INTEGER | Total rooms available |
| total_beds | INTEGER | Total beds available |
| occupied_rooms | INTEGER | Rooms occupied |

**Unique Constraint:** (governorate_id, year, month)

### capacity_indicators

Computed demand-capacity indicators per governorate/period.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| governorate_id | INTEGER (FK) | References governorates.id |
| year | INTEGER | Year |
| month | INTEGER | Month (0 = annual aggregate) |
| rooms_per_1000_visitors | FLOAT | Rooms per 1000 visitors |
| beds_per_1000_visitors | FLOAT | Beds per 1000 visitors |
| occupancy_pressure_index | FLOAT | Combined occupancy pressure (0-100) |
| growth_pressure_index | FLOAT | Visitor growth rate (%) |
| capacity_adequacy_index | FLOAT | Supply/demand ratio |
| capacity_classification | VARCHAR(20) | under, balanced, over |
| priority_score | FLOAT | Investment priority score (0-100) |

**Unique Constraint:** (governorate_id, year, month)

### etl_log

Log of all ETL (data import) operations.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| filename | VARCHAR(255) | Source filename |
| dataset_type | VARCHAR(50) | visitors, occupancy, site_visits, hotels, sites |
| records_processed | INTEGER | Total records processed |
| records_inserted | INTEGER | Records successfully inserted |
| records_skipped | INTEGER | Duplicate records skipped |
| records_errored | INTEGER | Records with errors |
| status | VARCHAR(20) | success, partial, failed |
| error_details | TEXT | Error description |
| imported_at | VARCHAR | ISO timestamp |

## SQL Views

Seven pre-built views for Apache Superset dashboards. Run `data/schema/views.sql` after seeding.

| View | Purpose |
|------|---------|
| v_monthly_tourism | Visitors + occupancy by governorate/month |
| v_site_visits | Site-level visit data with site/governorate info |
| v_hotels | Hotels with governorate info |
| v_tourism_sites | Sites with governorate info |
| v_capacity_indicators | Computed indicators per governorate |
| v_national_summary | National totals by year |
| v_governorate_comparison | Side-by-side governorate comparison |

## Data Dictionary

### Site Types
- **archaeological**: Historical ruins, monuments, castles
- **natural**: Wadis, nature reserves, beaches, mountains
- **religious**: Mosques, churches, shrines, pilgrimage sites
- **coastal**: Beach and marine areas
- **cultural**: Streets, souks, cultural districts
- **museum**: Museums and galleries

### Hotel Classes
- **3-star**: Budget accommodation
- **4-star**: Mid-range accommodation
- **5-star**: Luxury accommodation
- **eco-lodge**: Eco-friendly/camp accommodation
- **unclassified**: Not rated

### Capacity Classification
- **under**: Under-capacity (demand exceeds supply, needs investment)
- **balanced**: Balanced capacity (supply meets demand)
- **over**: Over-capacity (excess supply)

### ETL Status
- **success**: All records processed correctly
- **partial**: Some records inserted, some skipped/errored
- **failed**: No records inserted, all errored
