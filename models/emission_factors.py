"""
Emission Factors Database

Sources:
  - EPA (2024) — US grid electricity factors
  - DEFRA (2024) — UK Government GHG Conversion Factors
  - IPCC AR6 — Global Warming Potentials
  - IEA (2023) — International electricity factors

All factors are in kg CO₂e per unit specified.
"""

from __future__ import annotations
from database import get_connection

# ── Master emission factor table ──────────────────────────────────────

EMISSION_FACTORS: list[dict] = [
    # ── ELECTRICITY (kg CO₂e per kWh) ────────────────────────────────
    {"id": 1,   "category": "electricity", "subcategory": "grid_us",          "unit": "kWh", "factor_kg_co2e": 0.417,   "source": "EPA 2024",     "country": "US"},
    {"id": 2,   "category": "electricity", "subcategory": "grid_uk",          "unit": "kWh", "factor_kg_co2e": 0.207,   "source": "DEFRA 2024",   "country": "UK"},
    {"id": 3,   "category": "electricity", "subcategory": "grid_eu",          "unit": "kWh", "factor_kg_co2e": 0.276,   "source": "IEA 2023",     "country": "EU"},
    {"id": 4,   "category": "electricity", "subcategory": "grid_global",      "unit": "kWh", "factor_kg_co2e": 0.494,   "source": "IEA 2023",     "country": "GLOBAL"},
    {"id": 5,   "category": "electricity", "subcategory": "renewable",        "unit": "kWh", "factor_kg_co2e": 0.0,     "source": "N/A",          "country": "GLOBAL"},

    # ── NATURAL GAS (kg CO₂e per therm) ──────────────────────────────
    {"id": 6,   "category": "electricity", "subcategory": "natural_gas",      "unit": "therm", "factor_kg_co2e": 5.31,  "source": "EPA 2024",     "country": "US"},

    # ── BUSINESS TRAVEL (kg CO₂e per km) ─────────────────────────────
    {"id": 10,  "category": "travel", "subcategory": "flight_short",          "unit": "km", "factor_kg_co2e": 0.255,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 11,  "category": "travel", "subcategory": "flight_medium",         "unit": "km", "factor_kg_co2e": 0.156,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 12,  "category": "travel", "subcategory": "flight_long",           "unit": "km", "factor_kg_co2e": 0.150,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 13,  "category": "travel", "subcategory": "car_petrol",            "unit": "km", "factor_kg_co2e": 0.171,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 14,  "category": "travel", "subcategory": "car_diesel",            "unit": "km", "factor_kg_co2e": 0.168,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 15,  "category": "travel", "subcategory": "car_electric",          "unit": "km", "factor_kg_co2e": 0.047,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 16,  "category": "travel", "subcategory": "train",                 "unit": "km", "factor_kg_co2e": 0.041,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 17,  "category": "travel", "subcategory": "bus",                   "unit": "km", "factor_kg_co2e": 0.089,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 18,  "category": "travel", "subcategory": "taxi",                  "unit": "km", "factor_kg_co2e": 0.149,    "source": "DEFRA 2024",   "country": "GLOBAL"},

    # ── EMPLOYEE COMMUTING (kg CO₂e per km) ──────────────────────────
    {"id": 20,  "category": "commuting", "subcategory": "car_petrol",         "unit": "km", "factor_kg_co2e": 0.171,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 21,  "category": "commuting", "subcategory": "car_diesel",         "unit": "km", "factor_kg_co2e": 0.168,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 22,  "category": "commuting", "subcategory": "car_electric",       "unit": "km", "factor_kg_co2e": 0.047,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 23,  "category": "commuting", "subcategory": "public_transit",     "unit": "km", "factor_kg_co2e": 0.065,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 24,  "category": "commuting", "subcategory": "bicycle",            "unit": "km", "factor_kg_co2e": 0.0,      "source": "N/A",          "country": "GLOBAL"},
    {"id": 25,  "category": "commuting", "subcategory": "walking",            "unit": "km", "factor_kg_co2e": 0.0,      "source": "N/A",          "country": "GLOBAL"},
    {"id": 26,  "category": "commuting", "subcategory": "motorcycle",         "unit": "km", "factor_kg_co2e": 0.114,    "source": "DEFRA 2024",   "country": "GLOBAL"},

    # ── CLOUD COMPUTING (kg CO₂e per USD spend) ──────────────────────
    {"id": 30,  "category": "cloud", "subcategory": "aws",                    "unit": "USD", "factor_kg_co2e": 0.0006,  "source": "Estimate",     "country": "GLOBAL"},
    {"id": 31,  "category": "cloud", "subcategory": "gcp",                    "unit": "USD", "factor_kg_co2e": 0.0003,  "source": "Estimate",     "country": "GLOBAL"},
    {"id": 32,  "category": "cloud", "subcategory": "azure",                  "unit": "USD", "factor_kg_co2e": 0.0005,  "source": "Estimate",     "country": "GLOBAL"},
    # Alternative: per server-hour
    {"id": 33,  "category": "cloud", "subcategory": "server_hour",            "unit": "hour", "factor_kg_co2e": 0.06,   "source": "Estimate",     "country": "GLOBAL"},

    # ── OFFICE EQUIPMENT (kg CO₂e per item — lifecycle) ──────────────
    {"id": 40,  "category": "equipment", "subcategory": "laptop",             "unit": "item", "factor_kg_co2e": 350.0,  "source": "Dell/HP LCA",  "country": "GLOBAL"},
    {"id": 41,  "category": "equipment", "subcategory": "desktop",            "unit": "item", "factor_kg_co2e": 700.0,  "source": "Dell/HP LCA",  "country": "GLOBAL"},
    {"id": 42,  "category": "equipment", "subcategory": "monitor",            "unit": "item", "factor_kg_co2e": 450.0,  "source": "Dell/HP LCA",  "country": "GLOBAL"},
    {"id": 43,  "category": "equipment", "subcategory": "phone",              "unit": "item", "factor_kg_co2e": 70.0,   "source": "Apple LCA",    "country": "GLOBAL"},
    {"id": 44,  "category": "equipment", "subcategory": "printer",            "unit": "item", "factor_kg_co2e": 200.0,  "source": "Estimate",     "country": "GLOBAL"},
    {"id": 45,  "category": "equipment", "subcategory": "server",             "unit": "item", "factor_kg_co2e": 1500.0, "source": "Estimate",     "country": "GLOBAL"},
    {"id": 46,  "category": "equipment", "subcategory": "furniture",          "unit": "item", "factor_kg_co2e": 100.0,  "source": "Estimate",     "country": "GLOBAL"},

    # ── WASTE (kg CO₂e per kg of waste) ──────────────────────────────
    {"id": 50,  "category": "waste", "subcategory": "general_landfill",       "unit": "kg", "factor_kg_co2e": 0.587,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 51,  "category": "waste", "subcategory": "recycled_paper",         "unit": "kg", "factor_kg_co2e": 0.021,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 52,  "category": "waste", "subcategory": "recycled_plastic",       "unit": "kg", "factor_kg_co2e": 0.021,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 53,  "category": "waste", "subcategory": "recycled_metal",         "unit": "kg", "factor_kg_co2e": 0.021,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 54,  "category": "waste", "subcategory": "electronic_waste",       "unit": "kg", "factor_kg_co2e": 1.200,    "source": "Estimate",     "country": "GLOBAL"},
    {"id": 55,  "category": "waste", "subcategory": "food_waste",             "unit": "kg", "factor_kg_co2e": 0.580,    "source": "DEFRA 2024",   "country": "GLOBAL"},
    {"id": 56,  "category": "waste", "subcategory": "composted",              "unit": "kg", "factor_kg_co2e": 0.010,    "source": "DEFRA 2024",   "country": "GLOBAL"},
]


# ── Scope mapping ────────────────────────────────────────────────────

SCOPE_MAP: dict[str, int] = {
    "electricity": 2,     # Scope 2 — purchased electricity
    "natural_gas": 1,     # Scope 1 — direct combustion
    "travel":      3,     # Scope 3 — business travel
    "commuting":   3,     # Scope 3 — employee commuting
    "cloud":       3,     # Scope 3 — purchased services
    "equipment":   3,     # Scope 3 — purchased goods
    "waste":       3,     # Scope 3 — waste
}


def get_scope(category: str) -> int:
    return SCOPE_MAP.get(category, 3)


def seed_emission_factors() -> int:
    """Insert all factors into the database (idempotent)."""
    conn = get_connection()
    conn.execute("DELETE FROM emission_factors;")
    for ef in EMISSION_FACTORS:
        conn.execute(
            """
            INSERT INTO emission_factors (id, category, subcategory, unit, factor_kg_co2e, source, country, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [ef["id"], ef["category"], ef.get("subcategory"), ef["unit"],
             ef["factor_kg_co2e"], ef.get("source"), ef.get("country", "GLOBAL"), ef.get("year", 2024)],
        )
    return len(EMISSION_FACTORS)


def lookup_factor(category: str, subcategory: str | None = None, country: str = "GLOBAL") -> float:
    """
    Look up the best-matching emission factor.
    Falls back: exact match → country match → GLOBAL → category default.
    """
    conn = get_connection()

    if subcategory:
        # Try exact match
        result = conn.execute(
            "SELECT factor_kg_co2e FROM emission_factors WHERE category = ? AND subcategory = ? AND country = ? LIMIT 1",
            [category, subcategory, country],
        ).fetchone()
        if result:
            return result[0]

        # Try global
        result = conn.execute(
            "SELECT factor_kg_co2e FROM emission_factors WHERE category = ? AND subcategory = ? AND country = 'GLOBAL' LIMIT 1",
            [category, subcategory],
        ).fetchone()
        if result:
            return result[0]

    # Fallback: first factor for category in country
    result = conn.execute(
        "SELECT factor_kg_co2e FROM emission_factors WHERE category = ? AND country = ? LIMIT 1",
        [category, country],
    ).fetchone()
    if result:
        return result[0]

    # Last fallback: any factor for category
    result = conn.execute(
        "SELECT factor_kg_co2e FROM emission_factors WHERE category = ? LIMIT 1",
        [category],
    ).fetchone()
    return result[0] if result else 0.0
