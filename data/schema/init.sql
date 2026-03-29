-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tables are created by SQLAlchemy (app.main creates them on startup)
-- Views are created by views.sql (run after seeding)
-- This init script ensures PostGIS is ready
