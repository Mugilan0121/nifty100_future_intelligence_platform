from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

candidates = [
    PROJECT_ROOT / "data" / "raw" / "companies.xlsx",
    PROJECT_ROOT / "data" / "companies.xlsx",
]

for path in candidates:
    if path.exists():
        df = pd.read_excel(path)
        print(f"{path}: {len(df)} rows")
        id_col = next((c for c in df.columns if c.lower() in ("id", "company_id", "ticker")), df.columns[0])
        print(f"Using column: {id_col}")
        sorted_ids = sorted(df[id_col].dropna().astype(str).tolist())
        print(f"First 5 (alphabetical): {sorted_ids[:5]}")
        print(f"Last 10 (alphabetical): {sorted_ids[-10:]}")
        break
else:
    print("companies.xlsx not found in expected locations — check data/raw/ manually")