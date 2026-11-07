"""Official data semantics and isolation from the legacy demonstration routes."""
import json
import math
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from shapely.geometry import shape, Point
from app.official import official_data, overview
from app.config import get_settings
from app.main import app
from app.sdk.tourism import TourismSDK

ROOT=Path(__file__).resolve().parents[2]


def test_national_months_and_published_annuals_reconcile():
    data=official_data()
    rows=data['national_monthly']
    assert len(rows)==96
    assert len({(r['year'],r['month']) for r in rows})==96
    assert {r['year'] for r in rows}==set(range(2018,2026))
    assert any(r['total_visitors']==0 for r in rows)
    for r in rows:
        assert r['sheet']!='Sheet1'  # these workbooks contain stale 2004 template sheets
        assert math.isclose(r['overnight_visitors']+r['same_day_visitors'],r['total_visitors'],abs_tol=.01)
    for r in data['national_annual']:
        assert math.isclose(sum(x['total_visitors'] for x in rows if x['year']==r['year']),r['total_visitors'],abs_tol=.02)
    assert round(overview(2025)['national']['total_visitors'])==7041287


def test_sites_missingness_and_source_discrepancies_are_preserved():
    data=official_data()
    assert len(data['site_annual'])==60
    petra=next(r for r in overview(2025)['sites'] if r['site']=='Petra')
    assert petra['total_visits']==582550 and petra['preliminary']
    assert len(data['source_issues'])==2
    assert all(r['year']==2024 for r in data['source_issues'])
    assert any(r['room_occupancy_pct'] is None for r in data['occupancy_regions'])
    assert overview(2025)['accommodation']['hotel_arrivals']==3202595
    assert overview(2025)['accommodation']['guest_nights']==5179961
    assert 'governorates' not in data
    assert all(r['source_id'] and r['sheet'] and r.get('row',r.get('rows')) for key in ['national_monthly','national_annual','site_annual','site_monthly','accommodation_annual','occupancy_regions','hotel_regions'] for r in data[key])


def test_twelve_reviewed_points_match_their_assigned_boundaries():
    geo=json.loads((ROOT/'data/geo/jordan_governorates_gbopen.geojson').read_text())
    iso={'AMM':'JO-AM','ZAR':'JO-AZ','MAF':'JO-MA','BAL':'JO-BA','MAD':'JO-MD','KAR':'JO-KA','TAF':'JO-AT','AQAB':'JO-AQ'}
    polygons={f['properties']['shapeISO']:shape(f['geometry']) for f in geo['features']}
    fixes=json.loads((ROOT/'data/geo/location-corrections.json').read_text())
    assert len(fixes)==12 and sum(r['kind']=='hotel' for r in fixes)==3
    for r in fixes:
        assert polygons[iso[r['governorate_code']]].covers(Point(r['longitude'],r['latitude'])),r['name']
        assert r['source_url'].startswith('https://')


@pytest.fixture
def official(monkeypatch):
    monkeypatch.setattr(get_settings(),'data_mode','official')
    # No lifespan/database is needed for the JSON-backed official endpoints.
    return TestClient(app)


def test_official_api_and_sdk(official):
    response=official.get('/api/official/overview?year=2025')
    assert response.status_code==200
    assert round(response.json()['national']['total_visitors'])==7041287
    assert official.get('/api/official/overview?year=2004').status_code==422
    assert official.post('/api/official/forecast?horizon_months=0').status_code==422
    assert len(official.get('/api/sources').json()['sources'])==23
    sdk=TourismSDK()
    assert len(sdk.visitors.national(2025))==12
    assert 'domestic' not in sdk.visitors.national(2025).columns
    with pytest.raises(ValueError):sdk.visitors.governorate('AMM',2025)


@pytest.mark.parametrize('path',['/api/tourism/visitors','/api/summary/national','/api/research/cross-governorate','/api/actions/incidents','/api/export/executive-summary'])
def test_demo_gets_inaccessible_in_official_mode(official,path):
    assert official.get(path).status_code==410


@pytest.mark.parametrize('path',['/api/analytics/compute-all','/api/etl/upload','/api/actions/incidents/report'])
def test_legacy_writes_inaccessible_in_official_mode(official,path):
    assert official.post(path).status_code==410
