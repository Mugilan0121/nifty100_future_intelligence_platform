import sqlite3

conn = sqlite3.connect('nifty100.db')

tables_to_check = [
    "companies","stock_prices"
]

for t in tables_to_check:
    print(f"\nCOLUMNS in {t}:")
    for r in conn.execute(f"PRAGMA table_info({t})").fetchall():
        print(" -", r[1])