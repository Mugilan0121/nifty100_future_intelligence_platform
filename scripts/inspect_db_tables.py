"""
Lists every table in nifty100.db and inspects any table that looks like
it holds the raw 'analysis' text fields (compounded_sales_growth,
compounded_profit_growth, stock_price_cagr, roe, etc.) referenced in the
Sprint 5 spec for src/nlp/parser.py.
"""
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"

if not DB_PATH.exists():
    print(f"DB not found at {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)

print("=== All tables in nifty100.db ===")
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
)
print(tables["name"].tolist())

target_words = ["analysis", "growth", "cagr", "compound"]

print("\n=== Tables matching analysis-related keywords ===")
for t in tables["name"]:
    if any(w in t.lower() for w in target_words):
        print(f"\n--- {t} ---")
        cols = pd.read_sql_query(f"PRAGMA table_info({t})", conn)
        print(cols[["name", "type"]].to_string(index=False))
        sample = pd.read_sql_query(f"SELECT * FROM {t} LIMIT 3", conn)
        print(sample.to_string())

print("\n=== Column-level search: any table with a column matching target fields ===")
target_fields = ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]
for t in tables["name"]:
    cols = pd.read_sql_query(f"PRAGMA table_info({t})", conn)
    col_names = cols["name"].tolist()
    matches = [c for c in col_names if any(tf in c.lower() for tf in target_fields)]
    if matches:
        print(f"{t}: {matches}")

conn.close()