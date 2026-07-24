"""
Day 29 — NLP: Analysis Text Parser

Parses the 4 text fields in the `analysis` table (compounded_sales_growth,
compounded_profit_growth, stock_price_cagr, roe) using regex, extracting
(period_years, value_pct) from strings like "10 Years: 21%".

The `analysis` table has one row per (company, period) — e.g. company
HDFCBANK has separate rows for its 10yr, 5yr, and 3yr figures, and all
4 metric columns in a given row share that row's period.

Outputs:
    output/analysis_parsed.csv  — company_id, metric_type, period_years, value_pct
    output/parse_failures.csv   — company_id, metric_type, raw_text (rows that didn't match the regex)
    output/cagr_divergence.csv  — 5yr parsed sales/profit growth vs computed
                                   revenue_cagr_5yr/pat_cagr_5yr, flagged where |diff| > 5pp
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

METRIC_COLS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]

# Period + value, e.g. "10 Years: 21%" or "5 Years 14%" (colon optional)
PATTERN = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)\s*%")


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to the project database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def parse_period_value(text):
    """Returns (period_years, value_pct) or None if the text doesn't match."""
    if not isinstance(text, str) or not text.strip():
        return None
    match = PATTERN.search(text)
    if not match:
        return None
    period_years = int(match.group(1))
    value_pct = float(match.group(2))
    return period_years, value_pct


def parse_analysis_table(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (parsed_rows_df, failures_df)."""
    parsed_rows = []
    failures = []

    for _, row in df.iterrows():
        company_id = row["company_id"]
        for metric_col in METRIC_COLS:
            raw_text = row.get(metric_col)
            result = parse_period_value(raw_text)
            if result is None:
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_col,
                        "raw_text": raw_text,
                    }
                )
                continue
            period_years, value_pct = result
            parsed_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_col,
                    "period_years": period_years,
                    "value_pct": value_pct,
                }
            )

    return pd.DataFrame(parsed_rows), pd.DataFrame(failures)


def cross_validate_cagr(parsed_df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Compares 5-year parsed compounded_sales_growth / compounded_profit_growth
    against the computed revenue_cagr_5yr / pat_cagr_5yr in financial_ratios
    (latest year per company). Flags |diff| > 5 percentage points.
    """
    ratios = pd.read_sql_query(
        "SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios",
        conn,
    )
    if ratios.empty:
        return pd.DataFrame()

    latest_ratios = (
        ratios.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    five_yr = parsed_df[parsed_df["period_years"] == 5]

    sales_5yr = five_yr[five_yr["metric_type"] == "compounded_sales_growth"][
        ["company_id", "value_pct"]
    ].rename(columns={"value_pct": "parsed_sales_growth_5yr"})

    profit_5yr = five_yr[five_yr["metric_type"] == "compounded_profit_growth"][
        ["company_id", "value_pct"]
    ].rename(columns={"value_pct": "parsed_profit_growth_5yr"})

    merged = latest_ratios.merge(sales_5yr, on="company_id", how="inner").merge(
        profit_5yr, on="company_id", how="inner"
    )

    merged["sales_diff_pp"] = (
        merged["parsed_sales_growth_5yr"] - merged["revenue_cagr_5yr"]
    ).abs()
    merged["profit_diff_pp"] = (
        merged["parsed_profit_growth_5yr"] - merged["pat_cagr_5yr"]
    ).abs()

    merged["sales_flag"] = merged["sales_diff_pp"] > 5
    merged["profit_flag"] = merged["profit_diff_pp"] > 5

    flagged = merged[merged["sales_flag"] | merged["profit_flag"]].copy()
    return flagged[
        [
            "company_id",
            "parsed_sales_growth_5yr",
            "revenue_cagr_5yr",
            "sales_diff_pp",
            "sales_flag",
            "parsed_profit_growth_5yr",
            "pat_cagr_5yr",
            "profit_diff_pp",
            "profit_flag",
        ]
    ]


def main():
    """Runs the NLP regex parser against company data and writes parsed output."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    conn = get_connection()

    df = pd.read_sql_query("SELECT * FROM analysis", conn)
    print(f"Loaded {len(df)} rows from analysis table.")

    parsed_df, failures_df = parse_analysis_table(df)

    parsed_path = OUTPUT_DIR / "analysis_parsed.csv"
    parsed_df.to_csv(parsed_path, index=False)
    print(f"Wrote {len(parsed_df)} parsed rows -> {parsed_path}")

    failures_path = OUTPUT_DIR / "parse_failures.csv"
    failures_df.to_csv(failures_path, index=False)
    print(f"Wrote {len(failures_df)} parse failures -> {failures_path}")
    if not failures_df.empty:
        print("\nParse failures (review these — regex may need a tweak, or data is genuinely dirty):")
        print(failures_df.to_string(index=False))

    divergence_df = cross_validate_cagr(parsed_df, conn)
    divergence_path = OUTPUT_DIR / "cagr_divergence.csv"
    divergence_df.to_csv(divergence_path, index=False)
    print(f"\nWrote {len(divergence_df)} CAGR divergence flags (>5pp) -> {divergence_path}")
    if not divergence_df.empty:
        print(divergence_df.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()