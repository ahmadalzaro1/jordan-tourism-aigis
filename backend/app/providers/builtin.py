"""
Built-in Providers for Jordan Tourism AI-GIS.

Implements the TourismProvider interface for all data sources.
"""

import pandas as pd
import os
from app.providers.base import TourismProvider, ProviderRegistry

DATA_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "data",
)


class MoTAProvider(TourismProvider):
    """MoTA tourism statistics (visitors, occupancy, sites, hotels)."""

    name = "mota"
    description = (
        "Ministry of Tourism and Antiquities — visitor counts, occupancy, sites, hotels"
    )

    def _load(self, filename):
        path = os.path.join(DATA_DIR, "sample", filename)
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

    def get_visitors(self, governorate=None, year=None, month=None):
        df = self._load("visitors.csv")
        if governorate:
            df = df[df["governorate_code"] == governorate]
        if year:
            df = df[df["year"] == year]
        if month:
            df = df[df["month"] == month]
        return df

    def get_occupancy(self, governorate=None, year=None, month=None):
        df = self._load("occupancy.csv")
        if governorate:
            df = df[df["governorate_code"] == governorate]
        if year:
            df = df[df["year"] == year]
        if month:
            df = df[df["month"] == month]
        return df

    def get_hotels(self, governorate=None):
        df = self._load("hotels.csv")
        if governorate:
            df = df[df["governorate_code"] == governorate]
        return df

    def get_sites(self, governorate=None, site_type=None):
        df = self._load("sites.csv")
        if governorate:
            df = df[df["governorate_code"] == governorate]
        if site_type:
            df = df[df["site_type"] == site_type]
        return df

    def get_site_visits(self, site_id=None, year=None):
        df = self._load("site_visits.csv")
        if site_id:
            df = df[df["site_id"] == site_id]
        if year:
            df = df[df["year"] == year]
        return df


class OpenMeteoProvider(TourismProvider):
    """Open-Meteo weather data."""

    name = "openmeteo"
    description = "Open-Meteo — temperature, rainfall, sunshine hours"

    def get_weather(self, governorate=None, year=None, month=None):
        path = os.path.join(DATA_DIR, "weather", "all_governorates_weather.csv")
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path).rename(columns={"gov": "governorate_code"})
        if governorate:
            df = df[df["governorate_code"] == governorate]
        if year:
            df = df[df["year"] == year]
        if month:
            df = df[df["month"] == month]
        return df

    def get_visitors(self, **kwargs):
        return pd.DataFrame()

    def get_occupancy(self, **kwargs):
        return pd.DataFrame()

    def get_hotels(self, **kwargs):
        return pd.DataFrame()

    def get_sites(self, **kwargs):
        return pd.DataFrame()


class IslamicCalendarProvider(TourismProvider):
    """Islamic calendar (Ramadan, Eid dates)."""

    name = "islamic_calendar"
    description = "Islamic calendar — Ramadan, Eid al-Fitr, Eid al-Adha dates"

    def get_calendar(self, year=None):
        path = os.path.join(DATA_DIR, "calendar", "islamic_calendar.csv")
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        if year:
            df = df[df["year"] == year]
        return df

    def get_visitors(self, **kwargs):
        return pd.DataFrame()

    def get_occupancy(self, **kwargs):
        return pd.DataFrame()

    def get_hotels(self, **kwargs):
        return pd.DataFrame()

    def get_sites(self, **kwargs):
        return pd.DataFrame()


class WorldBankProvider(TourismProvider):
    """World Bank economic indicators."""

    name = "worldbank"
    description = "World Bank — GDP, inflation, unemployment, exchange rates"

    def get_economic(self, indicator=None, year=None):
        path = os.path.join(DATA_DIR, "economic", "jordan_economic_indicators.csv")
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        if year:
            df = df[df["year"] == year]
        return df

    def get_visitors(self, **kwargs):
        return pd.DataFrame()

    def get_occupancy(self, **kwargs):
        return pd.DataFrame()

    def get_hotels(self, **kwargs):
        return pd.DataFrame()

    def get_sites(self, **kwargs):
        return pd.DataFrame()


class WikipediaProvider(TourismProvider):
    """Wikipedia page views."""

    name = "wikipedia"
    description = "Wikipedia — page views for tourism sites"

    def get_wikipedia(self, page=None, year=None):
        path = os.path.join(DATA_DIR, "external", "wikipedia_views.csv")
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        if page:
            df = df[df["page"] == page]
        if year:
            df = df[df["year"] == year]
        return df

    def get_visitors(self, **kwargs):
        return pd.DataFrame()

    def get_occupancy(self, **kwargs):
        return pd.DataFrame()

    def get_hotels(self, **kwargs):
        return pd.DataFrame()

    def get_sites(self, **kwargs):
        return pd.DataFrame()


class ConflictProvider(TourismProvider):
    """Regional conflict events."""

    name = "conflicts"
    description = "Regional conflicts — war, crises affecting tourism"

    def get_conflicts(self, status="active"):
        path = os.path.join(DATA_DIR, "external", "regional_conflicts.csv")
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        return df

    def get_visitors(self, **kwargs):
        return pd.DataFrame()

    def get_occupancy(self, **kwargs):
        return pd.DataFrame()

    def get_hotels(self, **kwargs):
        return pd.DataFrame()

    def get_sites(self, **kwargs):
        return pd.DataFrame()


class TransportProvider(TourismProvider):
    """Transport accessibility data."""

    name = "transport"
    description = "Transport network — road accessibility scores"

    def get_transport(self, governorate=None):
        path = os.path.join(DATA_DIR, "transport", "governorate_accessibility.csv")
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        if governorate:
            df = df[df["governorate_code"] == governorate]
        return df

    def get_visitors(self, **kwargs):
        return pd.DataFrame()

    def get_occupancy(self, **kwargs):
        return pd.DataFrame()

    def get_hotels(self, **kwargs):
        return pd.DataFrame()

    def get_sites(self, **kwargs):
        return pd.DataFrame()


# Register all providers
ProviderRegistry.register(MoTAProvider())
ProviderRegistry.register(OpenMeteoProvider())
ProviderRegistry.register(IslamicCalendarProvider())
ProviderRegistry.register(WorldBankProvider())
ProviderRegistry.register(WikipediaProvider())
ProviderRegistry.register(ConflictProvider())
ProviderRegistry.register(TransportProvider())
