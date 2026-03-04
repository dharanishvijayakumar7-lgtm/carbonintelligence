"""
CSV / Excel data loader.

Supports flexible column mapping so users can upload files with varying headers.
"""
from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from database import get_connection

# ── Column mapping ────────────────────────────────────────────────────
# We try to auto-detect columns by looking for known names (case-insensitive).

_COL_ALIASES: dict[str, list[str]] = {
    "category":     ["category", "type", "emission_type", "source_type"],
    "subcategory":  ["subcategory", "sub_category", "subtype", "mode", "fuel_type", "provider"],
    "department":   ["department", "dept", "team", "business_unit", "cost_center"],
    "description":  ["description", "desc", "notes", "details", "item"],
    "quantity":     ["quantity", "amount", "value", "kwh", "km", "kg", "hours", "spend", "cost", "distance"],
    "unit":         ["unit", "units", "uom", "measure"],
    "date":         ["date", "invoice_date", "bill_date", "period", "month", "transaction_date"],
}


def _resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    """Map our schema columns to actual DataFrame column names."""
    mapping: dict[str, str] = {}
    lower_cols = {c.lower().strip(): c for c in df.columns}

    for target, aliases in _COL_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                mapping[target] = lower_cols[alias]
                break
    return mapping


def load_csv(file_path: str | Path, *, source_label: str | None = None) -> list[dict]:
    """
    Load a CSV or Excel file and return a list of activity record dicts.
    """
    path = Path(file_path)
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    return _parse_dataframe(df, source_label or path.name)


def load_csv_bytes(content: bytes, filename: str) -> list[dict]:
    """Load CSV/Excel from in-memory bytes (file upload)."""
    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))
    return _parse_dataframe(df, filename)


def _parse_dataframe(df: pd.DataFrame, source: str) -> list[dict]:
    """Convert a DataFrame into a list of raw_activity dicts."""
    col_map = _resolve_columns(df)

    if "category" not in col_map:
        raise ValueError(
            f"Cannot find a 'category' column. Available columns: {list(df.columns)}"
        )
    if "quantity" not in col_map:
        raise ValueError(
            f"Cannot find a 'quantity' column. Available columns: {list(df.columns)}"
        )

    records: list[dict] = []
    for _, row in df.iterrows():
        rec = {
            "source_file": source,
            "category": str(row[col_map["category"]]).strip().lower(),
            "subcategory": _safe_str(row.get(col_map.get("subcategory", ""), None)),
            "department": _safe_str(row.get(col_map.get("department", ""), None)),
            "description": _safe_str(row.get(col_map.get("description", ""), None)),
            "quantity": float(row[col_map["quantity"]]),
            "unit": _safe_str(row.get(col_map.get("unit", ""), None)) or _guess_unit(
                str(row[col_map["category"]]).strip().lower()
            ),
            "date": _parse_date(row.get(col_map.get("date", ""), None)),
        }
        records.append(rec)
    return records


def insert_activities(records: list[dict]) -> int:
    """Insert parsed activity records into the database."""
    conn = get_connection()
    count = 0
    for r in records:
        conn.execute(
            """
            INSERT INTO raw_activity (id, source_file, category, subcategory, department,
                                      description, quantity, unit, date)
            VALUES (nextval('seq_raw_activity'), ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                r["source_file"], r["category"], r.get("subcategory"),
                r.get("department"), r.get("description"),
                r["quantity"], r["unit"], r["date"],
            ],
        )
        count += 1
    return count


# ── Helpers ───────────────────────────────────────────────────────────

def _safe_str(val) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s and s.lower() != "nan" else None


def _parse_date(val) -> date:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return date.today()
    if isinstance(val, (datetime, date)):
        return val if isinstance(val, date) else val.date()
    try:
        return pd.to_datetime(str(val)).date()
    except Exception:
        return date.today()


def _guess_unit(category: str) -> str:
    """Guess the unit from the category name."""
    defaults = {
        "electricity": "kWh",
        "travel": "km",
        "commuting": "km",
        "cloud": "USD",
        "equipment": "item",
        "waste": "kg",
    }
    return defaults.get(category, "unit")
