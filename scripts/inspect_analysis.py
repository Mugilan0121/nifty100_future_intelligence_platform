"""
Quick inspection of analysis.xlsx before building src/nlp/parser.py.
Run once, paste the output back so the parser targets real column
names and real text formatting instead of guessed ones.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import pandas as pd

# Try a few likely locations
candidates = [
    PROJECT_ROOT / "data" / "analysis.xlsx",
    PROJECT_ROOT / "analysis.xlsx",
    PROJECT_ROOT / "output" / "analysis.xlsx",
]

path = next((p for p in candidates if p.exists()), None)

if path is None:
    print("Could not find analysis.xlsx in expected locations:")
    for p in candidates:
        print(f"  - {p}")
    print("\nSearching data/ and output/ for any .xlsx with 'analysis' in the name...")
    for folder in [PROJECT_ROOT / "data", PROJECT_ROOT / "output"]:
        if folder.exists():
            for f in folder.glob("*.xlsx"):
                if "analysis" in f.name.lower():
                    print(f"  found: {f}")
    sys.exit(1)

print(f"Reading: {path}\n")
df = pd.read_excel(path)

print("=== Columns ===")
print(list(df.columns))

print("\n=== Shape ===")
print(df.shape)

print("\n=== First 3 rows (all columns) ===")
print(df.head(3).to_string())

# Specifically look at the 4 target text fields, if present
target_fields = ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]
print("\n=== Sample text values for target fields ===")
for col in target_fields:
    matches = [c for c in df.columns if col.lower() in c.lower().replace(" ", "_")]
    if matches:
        real_col = matches[0]
        print(f"\n-- {real_col} --")
        print(df[real_col].dropna().head(5).tolist())
    else:
        print(f"\n-- {col}: NOT FOUND (closest columns: {[c for c in df.columns if any(w in c.lower() for w in col.split('_'))]}) --")  