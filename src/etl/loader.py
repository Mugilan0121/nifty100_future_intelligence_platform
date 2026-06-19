"""
Excel loading utilities for ETL pipeline.
"""

from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker
from src.etl.normaliser import normalize_year


CORE_FILES = {
    "companies.xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx",
}


def load_excel(path: str | Path) -> pd.DataFrame:
    """Load Excel file using correct header row."""

    path = Path(path)

    header_row = 1 if path.name in CORE_FILES else 0

    df = pd.read_excel(path, header=header_row)

    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)

    if "id" in df.columns and path.name == "companies.xlsx":
        df["id"] = df["id"].apply(normalize_ticker)

    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    return df


def load_companies(path: str | Path) -> pd.DataFrame:
    """Load companies dataset."""
    return load_excel(path)


def load_profitandloss(path: str | Path) -> pd.DataFrame:
    """Load profit and loss dataset."""
    return load_excel(path)


def load_balancesheet(path: str | Path) -> pd.DataFrame:
    """Load balance sheet dataset."""
    return load_excel(path)


def load_cashflow(path: str | Path) -> pd.DataFrame:
    """Load cashflow dataset."""
    return load_excel(path)