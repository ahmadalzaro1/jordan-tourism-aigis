"""
Provider Interface for Jordan Tourism AI-GIS.

Inspired by OpenBB's provider pattern:
- Unified interface for all data sources
- Extensible: add new providers without changing core code
- Each provider implements the same interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd


class TourismProvider(ABC):
    """
    Abstract base class for all tourism data providers.
    Every data source implements this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'mota', 'openmeteo', 'worldbank')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """What this provider does."""
        pass

    @abstractmethod
    def get_visitors(
        self, governorate: str = None, year: int = None, month: int = None
    ) -> pd.DataFrame:
        """Get visitor data."""
        pass

    @abstractmethod
    def get_occupancy(
        self, governorate: str = None, year: int = None, month: int = None
    ) -> pd.DataFrame:
        """Get occupancy data."""
        pass

    @abstractmethod
    def get_hotels(self, governorate: str = None) -> pd.DataFrame:
        """Get hotel data."""
        pass

    @abstractmethod
    def get_sites(self, governorate: str = None, site_type: str = None) -> pd.DataFrame:
        """Get tourism site data."""
        pass

    def get_site_visits(self, site_id: int = None, year: int = None) -> pd.DataFrame:
        """Get site visit data. Optional — not all providers have this."""
        return pd.DataFrame()

    def get_weather(
        self, governorate: str = None, year: int = None, month: int = None
    ) -> pd.DataFrame:
        """Get weather data. Optional."""
        return pd.DataFrame()

    def get_calendar(self, year: int = None) -> pd.DataFrame:
        """Get calendar events (Ramadan, Eid, holidays). Optional."""
        return pd.DataFrame()

    def get_economic(self, indicator: str = None, year: int = None) -> pd.DataFrame:
        """Get economic indicators. Optional."""
        return pd.DataFrame()

    def get_conflicts(self, status: str = "active") -> pd.DataFrame:
        """Get conflict events. Optional."""
        return pd.DataFrame()

    def get_wikipedia(self, page: str = None, year: int = None) -> pd.DataFrame:
        """Get Wikipedia page views. Optional."""
        return pd.DataFrame()

    def get_transport(self, governorate: str = None) -> pd.DataFrame:
        """Get transport accessibility data. Optional."""
        return pd.DataFrame()


class ProviderRegistry:
    """
    Registry of all available providers.
    Inspired by OpenBB's provider discovery pattern.
    """

    _providers: Dict[str, TourismProvider] = {}

    @classmethod
    def register(cls, provider: TourismProvider):
        """Register a provider."""
        cls._providers[provider.name] = provider

    @classmethod
    def get(cls, name: str) -> Optional[TourismProvider]:
        """Get a provider by name."""
        return cls._providers.get(name)

    @classmethod
    def list_all(cls) -> List[Dict[str, str]]:
        """List all registered providers."""
        return [
            {"name": p.name, "description": p.description}
            for p in cls._providers.values()
        ]

    @classmethod
    def get_data(cls, provider_name: str, data_type: str, **kwargs) -> pd.DataFrame:
        """Unified data access: provider.get_data('mota', 'visitors', governorate='AQAB')."""
        provider = cls.get(provider_name)
        if not provider:
            raise ValueError(
                f"Provider '{provider_name}' not found. Available: {list(cls._providers.keys())}"
            )

        method = getattr(provider, f"get_{data_type}", None)
        if not method:
            raise ValueError(
                f"Data type '{data_type}' not available from {provider_name}"
            )

        return method(**kwargs)
