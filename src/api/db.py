"""
Shared data-access layer for the FastAPI server.

Mirrors src/dashboard/utils/db.py's connection pattern, minus the
Streamlit caching decorators (FastAPI has its own request lifecycle).
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run `python src/etl/loader.py` first."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# The 10 core company-data tables (excludes stock_prices, analysis,
# peer_percentiles, and sqlite_sequence, which are auxiliary/derived
# rather than part of the core per-company data model). Used by the
# health check's db_row_counts. Flag for team lead if a different set
# of 10 was intended.
CORE_TABLES = [
    "companies",
    "sectors",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "documents",
    "prosandcons",
    "peer_groups",
]


def get_table_row_counts() -> dict[str, int]:
    """Row count for each of the 10 core tables, for GET /health."""
    counts = {}
    with get_connection() as conn:
        for table in CORE_TABLES:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
    return counts