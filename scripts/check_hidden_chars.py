import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"

suspects = ["ULTRACEMCO", "UNIONBANK", "UNITDSPR", "VBL", "VEDL", "WIPRO", "ZOMATO", "ZYDUSLIFE", "ATGL"]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=== companies.id — repr() to reveal hidden whitespace/newlines ===")
cur.execute("SELECT id FROM companies")
all_ids = [row[0] for row in cur.fetchall()]

for s in suspects:
    matches = [i for i in all_ids if s in i]
    for m in matches:
        flag = " <-- HAS HIDDEN CHARS" if m != s else ""
        print(f"  {s:12s} -> {repr(m)}{flag}")
    if not matches:
        print(f"  {s:12s} -> NOT FOUND in companies table at all")

conn.close()