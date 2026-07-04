"""
Financial Screener Engine.

Sprint 3 - Day 15

Loads screener configuration and applies threshold filters
to the financial_ratios dataset.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd
import yaml


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

def load_screener_config() -> dict:
    """
    Load screener configuration from YAML file.
    """

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Screener configuration not found: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    logger.info("Loaded screener configuration.")

    return config

# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

def load_financial_ratios() -> pd.DataFrame:
    """
    Load the financial_ratios table from SQLite.
    """

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as conn:
        df = pd.read_sql_query(
    """
    SELECT
        fr.*,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category
    FROM financial_ratios fr
    LEFT JOIN sectors s
        ON fr.company_id = s.company_id
    """,
    conn,
)

    logger.info(
        "Loaded financial_ratios table (%d rows).",
        len(df),
    )

    return df

# ---------------------------------------------------------------------
# Filter Engine
# ---------------------------------------------------------------------

def apply_filters(
    df: pd.DataFrame,
    filters: dict,
) -> pd.DataFrame:
    """
    Apply threshold filters to a DataFrame.
    """

    filtered_df = df.copy()

    for column, limits in filters.items():

        if column not in filtered_df.columns:
            logger.warning(
                "Column '%s' not found. Skipping filter.",
                column,
            )
            continue

        if "min" in limits:
            filtered_df = filtered_df[
                filtered_df[column] >= limits["min"]
            ]

        if "max" in limits:
            filtered_df = filtered_df[
                filtered_df[column] <= limits["max"]
            ]

    logger.info(
        "Filtered dataframe contains %d rows.",
        len(filtered_df),
    )

    return filtered_df


def apply_de_filter(
    df: pd.DataFrame,
    max_de: float,
) -> pd.DataFrame:
    """
    Apply Debt-to-Equity filter while excluding Financial companies.
    """

    financial_df = df[
        df["broad_sector"] == "Financials"
    ]

    non_financial_df = df[
        df["broad_sector"] != "Financials"
    ]

    non_financial_df = non_financial_df[
        non_financial_df["debt_to_equity"] <= max_de
    ]

    filtered_df = pd.concat(
        [financial_df, non_financial_df],
        ignore_index=True,
    )

    logger.info(
        "Applied Debt-to-Equity filter excluding Financial sector."
    )

    return filtered_df

def apply_icr_filter(
    df: pd.DataFrame,
    min_icr: float,
) -> pd.DataFrame:
    """
    Apply Interest Coverage Ratio filter.

    Companies with missing Interest Coverage (Debt Free)
    automatically pass the filter.
    """

    filtered_df = df[
        (df["interest_coverage"].isna())
        | (df["interest_coverage"] >= min_icr)
    ]

    logger.info(
        "Applied Interest Coverage filter (Debt Free companies included)."
    )

    return filtered_df

# ---------------------------------------------------------------------
# Main Screener
# ---------------------------------------------------------------------

def run_custom_screen() -> pd.DataFrame:
    """
    Run the financial screener using the configured thresholds.
    """

    config = load_screener_config()

    df = load_financial_ratios()

    filters = config.get("filters", {}).copy()

    de_filter = filters.pop("debt_to_equity", None)
    icr_filter = filters.pop("interest_coverage", None)

    filtered_df = apply_filters(
        df=df,
        filters=filters,
    )

    # Apply Debt-to-Equity rule
    if de_filter and "max" in de_filter:
        filtered_df = apply_de_filter(
            filtered_df,
            de_filter["max"],
        )

    # Apply Interest Coverage rule
    if icr_filter and "min" in icr_filter:
        filtered_df = apply_icr_filter(
            filtered_df,
            icr_filter["min"],
        )

    filtered_df = filtered_df.sort_values(
        by="composite_quality_score",
        ascending=False,
    ).reset_index(
        drop=True,
    )

    logger.info(
        "Screening completed. %d companies matched.",
        len(filtered_df),
    )

    return filtered_df