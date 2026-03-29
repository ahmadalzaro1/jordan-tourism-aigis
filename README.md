# Jordan Tourism AI-GIS

AI-Enabled Geo-Analytics Platform for Tourism Demand, Infrastructure Optimization, and Investment Prioritization in Jordan.

## What This Is

An open-source analytics platform that integrates 55 data sources across 12 tiers to provide data-driven insights into Jordan's tourism sector. Built for the Ministry of Tourism and Antiquities (MoTA) / Ministry of Digital Economy and Entrepreneurship (MoDEE).

## Key Results

| Metric | Target (RFP) | Achieved |
|--------|-------------|----------|
| Forecast MAPE | ≤ 20% | **3.58%** |
| Reproducibility | 100% | **100%** |
| Data Sources | 3 | **55** |
| Analytics Functions | 15+ | **70** |

## Architecture

```
Frontend (Next.js + MapLibre + shadcn/ui)    ← 22 React components
    ↕
Backend (FastAPI + PostgreSQL/PostGIS)        ← 28 Python modules
    ↕
Apache Superset                               ← BI dashboards
    ↕
55 Data Sources                               ← Tourism, weather, calendar, conflicts, economics
```

## Quick Start

```bash
# Start all services
docker-compose up -d

# Seed database + create views
cd backend && python3 scripts/setup_database.py

# Access:
# Dashboard:  http://localhost:3000
# API:        http://localhost:8000/docs
# Superset:   http://localhost:8088 (admin/admin)
```

## Data Sources (55 files, 12 tiers)

| Tier | Data | Records |
|------|------|---------|
| Tourism | Visitors, occupancy, sites, hotels | 7,680 |
| OpenStreetMap | Hotels, restaurants, historic sites | 15,224 |
| Weather | Temperature, rainfall × 12 governorates | 936 |
| Calendar | Ramadan, Eid, public holidays | 108 |
| Economics | GDP, inflation, unemployment, exchange rates | 70 |
| Wikipedia | Page views for 7 tourism sites | 432 |
| Aviation | Queen Alia airport passengers | 72 |
| Conflicts | Regional conflict timeline | 21 events |
| Markets | Source market vulnerability analysis | 12 markets |
| Transport | Road accessibility scores | 12 governorates |

## Analytics Functions (70)

- **Indicators** (32): capacity, seasonality, elasticity, concentration, recovery, spillover
- **Scoring** (14): priority investment, conflict resilience, ROI proxy
- **Classification** (3): capacity classification (data-driven thresholds)
- **Forecasting** (4): Prophet + ARIMA with autoresearch optimization
- **Simulation** (2): accommodation and demand scenarios
- **Data-Driven** (7): anomaly detection, trend analysis, confidence scoring
- **Clusters** (6): tourism clusters (Petra, Wadi Rum, Aqaba, Dead Sea, Amman, Karak)

## Key Findings

1. **Hotel supply predicts demand** (r=+0.812) — build more hotels, tourists come
2. **All governorates complement each other** (r=+0.82-0.90) — tourists visit multiple
3. **Petra is 41% dependent on tourism** — extreme vulnerability
4. **43% of tourism is conflict-vulnerable** — regional instability matters
5. **Neighbor spillover**: Dead Sea→Amman (r=+0.546), Aqaba→Petra (r=+0.424)
6. **GDP growth predicts next year tourism** (r=+0.841)
7. **Summer drops recover in 10 months, winter drops in 3 months**

## Forecast Performance

| Configuration | MAPE |
|--------------|------|
| Prophet cps=0.01 (optimal) | **3.58%** |
| Prophet cps=0.05 (default) | 4.89% |
| ExpSmoothing (mul, mul) | 3.71% |
| ARIMA (1,1,1) | 26.5% |

## License

MIT
