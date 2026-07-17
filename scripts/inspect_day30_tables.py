"""
Inspects financial_ratios, balancesheet, and cashflow table columns
before writing src/nlp/pros_cons_generator.py (Day 30), so the 24 rules
reference real column names instead of guessed ones.
"""
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"

conn = sqlite3.connect(DB_PATH)

TABLES = ["financial_ratios", "balancesheet", "cashflow", "companies", "profitandloss"]

for t in TABLES:
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}")
    cols = pd.read_sql_query(f"PRAGMA table_info({t})", conn)
    print(cols[["name", "type"]].to_string(index=False))
    sample = pd.read_sql_query(f"SELECT * FROM {t} LIMIT 2", conn)
    print("\nSample row:")
    print(sample.to_string())

conn.close()