#!/usr/bin/env python3
"""
CLI Report Generator

Generate sustainability reports from the command line.

Usage:
    python scripts/generate_report.py 2025-01
    python scripts/generate_report.py 2025-Q1
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.report_generator import generate_monthly_report


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_report.py <period>")
        print("  Period: '2025-01' (monthly) or '2025-Q1' (quarterly)")
        sys.exit(1)

    period = sys.argv[1]
    print(f"📊 Generating report for {period}...")

    report = generate_monthly_report(period)

    print(f"✅ Report generated!")
    print(f"   Total Emissions: {report['summary']['total_co2e_kg']:,.2f} kg CO₂e")
    print(f"   Report file: {report.get('report_file', 'N/A')}")
    print(f"\nRecommendations:")
    print(report.get("recommendations", "No recommendations."))


if __name__ == "__main__":
    main()
