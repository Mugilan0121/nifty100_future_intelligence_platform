import sqlite3

conn = sqlite3.connect("nifty100.db")

tables = [
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

for table in tables:
    print(f"\n{table}")
    fks = conn.execute(
        f"PRAGMA foreign_key_list({table})"
    ).fetchall()

    for fk in fks:
        print(fk)

conn.close()