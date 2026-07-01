import sqlite3
import pandas as pd

conn = sqlite3.connect("nifty100.db")

companies = [
    "ABB",
    "ASIANPAINT",
    "BHARTIARTL",
]

for company in companies:
    print("=" * 70)
    print(company)
    print("=" * 70)

    df = pd.read_sql(
        f"""
        SELECT *
        FROM financial_ratios
        WHERE company_id = '{company}'
        ORDER BY year
        """,
        conn,
    )

    print(
        df[
            [
                "company_id",
                "year",
                "return_on_equity_pct",
                "revenue_cagr_5yr",
            ]
        ]
    )

conn.close()