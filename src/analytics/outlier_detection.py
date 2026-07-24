"""
Sector-Relative Outlier Detection.

Sprint 6 - Day 37

Computes a Z-score for each of the 10 core KPIs within each company's
broad_sector (not across the whole market, since a normal D/E for a
bank is an outlier for an FMCG company), and flags any company where
at least one metric has |Z| > 3 into output/outlier_report.csv.
"""

import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output" / "outlier_report.csv"

Z_THRESHOLD = 3.0

# Same 10 KPIs as peer.py's RANKING_METRICS / Day 37 correlation heatmap,
# kept consistent across the project's cross-sectional analyses.
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


def load_latest_kpis_with_sector() -> pd.DataFrame:
    """
    Load the latest-year row per company for the 10 core KPIs, joined
    with broad_sector.
    """
    columns = ", ".join(f"fr.{col}" for col in KPIS)

    with get_connection() as conn:
        df = pd.read_sql_query(
            f"""
            SELECT
                fr.company_id,
                fr.year,
                {columns},
                s.broad_sector
            FROM financial_ratios fr
            LEFT JOIN sectors s
            ON fr.company_id = s.company_id
            """,
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
    (thousands of percent). Excluding these from the Z-score calculation
    itself would be circular (that's exactly the kind of value Z-scores
    exist to catch) - but since the root cause is a known data-entry bug
    rather than a genuine outlier company, they're set to NaN here to
    avoid also dragging the whole sector's std up and masking other,
    real outliers in the same sector.
    """
    guarded = df.copy()
    for col in ("return_on_equity_pct", "return_on_capital_employed_pct"):
        if col in guarded.columns:
            bad = guarded[col].abs() > 200
            if bad.any():
                print(
                    f"ROE sanity guard: {bad.sum()} row(s) in {col} "
                    f"beyond +-200% ({guarded.loc[bad, 'company_id'].tolist()}) "
                    "set to NaN (known Day 34 data bug, not a genuine outlier)."
                )
                guarded.loc[bad, col] = None
    return guarded


def compute_sector_zscores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a Z-score for each KPI within each company's broad_sector.
    Sectors with only 1 company (zero std) yield NaN Z-scores rather
    than dividing by zero.
    """
    z_df = df.copy()

    for kpi in KPIS:
        z_col = f"{kpi}_zscore"
        z_df[z_col] = (
            df.groupby("broad_sector")[kpi]
            .transform(lambda x: (x - x.mean()) / x.std(ddof=0) if x.std(ddof=0) else pd.NA)
        )

    return z_df


def flag_outliers(z_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each company, find every KPI where |Z| > 3 and produce one row
    per (company, metric, z-score) flagged pair.
    """
    rows = []

    for _, row in z_df.iterrows():
        for kpi in KPIS:
            z_val = row.get(f"{kpi}_zscore")
            if pd.notna(z_val) and abs(z_val) > Z_THRESHOLD:
                rows.append({
                    "company_id": row["company_id"],
                    "broad_sector": row["broad_sector"],
                    "metric": kpi,
                    "value": row[kpi],
                    "zscore": round(float(z_val), 2),
                })

    return pd.DataFrame(rows)


def main() -> None:
    """Runs Z-score outlier detection across all KPIs and writes outlier_report.csv."""
    df = load_latest_kpis_with_sector()
    df = apply_roe_sanity_guard(df)

    missing_sector = df["broad_sector"].isna().sum()
    if missing_sector:
        print(
            f"Warning: {missing_sector} companies have no broad_sector "
            "match (known scope gap - see Day 32 note) and were excluded "
            "from sector Z-scoring."
        )
        df = df.dropna(subset=["broad_sector"])

    z_df = compute_sector_zscores(df)
    outliers = flag_outliers(z_df)

    outliers = outliers.sort_values(
        by="zscore", key=lambda s: s.abs(), ascending=False
    ).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    outliers.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(outliers)} outlier flags -> {OUTPUT_PATH}")
    print(f"Companies flagged: {outliers['company_id'].nunique()}")


if __name__ == "__main__":
    main()