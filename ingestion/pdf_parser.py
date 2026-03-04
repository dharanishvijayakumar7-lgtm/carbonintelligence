"""
PDF Bill Parser

Extracts electricity usage, amounts, and dates from PDF utility bills.
Uses pdfplumber for text extraction and regex patterns for data extraction.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Optional


def parse_pdf_bill(file_path: str | Path) -> list[dict]:
    """
    Parse a PDF electricity / utility bill and extract activity records.
    Returns a list of activity record dicts.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF parsing. Install with: pip install pdfplumber")

    path = Path(file_path)
    records: list[dict] = []

    with pdfplumber.open(path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    if not full_text.strip():
        return records

    # Try to extract structured data from the bill text
    extracted = _extract_bill_data(full_text)

    for item in extracted:
        records.append({
            "source_file": path.name,
            "category": item.get("category", "electricity"),
            "subcategory": item.get("subcategory", "grid_us"),
            "department": item.get("department"),
            "description": item.get("description", f"PDF bill: {path.name}"),
            "quantity": item["quantity"],
            "unit": item.get("unit", "kWh"),
            "date": item.get("date", date.today()),
        })

    return records


def parse_pdf_bytes(content: bytes, filename: str) -> list[dict]:
    """Parse PDF from in-memory bytes."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(content)
        tmp_path = f.name

    try:
        records = parse_pdf_bill(tmp_path)
        for r in records:
            r["source_file"] = filename
        return records
    finally:
        os.unlink(tmp_path)


def _extract_bill_data(text: str) -> list[dict]:
    """
    Use regex patterns to extract electricity usage data from bill text.
    Handles common US and UK utility bill formats.
    """
    results: list[dict] = []

    # Pattern 1: kWh usage
    kwh_patterns = [
        r"(\d[\d,]*\.?\d*)\s*kWh",
        r"usage[:\s]*(\d[\d,]*\.?\d*)\s*(?:kWh)?",
        r"consumption[:\s]*(\d[\d,]*\.?\d*)\s*(?:kWh)?",
        r"total\s+(?:usage|kwh|energy)[:\s]*(\d[\d,]*\.?\d*)",
    ]

    for pattern in kwh_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            qty = float(match.replace(",", ""))
            if 10 < qty < 1_000_000:  # sanity check
                results.append({
                    "quantity": qty,
                    "unit": "kWh",
                    "category": "electricity",
                    "subcategory": "grid_us",
                    "description": "Extracted from PDF bill",
                })

    # Pattern 2: Therms (natural gas)
    therm_patterns = [
        r"(\d[\d,]*\.?\d*)\s*therms?",
        r"gas\s+usage[:\s]*(\d[\d,]*\.?\d*)",
    ]

    for pattern in therm_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            qty = float(match.replace(",", ""))
            if 1 < qty < 100_000:
                results.append({
                    "quantity": qty,
                    "unit": "therm",
                    "category": "electricity",
                    "subcategory": "natural_gas",
                    "description": "Natural gas from PDF bill",
                })

    # Pattern 3: Date extraction
    bill_date = _extract_date(text)

    for r in results:
        if bill_date:
            r["date"] = bill_date

    # If no structured data found, try to extract a dollar amount as a proxy
    if not results:
        amount_patterns = [
            r"\$\s*(\d[\d,]*\.?\d*)",
            r"total[:\s]*\$?\s*(\d[\d,]*\.?\d*)",
            r"amount\s+due[:\s]*\$?\s*(\d[\d,]*\.?\d*)",
        ]
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amt = float(match.replace(",", ""))
                if 10 < amt < 100_000:
                    # Estimate kWh from dollar amount (avg US rate ~$0.12/kWh)
                    estimated_kwh = amt / 0.12
                    results.append({
                        "quantity": round(estimated_kwh, 1),
                        "unit": "kWh",
                        "category": "electricity",
                        "subcategory": "grid_us",
                        "description": f"Estimated from ${amt:.2f} bill amount",
                        "date": bill_date or date.today(),
                    })
                    break
            if results:
                break

    return results


def _extract_date(text: str) -> Optional[date]:
    """Extract a billing date from text."""
    from datetime import datetime

    date_patterns = [
        r"(?:bill|invoice|statement)\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(?:period|service)\s*(?:ending|to|through)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\w+\s+\d{1,2},?\s+\d{4})",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                import pandas as pd
                return pd.to_datetime(match.group(1)).date()
            except Exception:
                pass

    return None
