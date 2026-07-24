"""
Day 34 — Batch Report Generation (Part 1: Tearsheets)

Runs tearsheet.build_tearsheet() for every company in the companies table,
skipping any with fewer than 3 years of financial_ratios history (handled
inside build_tearsheet itself), and logs skipped tickers.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from tearsheet import build_tearsheet, TEARSHEETS_DIR, get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


def main():
    """Generates a tearsheet PDF for every company in the database."""
    TEARSHEETS_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    companies = pd.read_sql_query("SELECT id AS company_id FROM companies ORDER BY id", conn)
    conn.close()

    generated = []
    skipped = []

    for ticker in companies["company_id"]:
        out_path = TEARSHEETS_DIR / f"{ticker}_tearsheet.pdf"
        try:
            ok = build_tearsheet(ticker, out_path)
        except Exception as e:
            print(f"[ERROR] {ticker}: {type(e).__name__}: {e}")
            skipped.append({"company_id": ticker, "reason": f"{type(e).__name__}: {e}"})
            continue

        if ok:
            size_kb = out_path.stat().st_size / 1024
            generated.append({"company_id": ticker, "size_kb": round(size_kb, 1)})
            print(f"[OK] {ticker} -> {out_path.name} ({size_kb:.1f} KB)")
        else:
            skipped.append({"company_id": ticker, "reason": "fewer than 3 years of financial_ratios data"})
            print(f"[SKIP] {ticker} — insufficient data")

    skipped_df = pd.DataFrame(skipped)
    skipped_path = OUTPUT_DIR / "skipped_tearsheets.csv"
    skipped_df.to_csv(skipped_path, index=False)

    print(f"\n{'=' * 60}")
    print(f"Generated: {len(generated)} / {len(companies)}")
    print(f"Skipped:   {len(skipped)} -> {skipped_path}")
    print(f"{'=' * 60}")

    if generated:
        sizes = [g["size_kb"] for g in generated]
        under_30kb = [g for g in generated if g["size_kb"] < 30]
        print(f"Size range: {min(sizes):.1f} - {max(sizes):.1f} KB")
        if under_30kb:
            print(f"\nWARNING: {len(under_30kb)} tearsheet(s) under the 30 KB exit-criteria threshold:")
            for g in under_30kb:
                print(f"  - {g['company_id']}: {g['size_kb']} KB")
        else:
            print("All generated tearsheets are >= 30 KB (exit criteria met).")


if __name__ == "__main__":
    main()  