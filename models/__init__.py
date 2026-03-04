"""
Pydantic schemas for API request / response validation.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Activity Data ─────────────────────────────────────────────────────

class ActivityRecord(BaseModel):
    category: str = Field(..., description="electricity, travel, commuting, cloud, equipment, waste")
    subcategory: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit: str
    date: date


class ActivityBatch(BaseModel):
    records: list[ActivityRecord]


# ── Emissions ─────────────────────────────────────────────────────────

class EmissionRecord(BaseModel):
    id: int
    activity_id: Optional[int] = None
    category: str
    subcategory: Optional[str] = None
    department: Optional[str] = None
    co2e_kg: float
    scope: Optional[int] = None
    date: date


class EmissionSummary(BaseModel):
    total_co2e_kg: float
    total_co2e_tonnes: float
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    by_category: dict[str, float] = {}
    by_department: dict[str, float] = {}
    by_scope: dict[int, float] = {}
    record_count: int = 0


class MonthlyTrend(BaseModel):
    month: str
    co2e_kg: float


# ── Chat ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    data: Optional[dict] = None


# ── Reports ───────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    period: str = Field(..., description="e.g. '2025-01' or '2025-Q1'")


class ReportResponse(BaseModel):
    id: int
    period: str
    generated_at: datetime
    total_co2e_kg: float
    summary: dict
    recommendations: str


# ── Insights ──────────────────────────────────────────────────────────

class Insight(BaseModel):
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    estimated_reduction_pct: Optional[float] = None
    estimated_reduction_kg: Optional[float] = None


class InsightsResponse(BaseModel):
    insights: list[Insight]
    total_potential_reduction_kg: float
    total_potential_reduction_pct: float


# ── Upload ────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    filename: str
    records_imported: int
    emissions_calculated: int
    message: str
