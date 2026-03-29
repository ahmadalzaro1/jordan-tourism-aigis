# Forecast Methodology

**Project:** Jordan Tourism AI-GIS
**Last Updated:** 2026-03-29

## Overview

The forecasting module predicts future tourism demand (visitor counts) per governorate using time-series statistical methods. Forecasts serve as the baseline for capacity analysis and investment scoring.

## Methods

### Primary: Facebook Prophet

**Why Prophet:**
- Handles yearly seasonality automatically (critical for Jordan's tourism peaks in spring/fall)
- Robust to missing data and outliers
- Produces interpretable confidence intervals
- No manual parameter tuning required
- Accepted by the RFP as an interpretable statistical method

**Configuration:**
- Yearly seasonality: enabled (captures Jordan's Mar-May and Sep-Nov peaks)
- Weekly seasonality: disabled (data is monthly)
- Daily seasonality: disabled (data is monthly)
- Changepoint prior scale: 0.05 (conservative trend changes)

**Output:**
- Point forecast for each future month
- 80% confidence interval (yhat_lower, yhat_upper)

### Fallback: ARIMA(1,1,1)

Used when Prophet fails or is unavailable.

**Why ARIMA:**
- Classical, well-understood statistical method
- Lightweight (no external dependencies beyond statsmodels)
- Suitable for moderately complex time series

**Configuration:**
- Order: (1,1,1) — first-order autoregression, first-order differencing, first-order moving average
- Confidence level: 80%

## Forecasting Pipeline

```
Historical Data (monthly visitors per governorate)
    ↓
Prepare Time Series (datetime index + value column)
    ↓
Prophet Model Fit (yearly seasonality)
    ↓
Generate Forecast (12 months ahead)
    ↓
Back-Test Evaluation (last 12 months as test set)
    ↓
Output: forecast[] + metrics (MAPE, MAE, RMSE)
```

## Back-Testing

**Method:** Hold-out validation
- Reserve last N months of historical data as test set
- Train model on remaining data
- Predict test period
- Compare predicted vs actual

**Metrics:**
- **MAPE** (Mean Absolute Percentage Error): Target ≤ 20% at national level
- **MAE** (Mean Absolute Error): Average absolute difference
- **RMSE** (Root Mean Squared Error): Penalizes large errors more

**KPI (per RFP):**
> National-level forecast MAPE for total tourism (12-month back-test): ≤ 20%

## Assumptions

1. **No external regressors**: PoC uses univariate time series only (per RFP)
2. **No deep learning**: No LSTM, Transformer, or neural network models (per RFP)
3. **Monthly granularity**: All data aligned to monthly time steps
4. **Historical data required**: Minimum 12 months, ideally 3+ years
5. **Stationarity**: ARIMA assumes non-stationarity handled by differencing

## Limitations

1. Cannot predict external shocks (war, pandemic, policy changes)
2. Confidence intervals widen significantly beyond 12 months
3. Accuracy depends on data quality and consistency
4. Seasonal patterns may shift over time (e.g., post-COVID tourism recovery)

## Reproducibility

Same input data + same parameters = same forecast output (100% reproducible).
Prophet uses deterministic optimization (no random seed issues).
