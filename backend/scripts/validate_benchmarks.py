"""Compare models on fixed temporal folds of bundled DEMO observations."""
import sys, json, hashlib, platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import numpy as np
from app.analytics.forecasting import forecast_prophet,forecast_arima,prepare_monthly_series
from importlib.metadata import version
root=Path(__file__).resolve().parents[2]
source=root/'data/sample/visitors.csv'
data=pd.read_csv(source).groupby(['year','month'],as_index=False).total_visitors.sum()
records=[]
for year in [2023,2024,2025]:
    train=data[data.year<year]
    test=data[data.year==year].sort_values('month')
    df=prepare_monthly_series([{'year':r.year,'month':r.month,'total':r.total_visitors} for r in train.itertuples()])
    actual=test.total_visitors.to_numpy()
    models={
      'seasonal_naive':data[data.year==year-1].sort_values('month').total_visitors.to_numpy(),
      'prophet_cps_0.05':[r['predicted'] for r in forecast_prophet(df,12,_evaluate=False)['forecast']],
      'prophet_cps_0.01':[r['predicted'] for r in forecast_prophet(df,12,_evaluate=False,changepoint_prior_scale=0.01)['forecast']],
      'arima_1_1_1':[r['predicted'] for r in forecast_arima(df,12,_evaluate=False)['forecast']],
    }
    for name,predicted in models.items():
      records.append({'test_year':year,'train_months':len(train),'model':name,'mape':round(float(np.mean(np.abs((actual-np.asarray(predicted))/actual))*100),2),'mae':round(float(np.mean(np.abs(actual-predicted))),2),'predicted':list(map(int,predicted)),'actual':list(map(int,actual))})
report={'data_kind':'generated_demo','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'python':platform.python_version(),'versions':{n:version(n) for n in ['prophet','cmdstanpy','pandas','numpy','statsmodels']},'folds':records,'warning':'Comparisons on demo data do not validate performance on real tourism. Choosing a model using these folds requires a fresh unseen real-data evaluation.'}
p=root/'output/validation/model-comparison.json';p.write_text(json.dumps(report,indent=2))
for row in records:print(row['test_year'],row['model'],row['mape'])
