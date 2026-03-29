#!/bin/bash
# Superset initialization script
# Adds the tourism_gis database connection and creates initial dashboards

set -e

echo "=== Jordan Tourism AI-GIS: Superset Init ==="

# Wait for Superset to be ready
sleep 10

# Initialize the database (first run only)
superset db upgrade

# Create admin user
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@tourism.jo \
    --password admin

# Initialize Superset
superset init

echo "=== Superset initialized ==="
echo "Access at: http://localhost:8088"
echo "Login: admin / admin"
echo ""
echo "After login, add the database connection:"
echo "  1. Go to Settings > Database Connections"
echo "  2. Add database with URI: postgresql://tourism:tourism@db:5432/tourism_gis"
echo "  3. Enable 'Allow DML' for SQL Lab access"
