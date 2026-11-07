-- SQL Views for Apache Superset dashboards
-- These pre-join data so Superset can build charts without complex queries.
-- Run AFTER seed_database.py

-- ==========================================
-- View: Monthly tourism by governorate (main dashboard table)
-- ==========================================
CREATE OR REPLACE VIEW v_monthly_tourism AS
SELECT
    g.id AS governorate_id,
    g.name_en AS governorate,
    g.name_ar AS governorate_ar,
    g.code AS governorate_code,
    v.year,
    v.month,
    TO_DATE(v.year || '-' || LPAD(v.month::text, 2, '0') || '-01', 'YYYY-MM-DD') AS date,
    v.total_visitors,
    v.international_visitors,
    v.domestic_visitors,
    o.avg_occupancy_rate,
    o.total_rooms,
    o.total_beds,
    o.occupied_rooms
FROM governorates g
LEFT JOIN visitor_data v ON v.governorate_id = g.id
LEFT JOIN occupancy_data o ON o.governorate_id = g.id AND o.year = v.year AND o.month = v.month;

-- ==========================================
-- View: Site visits with site details
-- ==========================================
CREATE OR REPLACE VIEW v_site_visits AS
SELECT
    ts.id AS site_id,
    ts.name_en AS site_name,
    ts.name_ar AS site_name_ar,
    ts.site_type,
    g.name_en AS governorate,
    g.code AS governorate_code,
    sv.year,
    sv.month,
    TO_DATE(sv.year || '-' || LPAD(sv.month::text, 2, '0') || '-01', 'YYYY-MM-DD') AS date,
    sv.total_visits
FROM site_visit_data sv
JOIN tourism_sites ts ON ts.id = sv.site_id
JOIN governorates g ON g.id = ts.governorate_id;

-- ==========================================
-- View: Hotels with governorate info
-- ==========================================
CREATE OR REPLACE VIEW v_hotels AS
SELECT
    h.id,
    h.name AS hotel_name,
    h.hotel_class,
    g.name_en AS governorate,
    g.code AS governorate_code,
    h.latitude,
    h.longitude,
    h.total_rooms,
    h.total_beds
FROM hotels h
JOIN governorates g ON g.id = h.governorate_id;

-- ==========================================
-- View: Tourism sites with governorate info
-- ==========================================
CREATE OR REPLACE VIEW v_tourism_sites AS
SELECT
    ts.id,
    ts.name_en AS site_name,
    ts.name_ar AS site_name_ar,
    ts.site_type,
    ts.era,
    ts.description,
    g.name_en AS governorate,
    g.code AS governorate_code,
    ts.latitude,
    ts.longitude
FROM tourism_sites ts
JOIN governorates g ON g.id = ts.governorate_id;

-- ==========================================
-- View: Capacity indicators (latest per governorate)
-- ==========================================
CREATE OR REPLACE VIEW v_capacity_indicators AS
SELECT
    g.name_en AS governorate,
    g.code AS governorate_code,
    ci.year,
    ci.month,
    ci.rooms_per_1000_visitors,
    ci.beds_per_1000_visitors,
    ci.occupancy_pressure_index,
    ci.growth_pressure_index,
    ci.capacity_adequacy_index,
    ci.capacity_classification,
    ci.priority_score
FROM capacity_indicators ci
JOIN governorates g ON g.id = ci.governorate_id;

-- ==========================================
-- View: National summary by year
-- ==========================================
CREATE OR REPLACE VIEW v_national_summary AS
WITH visitors AS (
 SELECT year, SUM(total_visitors) AS total_visitors,
 SUM(international_visitors) AS international_visitors,
 SUM(domestic_visitors) AS domestic_visitors FROM visitor_data GROUP BY year
), occupancy AS (
 SELECT year, AVG(avg_occupancy_rate) AS avg_occupancy_rate FROM occupancy_data GROUP BY year
), hotels_summary AS (
 SELECT COALESCE(SUM(total_rooms),0) AS total_rooms,
 COALESCE(SUM(total_beds),0) AS total_beds, COUNT(*) AS total_hotels FROM hotels
)
SELECT v.*, o.avg_occupancy_rate, h.total_rooms, h.total_beds, h.total_hotels
FROM visitors v LEFT JOIN occupancy o USING(year) CROSS JOIN hotels_summary h;

-- ==========================================
-- View: Governorate comparison (for bar charts)
-- ==========================================
CREATE OR REPLACE VIEW v_governorate_comparison AS
SELECT g.name_en AS governorate, g.code, g.area_km2, g.population,
 COALESCE(v.total_visitors,0) AS total_visitors,
 COALESCE(o.avg_occupancy_rate,0) AS avg_occupancy_rate,
 COALESCE(h.total_rooms,0) AS total_rooms, COALESCE(h.total_beds,0) AS total_beds,
 COALESCE(h.hotel_count,0) AS hotel_count, COALESCE(ts.site_count,0) AS site_count
FROM governorates g
LEFT JOIN (SELECT governorate_id,SUM(total_visitors) AS total_visitors FROM visitor_data WHERE year=2025 GROUP BY governorate_id) v ON v.governorate_id=g.id
LEFT JOIN (SELECT governorate_id,AVG(avg_occupancy_rate) AS avg_occupancy_rate FROM occupancy_data WHERE year=2025 GROUP BY governorate_id) o ON o.governorate_id=g.id
LEFT JOIN (SELECT governorate_id,SUM(total_rooms) AS total_rooms,SUM(total_beds) AS total_beds,COUNT(*) AS hotel_count FROM hotels GROUP BY governorate_id) h ON h.governorate_id=g.id
LEFT JOIN (SELECT governorate_id,COUNT(*) AS site_count FROM tourism_sites GROUP BY governorate_id) ts ON ts.governorate_id=g.id;
