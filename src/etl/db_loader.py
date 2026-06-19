import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "nifty100.db"

FILES = {
    "companies": "data/raw/companies.xlsx",
    "profitandloss": "data/raw/profitandloss.xlsx",
    "balancesheet": "data/raw/balancesheet.xlsx",
    "cashflow": "data/raw/cashflow.xlsx",
    "analysis": "data/raw/analysis.xlsx",
    "documents": "data/raw/documents.xlsx",
    "prosandcons": "data/raw/prosandcons.xlsx",
    "sectors": "data/supporting/sectors.xlsx",
    "stock_prices": "data/supporting/stock_prices.xlsx",
    "market_cap": "data/supporting/market_cap.xlsx",
    "financial_ratios": "data/supporting/financial_ratios.xlsx",
    "peer_groups": "data/supporting/peer_groups.xlsx"
}

RAW_TABLES = {
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons"
}

conn = sqlite3.connect(DB_PATH)

for table_name, file_path in FILES.items():

    print(f"\nLoading {table_name}...")

    try:
        path = Path(file_path)

        if not path.exists():
            print(f"FILE NOT FOUND: {file_path}")
            continue

        # Raw files contain a metadata row
        if table_name in RAW_TABLES:
            df = pd.read_excel(path, header=1)
        else:
            df = pd.read_excel(path)

        print(f"Rows found: {len(df)}")

        df.to_sql(
    table_name,
    conn,
    if_exists="fail",
    index=False
)

        print(f"Loaded successfully into {table_name}")

    except Exception as e:
        print(f"ERROR IN TABLE: {table_name}")
        print(str(e))

conn.commit()
conn.close()

print("\nDatabase loading completed.")