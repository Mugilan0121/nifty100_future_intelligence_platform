"""
Correlation Matrix Heatmap.

Sprint 6 - Day 37

Computes the Pearson correlation of the 10 core KPIs (same list used
by src/analytics/peer.py's RANKING_METRICS, for consistency across the
project) across all 92 companies' latest year, and saves an annotated
seaborn heatmap to reports/correlation_heatmap.png.
"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "correlation_heatmap.png"

# Same 10 KPIs as peer.py's RANKING_METRICS, kept consistent across
# the project's correlation, outlier, and portfolio-stats outputs.
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

KPI_LABELS = {
    "return_on_equity_pct": "ROE %",
    "return_on_capital_employed_pct": "ROCE %",
    "net_profit_margin_pct": "NPM %",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "eps_cagr_5yr": "EPS CAGR 5Y",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover",
}


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
    Day 34 guard: financial_ratios ROE/ROCE is corrupted for BEL and HAL
    (thousands of percent). Treat values beyond +-200% as NaN so they
    don't distort the correlation matrix, mirroring tearsheet.py and
    sector_report.py's existing display-layer guard.
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


def main() -> None:
    """Generates the KPI correlation heatmap and saves it to reports/."""
    df = load_latest_kpis()
    df = apply_roe_sanity_guard(df)

    print(f"Computing correlation across {len(df)} companies' latest year.")

    corr = df[KPIS].corr(method="pearson")
    corr = corr.rename(index=KPI_LABELS, columns=KPI_LABELS)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )
    plt.title("Pearson Correlation - 10 Core KPIs (Latest Year, 92 Companies)")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    plt.close()

    print(f"Wrote correlation heatmap -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()