#!/usr/bin/env python3
"""
Seed Database Script

Loads emission factors and sample datasets into the database.
Run this once to initialize the system with example data.

Usage:
    python scripts/seed_data.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import reset_database, get_connection
from models.emission_factors import seed_emission_factors
from ingestion.csv_loader import load_csv, insert_activities
from engine.carbon_estimator import process_all_unprocessed
from config import SAMPLE_DIR


def main():
    print("🌍 Carbon Intelligence System — Database Seeder")
    print("=" * 55)

    # Reset database
    print("\n📦 Resetting database...")
    reset_database()
    print("   ✅ Database reset complete")

    # Seed emission factors
    print("\n📊 Loading emission factors...")
    count = seed_emission_factors()
    print(f"   ✅ Loaded {count} emission factors (EPA, DEFRA, IPCC, IEA)")

    # Load sample datasets
    sample_files = [
        ("electricity_bills.csv", "Electricity bills"),
        ("travel_expenses.csv", "Travel expenses"),
        ("employee_commute.csv", "Employee commuting"),
        ("cloud_usage.csv", "Cloud usage"),
        ("office_purchases.csv", "Office equipment"),
        ("waste_records.csv", "Waste records"),
    ]

    total_records = 0
    for filename, label in sample_files:
        filepath = SAMPLE_DIR / filename
        if filepath.exists():
            print(f"\n📄 Loading {label}...")
            records = load_csv(filepath)
            count = insert_activities(records)
            total_records += count
            print(f"   ✅ Imported {count} records from {filename}")
        else:
            print(f"   ⚠️  {filename} not found, skipping")

    # Calculate emissions
    print(f"\n🔬 Calculating emissions for {total_records} activity records...")
    emissions_count = process_all_unprocessed()
    print(f"   ✅ Calculated {emissions_count} emission entries")

    # Summary
    conn = get_connection()
    summary = conn.execute("""
        SELECT
            COUNT(*) as records,
            ROUND(SUM(co2e_kg), 2) as total_kg,
            ROUND(SUM(co2e_kg) / 1000, 2) as total_tonnes
        FROM emissions
    """).fetchone()

    by_cat = conn.execute("""
        SELECT category, ROUND(SUM(co2e_kg), 2)
        FROM emissions
        GROUP BY category
        ORDER BY SUM(co2e_kg) DESC
    """).fetchall()

    print("\n" + "=" * 55)
    print("📊 SUMMARY")
    print("=" * 55)
    print(f"   Total Records:    {summary[0]}")
    print(f"   Total Emissions:  {summary[1]:,.2f} kg CO₂e ({summary[2]:,.2f} tonnes)")
    print(f"\n   By Category:")
    for cat, val in by_cat:
        pct = (val / summary[1] * 100) if summary[1] > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"     {cat:<15} {val:>10,.2f} kg  ({pct:>5.1f}%) {bar}")

    print(f"\n✅ Database seeded successfully!")
    print(f"\n🚀 Next steps:")
    print(f"   1. Start API:        uvicorn main:app --reload --port 8000")
    print(f"   2. Start Dashboard:  streamlit run dashboard/app.py")
    print(f"   3. Open API docs:    http://localhost:8000/docs")
    print(f"   4. Open Dashboard:   http://localhost:8501")


if __name__ == "__main__":
    main()
