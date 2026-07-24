import sqlite3

conn = sqlite3.connect('nifty100.db')

tables_to_check = [
    "companies","stock_prices"
]

for t in tables_to_check:
    print(f"\nCOLUMNS in {t}:")
    for r in conn.execute(f"PRAGMA table_info({t})").fetchall():
        print(" -", r[1])

print("\nEXISTING INDEXES:")
for r in conn.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'").fetchall():
    print(" -", r[0], "on", r[1])