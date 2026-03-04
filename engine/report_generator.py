"""
Automated Sustainability Report Generator

Generates comprehensive monthly/quarterly sustainability reports
in both structured JSON and readable Markdown formats.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from config import REPORTS_DIR, DEFAULT_ORG
from database import get_connection
from engine.carbon_estimator import (
    get_total_emissions,
    get_emissions_by_category,
    get_emissions_by_department,
    get_monthly_trends,
)
from engine.insights_engine import generate_insights
from engine.prediction import predict_emissions


def generate_monthly_report(period: str) -> dict:
    """
    Generate a sustainability report for a given period.

    Args:
        period: String like '2025-01' (month) or '2025-Q1' (quarter)

    Returns:
        Report dict with all sections.
    """
    start_date, end_date = _parse_period(period)

    # Gather all data
    summary = get_total_emissions(start_date, end_date)
    by_category = get_emissions_by_category(start_date, end_date)
    by_department = get_emissions_by_department(start_date, end_date)
    monthly = get_monthly_trends()
    insights_data = generate_insights()
    prediction = predict_emissions(months_ahead=6)

    # Build report
    report = {
        "organization": DEFAULT_ORG,
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "by_category": by_category,
        "by_department": by_department,
        "monthly_trends": monthly,
        "insights": insights_data,
        "predictions": prediction,
    }

    # Generate readable recommendations
    recommendations = _format_recommendations(insights_data)

    # Store in database
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO reports (id, period, total_co2e_kg, summary_json, recommendations)
        VALUES (nextval('seq_reports'), ?, ?, ?, ?)
        """,
        [period, summary["total_co2e_kg"], json.dumps(report), recommendations],
    )

    # Also write markdown report to file
    md_content = _generate_markdown_report(report, recommendations)
    report_path = REPORTS_DIR / f"report_{period.replace('-', '_')}.md"
    report_path.write_text(md_content)

    report["report_file"] = str(report_path)
    report["recommendations"] = recommendations

    return report


def get_latest_report() -> Optional[dict]:
    """Get the most recently generated report."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, period, generated_at, total_co2e_kg, summary_json, recommendations "
        "FROM reports ORDER BY generated_at DESC LIMIT 1"
    ).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "period": row[1],
        "generated_at": str(row[2]),
        "total_co2e_kg": row[3],
        "summary": json.loads(row[4]) if row[4] else {},
        "recommendations": row[5] or "",
    }


def _parse_period(period: str) -> tuple[date, date]:
    """Parse period string into start and end dates."""
    if "Q" in period.upper():
        # Quarterly: '2025-Q1'
        parts = period.upper().split("-Q")
        year = int(parts[0])
        quarter = int(parts[1])
        month_start = (quarter - 1) * 3 + 1
        month_end = month_start + 2
        start = date(year, month_start, 1)
        if month_end == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month_end + 1, 1) - __import__("datetime").timedelta(days=1)
    else:
        # Monthly: '2025-01'
        parts = period.split("-")
        year = int(parts[0])
        month = int(parts[1])
        start = date(year, month, 1)
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - __import__("datetime").timedelta(days=1)

    return start, end


def _format_recommendations(insights_data: dict) -> str:
    """Format insights into readable recommendations text."""
    insights = insights_data.get("insights", [])
    if not insights:
        return "No specific recommendations at this time. Continue monitoring your emissions."

    lines = ["## Carbon Reduction Recommendations\n"]
    for i, insight in enumerate(insights, 1):
        lines.append(f"### {i}. {insight['title']} [{insight['priority'].upper()} PRIORITY]")
        lines.append(f"**Category:** {insight['category'].title()}")
        lines.append(f"**Potential Reduction:** {insight['estimated_reduction_kg']:.0f} kg CO₂e "
                      f"({insight['estimated_reduction_pct']:.0f}% of category)")
        lines.append(f"\n{insight['description']}\n")

    total_red = insights_data.get("total_potential_reduction_kg", 0)
    total_pct = insights_data.get("total_potential_reduction_pct", 0)
    lines.append(f"\n---\n**Total Potential Reduction: {total_red:,.0f} kg CO₂e ({total_pct:.1f}%)**")

    return "\n".join(lines)


def _generate_markdown_report(report: dict, recommendations: str) -> str:
    """Generate a full markdown sustainability report."""
    summary = report["summary"]
    org = report["organization"]
    period = report["period"]
    generated = report["generated_at"]

    lines = [
        f"# 🌍 Sustainability Report — {org}",
        f"**Period:** {period}",
        f"**Generated:** {generated[:10]}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Emissions | **{summary['total_co2e_kg']:,.1f} kg CO₂e** ({summary['total_co2e_tonnes']:,.2f} tonnes) |",
        f"| Records Processed | {summary['record_count']} |",
        "",
    ]

    # Scope breakdown
    if summary.get("by_scope"):
        lines.extend([
            "## Emissions by Scope",
            "",
            "| Scope | Emissions (kg CO₂e) | % of Total |",
            "|-------|--------------------:|----------:|",
        ])
        total = summary["total_co2e_kg"]
        for scope, val in sorted(summary["by_scope"].items()):
            pct = (val / total * 100) if total > 0 else 0
            scope_desc = {1: "Direct", 2: "Electricity", 3: "Value Chain"}.get(scope, "Other")
            lines.append(f"| Scope {scope} ({scope_desc}) | {val:,.1f} | {pct:.1f}% |")
        lines.append("")

    # Category breakdown
    if report.get("by_category"):
        lines.extend([
            "## Emissions by Category",
            "",
            "| Category | Subcategory | Emissions (kg CO₂e) | Records |",
            "|----------|-------------|--------------------:|--------:|",
        ])
        for cat in report["by_category"]:
            lines.append(
                f"| {cat['category'].title()} | {cat['subcategory']} | {cat['co2e_kg']:,.1f} | {cat['records']} |"
            )
        lines.append("")

    # Department breakdown
    if report.get("by_department"):
        lines.extend([
            "## Emissions by Department",
            "",
            "| Department | Emissions (kg CO₂e) | Records |",
            "|------------|--------------------:|--------:|",
        ])
        for dept in report["by_department"]:
            lines.append(f"| {dept['department']} | {dept['co2e_kg']:,.1f} | {dept['records']} |")
        lines.append("")

    # Predictions
    pred = report.get("predictions", {})
    if pred.get("trend"):
        lines.extend([
            "## Forecast",
            "",
            f"- **Trend:** {pred.get('trend', 'N/A').title()}",
            f"- **Monthly Average:** {pred.get('monthly_average_kg', 0):,.1f} kg CO₂e",
            f"- **Annual Forecast:** {pred.get('annual_forecast_kg', 0):,.1f} kg CO₂e "
            f"({pred.get('annual_forecast_tonnes', 0):,.2f} tonnes)",
            "",
        ])

    # Recommendations
    lines.extend(["", recommendations, ""])

    # Footer
    lines.extend([
        "",
        "---",
        f"*Report generated by Carbon Intelligence System on {generated[:10]}*",
        "*Emission factors sourced from EPA, DEFRA, IPCC, and IEA*",
    ])

    return "\n".join(lines)
