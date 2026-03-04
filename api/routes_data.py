"""
Data Ingestion API Routes

Handles file uploads (CSV, Excel, PDF) and manual data entry.
"""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from ingestion.csv_loader import load_csv_bytes, insert_activities
from ingestion.pdf_parser import parse_pdf_bytes
from engine.carbon_estimator import process_all_unprocessed
from models import UploadResponse, ActivityBatch

router = APIRouter(prefix="/api/data", tags=["Data Ingestion"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category_override: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
):
    """
    Upload a CSV, Excel, or PDF file for emission data extraction.

    Supported formats:
    - CSV (.csv) — activity records
    - Excel (.xlsx, .xls) — activity records
    - PDF (.pdf) — utility bills
    """
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    content = await file.read()
    filename = file.filename.lower()

    try:
        if filename.endswith(".pdf"):
            records = parse_pdf_bytes(content, file.filename)
        elif filename.endswith((".csv", ".xlsx", ".xls")):
            records = load_csv_bytes(content, file.filename)
        else:
            raise HTTPException(
                400,
                f"Unsupported file format. Supported: .csv, .xlsx, .xls, .pdf",
            )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error parsing file: {str(e)}")

    # Apply overrides
    if category_override or department:
        for r in records:
            if category_override:
                r["category"] = category_override
            if department:
                r["department"] = department

    # Insert into database
    records_count = insert_activities(records)

    # Calculate emissions
    emissions_count = process_all_unprocessed()

    return UploadResponse(
        filename=file.filename,
        records_imported=records_count,
        emissions_calculated=emissions_count,
        message=f"Successfully imported {records_count} records and calculated {emissions_count} emission entries.",
    )


@router.post("/batch", response_model=UploadResponse)
async def batch_import(batch: ActivityBatch):
    """Import a batch of activity records via JSON."""
    records = [
        {
            "source_file": "api_batch",
            "category": r.category,
            "subcategory": r.subcategory,
            "department": r.department,
            "description": r.description,
            "quantity": r.quantity,
            "unit": r.unit,
            "date": r.date,
        }
        for r in batch.records
    ]

    records_count = insert_activities(records)
    emissions_count = process_all_unprocessed()

    return UploadResponse(
        filename="api_batch",
        records_imported=records_count,
        emissions_calculated=emissions_count,
        message=f"Batch imported {records_count} records.",
    )
