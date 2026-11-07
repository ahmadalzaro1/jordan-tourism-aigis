from fastapi import APIRouter,Query,HTTPException
from app.official import official_data,overview
from app.analytics.forecasting import prepare_monthly_series,forecast_best,_mape
from functools import lru_cache
router=APIRouter()

@router.get('/overview')
def get_overview(year:int=Query(2025,ge=2018,le=2025)):
    return overview(year)

@router.get('/sources')
def get_sources():
    data=official_data()
    return {'sources':data['sources'],'definitions':data['definitions'],'source_issues':data['source_issues']}

@router.post('/forecast')
@lru_cache(maxsize=6)
def national_forecast(horizon_months:int=Query(12,ge=1,le=24)):
    data=official_data()['national_monthly']
    df=prepare_monthly_series([{'year':r['year'],'month':r['month'],'total':r['total_visitors']} for r in data])
    result=forecast_best(df,horizon_months)
    result['benchmark']={'method':'seasonal_naive','definition':'Repeat the same month of the previous year','mape':round(_mape(df.y.iloc[-12:].to_numpy(),df.y.iloc[-24:-12].to_numpy()),2),'test_start':'2025-01-01','test_end':'2025-12-01'}
    return {**result,'geography':'Jordan — national inbound visitor trips','data_mode':'official','source_ids':sorted({r['source_id'] for r in data}),'scope':'National arrivals only; no governorate forecasts are inferred. Historical holdout performance is not a guarantee.'}
