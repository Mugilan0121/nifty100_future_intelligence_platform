"""
One-time (re-runnable) backfill: computes composite_quality_score and
sector_relative_score for every row in financial_ratios and writes them
back to the table.

Run after any change to ratio data or to COMPOSITE_WEIGHTS in screener/engine.py:
    python src/analytics/backfill_composite_score.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from screener.engine import (
    load_financial_ratios,
    calculate_composite_score,
    calculate_sector_relative_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"


def add_score_columns_if_missing(conn: sqlite3.Connection) -> None:
    """Adds composite_quality_score and sector_relative_score columns to financial_ratios if missing."""
    existing_cols = [
        row[1] for row in conn.execute("PRAGMA table_info(financial_ratios)").fetchall()
    ]
    if "composite_quality_score" not in existing_cols:
        conn.execute("ALTER TABLE financial_ratios ADD COLUMN composite_quality_score REAL")
    if "sector_relative_score" not in existing_cols:
        conn.execute("ALTER TABLE financial_ratios ADD COLUMN sector_relative_score REAL")


def backfill() -> None:
    """Backfills composite quality scores into financial_ratios for all companies."""
    df = load_financial_ratios()
    df = calculate_composite_score(df)
    df = calculate_sector_relative_score(df)

    with sqlite3.connect(DATABASE_PATH) as conn:
        add_score_columns_if_missing(conn)

        rows_updated = 0
        for _, row in df.iterrows():
            conn.execute(
                """
                UPDATE financial_ratios
                SET composite_quality_score = ?,
                    sector_relative_score = ?
                WHERE company_id = ? AND year = ?
                """,
                (
                    row["composite_quality_score"],
                    row["sector_relative_score"],
                    row["company_id"],
                    row["year"],
                ),
            )
            rows_updated += 1

        conn.commit()

    print(f"Backfilled composite_quality_score for {rows_updated} company-year rows.")


if __name__ == "__main__":
    backfill()