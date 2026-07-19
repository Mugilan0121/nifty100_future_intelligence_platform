import sqlite3
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"

conn = sqlite3.connect(DB_PATH)

print("=== Distinct broad_sector values in sectors table ===")
df = pd.read_sql_query("SELECT broad_sector, COUNT(*) as company_count FROM sectors GROUP BY broad_sector ORDER BY broad_sector", conn)
print(df.to_string(index=False))
print(f"\nTotal distinct sectors: {len(df)}")

print("\n=== Companies with NULL/missing broad_sector ===")
null_sector = pd.read_sql_query(
    "SELECT c.id FROM companies c LEFT JOIN sectors s ON c.id = s.company_id WHERE s.broad_sector IS NULL", conn
)
print(null_sector.to_string(index=False) if not null_sector.empty else "(none)")

conn.close()