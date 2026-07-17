"""
Pre-Day-31 check: look for existing Sprint 2 cash flow / capital allocation
code (Day 11 built FCF calc + 8-pattern classifier already) and inspect
output/capital_allocation.csv, so Day 31's cashflow_kpis.py reuses rather
than duplicates or conflicts with that work.
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

print("=== Files in src/analytics/ ===")
analytics_dir = PROJECT_ROOT / "src" / "analytics"
if analytics_dir.exists():
    for f in sorted(analytics_dir.glob("*.py")):
        print(f" - {f.name}")
else:
    print("src/analytics/ not found")

print("\n=== output/capital_allocation.csv ===")
cap_alloc_path = PROJECT_ROOT / "output" / "capital_allocation.csv"
if cap_alloc_path.exists():
    df = pd.read_csv(cap_alloc_path)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 5 rows:")
    print(df.head(5).to_string())
    if "company_id" in df.columns:
        print(f"\nUnique companies: {df['company_id'].nunique()}")
else:
    print("Not found at expected path.")