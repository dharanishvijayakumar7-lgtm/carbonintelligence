"""
Reports API Routes

Generate and retrieve sustainability reports.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engine.report_generator import generate_monthly_report, get_latest_report
from models import ReportRequest

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate")
async def generate_report(request: ReportRequest):
    """
    Generate a sustainability report for a given period.

    Period format: '2025-01' (monthly) or '2025-Q1' (quarterly)
    """
    try:
        report = generate_monthly_report(request.period)
        return {
            "status": "success",
            "period": request.period,
            "total_co2e_kg": report["summary"]["total_co2e_kg"],
            "report_file": report.get("report_file"),
            "recommendations": report.get("recommendations", ""),
            "message": f"Report generated for {request.period}",
        }
    except Exception as e:
        raise HTTPException(500, f"Error generating report: {str(e)}")


@router.get("/latest")
async def latest_report():
    """Get the most recently generated report."""
    report = get_latest_report()
    if not report:
        raise HTTPException(404, "No reports have been generated yet.")
    return report
