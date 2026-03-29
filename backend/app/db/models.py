from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from geoalchemy2 import Geometry
from app.db.database import Base


class Governorate(Base):
    __tablename__ = "governorates"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(100), nullable=False, unique=True)
    name_ar = Column(String(100), nullable=False)
    code = Column(String(10), unique=True)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326))
    area_km2 = Column(Float)
    population = Column(Integer)


class TourismSite(Base):
    __tablename__ = "tourism_sites"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    site_type = Column(
        String(50)
    )  # archaeological, natural, religious, coastal, cultural, museum
    governorate_id = Column(Integer, ForeignKey("governorates.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    geometry = Column(Geometry("POINT", srid=4326))
    era = Column(String(100))  # historical era (e.g. "Nabataean", "Roman-Byzantine")
    description = Column(String(500))  # brief description of the site


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    hotel_class = Column(String(20))  # 3-star, 4-star, 5-star, eco-lodge
    governorate_id = Column(Integer, ForeignKey("governorates.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    geometry = Column(Geometry("POINT", srid=4326))
    total_rooms = Column(Integer, default=0)
    total_beds = Column(Integer, default=0)


class VisitorData(Base):
    __tablename__ = "visitor_data"

    id = Column(Integer, primary_key=True, index=True)
    governorate_id = Column(Integer, ForeignKey("governorates.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_visitors = Column(Integer, default=0)
    international_visitors = Column(Integer, default=0)
    domestic_visitors = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("governorate_id", "year", "month", name="uq_visitor_period"),
    )


class SiteVisitData(Base):
    __tablename__ = "site_visit_data"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("tourism_sites.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_visits = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("site_id", "year", "month", name="uq_site_visit_period"),
    )


class OccupancyData(Base):
    __tablename__ = "occupancy_data"

    id = Column(Integer, primary_key=True, index=True)
    governorate_id = Column(Integer, ForeignKey("governorates.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    avg_occupancy_rate = Column(Float, default=0.0)  # percentage 0-100
    total_rooms = Column(Integer, default=0)
    total_beds = Column(Integer, default=0)
    occupied_rooms = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("governorate_id", "year", "month", name="uq_occupancy_period"),
    )


class CapacityIndicator(Base):
    __tablename__ = "capacity_indicators"

    id = Column(Integer, primary_key=True, index=True)
    governorate_id = Column(Integer, ForeignKey("governorates.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    rooms_per_1000_visitors = Column(Float)
    beds_per_1000_visitors = Column(Float)
    occupancy_pressure_index = Column(Float)
    growth_pressure_index = Column(Float)
    capacity_adequacy_index = Column(Float)
    capacity_classification = Column(String(20))  # under, balanced, over
    priority_score = Column(Float)

    __table_args__ = (
        UniqueConstraint("governorate_id", "year", "month", name="uq_indicator_period"),
    )


class ETLLog(Base):
    __tablename__ = "etl_log"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    dataset_type = Column(String(50), nullable=False)
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_errored = Column(Integer, default=0)
    status = Column(String(20), default="success")
    error_details = Column(String)
    imported_at = Column(String)


class TransportNetworkVersion(Base):
    """
    Versioned transport network data.
    Per RFP ToR Section 3.2.2(6): "data store should keep all historical versions
    of transport network data"
    """

    __tablename__ = "transport_network_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, nullable=False)
    filename = Column(String(255), nullable=False)
    effective_date = Column(String)  # ISO date when this data becomes effective
    description = Column(String(500))
    record_count = Column(Integer, default=0)
    imported_at = Column(String)  # ISO timestamp
