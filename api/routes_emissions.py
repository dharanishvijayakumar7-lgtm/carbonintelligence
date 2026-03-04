"""
Emissions Query API Routes

Provides endpoints for querying calculated emissions data.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from engine.carbon_estimator import (
    get_total_emissions,
    get_emissions_by_category,
    get_emissions_by_department,
    get_monthly_trends,
)
from engine.insights_engine import generate_insights
from engine.prediction import predict_emissions

router = APIRouter(prefix="/api/emissions", tags=["Emissions"])


@router.get("/summary")
async def emissions_summary(
    start_date: Optional[date] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter end date (YYYY-MM-DD)"),
):
    """Get total emissions summary with breakdowns."""
    return get_total_emissions(start_date, end_date)


@router.get("/by-category")
async def emissions_by_category(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get emissions breakdown by category and subcategory."""
    return get_emissions_by_category(start_date, end_date)


@router.get("/by-department")
async def emissions_by_department(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get emissions breakdown by department."""
    return get_emissions_by_department(start_date, end_date)


@router.get("/monthly")
async def monthly_trends(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Get monthly emission trends."""
    return get_monthly_trends(start_date, end_date)


@router.get("/insights")
async def get_insights():
    """Get AI-generated carbon reduction recommendations."""
    return generate_insights()


@router.get("/forecast")
async def forecast(
    months: int = Query(6, ge=1, le=24, description="Number of months to forecast"),
):
    """Get emission predictions/forecast."""
    return predict_emissions(months_ahead=months)
