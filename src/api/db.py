"""
Shared data-access layer for the FastAPI server.

Mirrors src/dashboard/utils/db.py's connection pattern, minus the
Streamlit caching decorators (FastAPI has its own request lifecycle).
"""

import sqlite3
from pathlib import Path

from src.etl.normaliser import normalize_year

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


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper() if ticker else ""


def company_exists(conn: sqlite3.Connection, ticker: str) -> bool:
    cur = conn.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,))
    return cur.fetchone() is not None


def get_companies_list(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """
    All companies with id, company_name, broad_sector, sub_sector,
    roe_pct, roce_pct - filterable by sector, market_cap_category, and
    partial name/ticker search.
    """
    query = """
        SELECT
            c.id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
    """
    conditions, params = [], []

    if sector:
        conditions.append("s.broad_sector = ?")
        params.append(sector)
    if market_cap_category:
        conditions.append("s.market_cap_category = ?")
        params.append(market_cap_category)
    if search:
        conditions.append("(c.company_name LIKE ? OR c.id LIKE ?)")
        like_term = f"%{search}%"
        params.extend([like_term, like_term])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY c.id"

    with get_connection() as conn:
        cur = conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_company_profile(ticker: str) -> dict | None:
    """
    Full company profile: all companies fields + sector data + the
    latest year's financial_ratios row. Returns None if not found.
    """
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT c.*, s.broad_sector, s.sub_sector,
                   s.market_cap_category, s.index_weight_pct
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE c.id = ?
            """,
            (ticker,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        profile = dict(row)

        cur = conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
            (ticker,),
        )
        ratio_rows = [dict(r) for r in cur.fetchall()]

    if ratio_rows:
        # Sort by normalized year to find the true latest, since the raw
        # year column mixes several formats (see normalize_year fix).
        for r in ratio_rows:
            r["_normalized_year"] = normalize_year(r["year"])
        ratio_rows = [r for r in ratio_rows if r["_normalized_year"] != "PARSE_ERROR"]
        if ratio_rows:
            latest = max(ratio_rows, key=lambda r: r["_normalized_year"])
            latest.pop("_normalized_year", None)
            latest.pop("company_id", None)
            profile["latest_ratios"] = latest

    return profile


def _rows_with_normalized_year(rows: list[dict]) -> list[dict]:
    """Attach a normalized_year field and sort ascending by it."""
    for r in rows:
        r["normalized_year"] = normalize_year(r["year"])
    return sorted(rows, key=lambda r: (r["normalized_year"] == "PARSE_ERROR", r["normalized_year"]))


def _filter_year_range(rows: list[dict], from_year: str | None, to_year: str | None) -> list[dict]:
    """
    Filter rows (already carrying normalized_year) to [from_year, to_year]
    inclusive, both in YYYY-MM format. Rows that failed year parsing are
    dropped when a range filter is applied, since they can't be compared.
    """
    if not from_year and not to_year:
        return rows

    filtered = []
    for r in rows:
        ny = r["normalized_year"]
        if ny == "PARSE_ERROR":
            continue
        if from_year and ny < from_year:
            continue
        if to_year and ny > to_year:
            continue
        filtered.append(r)
    return filtered


def get_statement(
    table: str, ticker: str, from_year: str | None = None, to_year: str | None = None
) -> list[dict]:
    """
    Shared implementation for the pl/bs/cashflow endpoints: fetch all
    rows for a ticker from the given table, attach normalized_year,
    sort chronologically, and optionally filter to a YYYY-MM range.
    """
    with get_connection() as conn:
        cur = conn.execute(f"SELECT * FROM {table} WHERE company_id = ?", (ticker,))
        rows = [dict(r) for r in cur.fetchall()]

    rows = _rows_with_normalized_year(rows)
    rows = _filter_year_range(rows, from_year, to_year)
    return rows


def get_company_ratios(ticker: str, year: str | None = None) -> list[dict]:
    """
    All financial_ratios rows for a company, sorted chronologically.
    If year is given, normalizes both the query value and stored values
    and returns only the matching row(s).
    """
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ?", (ticker,)
        )
        rows = [dict(r) for r in cur.fetchall()]

    rows = _rows_with_normalized_year(rows)

    if year:
        target = normalize_year(year)
        rows = [r for r in rows if r["normalized_year"] == target]

    return rows


def get_tearsheet_path(ticker: str) -> Path | None:
    """Path to the pre-generated tearsheet PDF, or None if missing."""
    path = PROJECT_ROOT / "reports" / "tearsheets" / f"{ticker}_tearsheet.pdf"
    return path if path.exists() else None