"""
Tourism Clusters for Jordan Tourism AI-GIS.

Per RFP ToR Section 3.1.2 — Geographic coverage focuses on representative tourism clusters:
1. Petra – Wadi Musa Cluster
2. Wadi Rum – Desert Experience Cluster
3. Aqaba – Coastal Tourism Hub
4. Dead Sea Corridor
5. Amman & Surroundings
6. Karak Corridor

Each cluster maps to specific governorate(s) and can contain multiple tourism sites.
"""

TOURISM_CLUSTERS = {
    "petra_wadi_musa": {
        "name_en": "Petra – Wadi Musa",
        "name_ar": "البتراء – وادي موسى",
        "governorate_codes": ["MAA"],
        "site_names": ["Petra", "Little Petra", "Shobak Castle", "Ba'ja", "Basta"],
        "description": "High international visitation, strong demand seasonality. Need to examine distribution of beds between central Wadi Musa and surrounding villages.",
    },
    "wadi_rum": {
        "name_en": "Wadi Rum – Desert Experience",
        "name_ar": "وادي رم – تجربة الصحراء",
        "governorate_codes": ["AQAB"],
        "site_names": [
            "Wadi Rum",
            "Khazali Canyon",
            "Lawrence's Spring",
            "Burdah Rock Bridge",
            "Um Fruth Rock Bridge",
            "Jabal Umm ad-Dami",
        ],
        "description": "Rising demand for camps and eco-lodge type accommodation. Environmental and cultural sensitivity requiring careful capacity planning.",
    },
    "aqaba": {
        "name_en": "Aqaba – Coastal Tourism Hub",
        "name_ar": "العقبة – مركز السياحة الساحلية",
        "governorate_codes": ["AQAB"],
        "site_names": ["Aqaba Marine Park", "Aqaba Castle", "Aqaba Church", "Ayla"],
        "description": "Significant hotel capacity and international arrivals. Need to balance occupancy, diversification, and linkages to other regions.",
    },
    "dead_sea": {
        "name_en": "Dead Sea Corridor",
        "name_ar": "ممر البحر الميت",
        "governorate_codes": ["BAL"],
        "site_names": ["Dead Sea Beaches", "Al-Maghtas", "Wadi Mujib"],
        "description": "High-value, resort-based tourism with environmental constraints. Opportunity to assess long-term capacity and diversification options.",
    },
    "amman": {
        "name_en": "Amman & Surroundings",
        "name_ar": "عمان والمناطق المحيطة",
        "governorate_codes": ["AMM"],
        "site_names": [
            "Amman Citadel",
            "Roman Theatre",
            "Jordan Museum",
            "Rainbow Street",
            "King Abdullah I Mosque",
            "Iraq al-Amir",
        ],
        "description": "Gateway city with diverse accommodation types. Key to connecting international arrivals with other regions.",
    },
    "karak": {
        "name_en": "Karak Corridor",
        "name_ar": "ممر الكرك",
        "governorate_codes": ["KAR"],
        "site_names": ["Karak Castle", "Bab ed-Dhra", "Ghor es-Safi", "Lot's Cave"],
        "description": "Emerging route where cultural/religious tourism may grow. Infrastructure still developing, ideal test case for early-stage investment guidance.",
    },
}

# Accommodation classes for simulation filtering
ACCOMMODATION_CLASSES = {
    "5star": {"label": "5-star Hotels", "label_ar": "فنادق 5 نجوم"},
    "4star": {"label": "4-star Hotels", "label_ar": "فنادق 4 نجوم"},
    "3star": {"label": "3-star Hotels", "label_ar": "فنادق 3 نجوم"},
    "eco_lodge": {"label": "Eco-Lodges & Camps", "label_ar": "النزل البيئية والتخييم"},
    "guest_house": {"label": "Guest Houses", "label_ar": "بيت الضيافة"},
    "all": {"label": "All Classes", "label_ar": "جميع الفئات"},
}


def get_cluster_governorate_ids(cluster_key, db_governorates):
    """Get governorate IDs for a cluster."""
    cluster = TOURISM_CLUSTERS.get(cluster_key)
    if not cluster:
        return []
    return [g.id for g in db_governorates if g.code in cluster["governorate_codes"]]


def get_cluster_summary(cluster_key, db):
    """Get aggregated data for a cluster."""
    from sqlalchemy import func
    from app.db.models import Governorate, VisitorData, OccupancyData, Hotel

    cluster = TOURISM_CLUSTERS.get(cluster_key)
    if not cluster:
        return None

    gov_ids = get_cluster_governorate_ids(cluster_key, db.query(Governorate).all())
    if not gov_ids:
        return None

    year = 2025
    visitors = (
        db.query(func.sum(VisitorData.total_visitors))
        .filter(
            VisitorData.governorate_id.in_(gov_ids),
            VisitorData.year == year,
        )
        .scalar()
        or 0
    )

    occupancy = (
        db.query(
            func.avg(OccupancyData.avg_occupancy_rate),
            func.coalesce(func.sum(OccupancyData.total_rooms), 0),
            func.coalesce(func.sum(OccupancyData.total_beds), 0),
        )
        .filter(
            OccupancyData.governorate_id.in_(gov_ids),
            OccupancyData.year == year,
        )
        .first()
    )

    hotels = (
        db.query(func.count(Hotel.id))
        .filter(
            Hotel.governorate_id.in_(gov_ids),
        )
        .scalar()
        or 0
    )

    return {
        "key": cluster_key,
        "name_en": cluster["name_en"],
        "name_ar": cluster["name_ar"],
        "description": cluster["description"],
        "governorate_codes": cluster["governorate_codes"],
        "site_names": cluster["site_names"],
        "total_visitors": visitors,
        "avg_occupancy": round(occupancy[0], 1) if occupancy and occupancy[0] else 0,
        "total_rooms": occupancy[1] if occupancy else 0,
        "total_beds": occupancy[2] if occupancy else 0,
        "hotel_count": hotels,
    }
