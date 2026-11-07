"""
Demand Forecasting Module for Jordan Tourism AI-GIS.

Per RFP ToR Section 3.2.3:
- Univariate demand forecasting per governorate
- Default 12-month horizon (adjustable: 6/12/24)
- Interpretable statistical methods (Prophet or ARIMA)
- Back-testing for accuracy evaluation
- No external regressors or deep learning for PoC

Methods:
  1. Prophet (primary) — handles seasonality, holidays, trend changes
  2. ARIMA (fallback) — classical time-series, more lightweight
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional
from statsmodels.tsa.arima.model import ARIMA as StatsARIMA
from statsmodels.tsa.seasonal import seasonal_decompose


def prepare_monthly_series(data: list) -> pd.DataFrame:
    """
    Convert list of {year, month, total} dicts to a monthly time series DataFrame.

    Args:
        data: List of dicts with 'year', 'month', 'total' keys

    Returns:
        DataFrame with datetime index and 'y' column
    """
    if not data:
        raise ValueError("Monthly series cannot be empty")
    df = pd.DataFrame(data)
    df["ds"] = pd.to_datetime(
        df.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}-01", axis=1)
    )
    df["y"] = df["total"].astype(float)
    df = df.sort_values("ds").reset_index(drop=True)
    return _validate_series(df[["ds", "y"]])


def _validate_series(df):
    df = df[["ds", "y"]].copy().sort_values("ds").reset_index(drop=True)
    df["ds"] = pd.to_datetime(df["ds"])
    if len(df) < 2 or df["ds"].duplicated().any():
        raise ValueError("At least two distinct monthly observations are required")
    if not np.isfinite(df["y"].astype(float)).all() or (df["y"] < 0).any():
        raise ValueError("Visitor values must be finite and nonnegative")
    if not df["ds"].equals(pd.Series(pd.date_range(df.ds.iloc[0], periods=len(df), freq="MS"))):
        raise ValueError("Monthly observations must be contiguous month starts")
    return df


def _holdout_metrics(df, forecast_func, **kwargs):
    """Fit only on earlier observations; evaluate against unseen final months."""
    n = min(12, len(df) // 3)
    if n < 1 or len(df) - n < 6:
        return {"mape": None, "mae": None, "rmse": None, "backtest_months": 0,
                "evaluation": "insufficient_history"}
    train, test = df.iloc[:-n], df.iloc[-n:]
    result = forecast_func(train, n, _evaluate=False, **kwargs)
    expected_dates = test.ds.dt.strftime("%Y-%m-%d").tolist()
    if [f["date"] for f in result["forecast"]] != expected_dates:
        raise ValueError("Holdout forecast dates do not match observations")
    actual = test.y.to_numpy()
    predicted = [f["predicted"] for f in result["forecast"]]
    return {"mape": round(_mape(actual, predicted), 2) if np.any(actual != 0) else None,
            "mae": round(_mae(actual, predicted), 2),
            "rmse": round(_rmse(actual, predicted), 2),
            "backtest_months": n, "evaluation": "temporal_holdout",
            "train_end": train.ds.iloc[-1].strftime("%Y-%m-%d"),
            "test_start": expected_dates[0], "test_end": expected_dates[-1]}


def forecast_prophet(df: pd.DataFrame, horizon_months: int = 12, _evaluate: bool = True, **kwargs) -> dict:
    """
    Forecast using Facebook Prophet.

    Args:
        df: DataFrame with 'ds' (datetime) and 'y' (value) columns
        horizon_months: Number of months to forecast

    Returns:
        dict with 'forecast', 'history', 'metrics'
    """
    df = _validate_series(df)
    if not 1 <= horizon_months <= 36:
        raise ValueError("Forecast horizon must be between 1 and 36 months")
    try:
        from prophet import Prophet
    except ImportError:
        # Fallback to ARIMA if Prophet not installed
        return forecast_arima(df, horizon_months, _evaluate=_evaluate)

    options = dict(yearly_seasonality=True, weekly_seasonality=False,
                   daily_seasonality=False, changepoint_prior_scale=0.05)
    options.update(kwargs)
    model = Prophet(**options)

    model.fit(df)

    # Future dataframe
    future = model.make_future_dataframe(periods=horizon_months, freq="MS")
    prediction = model.predict(future)

    # Split into history and forecast
    history_end = len(df)
    forecast_df = prediction.iloc[history_end:]

    forecast = []
    for _, row in forecast_df.iterrows():
        forecast.append(
            {
                "date": row["ds"].strftime("%Y-%m-%d"),
                "year": row["ds"].year,
                "month": row["ds"].month,
                "predicted": max(0, round(row["yhat"])),
                "lower_bound": max(0, round(row["yhat_lower"])),
                "upper_bound": max(0, round(row["yhat_upper"])),
            }
        )

    # Compute back-test metrics (last 12 months if available)
    metrics = _holdout_metrics(df, forecast_prophet, **kwargs) if _evaluate else {}

    return {
        "method": "prophet",
        "horizon_months": horizon_months,
        "forecast": forecast,
        "metrics": metrics,
        "history": [
            {"date": row["ds"].strftime("%Y-%m-%d"), "actual": round(row["y"])}
            for _, row in df.iterrows()
        ],
    }


def forecast_arima(df: pd.DataFrame, horizon_months: int = 12, order=(1, 1, 1), _evaluate: bool = True) -> dict:
    """
    Forecast using ARIMA.

    Args:
        df: DataFrame with 'ds' (datetime) and 'y' (value) columns
        horizon_months: Number of months to forecast
        order: ARIMA (p, d, q) order

    Returns:
        dict with 'forecast', 'history', 'metrics'
    """
    df = _validate_series(df)
    if not 1 <= horizon_months <= 36:
        raise ValueError("Forecast horizon must be between 1 and 36 months")
    ts = df.set_index("ds")["y"]

    # Fit ARIMA
    model = StatsARIMA(ts, order=order)
    fitted = model.fit()

    # Forecast
    forecast_result = fitted.get_forecast(steps=horizon_months)
    predicted = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int(alpha=0.2)

    forecast = []
    for i in range(horizon_months):
        date = ts.index[-1] + pd.DateOffset(months=i + 1)
        forecast.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "year": date.year,
                "month": date.month,
                "predicted": max(0, round(predicted.iloc[i])),
                "lower_bound": max(0, round(conf_int.iloc[i, 0])),
                "upper_bound": max(0, round(conf_int.iloc[i, 1])),
            }
        )

    metrics = _holdout_metrics(df, forecast_arima, order=order) if _evaluate else {}

    return {
        "method": "arima",
        "order": list(order),
        "horizon_months": horizon_months,
        "forecast": forecast,
        "metrics": metrics,
        "history": [
            {"date": d.strftime("%Y-%m-%d"), "actual": round(v)} for d, v in ts.items()
        ],
    }


def forecast_best(df: pd.DataFrame, horizon_months: int = 12) -> dict:
    """
    Try Prophet first, fall back to ARIMA.
    """
    try:
        result = forecast_prophet(df, horizon_months)
        if result.get("forecast"):
            return result
    except Exception as exc:
        logging.getLogger(__name__).warning("Prophet failed; falling back to ARIMA: %s", exc)
        result = forecast_arima(df, horizon_months)
        result["fallback_from"] = "prophet"
        result["warning"] = "Prophet unavailable; ARIMA forecast and evaluation returned"
        return result

    return forecast_arima(df, horizon_months)


def _mape(actual, predicted):
    """Mean Absolute Percentage Error."""
    actual, predicted = np.array(actual, dtype=float), np.array(predicted, dtype=float)
    mask = actual != 0
    if mask.sum() == 0:
        return None
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100


def _mae(actual, predicted):
    """Mean Absolute Error."""
    return np.mean(
        np.abs(np.array(actual, dtype=float) - np.array(predicted, dtype=float))
    )


def _rmse(actual, predicted):
    """Root Mean Squared Error."""
    return np.sqrt(
        np.mean((np.array(actual, dtype=float) - np.array(predicted, dtype=float)) ** 2)
    )
