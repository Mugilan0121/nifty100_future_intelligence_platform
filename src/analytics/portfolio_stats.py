"""
Portfolio Percentile Statistics.

Sprint 6 - Day 37

Computes P10, P25, P50, P75, P90, Mean, and Std for each of the 10
core KPIs across all 92 companies' latest year and saves
output/portfolio_stats.csv. Reused as-is by the Day 40
GET /api/v1/portfolio/stats endpoint.
"""

import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output" / "portfolio_stats.csv"

PERCENTILES = [0.10, 0.25, 0.50, 0.75, 0.90]
PERCENTILE_LABELS = ["P10", "P25", "P50", "P75", "P90"]

# Same 10 KPIs as peer.py's RANKING_METRICS / Day 37 correlation heatmap
# and outlier report, kept consistent across the project.
KPIS = [
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to the project database."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")
    return sqlite3.connect(DATABASE_PATH)


def load_latest_kpis() -> pd.DataFrame:
    """
    Load the latest-year row per company for the 10 core KPIs.
    """
    columns = ", ".join(KPIS)

    with get_connection() as conn:
        df = pd.read_sql_query(
            f"SELECT company_id, year, {columns} FROM financial_ratios",
            conn,
        )

    df = df.drop_duplicates()

    df = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return df


def apply_roe_sanity_guard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Day 34 guard: financial_ratios ROE/ROCE is corrupted for BEL and HAL.
    Excluded from the percentile stats so the market-wide P90/Mean isn't
    skewed by a known data-entry bug rather than genuine performance.
    """
    guarded = df.copy()
    for col in ("return_on_equity_pct", "return_on_capital_employed_pct"):
        if col in guarded.columns:
            bad = guarded[col].abs() > 200
            if bad.any():
                print(
                    f"ROE sanity guard: {bad.sum()} row(s) in {col} "
                    f"beyond +-200% ({guarded.loc[bad, 'company_id'].tolist()}) "
                    "set to NaN."
                )
                guarded.loc[bad, col] = None
    return guarded


def compute_portfolio_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute P10-P90, Mean, and Std for each KPI, ignoring NaNs.
    """
    rows = []

    for kpi in KPIS:
        series = df[kpi].dropna()

        row = {"metric": kpi, "n": len(series)}

        for label, pct in zip(PERCENTILE_LABELS, PERCENTILES):
            row[label] = round(series.quantile(pct), 2)

        row["Mean"] = round(series.mean(), 2)
        row["Std"] = round(series.std(), 2)

        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    """Computes portfolio-wide percentile statistics and writes portfolio_stats.csv."""
    df = load_latest_kpis()
    df = apply_roe_sanity_guard(df)

    print(f"Computing portfolio stats across {len(df)} companies' latest year.")

    stats_df = compute_portfolio_stats(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(stats_df)} KPI rows -> {OUTPUT_PATH}")
    print(stats_df.to_string(index=False))


if __name__ == "__main__":
    main()