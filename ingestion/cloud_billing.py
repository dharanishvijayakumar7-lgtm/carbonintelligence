"""
Cloud Billing Parser

Parses billing exports from AWS, GCP, and Azure into activity records.
Supports CSV exports from cloud cost management tools.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd


def parse_cloud_billing(file_path: str | Path, provider: str = "aws") -> list[dict]:
    """
    Parse a cloud provider billing CSV.

    Supports:
      - AWS Cost and Usage Report (CSV)
      - GCP Billing Export (CSV)
      - Azure Cost Management Export (CSV)
    """
    path = Path(file_path)
    df = pd.read_csv(path)
    provider = provider.lower().strip()

    if provider == "aws":
        return _parse_aws(df, path.name)
    elif provider == "gcp":
        return _parse_gcp(df, path.name)
    elif provider == "azure":
        return _parse_azure(df, path.name)
    else:
        return _parse_generic_cloud(df, path.name, provider)


def _parse_aws(df: pd.DataFrame, source: str) -> list[dict]:
    """Parse AWS Cost and Usage Report."""
    records: list[dict] = []
    cost_col = _find_col(df, ["lineItem/UnblendedCost", "Cost", "cost", "amount", "total"])
    date_col = _find_col(df, ["lineItem/UsageStartDate", "Date", "date", "UsageStartDate"])
    service_col = _find_col(df, ["lineItem/ProductCode", "Service", "service", "ProductCode"])

    if cost_col is None:
        # Fallback: aggregate all numeric columns
        return _parse_generic_cloud(df, source, "aws")

    for _, row in df.iterrows():
        cost = _safe_float(row.get(cost_col))
        if cost and cost > 0:
            records.append({
                "source_file": source,
                "category": "cloud",
                "subcategory": "aws",
                "department": _safe_str(row.get(service_col)) if service_col else None,
                "description": f"AWS: {_safe_str(row.get(service_col)) or 'cloud usage'}",
                "quantity": cost,
                "unit": "USD",
                "date": _parse_date(row.get(date_col)) if date_col else date.today(),
            })
    return records


def _parse_gcp(df: pd.DataFrame, source: str) -> list[dict]:
    """Parse GCP Billing Export."""
    records: list[dict] = []
    cost_col = _find_col(df, ["cost", "Cost", "amount", "total_cost"])
    date_col = _find_col(df, ["usage_start_time", "date", "Date", "invoice.month"])
    service_col = _find_col(df, ["service.description", "service", "Service"])

    if cost_col is None:
        return _parse_generic_cloud(df, source, "gcp")

    for _, row in df.iterrows():
        cost = _safe_float(row.get(cost_col))
        if cost and cost > 0:
            records.append({
                "source_file": source,
                "category": "cloud",
                "subcategory": "gcp",
                "department": _safe_str(row.get(service_col)) if service_col else None,
                "description": f"GCP: {_safe_str(row.get(service_col)) or 'cloud usage'}",
                "quantity": cost,
                "unit": "USD",
                "date": _parse_date(row.get(date_col)) if date_col else date.today(),
            })
    return records


def _parse_azure(df: pd.DataFrame, source: str) -> list[dict]:
    """Parse Azure Cost Management Export."""
    records: list[dict] = []
    cost_col = _find_col(df, ["CostInBillingCurrency", "Cost", "cost", "PreTaxCost"])
    date_col = _find_col(df, ["Date", "date", "UsageDateTime", "BillingPeriodStartDate"])
    service_col = _find_col(df, ["ServiceName", "MeterCategory", "service"])

    if cost_col is None:
        return _parse_generic_cloud(df, source, "azure")

    for _, row in df.iterrows():
        cost = _safe_float(row.get(cost_col))
        if cost and cost > 0:
            records.append({
                "source_file": source,
                "category": "cloud",
                "subcategory": "azure",
                "department": _safe_str(row.get(service_col)) if service_col else None,
                "description": f"Azure: {_safe_str(row.get(service_col)) or 'cloud usage'}",
                "quantity": cost,
                "unit": "USD",
                "date": _parse_date(row.get(date_col)) if date_col else date.today(),
            })
    return records


def _parse_generic_cloud(df: pd.DataFrame, source: str, provider: str) -> list[dict]:
    """Fallback parser for generic cloud billing CSVs."""
    records: list[dict] = []

    # Find any numeric column that could be cost
    cost_col = None
    for col in df.columns:
        if df[col].dtype in ("float64", "int64") and df[col].sum() > 0:
            cost_col = col
            break

    date_col = _find_col(df, ["date", "Date", "month", "period"])

    if cost_col is None:
        return records

    for _, row in df.iterrows():
        cost = _safe_float(row.get(cost_col))
        if cost and cost > 0:
            records.append({
                "source_file": source,
                "category": "cloud",
                "subcategory": provider,
                "description": f"{provider.upper()} cloud usage",
                "quantity": cost,
                "unit": "USD",
                "date": _parse_date(row.get(date_col)) if date_col else date.today(),
            })
    return records


# ── Helpers ───────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        v = float(val)
        return v if not pd.isna(v) else None
    except (ValueError, TypeError):
        return None


def _safe_str(val) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s and s.lower() != "nan" else None


def _parse_date(val) -> date:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return date.today()
    try:
        return pd.to_datetime(str(val)).date()
    except Exception:
        return date.today()
