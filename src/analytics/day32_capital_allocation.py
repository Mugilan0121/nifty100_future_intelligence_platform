"""
Day 32 — Capital Allocation Report

1. Verifies output/capital_allocation.csv (from Sprint 2) against the
   known 92-company universe — investigates the 100-vs-92 discrepancy
   flagged on Day 31, and checks year coverage per company.
2. Generates a distribution summary: count of companies per pattern
   for the latest year.
3. Confirms cashflow_intelligence.xlsx already has a capital_allocation_label
   column (added Day 31) — no action needed if so.
4. Builds output/pattern_changes.csv showing companies whose pattern
   changed year-over-year.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to the project database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def year_num_flexible(y):
    """Parses a year value in any known format into a sortable numeric form."""
    s = str(y).strip()
    m = re.search(r"(\d{4})$", s)
    if m:
        return int(m.group(1))
    m2 = re.search(r"-(\d{2})$", s)
    if m2:
        return 2000 + int(m2.group(1))
    return None


def main():
    """Computes capital allocation patterns for all companies and writes the output CSV."""
    conn = get_connection()
    companies = pd.read_sql_query("SELECT id AS company_id FROM companies", conn)
    conn.close()

    known_ids = set(companies["company_id"])
    print(f"Known universe: {len(known_ids)} companies")

    cap_alloc_path = OUTPUT_DIR / "capital_allocation.csv"
    cap_alloc = pd.read_csv(cap_alloc_path)

    # Fix known ticker typo: capital_allocation.csv has "AGTL" where every
    # other table correctly uses "ATGL" (Adani Total Gas) — letters transposed.
    typo_fixes = {"AGTL": "ATGL"}
    n_fixed = (cap_alloc["company_id"].isin(typo_fixes)).sum()
    if n_fixed:
        print(f"Fixing {n_fixed} row(s) with ticker typo AGTL -> ATGL")
    cap_alloc["company_id"] = cap_alloc["company_id"].replace(typo_fixes)

    cap_alloc["year_num"] = cap_alloc["year"].apply(year_num_flexible)

    cap_ids = set(cap_alloc["company_id"])
    print(f"capital_allocation.csv: {len(cap_ids)} unique company_ids, {len(cap_alloc)} rows")

    extra_ids = cap_ids - known_ids
    missing_ids = known_ids - cap_ids

    print(f"\n=== Extra company_ids in capital_allocation.csv NOT in companies table ({len(extra_ids)}) ===")
    if extra_ids:
        extra_rows = cap_alloc[cap_alloc["company_id"].isin(extra_ids)]
        print(extra_rows.groupby("company_id").size().to_string())
        print("\nSample rows for extra ids:")
        print(extra_rows.head(10).to_string(index=False))
    else:
        print("(none)")

    print(f"\n=== Known companies MISSING from capital_allocation.csv ({len(missing_ids)}) ===")
    print(sorted(missing_ids) if missing_ids else "(none)")

    # Year coverage check for the 92 known companies
    print("\n=== Year coverage per known company (row count) ===")
    known_cap = cap_alloc[cap_alloc["company_id"].isin(known_ids)]
    coverage = known_cap.groupby("company_id").size().reset_index(name="row_count")
    print(f"Row count distribution:\n{coverage['row_count'].describe()}")
    low_coverage = coverage[coverage["row_count"] < 5]
    if not low_coverage.empty:
        print(f"\nCompanies with fewer than 5 years of capital allocation data ({len(low_coverage)}):")
        print(low_coverage.to_string(index=False))

    # ------------------------------------------------------------------
    # Distribution summary — latest year per company
    # ------------------------------------------------------------------
    latest_per_company = (
        known_cap.dropna(subset=["year_num"])
        .sort_values("year_num")
        .groupby("company_id", as_index=False)
        .tail(1)
    )
    print(f"\n=== Pattern distribution — latest year ({len(latest_per_company)} companies) ===")
    dist = latest_per_company["pattern_label"].value_counts()
    print(dist.to_string())

    dist_path = OUTPUT_DIR / "capital_allocation_distribution.csv"
    dist.rename_axis("pattern_label").reset_index(name="company_count").to_csv(dist_path, index=False)
    print(f"\nWrote distribution summary -> {dist_path}")

    # ------------------------------------------------------------------
    # Pattern changes year-over-year
    # ------------------------------------------------------------------
    changes = []
    for company_id, group in known_cap.dropna(subset=["year_num"]).groupby("company_id"):
        group = group.sort_values("year_num")
        patterns = group["pattern_label"].tolist()
        years = group["year_num"].tolist()
        for i in range(1, len(patterns)):
            if patterns[i] != patterns[i - 1]:
                changes.append({
                    "company_id": company_id,
                    "year": years[i],
                    "previous_pattern": patterns[i - 1],
                    "new_pattern": patterns[i],
                })

    changes_df = pd.DataFrame(changes)
    changes_path = OUTPUT_DIR / "pattern_changes.csv"
    changes_df.to_csv(changes_path, index=False)
    print(f"\nWrote {len(changes_df)} pattern-change events -> {changes_path}")

    # ------------------------------------------------------------------
    # Confirm cashflow_intelligence.xlsx already has capital_allocation_label
    # ------------------------------------------------------------------
    cfi_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    if cfi_path.exists():
        cfi = pd.read_excel(cfi_path)
        if "capital_allocation_label" in cfi.columns:
            print(f"\ncashflow_intelligence.xlsx already has capital_allocation_label "
                  f"(added Day 31) — {cfi['capital_allocation_label'].notna().sum()} non-null of {len(cfi)} rows.")
        else:
            print("\nWARNING: capital_allocation_label column missing from cashflow_intelligence.xlsx")
    else:
        print("\nWARNING: cashflow_intelligence.xlsx not found — run Day 31's script first.")


if __name__ == "__main__":
    main()