"""
Checks whether pat_cagr_5yr / pe_ratio / etc. are null ONLY for the
latest year (expected — trailing calcs need history) or null across
ALL years for a ticker (a real bug).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "dashboard"))

from utils import db  # noqa: E402

cols = ["year", "pat_cagr_5yr", "revenue_cagr_5yr", "eps_cagr_5yr",
        "pe_ratio", "pb_ratio", "ev_ebitda"]

for ticker in ["AXISBANK", "CIPLA", "ADANIPOWER"]:
    print(f"\n--- {ticker}: all years ---")
    df = db.get_ratios(ticker)
    df = df.sort_values("year")
    print(df[cols].to_string(index=False))