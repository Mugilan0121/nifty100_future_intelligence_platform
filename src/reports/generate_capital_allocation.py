"""
Generate capital allocation pattern CSV.

Day 11 Deliverable
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.analytics.cashflow_kpis import capital_allocation_pattern

DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output" / "capital_allocation.csv"


def get_sign(value: float) -> str:
    """Return sign symbol for a cash flow value."""
    return "+" if value >= 0 else "-"


def main():
    """Generate capital allocation CSV."""

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        company_id,
        year,
        operating_activity,
        investing_activity,
        financing_activity
    FROM cashflow
    ORDER BY company_id, year
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["cfo_sign"] = df["operating_activity"].apply(get_sign)
    df["cfi_sign"] = df["investing_activity"].apply(get_sign)
    df["cff_sign"] = df["financing_activity"].apply(get_sign)

    df["pattern_label"] = df.apply(
        lambda row: capital_allocation_pattern(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"],
        ),
        axis=1,
    )

    output = df[
        [
            "company_id",
            "year",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ]
    ]

    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    output.to_csv(OUTPUT_PATH, index=False)

    print(f"Generated: {OUTPUT_PATH}")
    print(f"Rows exported: {len(output)}")


if __name__ == "__main__":
    main()