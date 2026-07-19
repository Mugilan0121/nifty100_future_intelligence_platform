import sqlite3
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"

conn = sqlite3.connect(DB_PATH)

for ticker in ["BEL", "HAL"]:
    print(f"\n=== {ticker}: financial_ratios (all years) ===")
    df = pd.read_sql_query(
        "SELECT year, return_on_equity_pct, return_on_capital_employed_pct, "
        "net_profit_margin_pct, book_value_per_share, earnings_per_share "
        "FROM financial_ratios WHERE company_id = ? ORDER BY year",
        conn, params=[ticker],
    )
    print(df.to_string(index=False))

    print(f"\n=== {ticker}: companies table roe/roce reference ===")
    ref = pd.read_sql_query(
        "SELECT roe_percentage, roce_percentage, book_value FROM companies WHERE id = ?",
        conn, params=[ticker],
    )
    print(ref.to_string(index=False))

conn.close()