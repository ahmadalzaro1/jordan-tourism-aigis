"""
Python SDK for Jordan Tourism AI-GIS.

OpenBB-inspired API:
    from tourism_gis.sdk import TourismSDK
    sdk = TourismSDK()
    sdk.visitors.governorate("AQAB", year=2025)
    sdk.forecast.run("AQAB", horizon=12)
    sdk.simulation.accommodation("AQAB", added_beds=500)
"""

import os
import sys
import pandas as pd
from typing import Optional, List, Dict, Any

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class VisitorsAPI:
    """Visitor data queries."""

    def __init__(self, sdk):
        self._sdk = sdk

    def governorate(
        self, gov_code: str, year: int = None, month: int = None
    ) -> pd.DataFrame:
        """Get visitor data for a governorate."""
        from app.providers.builtin import ProviderRegistry

        return ProviderRegistry.get_data(
            "mota", "visitors", governorate=gov_code, year=year, month=month
        )

    def national(self, year: int = None) -> pd.DataFrame:
        """Get national visitor totals."""
        from app.providers.builtin import ProviderRegistry

        df = ProviderRegistry.get_data("mota", "visitors", year=year)
        if df.empty:
            return df
        return (
            df.groupby(["year", "month"])
            .agg(
                total_visitors=("total_visitors", "sum"),
                international=("international_visitors", "sum"),
                domestic=("domestic_visitors", "sum"),
            )
            .reset_index()
        )

    def all_governorates(self, year: int = None) -> pd.DataFrame:
        """Get visitors for all governorates."""
        from app.providers.builtin import ProviderRegistry

        return ProviderRegistry.get_data("mota", "visitors", year=year)


class OccupancyAPI:
    """Occupancy data queries."""

    def __init__(self, sdk):
        self._sdk = sdk

    def governorate(self, gov_code: str, year: int = None) -> pd.DataFrame:
        from app.providers.builtin import ProviderRegistry

        return ProviderRegistry.get_data(
            "mota", "occupancy", governorate=gov_code, year=year
        )

    def national(self, year: int = None) -> pd.DataFrame:
        from app.providers.builtin import ProviderRegistry

        df = ProviderRegistry.get_data("mota", "occupancy", year=year)
        if df.empty:
            return df
        return (
            df.groupby(["year", "month"])
            .agg(
                avg_occupancy=("avg_occupancy_rate", "mean"),
                total_rooms=("total_rooms", "sum"),
                total_beds=("total_beds", "sum"),
            )
            .reset_index()
        )


class ForecastAPI:
    """Forecasting queries."""

    def __init__(self, sdk=None):
        self._sdk = sdk

    def run(self, gov_code: str, horizon: int = 12, method: str = "auto") -> dict:
        """Run a forecast for a governorate."""
        from app.providers.builtin import ProviderRegistry
        from app.analytics.forecasting import prepare_monthly_series, forecast_best

        df = ProviderRegistry.get_data("mota", "visitors", governorate=gov_code)
        if df.empty or len(df) < 12:
            return {"error": "Insufficient data"}

        data_list = [
            {"year": r.year, "month": r.month, "total": r.total_visitors}
            for _, r in df.iterrows()
        ]
        ts = prepare_monthly_series(data_list)
        return forecast_best(ts, horizon)

    def backtest(self, gov_code: str = None) -> dict:
        """Run back-test on historical data."""
        from scripts.backtest_forecast import run_backtest
        from app.providers.builtin import ProviderRegistry

        df = ProviderRegistry.get_data("mota", "visitors")
        return run_backtest(df)


class SimulationAPI:
    """What-if simulation queries."""

    def __init__(self, sdk=None):
        self._sdk = sdk

    def accommodation(
        self, gov_code: str, added_beds: int, target_months: int = 12
    ) -> dict:
        """Run accommodation scenario simulation."""
        from app.analytics.simulation import accommodation_scenario
        from app.analytics.indicators import compute_indicators_for_period
        from app.providers.builtin import ProviderRegistry

        occ = ProviderRegistry.get_data("mota", "occupancy", governorate=gov_code)
        vis = ProviderRegistry.get_data("mota", "visitors", governorate=gov_code)

        if occ.empty or vis.empty:
            return {"error": "Insufficient data"}

        baseline = {
            "total_rooms": int(occ["total_rooms"].mean()),
            "total_beds": int(occ["total_beds"].mean()),
            "total_visitors": int(vis["total_visitors"].sum()),
            "avg_occupancy": float(occ["avg_occupancy_rate"].mean()),
            "peak_occupancy": float(occ["avg_occupancy_rate"].max()),
            "visitors_prev_year": int(
                vis[vis["year"] == vis["year"].max() - 1]["total_visitors"].sum()
            ),
        }
        return accommodation_scenario(baseline, gov_code, added_beds)

    def demand(self, gov_code: str, change_pct: float, target_months: int = 12) -> dict:
        """Run demand scenario simulation."""
        from app.analytics.simulation import demand_scenario
        from app.providers.builtin import ProviderRegistry

        vis = ProviderRegistry.get_data("mota", "visitors", governorate=gov_code)
        occ = ProviderRegistry.get_data("mota", "occupancy", governorate=gov_code)

        baseline = {
            "total_rooms": int(occ["total_rooms"].mean()) if not occ.empty else 0,
            "total_beds": int(occ["total_beds"].mean()) if not occ.empty else 0,
            "total_visitors": int(vis["total_visitors"].sum()),
            "avg_occupancy": float(occ["avg_occupancy_rate"].mean())
            if not occ.empty
            else 0,
            "peak_occupancy": float(occ["avg_occupancy_rate"].max())
            if not occ.empty
            else 0,
            "visitors_prev_year": int(
                vis[vis["year"] == vis["year"].max() - 1]["total_visitors"].sum()
            ),
        }
        return demand_scenario(baseline, gov_code, change_pct)


class IndicatorsAPI:
    """Indicator computation."""

    def __init__(self, sdk=None):
        self._sdk = sdk

    def compute(self, gov_code: str, year: int = 2025) -> dict:
        """Compute all indicators for a governorate."""
        from app.analytics.indicators import compute_indicators_for_period
        from app.analytics.classification import classify_capacity
        from app.providers.builtin import ProviderRegistry

        vis = ProviderRegistry.get_data(
            "mota", "visitors", governorate=gov_code, year=year
        )
        occ = ProviderRegistry.get_data(
            "mota", "occupancy", governorate=gov_code, year=year
        )

        if vis.empty or occ.empty:
            return {"error": "No data"}

        prev = ProviderRegistry.get_data(
            "mota", "visitors", governorate=gov_code, year=year - 1
        )
        prev_total = int(prev["total_visitors"].sum()) if not prev.empty else 0

        indicators = compute_indicators_for_period(
            total_rooms=int(occ["total_rooms"].mean()),
            total_beds=int(occ["total_beds"].mean()),
            total_visitors=int(vis["total_visitors"].sum()),
            avg_occupancy=float(occ["avg_occupancy_rate"].mean()),
            peak_occupancy=float(occ["avg_occupancy_rate"].max()),
            visitors_prev_year=prev_total,
        )
        classification = classify_capacity(indicators)
        return {"indicators": indicators, "classification": classification}


class WeatherAPI:
    """Weather data queries."""

    def __init__(self, sdk=None):
        self._sdk = sdk

    def governorate(self, gov_code: str, year: int = None) -> pd.DataFrame:
        from app.providers.builtin import ProviderRegistry

        return ProviderRegistry.get_data(
            "openmeteo", "weather", governorate=gov_code, year=year
        )


class ConflictsAPI:
    """Conflict event queries."""

    def __init__(self, sdk=None):
        self._sdk = sdk

    def active(self) -> pd.DataFrame:
        from app.providers.builtin import ProviderRegistry

        return ProviderRegistry.get_data("conflicts", "conflicts", status="active")


class ProvidersAPI:
    """Provider management."""

    def list(self) -> list:
        from app.providers.builtin import ProviderRegistry

        return ProviderRegistry.list_all()


class TourismSDK:
    """
    Python SDK for Jordan Tourism AI-GIS.

    Usage:
        from tourism_gis.sdk import TourismSDK
        sdk = TourismSDK()

        # Query data
        sdk.visitors.governorate("AQAB", year=2025)
        sdk.occupancy.national(2025)
        sdk.weather.governorate("AMM")

        # Analytics
        sdk.forecast.run("AQAB", horizon=12)
        sdk.simulation.accommodation("AQAB", added_beds=500)
        sdk.indicators.compute("AQAB")

        # Conflicts
        sdk.conflicts.active()

        # Providers
        sdk.providers.list()
    """

    def __init__(self):
        self.visitors = VisitorsAPI(self)
        self.occupancy = OccupancyAPI(self)
        self.forecast = ForecastAPI(self)
        self.simulation = SimulationAPI(self)
        self.indicators = IndicatorsAPI(self)
        self.weather = WeatherAPI(self)
        self.conflicts = ConflictsAPI(self)
        self.providers = ProvidersAPI()


# Singleton instance
sdk = TourismSDK()
