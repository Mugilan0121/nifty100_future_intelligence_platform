import sqlite3

conn = sqlite3.connect("nifty100.db")
cursor = conn.cursor()

tables = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
]

for table in tables:
    print("\n" + "=" * 60)
    print(table.upper())
    print("=" * 60)

    cursor.execute(f"PRAGMA table_info({table})")

    for row in cursor.fetchall():
        print(row)

conn.close()