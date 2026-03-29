"""
Superset configuration for Jordan Tourism AI-GIS.
Connects directly to the PostGIS database.
"""

import os

# Secret key for session signing
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "jordan-tourism-aigis-secret-key")

# Database connection for Superset's own metadata
SQLALCHEMY_DATABASE_URI = "postgresql://tourism:tourism@db:5432/tourism_gis"

# Redis for caching
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

# Cache configuration
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": 1,
}

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ENABLE_JAVASCRIPT_CONTROLS": True,
}

# Row limit for SQL Lab
SQL_MAX_ROW = 100000

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {"csv", "json", "parquet", "xlsx"}

# Enable geospatial visualizations
ENABLE_GEOJSON = True

# Default time grain for time series
DEFAULT_TIME_GRAIN = "P1M"  # Monthly

# CORS
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": ["http://localhost:3000", "http://localhost:8000"],
}
