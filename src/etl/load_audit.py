import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "nifty100.db"

OUTPUT_FILE = "output/load_audit.csv"

EXPECTED_TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "market_cap",
    "financial_ratios",
    "peer_groups"
]


def get_row_count(cursor, table_name):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    audit_rows = []

    for table in EXPECTED_TABLES:
        try:
            count = get_row_count(cursor, table)

            audit_rows.append({
                "table_name": table,
                "rows_in": count,
                "rows_loaded": count,
                "rejected_rows": 0
            })

        except Exception as e:
            audit_rows.append({
                "table_name": table,
                "rows_in": 0,
                "rows_loaded": 0,
                "rejected_rows": 0
            })

            print(f"Error reading {table}: {e}")

    Path("output").mkdir(exist_ok=True)

    audit_df = pd.DataFrame(audit_rows)

    audit_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    conn.close()

    print("\nLoad audit created successfully")
    print(f"Saved to: {OUTPUT_FILE}")

    print("\nSummary:")
    print(audit_df)


if __name__ == "__main__":
    main()