# User Manual

**Project:** Jordan Tourism AI-GIS
**Version:** 1.0
**Last Updated:** 2026-03-29

## Getting Started

### Accessing the System

1. Open your web browser
2. Navigate to the system URL (provided by your IT administrator)
3. Log in with your assigned username and password

### Dashboard Overview

The system has four main components:
- **Apache Superset** — Main dashboard with charts and maps
- **Map Viewer** — Interactive Jordan map with tourism layers
- **Simulation Panel** — What-if scenario analysis
- **FastAPI Backend** — Data management and analytics API

## Apache Superset Dashboard

### National Overview

The main dashboard shows key tourism indicators for all of Jordan:
- **Total Visitors** — Total visitor count for the selected year
- **International vs Domestic** — Breakdown by visitor origin
- **Average Occupancy Rate** — Hotel occupancy across all governorates
- **Total Rooms and Beds** — Accommodation capacity

### Regional Deep-Dive

1. Use the governorate filter to select a specific region
2. View time-series charts showing monthly visitor trends
3. See occupancy rates and accommodation capacity
4. Check capacity indicators and classification

### Investment Explorer

1. Navigate to the Investment Explorer dashboard
2. View governorates ranked by investment priority score
3. Click a governorate to see detailed indicators
4. Understand justification for each ranking

### SQL Lab

For advanced users:
1. Go to SQL Lab in Superset
2. Select the "tourism_gis" database
3. Write SQL queries against any table or view
4. Export results as CSV

## Map Viewer

### Navigation

- **Zoom**: Scroll wheel or +/- buttons
- **Pan**: Click and drag
- **Click governorate**: View detailed information

### Layer Toggles

- **Hotels**: Toggle hotel markers on/off
- **Tourism Sites**: Toggle site markers on/off

### Site Information

Click any marker to see:
- Site name (English and Arabic)
- Site type (archaeological, natural, religious, etc.)
- Historical era
- Description

## What-If Simulation

### Running a Simulation

1. Select a governorate on the map
2. Go to the Simulation tab
3. Choose scenario type:
   - **Add Beds**: Enter number of beds to add
   - **Change Visitors**: Enter percentage change in visitors
4. Set the target future period (default: 12 months ahead)
5. Click "Run Simulation"

### Understanding Results

The simulation shows:
- **Forecasted Baseline**: Predicted values without your change
- **Scenario**: Predicted values with your change applied
- **Difference**: The impact of your change

### Indicators Explained

- **Rooms per 1000 visitors**: Higher = more capacity per visitor
- **Occupancy Pressure Index**: Higher = more stress on capacity (0-100)
- **Capacity Adequacy Index**: >1 = surplus, <1 = deficit
- **Classification**: Under (needs investment), Balanced, Over (surplus)

## Exporting Data

### From Superset

1. Click the three dots (⋮) on any chart
2. Select "Download" → CSV or PNG
3. For full dashboard: Use "Download as PDF"

### From SQL Lab

1. Run your query
2. Click "Download to CSV" button

## Getting Help

Contact your system administrator or the development team for assistance.
