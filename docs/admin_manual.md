# Administrator Manual

**Project:** Jordan Tourism AI-GIS
**Version:** 1.0
**Last Updated:** 2026-03-29

## System Architecture

```
PostgreSQL 16 + PostGIS 3.4  (Database - port 5433)
Apache Superset               (Dashboard - port 8088)
FastAPI Backend               (API - port 8000)
Next.js Frontend              (Map UI - port 3000)
Redis                         (Cache - port 6379)
```

## Installation

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM
- 50GB+ disk space

### First-Time Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd jordan-tourism-aigis

# 2. Start all services
docker-compose up -d

# 3. Wait for services to initialize (~60 seconds for Superset first run)

# 4. Seed the database with sample data
cd backend
pip install -r requirements.txt
python3 scripts/setup_database.py

# 5. Verify services
curl http://localhost:8000/health       # Backend
curl http://localhost:8088/health       # Superset
curl http://localhost:3000              # Frontend
```

### Accessing Services

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Superset | http://localhost:8088 | admin / admin |
| Backend API | http://localhost:8000 | — |
| Frontend | http://localhost:3000 | — |
| Database | localhost:5433 | tourism / tourism |

## Monthly Data Update Procedure

### Step 1: Prepare CSV Files

MoTA provides updated tourism data as CSV files:
- `visitors.csv` — Monthly visitor counts per governorate
- `occupancy.csv` — Monthly occupancy and room data
- `site_visits.csv` — Monthly site visit counts

Required columns per file are documented in `docs/database_schema.md`.

### Step 2: Upload via API

```bash
# Upload visitor data
curl -X POST http://localhost:8000/api/etl/upload \
  -F "file=@visitors.csv" \
  -F "dataset_type=visitors"

# Upload occupancy data
curl -X POST http://localhost:8000/api/etl/upload \
  -F "file=@occupancy.csv" \
  -F "dataset_type=occupancy"

# Upload site visit data
curl -X POST http://localhost:8000/api/etl/upload \
  -F "file=@site_visits.csv" \
  -F "dataset_type=site_visits"
```

### Step 3: Verify Import

```bash
# Check ETL logs
curl http://localhost:8000/api/etl/logs
```

### Step 4: Recompute Indicators

```bash
# Recompute all indicators for the current year
curl -X POST "http://localhost:8000/api/analytics/compute-all?year=2025"
```

### Step 5: Refresh Superset Dashboards

Superset caches queries. To refresh:
1. Go to Superset → Settings → Database Connections
2. Click "Test Connection" (triggers cache refresh)
3. Or reload individual dashboard pages

## Backup and Restore

### Database Backup

```bash
docker exec jordan-tourism-aigis_db_1 \
  pg_dump -U tourism tourism_gis > backup_$(date +%Y%m%d).sql
```

### Database Restore

```bash
docker exec -i jordan-tourism-aigis_db_1 \
  psql -U tourism tourism_gis < backup_20260329.sql
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker ps | grep postgis

# Restart database
docker-compose restart db

# Check logs
docker-compose logs db
```

### Superset Not Loading

```bash
# Check Superset logs
docker-compose logs superset

# Restart Superset
docker-compose restart superset

# First-time initialization takes ~60 seconds
```

### Backend API Errors

```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

## Security

### Change Default Passwords

1. **Superset admin**: Go to Superset → Settings → Users → Edit admin
2. **Database**: Update `POSTGRES_PASSWORD` in docker-compose.yml
3. **Backend**: Set `SECRET_KEY` in environment variables

### User Management

**Superset users:**
1. Go to Settings → List Users
2. Add users with appropriate roles (Admin, Alpha, Gamma, Public)

**Role permissions:**
- **Admin**: Full access to all dashboards and SQL Lab
- **Alpha**: Access to all data sources and dashboards
- **Gamma**: Access to specific dashboards only
- **Public**: Read-only access to public dashboards

## Server Migration (MoDEE Data Center)

Per RFP requirements, the system must be migrated from the staging server to the MoDEE data center:

1. Backup the database (see above)
2. Transfer the backup file to the new server
3. Install Docker and Docker Compose on the new server
4. Restore the database
5. Update environment variables with new server addresses
6. Start services with docker-compose
7. Verify all services are accessible
8. Update DNS/network configuration as needed
