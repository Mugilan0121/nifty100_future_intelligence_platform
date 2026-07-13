"""
Shared data-access layer for the Streamlit dashboard.

Every screen imports from here. No page should open sqlite3 directly —
that keeps caching, join logic, and error handling in one place.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run `python src/etl/loader.py` first."
        )
    return sqlite3.connect(DB_PATH)

import requests

@st.cache_data(ttl=86400)
def is_url_valid(url: str) -> bool:
    """
    Check whether an annual report URL is reachable.
    Mirrors DQ-13 from the project spec: 200 = valid.
    Uses a browser-like User-Agent since some hosts (e.g. BSE) reject
    bare requests with 403/406 even when the file is genuinely live.
    """
    if not url or not isinstance(url, str) or not url.strip():
        return False

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return True
        # Some servers don't support HEAD properly — fall back to GET
        response = requests.get(url, headers=headers, timeout=5, stream=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

# ---------------------------------------------------------------------
# Companies + Sectors
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """All 92 companies with sector info joined in."""
    query = """
        SELECT
            c.*,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            s.index_weight_pct
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Sector list with company counts — for dropdowns and the Home donut."""
    query = """
        SELECT broad_sector, COUNT(*) AS company_count
        FROM sectors
        GROUP BY broad_sector
        ORDER BY company_count DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


# ---------------------------------------------------------------------
# Financial Ratios (with market cap + P&L joined — screener/profile backbone)
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker: str | None = None, year: str | None = None) -> pd.DataFrame:
    """
    financial_ratios joined with market_cap (valuation multiples),
    profitandloss (sales, net_profit), and sectors.

    ticker: NSE ticker, e.g. 'TCS'. If None, returns all companies.
    year:   'YYYY-MM' format (e.g. '2023-03'). If None, returns all years.
    """
    query = """
        SELECT
            fr.*,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct,
            mc.market_cap_crore,
            mc.enterprise_value_crore,
            pl.sales,
            pl.net_profit,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category
        FROM financial_ratios fr
        LEFT JOIN market_cap mc
            ON fr.company_id = mc.company_id
            AND substr(fr.year, 1, 4) = CAST(mc.year AS TEXT)
        LEFT JOIN profitandloss pl
            ON fr.company_id = pl.company_id
            AND fr.year = pl.year
        LEFT JOIN sectors s
            ON fr.company_id = s.company_id
    """
    conditions, params = [], []

    if ticker:
        conditions.append("fr.company_id = ?")
        params.append(ticker.strip().upper())
    if year:
        conditions.append("fr.year = ?")
        params.append(year)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_latest_ratios() -> pd.DataFrame:
    """One row per company — most recent year only. Used by Home + Screener."""
    df = get_ratios()
    df = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    return df


# ---------------------------------------------------------------------
# Raw Financial Statements (Company Profile screen)
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=[ticker.strip().upper()])


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=[ticker.strip().upper()])


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=[ticker.strip().upper()])


@st.cache_data(ttl=600)
def get_prosandcons(ticker: str) -> pd.DataFrame:
    query = "SELECT * FROM prosandcons WHERE company_id = ?"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=[ticker.strip().upper()])


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    query = "SELECT * FROM documents WHERE company_id = ? ORDER BY Year DESC"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=[ticker.strip().upper()])


# ---------------------------------------------------------------------
# Peer Comparison
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_peer_groups() -> pd.DataFrame:
    """All 11 peer groups with their member companies."""
    query = "SELECT * FROM peer_groups"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """
    Companies in a peer group, with their latest financial ratios
    and their percentile rank within that group.
    """
    query = """
        SELECT
            pg.company_id,
            pg.is_benchmark,
            fr.year,
            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,
            fr.net_profit_margin_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.pat_cagr_5yr,
            fr.revenue_cagr_5yr,
            fr.eps_cagr_5yr
        FROM peer_groups pg
        LEFT JOIN financial_ratios fr ON pg.company_id = fr.company_id
        WHERE pg.peer_group_name = ?
    """
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=[group_name])

    if not df.empty:
        df = (
            df.sort_values("year")
            .groupby("company_id", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )
    return df


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name: str) -> pd.DataFrame:
    """Reads the peer_percentiles table populated by src/analytics/peer.py."""
    query = "SELECT * FROM peer_percentiles WHERE peer_group_name = ?"
    with get_connection() as conn:
        try:
            return pd.read_sql_query(query, conn, params=[group_name])
        except Exception:
            return pd.DataFrame()


# ---------------------------------------------------------------------
# Capital Allocation
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_capital_allocation(year: str | None = None) -> pd.DataFrame:
    """
    Capital allocation patterns, generated by src/reports/generate_capital_allocation.py
    into output/capital_allocation.csv (not a SQLite table).
    """
    csv_path = PROJECT_ROOT / "output" / "capital_allocation.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if year and "year" in df.columns:
        df = df[df["year"] == year]
    return df


# ---------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker: str | None = None) -> pd.DataFrame:
    valuation_path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
    if not valuation_path.exists():
        return pd.DataFrame()
    df = pd.read_excel(valuation_path)
    if ticker:
        df = df[df["company_id"] == ticker.strip().upper()]
    return df