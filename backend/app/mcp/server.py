"""
MCP Server for Jordan Tourism AI-GIS.

Allows AI agents to query tourism data via natural language.
Inspired by OpenBB's MCP integration.

Usage:
    from app.mcp.server import TourismMCPServer
    mcp = TourismMCPServer()
    result = mcp.query("What is the forecast for Aqaba next year?")
"""

import json
from typing import Dict, Any


class TourismMCPServer:
    """
    MCP-style server for AI agent integration.

    AI agents can query:
    - Tourism data (visitors, occupancy, hotels, sites)
    - Forecasts (Prophet/ARIMA)
    - Simulations (accommodation/demand scenarios)
    - Indicators (capacity, pressure, growth)
    - Conflicts (regional events)
    - Weather (temperature, rainfall)
    """

    def __init__(self):
        from app.sdk.tourism import TourismSDK

        self.sdk = TourismSDK()

    def query(self, natural_language: str) -> Dict[str, Any]:
        """
        Parse natural language and execute the appropriate action.

        Examples:
            "What is the forecast for Aqaba next year?"
            "Show me occupancy for all governorates in 2025"
            "What if we add 500 beds in Petra?"
            "Which governorate has the highest tourism dependency?"
        """
        nl = natural_language.lower()

        # Route to appropriate action
        if "forecast" in nl:
            return self._handle_forecast(nl)
        elif "simulation" in nl or "what if" in nl or "what-if" in nl:
            return self._handle_simulation(nl)
        elif "occupancy" in nl:
            return self._handle_occupancy(nl)
        elif "visitor" in nl or "tourist" in nl:
            return self._handle_visitors(nl)
        elif "indicator" in nl or "capacity" in nl or "pressure" in nl:
            return self._handle_indicators(nl)
        elif "conflict" in nl or "war" in nl:
            return self._handle_conflicts(nl)
        elif "weather" in nl or "temperature" in nl or "rain" in nl:
            return self._handle_weather(nl)
        elif "hotel" in nl:
            return self._handle_hotels(nl)
        elif "site" in nl or "attraction" in nl:
            return self._handle_sites(nl)
        elif "provider" in nl:
            return self._handle_providers(nl)
        else:
            return {
                "action": "help",
                "message": "I can help with: forecasts, simulations, visitors, occupancy, indicators, conflicts, weather, hotels, sites, providers",
                "examples": [
                    "What is the forecast for Aqaba next year?",
                    "Show me occupancy for Amman in 2025",
                    "What if we add 500 beds in Petra?",
                    "Which governorate has the highest capacity pressure?",
                ],
            }

    def _parse_governorate(self, text: str) -> str:
        """Extract governorate code from text."""
        gov_map = {
            "amman": "AMM",
            "irbid": "IRB",
            "zarqa": "ZAR",
            "mafraq": "MAF",
            "jerash": "JER",
            "ajloun": "AJL",
            "balqa": "BAL",
            "madaba": "MAD",
            "karak": "KAR",
            "tafilah": "TAF",
            "petra": "MAA",
            "ma'an": "MAA",
            "aqaba": "AQAB",
            "aqab": "AQAB",
            "dead sea": "BAL",
            "wadi musa": "MAA",
        }
        for name, code in gov_map.items():
            if name in text:
                return code
        return None

    def _parse_year(self, text: str) -> int:
        """Extract year from text."""
        import re

        match = re.search(r"20[12]\d", text)
        return int(match.group()) if match else 2025

    def _parse_number(self, text: str) -> int:
        """Extract a number from text."""
        import re

        match = re.search(r"\d+", text)
        return int(match.group()) if match else 0

    def _handle_forecast(self, nl: str) -> Dict:
        gov = self._parse_governorate(nl)
        if not gov:
            return {"action": "forecast", "error": "Please specify a governorate"}
        result = self.sdk.forecast.run(gov)
        return {
            "action": "forecast",
            "governorate": gov,
            "result": {
                "method": result.get("method"),
                "horizon": len(result.get("forecast", [])),
                "predictions": result.get("forecast", [])[:3],
                "metrics": result.get("metrics"),
            },
        }

    def _handle_simulation(self, nl: str) -> Dict:
        gov = self._parse_governorate(nl)
        beds = self._parse_number(nl)
        if not gov:
            return {"action": "simulation", "error": "Please specify a governorate"}
        if "bed" in nl or "accommodation" in nl:
            result = self.sdk.simulation.accommodation(gov, beds or 500)
            return {
                "action": "simulation",
                "type": "accommodation",
                "governorate": gov,
                "added_beds": beds or 500,
                "result": {
                    "classification_change": result.get("difference", {}).get(
                        "classification_changed"
                    ),
                    "before": result.get("difference", {}).get("classification_before"),
                    "after": result.get("difference", {}).get("classification_after"),
                },
            }
        else:
            pct = self._parse_number(nl) or 20
            result = self.sdk.simulation.demand(gov, pct)
            return {
                "action": "simulation",
                "type": "demand",
                "governorate": gov,
                "change_pct": pct,
                "result": result,
            }

    def _handle_occupancy(self, nl: str) -> Dict:
        gov = self._parse_governorate(nl)
        year = self._parse_year(nl)
        if gov:
            df = self.sdk.occupancy.governorate(gov, year)
            return {
                "action": "occupancy",
                "governorate": gov,
                "year": year,
                "avg": float(df["avg_occupancy_rate"].mean()) if not df.empty else None,
            }
        else:
            df = self.sdk.occupancy.national(year)
            return {
                "action": "occupancy",
                "scope": "national",
                "year": year,
                "data": df.to_dict("records")[:6] if not df.empty else [],
            }

    def _handle_visitors(self, nl: str) -> Dict:
        gov = self._parse_governorate(nl)
        year = self._parse_year(nl)
        if gov:
            df = self.sdk.visitors.governorate(gov, year)
            return {
                "action": "visitors",
                "governorate": gov,
                "year": year,
                "total": int(df["total_visitors"].sum()) if not df.empty else 0,
            }
        else:
            df = self.sdk.visitors.national(year)
            return {
                "action": "visitors",
                "scope": "national",
                "year": year,
                "total": int(df["total_visitors"].sum()) if not df.empty else 0,
            }

    def _handle_indicators(self, nl: str) -> Dict:
        gov = self._parse_governorate(nl)
        year = self._parse_year(nl)
        if gov:
            result = self.sdk.indicators.compute(gov, year)
            return {"action": "indicators", "governorate": gov, "result": result}
        else:
            return {"action": "indicators", "error": "Please specify a governorate"}

    def _handle_conflicts(self, nl: str) -> Dict:
        df = self.sdk.conflicts.active()
        return {
            "action": "conflicts",
            "count": len(df),
            "events": df.to_dict("records")[:5] if not df.empty else [],
        }

    def _handle_weather(self, nl: str) -> Dict:
        gov = self._parse_governorate(nl) or "AMM"
        year = self._parse_year(nl)
        df = self.sdk.weather.governorate(gov, year)
        return {
            "action": "weather",
            "governorate": gov,
            "year": year,
            "data": df.to_dict("records")[:6] if not df.empty else [],
        }

    def _handle_hotels(self, nl: str) -> Dict:
        from app.providers.builtin import ProviderRegistry

        gov = self._parse_governorate(nl)
        df = ProviderRegistry.get_data("mota", "hotels", governorate=gov)
        return {
            "action": "hotels",
            "governorate": gov,
            "count": len(df),
            "data": df.to_dict("records")[:10] if not df.empty else [],
        }

    def _handle_sites(self, nl: str) -> Dict:
        from app.providers.builtin import ProviderRegistry

        gov = self._parse_governorate(nl)
        df = ProviderRegistry.get_data("mota", "sites", governorate=gov)
        return {
            "action": "sites",
            "governorate": gov,
            "count": len(df),
            "data": df.to_dict("records")[:10] if not df.empty else [],
        }

    def _handle_providers(self, nl: str) -> Dict:
        return {"action": "providers", "list": self.sdk.providers.list()}
