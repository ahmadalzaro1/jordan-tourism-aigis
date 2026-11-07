from pathlib import Path
import json
import pandas as pd
import pytest
from app.etl import weather_import


def test_weather_uses_daily_and_preserves_missing_values(monkeypatch):
    payload={'daily':{'time':['2025-01-01','2025-01-02'],'temperature_2m_mean':[10,20], 'temperature_2m_max':[12,22], 'temperature_2m_min':[8,18], 'precipitation_sum':[None,None], 'sunshine_duration':[3600,7200]}}
    seen={}
    class Response:
        def raise_for_status(self): pass
        def json(self): return payload
    def get(url,params,timeout):
        seen.update(params);return Response()
    monkeypatch.setattr(weather_import.requests,'get',get)
    frame=weather_import.fetch_weather('AMM','2025-01-01','2025-01-02')
    assert 'daily' in seen and 'monthly' not in seen
    assert frame.iloc[0].temp_mean==15
    assert frame.iloc[0].temp_max==22
    assert frame.iloc[0].sunshine_hours==3
    assert pd.isna(frame.iloc[0].precipitation_mm)


def test_providers_read_shared_data_and_filter():
    from app.providers.builtin import MoTAProvider,OpenMeteoProvider,WorldBankProvider
    assert len(MoTAProvider().get_visitors(governorate='AMM',year=2025))==12
    assert len(OpenMeteoProvider().get_weather(governorate='AMM',year=2025))==12
    assert not WorldBankProvider().get_economic(year=2023).empty
