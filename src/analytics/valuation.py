"""
Valuation & Market Data Module

Sprint 4 - Day 26

Computes FCF yield, 5-year median P/E, and sector-relative
overvaluation flags for all companies. Reads from nifty100.db,
writes to output/valuation_summary.xlsx and output/valuation_flags.csv.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_SUMMARY_PATH = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
OUTPUT_FLAGS_PATH = PROJECT_ROOT / "output" / "valuation_flags.csv"

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------

def load_valuation_inputs() -> pd.DataFrame:
    """
    Load market_cap history joined with company, sector, and latest FCF data.
    Returns one row per company-year (needed for 5yr median P/E calc).
    """
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    query = """
        SELECT
            mc.company_id,
            mc.year,
            mc.market_cap_crore,
            mc.enterprise_value_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct,
            c.company_name,
            s.broad_sector
        FROM market_cap mc
        LEFT JOIN companies c ON mc.company_id = c.id
        LEFT JOIN sectors s ON mc.company_id = s.company_id
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        df = pd.read_sql_query(query, conn)

    logger.info("Loaded %d market_cap company-year rows.", len(df))
    return df


def load_latest_fcf() -> pd.DataFrame:
    """Latest-year Free Cash Flow per company, from financial_ratios."""
    query = """
        SELECT company_id, year, free_cash_flow_cr
        FROM financial_ratios
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        df = pd.read_sql_query(query, conn)

    df = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    return df[["company_id", "free_cash_flow_cr"]]


# ---------------------------------------------------------------------
# Valuation Calculations
# ---------------------------------------------------------------------

def compute_5yr_median_pe(df: pd.DataFrame) -> pd.DataFrame:
    """Median P/E per company across all available years (up to 5yr window)."""
    median_pe = (
        df.groupby("company_id")["pe_ratio"]
        .median()
        .reset_index()
        .rename(columns={"pe_ratio": "median_pe_5yr"})
    )
    return median_pe


def compute_sector_median_pe(latest_df: pd.DataFrame) -> pd.DataFrame:
    """Sector median P/E using each company's latest year."""
    sector_median = (
        latest_df.groupby("broad_sector")["pe_ratio"]
        .median()
        .reset_index()
        .rename(columns={"pe_ratio": "sector_median_pe"})
    )
    return sector_median


def apply_overvaluation_flag(row: pd.Series) -> str:
    """
    Flag logic per spec:
      P/E > sector_median * 1.5 -> Caution
      P/E < sector_median * 0.7 -> Discount
      otherwise -> Fair
    """
    pe = row["pe_ratio"]
    sector_median = row["sector_median_pe"]

    if pd.isna(pe) or pd.isna(sector_median) or sector_median == 0:
        return "N/A"
    if pe > sector_median * 1.5:
        return "Caution"
    if pe < sector_median * 0.7:
        return "Discount"
    return "Fair"


def build_valuation_summary() -> pd.DataFrame:
    """Builds the full valuation table: one row per company, latest year."""

    history_df = load_valuation_inputs()
    fcf_df = load_latest_fcf()

    # Latest year per company
    latest_df = (
        history_df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    # 5yr median P/E (across all available years per company)
    median_pe_df = compute_5yr_median_pe(history_df)

    # Sector median P/E (based on latest year only)
    sector_median_df = compute_sector_median_pe(latest_df)

    summary = latest_df.merge(median_pe_df, on="company_id", how="left")
    summary = summary.merge(sector_median_df, on="broad_sector", how="left")
    summary = summary.merge(fcf_df, on="company_id", how="left")

    # FCF Yield = FCF / Market Cap * 100
    summary["fcf_yield_pct"] = (
        summary["free_cash_flow_cr"] / summary["market_cap_crore"] * 100
    )

    # PE vs sector median, as a percentage difference
    summary["pe_vs_sector_median_pct"] = (
        (summary["pe_ratio"] - summary["sector_median_pe"])
        / summary["sector_median_pe"]
        * 100
    )

    # Overvaluation flag
    summary["flag"] = summary.apply(apply_overvaluation_flag, axis=1)

    summary = summary.rename(columns={
        "broad_sector": "sector",
        "pe_ratio": "pe",
        "pb_ratio": "pb",
        "ev_ebitda": "ev_ebitda",
        "median_pe_5yr": "5yr_median_pe",
    })

    output_columns = [
        "company_id", "company_name", "sector",
        "pe", "pb", "ev_ebitda",
        "fcf_yield_pct", "5yr_median_pe",
        "pe_vs_sector_median_pct", "flag",
    ]
    summary = summary[[c for c in output_columns if c in summary.columns]]

    logger.info("Built valuation summary for %d companies.", len(summary))
    return summary


# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------

def export_valuation_summary(summary: pd.DataFrame) -> None:
    OUTPUT_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_excel(OUTPUT_SUMMARY_PATH, index=False)
    logger.info("Exported valuation summary: %s", OUTPUT_SUMMARY_PATH)


def export_valuation_flags(summary: pd.DataFrame) -> None:
    flagged = summary[summary["flag"].isin(["Caution", "Discount"])].copy()
    flagged = flagged.sort_values("pe_vs_sector_median_pct", ascending=False)
    OUTPUT_FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    flagged.to_csv(OUTPUT_FLAGS_PATH, index=False)
    logger.info(
        "Exported %d flagged companies to: %s", len(flagged), OUTPUT_FLAGS_PATH
    )


# ---------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------

if __name__ == "__main__":
    summary_df = build_valuation_summary()
    export_valuation_summary(summary_df)
    export_valuation_flags(summary_df)

    print(f"\nValuation summary: {len(summary_df)} companies")
    print(summary_df["flag"].value_counts())
    print("\nSample:")
    print(summary_df.head(10))