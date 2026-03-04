"""
Carbon Estimation Engine

Core module that converts raw activity data into CO₂e emission estimates
using emission factors from EPA, DEFRA, IPCC, and IEA.

Estimation Formulas:
  - Electricity:  kWh × grid_factor(country) = kg CO₂e
  - Travel:       km × mode_factor = kg CO₂e
  - Commuting:    km × working_days × mode_factor = kg CO₂e
  - Cloud:        USD_spend × provider_factor = kg CO₂e
  - Equipment:    items × lifecycle_factor = kg CO₂e
  - Waste:        kg × waste_type_factor = kg CO₂e
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from database import get_connection
from models.emission_factors import lookup_factor, get_scope


def estimate_single(
    category: str,
    quantity: float,
    unit: str,
    subcategory: Optional[str] = None,
    country: str = "GLOBAL",
) -> float:
    """
    Estimate CO₂e (kg) for a single activity.

    Returns kg CO₂e.
    """
    factor = lookup_factor(category, subcategory, country)
    return round(quantity * factor, 4)


def process_activity(activity_id: int) -> float:
    """
    Process a single raw_activity record: compute emissions and store.
    Returns the computed CO₂e in kg.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT id, category, subcategory, department, quantity, unit, date FROM raw_activity WHERE id = ?",
        [activity_id],
    ).fetchone()

    if not row:
        raise ValueError(f"Activity {activity_id} not found")

    _, category, subcategory, department, quantity, unit, act_date = row
    co2e = estimate_single(category, quantity, unit, subcategory)
    scope = get_scope(category)

    conn.execute(
        """
        INSERT INTO emissions (id, activity_id, category, subcategory, department, co2e_kg, scope, date)
        VALUES (nextval('seq_emissions'), ?, ?, ?, ?, ?, ?, ?)
        """,
        [activity_id, category, subcategory, department, co2e, scope, act_date],
    )
    return co2e


def process_all_unprocessed() -> int:
    """Process all activities that don't have emissions records yet."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.id
        FROM raw_activity a
        LEFT JOIN emissions e ON a.id = e.activity_id
        WHERE e.id IS NULL
    """).fetchall()

    count = 0
    for (aid,) in rows:
        process_activity(aid)
        count += 1
    return count


def get_total_emissions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """Get total emissions summary."""
    conn = get_connection()
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date <= ?")
        params.append(end_date)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Total
    total = conn.execute(
        f"SELECT COALESCE(SUM(co2e_kg), 0), COUNT(*) FROM emissions {where}", params
    ).fetchone()

    # By category
    by_cat = conn.execute(
        f"SELECT category, SUM(co2e_kg) FROM emissions {where} GROUP BY category ORDER BY SUM(co2e_kg) DESC",
        params,
    ).fetchall()

    # By department
    by_dept = conn.execute(
        f"SELECT COALESCE(department, 'Unassigned'), SUM(co2e_kg) FROM emissions {where} GROUP BY department ORDER BY SUM(co2e_kg) DESC",
        params,
    ).fetchall()

    # By scope
    by_scope = conn.execute(
        f"SELECT scope, SUM(co2e_kg) FROM emissions {where} GROUP BY scope ORDER BY scope",
        params,
    ).fetchall()

    return {
        "total_co2e_kg": round(total[0], 2),
        "total_co2e_tonnes": round(total[0] / 1000, 4),
        "period_start": str(start_date) if start_date else None,
        "period_end": str(end_date) if end_date else None,
        "by_category": {row[0]: round(row[1], 2) for row in by_cat},
        "by_department": {row[0]: round(row[1], 2) for row in by_dept},
        "by_scope": {row[0]: round(row[1], 2) for row in by_scope},
        "record_count": total[1],
    }


def get_monthly_trends(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[dict]:
    """Get monthly emission trends."""
    conn = get_connection()
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date <= ?")
        params.append(end_date)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    rows = conn.execute(
        f"""
        SELECT strftime(date, '%Y-%m') as month, SUM(co2e_kg) as total
        FROM emissions {where}
        GROUP BY month
        ORDER BY month
        """,
        params,
    ).fetchall()

    return [{"month": row[0], "co2e_kg": round(row[1], 2)} for row in rows]


def get_emissions_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[dict]:
    """Get detailed emissions by category and subcategory."""
    conn = get_connection()
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date <= ?")
        params.append(end_date)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    rows = conn.execute(
        f"""
        SELECT category, COALESCE(subcategory, 'general'), SUM(co2e_kg), COUNT(*)
        FROM emissions {where}
        GROUP BY category, subcategory
        ORDER BY SUM(co2e_kg) DESC
        """,
        params,
    ).fetchall()

    return [
        {
            "category": row[0],
            "subcategory": row[1],
            "co2e_kg": round(row[2], 2),
            "records": row[3],
        }
        for row in rows
    ]


def get_emissions_by_department(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[dict]:
    """Get emissions grouped by department."""
    conn = get_connection()
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("date <= ?")
        params.append(end_date)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    rows = conn.execute(
        f"""
        SELECT COALESCE(department, 'Unassigned'), SUM(co2e_kg), COUNT(*)
        FROM emissions {where}
        GROUP BY department
        ORDER BY SUM(co2e_kg) DESC
        """,
        params,
    ).fetchall()

    return [
        {"department": row[0], "co2e_kg": round(row[1], 2), "records": row[2]}
        for row in rows
    ]
