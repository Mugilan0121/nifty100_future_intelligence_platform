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

import statistics


def _latest_row(table: str, ticker: str, conn: sqlite3.Connection | None = None) -> dict | None:
    """Latest (by normalized year) row for a company from a year-keyed table."""
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
    try:
        cur = conn.execute(f"SELECT * FROM {table} WHERE company_id = ?", (ticker,))
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        if owns_conn:
            conn.close()

    if not rows:
        return None
    rows = _rows_with_normalized_year(rows)
    valid = [r for r in rows if r["normalized_year"] != "PARSE_ERROR"]
    return valid[-1] if valid else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _percentiles(values: list[float]) -> dict | None:
    if not values:
        return None
    series = sorted(values)
    n = len(series)

    def pct(p):
        idx = min(n - 1, int(round(p / 100 * (n - 1))))
        return series[idx]

    return {
        "P10": pct(10), "P25": pct(25), "P50": pct(50),
        "P75": pct(75), "P90": pct(90),
        "mean": statistics.mean(series), "std": statistics.pstdev(series),
    }


def sector_exists(sector: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM sectors WHERE broad_sector = ?", (sector,))
        return cur.fetchone() is not None


def get_sectors_list() -> list[dict]:
    """All distinct sectors with company_count, median_roe, median_pe, median_de."""
    with get_connection() as conn:
        sector_names = [
            r[0] for r in conn.execute(
                "SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL"
            ).fetchall()
        ]
        result = []
        for sec in sector_names:
            company_ids = [
                r[0] for r in conn.execute(
                    "SELECT company_id FROM sectors WHERE broad_sector = ?", (sec,)
                ).fetchall()
            ]
            roes, des, pes = [], [], []
            for cid in company_ids:
                fr = _latest_row("financial_ratios", cid, conn=conn)
                if fr:
                    if fr.get("return_on_equity_pct") is not None:
                        roes.append(fr["return_on_equity_pct"])
                    if fr.get("debt_to_equity") is not None:
                        des.append(fr["debt_to_equity"])
                mc = _latest_row("market_cap", cid, conn=conn)
                if mc and mc.get("pe_ratio") is not None:
                    pes.append(mc["pe_ratio"])
            result.append({
                "broad_sector": sec,
                "company_count": len(company_ids),
                "median_roe": _median(roes),
                "median_pe": _median(pes),
                "median_de": _median(des),
            })
    return result


def get_sector_companies(sector: str) -> list[dict]:
    """Companies in a sector with latest-year KPIs."""
    with get_connection() as conn:
        company_ids = conn.execute(
            "SELECT company_id FROM sectors WHERE broad_sector = ?", (sector,)
        ).fetchall()
        results = []
        for row in company_ids:
            cid = row[0]
            name_row = conn.execute(
                "SELECT company_name FROM companies WHERE id = ?", (cid,)
            ).fetchone()
            fr = _latest_row("financial_ratios", cid, conn=conn)
            results.append({
                "id": cid,
                "company_name": name_row["company_name"] if name_row else None,
                "return_on_equity_pct": fr.get("return_on_equity_pct") if fr else None,
                "debt_to_equity": fr.get("debt_to_equity") if fr else None,
                "revenue_cagr_5yr": fr.get("revenue_cagr_5yr") if fr else None,
                "operating_profit_margin_pct": fr.get("operating_profit_margin_pct") if fr else None,
            })
    return results


def screen_companies(
    min_roe=None, max_de=None, min_fcf=None, sector=None,
    min_rev_cagr_5yr=None, min_pat_cagr_5yr=None, max_pe=None,
) -> list[dict]:
    """Screen companies against financial_ratios + market_cap latest-year data."""
    with get_connection() as conn:
        query = """
            SELECT c.id, c.company_name, s.broad_sector
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
        """
        params = []
        if sector:
            query += " WHERE s.broad_sector = ?"
            params.append(sector)
        base_rows = conn.execute(query, params).fetchall()

        results = []
        for row in base_rows:
            cid = row["id"]
            fr = _latest_row("financial_ratios", cid, conn=conn)
            mc = _latest_row("market_cap", cid, conn=conn)
            roe = fr.get("return_on_equity_pct") if fr else None
            de = fr.get("debt_to_equity") if fr else None
            fcf = fr.get("free_cash_flow_cr") if fr else None
            rev_cagr = fr.get("revenue_cagr_5yr") if fr else None
            pat_cagr = fr.get("pat_cagr_5yr") if fr else None
            pe = mc.get("pe_ratio") if mc else None

            if min_roe is not None and (roe is None or roe < min_roe):
                continue
            if max_de is not None and (de is None or de > max_de):
                continue
            if min_fcf is not None and (fcf is None or fcf < min_fcf):
                continue
            if min_rev_cagr_5yr is not None and (rev_cagr is None or rev_cagr < min_rev_cagr_5yr):
                continue
            if min_pat_cagr_5yr is not None and (pat_cagr is None or pat_cagr < min_pat_cagr_5yr):
                continue
            if max_pe is not None and (pe is None or pe > max_pe):
                continue

            results.append({
                "id": cid, "company_name": row["company_name"], "broad_sector": row["broad_sector"],
                "roe_pct": roe, "debt_to_equity": de, "free_cash_flow_cr": fcf,
                "revenue_cagr_5yr": rev_cagr, "pat_cagr_5yr": pat_cagr, "pe_ratio": pe,
            })

    results.sort(key=lambda r: (r["roe_pct"] is None, -(r["roe_pct"] or 0)))
    return results


def peer_group_exists(group_name: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 FROM peer_groups WHERE peer_group_name = ?", (group_name,))
        return cur.fetchone() is not None


def get_peer_group_data(group_name: str) -> list[dict]:
    """All companies + percentile ranks in a peer group."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT pp.company_id, c.company_name, pp.metric, pp.value, pp.percentile_rank, pp.year
            FROM peer_percentiles pp
            JOIN companies c ON c.id = pp.company_id
            WHERE pp.peer_group_name = ?
            ORDER BY c.company_name, pp.metric
            """,
            (group_name,),
        )
        return [dict(r) for r in rows.fetchall()]


RADAR_METRICS = [
    "return_on_equity_pct", "return_on_capital_employed_pct", "debt_to_equity",
    "revenue_cagr_5yr", "operating_profit_margin_pct", "pat_cagr_5yr",
    "net_profit_margin_pct", "asset_turnover",
]


def get_peer_radar(ticker: str) -> dict | None:
    """Radar data: company values + peer group avg + benchmark company. None if no peer group assigned."""
    with get_connection() as conn:
        pg_row = conn.execute(
            "SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (ticker,)
        ).fetchone()
        if pg_row is None:
            return None
        peer_group_name = pg_row["peer_group_name"]

        member_ids = [
            r[0] for r in conn.execute(
                "SELECT company_id FROM peer_groups WHERE peer_group_name = ?", (peer_group_name,)
            ).fetchall()
        ]
        benchmark_row = conn.execute(
            "SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1",
            (peer_group_name,),
        ).fetchone()

        own = _latest_row("financial_ratios", ticker, conn=conn)
        own_vals = {m: (own.get(m) if own else None) for m in RADAR_METRICS}

        sums = {m: [] for m in RADAR_METRICS}
        for cid in member_ids:
            fr = _latest_row("financial_ratios", cid, conn=conn)
            if fr:
                for m in RADAR_METRICS:
                    if fr.get(m) is not None:
                        sums[m].append(fr[m])
        peer_avg = {m: (sum(v) / len(v) if v else None) for m, v in sums.items()}

        benchmark_name, benchmark_vals = None, None
        if benchmark_row:
            bcid = benchmark_row["company_id"]
            b_fr = _latest_row("financial_ratios", bcid, conn=conn)
            benchmark_vals = {m: (b_fr.get(m) if b_fr else None) for m in RADAR_METRICS}
            name_row = conn.execute("SELECT company_name FROM companies WHERE id = ?", (bcid,)).fetchone()
            benchmark_name = name_row["company_name"] if name_row else None

    return {
        "ticker": ticker,
        "peer_group": peer_group_name,
        "company_values": own_vals,
        "peer_group_avg": peer_avg,
        "benchmark_company": benchmark_name,
        "benchmark_values": benchmark_vals,
    }


def get_market_cap_history(ticker: str) -> list[dict]:
    """market_cap rows for a ticker, restricted to years 2019-2024."""
    with get_connection() as conn:
        rows = [
            dict(r) for r in conn.execute(
                "SELECT * FROM market_cap WHERE company_id = ?", (ticker,)
            ).fetchall()
        ]
    rows = _rows_with_normalized_year(rows)
    rows = [
        r for r in rows
        if r["normalized_year"] != "PARSE_ERROR" and "2019-01" <= r["normalized_year"] <= "2024-12"
    ]
    return rows


PORTFOLIO_FR_METRICS = [
    "return_on_equity_pct", "return_on_capital_employed_pct", "debt_to_equity",
    "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct", "net_profit_margin_pct",
]
PORTFOLIO_MC_METRICS = ["pe_ratio", "pb_ratio", "ev_ebitda"]


def get_portfolio_stats() -> dict:
    """P10-P90 percentile table for 10 core KPIs across all companies."""
    with get_connection() as conn:
        ids = [r[0] for r in conn.execute("SELECT id FROM companies").fetchall()]
        result = {}
        for m in PORTFOLIO_FR_METRICS:
            vals = []
            for cid in ids:
                fr = _latest_row("financial_ratios", cid, conn=conn)
                if fr and fr.get(m) is not None:
                    vals.append(fr[m])
            result[m] = _percentiles(vals)
        for m in PORTFOLIO_MC_METRICS:
            vals = []
            for cid in ids:
                mc = _latest_row("market_cap", cid, conn=conn)
                if mc and mc.get(m) is not None:
                    vals.append(mc[m])
            result[m] = _percentiles(vals)
    return result


def get_company_documents(ticker: str) -> list[dict]:
    """Annual report links for a company with a computed is_url_valid flag."""
    with get_connection() as conn:
        rows = [
            dict(r) for r in conn.execute(
                "SELECT * FROM documents WHERE company_id = ?", (ticker,)
            ).fetchall()
        ]
    for r in rows:
        url = r.get("Annual_Report")
        r["is_url_valid"] = bool(url and isinstance(url, str) and url.strip().lower().startswith("http"))
    return rows