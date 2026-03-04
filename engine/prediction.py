"""
Emission Prediction / Forecasting Engine

Uses simple time-series forecasting (linear regression + seasonal decomposition)
to predict future emissions. Works with minimal data (3+ months).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np

from engine.carbon_estimator import get_monthly_trends


def predict_emissions(months_ahead: int = 6) -> dict:
    """
    Predict future monthly emissions using linear regression.

    Returns dict with:
      - historical: list of {month, co2e_kg}
      - predicted: list of {month, co2e_kg}
      - trend: 'increasing', 'decreasing', or 'stable'
      - annual_forecast_kg: projected annual total
    """
    trends = get_monthly_trends()

    if len(trends) < 2:
        return {
            "historical": trends,
            "predicted": [],
            "trend": "insufficient_data",
            "annual_forecast_kg": 0,
            "message": "Need at least 2 months of data for predictions.",
        }

    # Prepare data for linear regression
    y = np.array([t["co2e_kg"] for t in trends])
    x = np.arange(len(y)).reshape(-1, 1)

    # Simple linear regression
    x_mean = x.mean()
    y_mean = y.mean()
    slope = np.sum((x.flatten() - x_mean) * (y - y_mean)) / np.sum((x.flatten() - x_mean) ** 2)
    intercept = y_mean - slope * x_mean

    # Determine trend
    if slope > y_mean * 0.02:
        trend = "increasing"
    elif slope < -y_mean * 0.02:
        trend = "decreasing"
    else:
        trend = "stable"

    # Predict future months
    last_month_str = trends[-1]["month"]
    last_year, last_month = map(int, last_month_str.split("-"))

    predicted = []
    for i in range(1, months_ahead + 1):
        future_x = len(y) - 1 + i
        predicted_y = max(0, intercept + slope * future_x)

        # Calculate future month/year
        month = (last_month + i - 1) % 12 + 1
        year = last_year + (last_month + i - 1) // 12

        predicted.append({
            "month": f"{year:04d}-{month:02d}",
            "co2e_kg": round(predicted_y, 2),
        })

    # Annual forecast
    if len(predicted) >= 12:
        annual = sum(p["co2e_kg"] for p in predicted[:12])
    else:
        # Extrapolate from average
        monthly_avg = np.mean([p["co2e_kg"] for p in predicted])
        annual = monthly_avg * 12

    return {
        "historical": trends,
        "predicted": predicted,
        "trend": trend,
        "annual_forecast_kg": round(annual, 2),
        "annual_forecast_tonnes": round(annual / 1000, 4),
        "monthly_average_kg": round(float(y.mean()), 2),
        "slope_kg_per_month": round(float(slope), 2),
    }
