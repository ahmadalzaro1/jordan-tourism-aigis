"""Integration checks must target an explicitly opted-in disposable PostGIS DB."""
import os
import csv
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

URL = os.environ.get('GIS_VALIDATION_DATABASE_URL', '')
pytestmark = pytest.mark.skipif(not URL, reason='Set GIS_VALIDATION_DATABASE_URL to the disposable validation database')
if URL:
    if '127.0.0.1:5546/tourism_validation' not in URL:
        raise RuntimeError('Integration tests require the isolated GIS validation database')
    os.environ['DATABASE_URL'] = URL

from app.main import app
from app.db.database import engine

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c:
        yield c

GETS = ['/', '/health', '/api/sources', '/api/geo/governorates', '/api/geo/hotels', '/api/geo/sites',
 '/api/tourism/visitors?year=2025', '/api/tourism/occupancy?year=2025', '/api/tourism/site-visits', '/api/tourism/rooms-beds',
 '/api/summary/national?year=2025', '/api/summary/governorate/1?year=2025', '/api/etl/logs',
 '/api/analytics/investment-ranker', '/api/analytics/clusters', '/api/analytics/accommodation-classes',
 '/api/research/comprehensive/1?year=2025', '/api/research/cross-governorate', '/api/actions/ontology',
 '/api/actions/incidents', '/api/actions/investments', '/api/actions/conflicts']

@pytest.mark.parametrize('path',GETS)
def test_get_route(client,path):
    r=client.get(path)
    assert r.status_code==200, r.text
    assert 'error' not in r.json()


def test_geo_has_valid_all_twelve_polygons(client):
    features=client.get('/api/geo/governorates').json()['features']
    assert len(features)==12
    assert all(f['geometry']['type']=='MultiPolygon' for f in features)
    with engine.connect() as c:
        assert c.execute(text('SELECT COUNT(*) FROM governorates WHERE ST_IsValid(geometry) AND NOT ST_IsEmpty(geometry)')).scalar()==12


def test_totals_match_raw_csv_and_sql_views(client):
    root=Path(__file__).resolve().parents[2]
    rows=list(csv.DictReader((root/'data/sample/visitors.csv').open()))
    expected=sum(int(r['total_visitors']) for r in rows if r['year']=='2025')
    summary=client.get('/api/summary/national?year=2025').json()
    assert summary['total_visitors']==expected
    with engine.connect() as c:
        assert c.execute(text('SELECT total_visitors FROM v_national_summary WHERE year=2025')).scalar()==expected
        assert c.execute(text('SELECT SUM(total_visitors) FROM v_governorate_comparison')).scalar()==expected


def test_nonexistent_filter_returns_zero_not_all_data(client):
    summary=client.get('/api/summary/national?year=2025&destination_type=nonexistent').json()
    assert summary['total_visitors']==0 and summary['total_hotels']==0


def test_research_year_is_honored(client):
    x=client.get('/api/research/comprehensive/1?year=2025').json()
    assert x['data_points']==12
    y=client.get('/api/research/comprehensive/1?year=2019').json()
    assert y['data_points']==0


@pytest.mark.parametrize('gov',range(1,13))
def test_indicators_use_stock_not_sum_of_monthly_stock(client,gov):
    result=client.post(f'/api/analytics/indicators/{gov}?year=2025')
    assert result.status_code==200,result.text
    with engine.connect() as c:
        rooms=c.execute(text('SELECT AVG(total_rooms) FROM occupancy_data WHERE governorate_id=:g AND year=2025'),{'g':gov}).scalar()
    assert result.json()['inputs']['total_rooms']==float(rooms)


@pytest.mark.parametrize('horizon',[6,12,24])
def test_forecast_horizon_and_evaluation(client,horizon):
    r=client.post(f'/api/analytics/forecast/1?horizon_months={horizon}')
    assert r.status_code==200,r.text
    x=r.json(); assert len(x['forecast'])==horizon
    assert x['forecast'][0]['date']=='2026-01-01'
    assert x['metrics']['evaluation']=='temporal_holdout'
    assert x['metrics']['train_end'] < x['metrics']['test_start']
    assert all(0<=f['lower_bound']<=f['upper_bound'] for f in x['forecast'])


@pytest.mark.parametrize('scenario,params',[('accommodation','added_beds=500'),('demand','visitor_change_pct=20'),('demand','visitor_change_pct=-20')])
def test_scenarios_run(client,scenario,params):
    r=client.post(f'/api/analytics/simulate?governorate_id=1&scenario_type={scenario}&{params}')
    assert r.status_code==200,r.text
    assert all(k in r.json() for k in ['baseline','scenario','difference'])


def test_bulk_and_national_scenarios(client):
    x=client.post('/api/analytics/compute-all?year=2025').json()
    assert len(x['results'])==12 and not any('error' in r for r in x['results'])
    r=client.post('/api/analytics/simulate-national?scenario_type=accommodation&added_beds=500')
    assert r.status_code==200,r.text
    assert r.json()['simulation_time_reference']['forecast_applied'] is False


@pytest.mark.parametrize('query',['horizon_months=0','horizon_months=37'])
def test_bad_forecast_horizon(client,query):
    assert client.post('/api/analytics/forecast/1?'+query).status_code==422


def upload(client,content):
    return client.post('/api/etl/upload',data={'dataset_type':'visitors'}, files={'file':('visitors.csv',content,'text/csv')})


def test_upload_idempotency_and_validation(client):
    content='governorate_code,year,month,total_visitors,international_visitors,domestic_visitors\nAMM,2025,1,3,1,2\n'
    r=upload(client,content);assert r.status_code==200,r.text
    assert r.json()['skipped']==1 and r.json()['inserted']==0
    for bad in [content.replace('2025,1,3','2025,13,3'),content.replace(',3,1,2',',-3,1,2'),content.replace('AMM,','FAKE,'),content.replace(',3,1,2',',5,1,2')]:
        r=upload(client,bad);assert r.status_code==400,r.text
    assert client.get('/api/summary/national?year=2025').status_code==200


def test_export_pdf(client):
    r=client.get('/api/export/executive-summary?year=2025')
    assert r.status_code==200,r.text
    assert r.content.startswith(b'%PDF-') and len(r.content)>1000
    (Path(__file__).resolve().parents[2]/'output/validation/executive-summary.pdf').write_bytes(r.content)


def test_action_workflows(client):
    x=client.post('/api/actions/incidents/report',params={'title':'Validation only','governorate_id':1});assert x.status_code==200,x.text
    iid=x.json()['incident_id']
    assert client.post(f'/api/actions/incidents/{iid}/assign?assigned_to=validation').status_code==200
    assert client.post(f'/api/actions/incidents/{iid}/resolve?resolution=Test%20complete').status_code==200
    x=client.post('/api/actions/investments/propose',params={'governorate_id':1,'investment_type':'eco_lodge','estimated_cost':1000});assert x.status_code==200,x.text
    iid=x.json()['investment_id']
    assert client.post(f'/api/actions/investments/{iid}/approve?approved_budget=1000').status_code==200
    x=client.post('/api/actions/investments/propose',params={'governorate_id':1,'investment_type':'eco_lodge','estimated_cost':1000})
    assert client.post(f"/api/actions/investments/{x.json()['investment_id']}/reject?reason=test").status_code==200
    assert client.post('/api/actions/conflicts/trigger?conflict_name=Validation%20only').status_code==200


def test_sdk_and_query_router():
    from app.sdk.tourism import TourismSDK
    from app.mcp.server import TourismMCPServer
    sdk=TourismSDK()
    assert len(sdk.visitors.governorate('AQAB',year=2025))==12
    assert len(sdk.weather.governorate('AMM',year=2025))==12
    assert len(sdk.providers.list())==7
    result=TourismMCPServer().query('Show visitors for Amman in 2025')
    assert 'error' not in result


def test_simulation_uses_monthly_bed_nights_and_annualized_ratios(client):
    result=client.post('/api/analytics/simulate?governorate_id=1&scenario_type=accommodation&added_beds=500').json()
    b=result['baseline'];days=result['simulation_time_reference']['period_days']
    expected=round(b['total_beds']*days*0.75/(b['total_visitors']*2.5),3)
    assert b['indicators']['capacity_adequacy_index']==expected
    assert result['scenario']['indicators']['capacity_adequacy_index'] > expected
    assert result['scenario']['avg_occupancy'] < b['avg_occupancy']
