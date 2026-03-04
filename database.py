"""
Carbon Intelligence System — DuckDB Database Layer
"""
from __future__ import annotations

from typing import Optional
import duckdb
from config import DATABASE_URL

_conn: Optional[duckdb.DuckDBPyConnection] = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return a singleton DuckDB connection."""
    global _conn
    if _conn is None:
        _conn = duckdb.connect(DATABASE_URL)
        _initialize_schema(_conn)
    return _conn


def _initialize_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create tables if they don't exist."""

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emission_factors (
            id              INTEGER PRIMARY KEY,
            category        VARCHAR NOT NULL,
            subcategory     VARCHAR,
            unit            VARCHAR NOT NULL,
            factor_kg_co2e  DOUBLE NOT NULL,
            source          VARCHAR,
            country         VARCHAR DEFAULT 'GLOBAL',
            year            INTEGER DEFAULT 2024
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_activity (
            id              INTEGER PRIMARY KEY,
            source_file     VARCHAR,
            category        VARCHAR NOT NULL,
            subcategory     VARCHAR,
            department      VARCHAR,
            description     VARCHAR,
            quantity         DOUBLE NOT NULL,
            unit            VARCHAR NOT NULL,
            date            DATE NOT NULL,
            metadata_json   VARCHAR,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_raw_activity START 1;
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emissions (
            id              INTEGER PRIMARY KEY,
            activity_id     INTEGER REFERENCES raw_activity(id),
            category        VARCHAR NOT NULL,
            subcategory     VARCHAR,
            department      VARCHAR,
            co2e_kg         DOUBLE NOT NULL,
            scope           INTEGER,           -- 1, 2, or 3
            date            DATE NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_emissions START 1;
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY,
            period          VARCHAR NOT NULL,
            generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_co2e_kg   DOUBLE,
            summary_json    VARCHAR,
            recommendations VARCHAR
        );
    """)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_reports START 1;
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id              INTEGER PRIMARY KEY,
            role            VARCHAR NOT NULL,
            content         VARCHAR NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_chat START 1;
    """)


def reset_database() -> None:
    """Drop and recreate all tables — useful for testing."""
    conn = get_connection()
    for table in ["chat_history", "reports", "emissions", "raw_activity", "emission_factors"]:
        conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    for seq in ["seq_raw_activity", "seq_emissions", "seq_reports", "seq_chat"]:
        conn.execute(f"DROP SEQUENCE IF EXISTS {seq};")
    _initialize_schema(conn)
