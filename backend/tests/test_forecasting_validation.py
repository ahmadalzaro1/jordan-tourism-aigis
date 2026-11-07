import pandas as pd
import numpy as np
import pytest
from app.analytics import forecasting as f


def series(n=36):
    return pd.DataFrame({'ds': pd.date_range('2020-01-01', periods=n, freq='MS'), 'y': np.arange(n)+100.})


def test_holdout_never_trains_on_evaluation_rows():
    original = series()
    seen = []
    def model(train, horizon, **kwargs):
        seen.append(train.copy())
        return {'forecast': [{'date': d.strftime('%Y-%m-%d'), 'predicted': 130} for d in pd.date_range(train.ds.iloc[-1]+pd.offsets.MonthBegin(),periods=horizon,freq='MS')]}
    metrics = f._holdout_metrics(original, model)
    assert len(seen[0]) == 24
    assert seen[0].ds.max() < pd.Timestamp(metrics['test_start'])
    assert metrics['evaluation'] == 'temporal_holdout'


@pytest.mark.parametrize('bad', ['gap','duplicate','negative','nan'])
def test_invalid_monthly_data_rejected(bad):
    df=series()
    if bad=='gap': df=df.drop(4)
    if bad=='duplicate': df.loc[4,'ds']=df.loc[3,'ds']
    if bad=='negative': df.loc[4,'y']=-1
    if bad=='nan': df.loc[4,'y']=np.nan
    with pytest.raises(ValueError): f._validate_series(df)


def test_all_zero_mape_is_undefined():
    assert f._mape([0,0],[5,5]) is None


def test_prophet_options_are_used_and_forecasts_are_bounded():
    a=f.forecast_prophet(series(), 6, changepoint_prior_scale=0.01)
    assert a['metrics']['evaluation']=='temporal_holdout'
    assert len(a['forecast'])==6
    assert all(0 <= x['lower_bound'] <= x['upper_bound'] for x in a['forecast'])
